""" Create an Account Map

Account Map is needed for mapping account id to account name and other attributes (Business Unit, Scope, Cost Center or other)
"""
import os
import logging
from pathlib import Path
from functools import lru_cache

from string import Template
from pkg_resources import resource_string

from cid.base import CidBase
from cid.helpers import Athena, CUR
from cid.utils import get_parameter, get_parameters, cid_print, unset_parameter
from cid.exceptions import CidCritical, CidError
from cid.helpers.csv2view import read_csv

logger = logging.getLogger(__name__)

class AccountMap(CidBase):
    """
    Create an account_map view or aws_accounts view with following mandatory fields:
        account_id
        account_name
        parent_account_id (only used in trends)
        account_status (only used in trends)
        account_email (only used in trends)

    aws_accounts is only used in trends.
    """
    defaults = {
        'MetadataTableNames': ['acc_metadata_details', 'organisation_data']
    }
    _clients = {}
    _accounts = []
    _metadata_source: str = None
    _athena_table_name: str = None
    mappings = {
        'account_map': {
            'acc_metadata_details': {'account_id': 'account_id', 'account_name': 'account_name'},
            'organisation_data': {'account_id': 'id', 'account_name': 'name', 'email': 'email'}
        },
        'aws_accounts': {
            'acc_metadata_details': {'account_id': 'account_id', 'account_name': 'account_name', 'email': 'email'},
            'organisation_data': { 'account_id': 'id', 'account_name': 'name', 'email': 'email', 'status': 'status'},
            'cur_fields': ['bill_payer_account_id']
        }
    }


    @property
    def athena(self) -> Athena:
        """ Getter for Athena """
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': Athena(self.session)
            })
        return self._clients.get('athena')

    @athena.setter
    def athena(self, client) -> Athena:
        """ Setter for Athena """
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': client
            })
        return self.athena

    @property
    def cur(self) -> CUR:
        """ Getter for CUR """
        return self._clients.get('cur')

    @cur.setter
    def cur(self, client) -> CUR:
        """ Setter for CUR """
        if not self._clients.get('cur'):
            self._clients.update({
                'cur': client
            })
        return self.cur

    @property
    def accounts(self) -> dict:
        """ Get Accounts with the right mapping """
        if self._accounts:
            # Required keys mapping, used in renaming below
            key_mapping = {
                'accountid': 'account_id',
                'name': 'account_name'
            }
            for account in self._accounts:
                # Rename required keys according to expected names
                for old_key, new_key in key_mapping.items():
                    if not account.get(new_key) and account.get(old_key):
                        account[new_key] = account[old_key]
                        del account[old_key]
                # Fill optional keys
                account.update({
                    'parent_account_id': account.get('parent_account_id', '0'),
                    'account_status': account.get('account_status', 'unknown'),
                    'account_email': account.get('account_email', 'unknown')
                })
        return self._accounts

    @lru_cache(1000)
    def detect_metadata_table(self, name):
        """ detect meta table with the list of accounts """
        cid_print('Autodiscovering metadata table')

        # FIXME: This will only work for current Athena Database. We might want to check optimization_data base as well
        tables = self.athena.list_table_metadata()
        tables = [t for t in tables if t.get('TableType') == 'EXTERNAL_TABLE'] #filter only tables
        tables = [t for t in tables if t.get('Name') in self.defaults.get('MetadataTableNames')] #filter only with support names
        if not tables:
            cid_print('Account metadata not detected')
            return None
        for table in tables:
            table_name = table.get('Name')
            logger.debug(f"Detected table {table_name}")
            field_found = [col.get('Name') for col in table.get('Columns')]
            field_required = list(self.mappings.get(name).get(table_name).values())
            # Check if we have all the required fields
            if all(field in field_found for field in field_required):
                logger.info(f'All required fields found in {table_name} ')
                return table.get('Name')
            logger.info('Missing required fields')
            logger.info(f"Detected fields: {field_found}")
            logger.info(f"Required fields: {field_required}")
        return None


    def create(self, name) -> bool:
        """Create account map"""

        cid_print(f'Creating account mapping <BOLD>{name}<END>')
        try:
            if self.accounts:
                logger.info('Account information found, skipping autodiscovery')
                raise CidError('Account information found, skipping autodiscovery')
            if get_parameters().get('account-map-source'):
                raise CidError('Skipping autodiscovery')

            self._athena_table_name = self.detect_metadata_table(name)
            if not self._athena_table_name:
                raise CidError('Metadata table not found')

            # Query path
            view_definition = self.athena._resources.get('views').get(name, {})
            if view_definition.get('File'):
                view_file = view_definition.get('File')
                template = Template(resource_string(view_definition.get('providedBy'), f'data/queries/{view_file}').decode('utf-8'))
            elif view_definition.get('data'):
                template = Template(str(view_definition.get('data')))
            else:
                raise CidError(f'{name} definition does not contain File or data: {view_definition}')

            # Fill in TPLs
            columns_tpl = {
                'metadata_table_name': self._athena_table_name,
                'cur_table_name': self.cur.table_name # only for trends
            }
            for key, val in self.mappings.get(name).get(self._athena_table_name).items():
                logger.debug(f'Mapping field {key} to {val}')
                columns_tpl[key] = val
            compiled_query = template.safe_substitute(columns_tpl)
            logger.debug('compiled view.')

        except CidError as exc:
            logger.info(exc)
            compiled_query = self.create_account_mapping_sql(name)

        # Execute query
        cid_print('Creating Athena view')
        self.athena.query(compiled_query)
        cid_print(f'Created account mapping <BOLD>{name}<END>')

    def get_dummy_account_mapping_sql(self, name) -> list:
        """Create dummy account mapping"""
        logger.info(f'Creating dummy account mapping for {name}')
        template = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name='data/queries/shared/account_map_dummy.sql',
        ).decode('utf-8'))
        columns_tpl = {
            'athena_view_name': name,
            'cur_table_name': self.cur.table_name
        }
        compiled_query = template.safe_substitute(columns_tpl)
        return compiled_query

    def get_organization_accounts(self) -> list:
        """ Retrieve AWS Organization account """
        # Init clients
        accounts = []
        orgs = self.session.client('organizations')
        try:
            for page in orgs.get_paginator('list_accounts').paginate():
                for account in page['Accounts']:
                    accounts.append({
                        'account_id': account.get('Id'),
                        'account_name': account.get('Name'),
                        'account_status': account.get('Status'), #Only for Trends
                        'account_email': account.get('Email'), #Only for Trends
                    })
        except orgs.exceptions.AWSOrganizationsNotInUseException:
            cid_print('AWS Organization is not enabled')
        except orgs.exceptions.AccessDeniedException:
            cid_print('No access to AWS Organization.')
        except Exception as exc: #pylint: disable=broad-exception-caught
            cid_print(exc)

        return accounts

    def check_file_exists(self, file_path) -> bool:
        """ Checks if the given file exists """
        # Set base paths
        abs_path = Path().absolute()

        return Path.is_file(abs_path / file_path)

    def get_csv_accounts(self, file_path) -> list:
        """ Retrieve accounts from CSV file """
        accounts = [
            {str(k).lower().replace(" ", "_"): str(v) for k, v in row.items()}
            for row in read_csv(file_path)
        ]

        return accounts


    def select_metadata_collection_method(self) -> str:
        """ Selects the method to collect metadata """
        logger.info('Metadata source selection')
        # Ask user which method to use to retrieve account list
        account_map_sources = {
            'Dummy (CUR account data, no names)': 'dummy',
            'AWS Organizations (one time account listing)': 'organization',
            'CSV file (relative path required)': 'csv',
        }
        selected_source = get_parameter(
            param_name='account-map-source',
            message="Please select account metadata collection method",
            choices=account_map_sources,
        )
        logger.info(f'Selected {selected_source}')
        self._metadata_source = selected_source

        # Collect account list from different sources of user choice
        if self._metadata_source == 'csv':
            finished = False
            while not finished:
                mapping_file = get_parameter(
                    param_name='account-map-file',
                    message="Enter file path",
                )
                mapping_file = os.path.expanduser(mapping_file)
                finished = self.check_file_exists(mapping_file)
                if not finished:
                    cid_print(f'File not found: {mapping_file}')
                    unset_parameter('account-map-file')
            cid_print(f'\nReading {mapping_file}')
            self._accounts = self.get_csv_accounts(mapping_file)
            cid_print(f'{len(self.accounts)} accounts collected')
        elif self._metadata_source == 'organization':
            cid_print('\nCollecting account info from AWS Organizations')
            self._accounts = self.get_organization_accounts()
            cid_print(f'{len(self.accounts)} accounts collected')
        elif self._metadata_source == 'dummy':
            cid_print('Notice: Dummy account mapping will be created.')
        else:
            cid_print('Unsupported selection')

    def create_account_mapping_sql(self, name) -> str:
        """ Returns account mapping Athena query """
        for attempt in range(3):
            if self.accounts or self._metadata_source == 'dummy':
                break
            self.select_metadata_collection_method()
            logger.info(f'Attempt {attempt + 2}' )
        else:
            raise CidCritical('Failed to create account map')

        if self._metadata_source == 'dummy':
            return self.get_dummy_account_mapping_sql(name)

        template_str = '''CREATE OR REPLACE VIEW  ${athena_view_name} AS
            SELECT
                *
            FROM
                ( VALUES ${rows} )
            ignored_table_name (account_id, account_name, parent_account_id, account_status, account_email)
        '''
        template = Template(template_str)
        accounts_sql = []
        row_template = """ROW ('{account_id}', '{account_name}:{account_id}', '{parent_account_id}', '{account_status}', '{account_email}')"""
        for account in self.accounts:
            acc = account.copy()
            account_name = acc.pop('account_name').replace("'", "''")
            accounts_sql.append(row_template.format(account_name=account_name, **acc))
        # Fill in TPLs
        columns_tpl = {
            'athena_view_name': name,
            'rows': ','.join(accounts_sql)
        }
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query
