import csv
import logging
from pathlib import Path

import click
from pkg_resources import resource_string
from string import Template

from cid.base import CidBase
from cid.helpers import Athena, CUR
from cid.utils import get_parameter
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

class AccountMap(CidBase):
    defaults = {
        'MetadataTableNames': ['acc_metadata_details', 'organisation_data']
    } 
    _clients = dict()
    _accounts = list()
    _metadata_source: str = None
    _AthenaTableName: str = None
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

    def __init__(self, session) -> None:
        super().__init__(session)

    @property
    def athena(self) -> Athena:
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': Athena(self.session)
            })
        return self._clients.get('athena')
    
    @athena.setter
    def athena(self, client) -> Athena:
        if not self._clients.get('athena'):
            self._clients.update({
                'athena': client
            })
        return self.athena

    @property
    def cur(self) -> CUR:
        return self._clients.get('cur')
    
    @cur.setter
    def cur(self, client) -> CUR:
        if not self._clients.get('cur'):
            self._clients.update({
                'cur': client
            })
        return self.cur

    @property
    def accounts(self) -> dict:
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
    
    def create(self, name) -> bool:
        """Create account map"""
        
        print(f'\nCreating {name}...')
        logger.info(f'Creating account mapping "{name}"...')
        try:
            if self.accounts:
                logger.info('Account information found, skipping autodiscovery')
                raise Exception
            if not self._AthenaTableName:
                # Autodiscover
                print('\tautodiscovering...', end='')
                logger.info('Autodiscovering metadata table...')
                tables = self.athena.list_table_metadata()
                tables = [t for t in tables if t.get('TableType') == 'EXTERNAL_TABLE']
                tables = [t for t in tables if t.get('Name') in self.defaults.get('MetadataTableNames')]
                if not len(tables):
                    logger.info('Metadata table not found')
                    print('account metadata not detected')
                    raise Exception
                table = next(iter(tables))
                logger.info(f"Detected metadata table {table.get('Name')}")
                accounts = table.get('Columns')
                field_found = [v.get('Name') for v in accounts]
                field_required = list(self.mappings.get(name).get(table.get('Name')).values())
                logger.info(f"Detected fields: {field_found}")
                logger.info(f"Required fields: {field_required}")
                # Check if we have all the required fields
                if all(v in field_found for v in field_required):
                    logger.info('All required fields found')
                    self._AthenaTableName = table.get('Name')
                else:
                    logger.info('Missing required fields')
            if self._AthenaTableName:
                # Query path
                view_definition = self.athena._resources.get('views').get(name, dict())
                view_file = view_definition.get('File')

                template = Template(resource_string(view_definition.get('providedBy'), f'data/queries/{view_file}').decode('utf-8'))

                # Fill in TPLs
                columns_tpl = dict()
                parameters = {
                    'metadata_table_name': self._AthenaTableName,
                    'cur_table_name': self.cur.tableName
                }
                columns_tpl.update(**parameters)
                for k,v in self.mappings.get(name).get(self._AthenaTableName).items():
                    logger.info(f'Mapping field {k} to {v}')
                    columns_tpl.update({k: v})
                compiled_query = template.safe_substitute(columns_tpl)
                print('compiled view.')
            else:
                logger.info('Metadata table not found')
                print('account metadata not detected')
                raise Exception
        except:
            # TODO: Handle exceptions
            compiled_query = self.create_account_mapping_sql(name)

        # Execute query
        click.echo('\tcreating view...', nl=False)
        query_id = self.athena.execute_query(sql_query=compiled_query)
        # Get results as list
        response = self.athena.get_query_results(query_id)
        click.echo('done')

    def get_dummy_account_mapping_sql(self, name) -> list:
        """Create dummy account mapping"""
        logger.info(f'Creating dummy account mapping for {name}')
        template = Template(resource_string(
            package_or_requirement='cid.builtin.core',
            resource_name='data/queries/shared/account_map_dummy.sql',
        ).decode('utf-8'))
        columns_tpl = {
            'athena_view_name': name,
            'cur_table_name': self.cur.tableName
        }
        compiled_query = template.safe_substitute(columns_tpl)
        return compiled_query

    def get_organization_accounts(self) -> list:
        """ Retreive AWS Organization account """
        # Init clients
        orgs = self.session.client('organizations')
        try:
            paginator = orgs.get_paginator('list_accounts')
            page_iterator = paginator.paginate()
            accounts = list()
            for page in page_iterator:
                for account in page['Accounts']:
                    accounts.append({
                        'account_id': account.get('Id'),
                        'account_name': account.get('Name'),
                        'account_status': account.get('Status'),
                        'account_email': account.get('Email')
                    })
        except orgs.exceptions.AWSOrganizationsNotInUseException:
            print('AWS Organization is not enabled')
        except orgs.exceptions.AccessDeniedException:
            print('no access.')
        except Exception as e:
            print(e)
        finally:
            return accounts

    def check_file_exists(self, file_path) -> bool:
        """ Checks if the givven file exists """
        # Set base paths
        abs_path = Path().absolute()

        return Path.is_file(abs_path / file_path)

    def get_csv_accounts(self, file_path) -> list:
        """ Retreive accounts from CSV file """
        with open(file_path) as f:
            accounts = [{str(k).lower().replace(" ", "_"): str(v) for k, v in row.items()}
                        for row in csv.DictReader(f, skipinitialspace=True)]

        return accounts


    def select_metadata_collection_method(self) -> str:
        """ Selects the method to collect metadata """
        logger.info('Metadata source selection')
        # Ask user which method to use to retreive account list
        account_map_sources = {
            'CSV file (relative path required)': 'csv',
            'AWS Organizations (one time account listing)': 'organization',
            'Dummy (CUR account data, no names)': 'dummy',
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
                finished = self.check_file_exists(mapping_file)
                if not finished:
                    click.echo('File not found, ', nl=False)
            click.echo('\nCollecting account info...', nl=False)
            self._accounts = self.get_csv_accounts(mapping_file)
            logger.info(f'Found {len(self._accounts)} accounts')
            click.echo(f' {len(self.accounts)} collected')
        elif self._metadata_source == 'organization':
            click.echo('\nCollecting account info...', nl=False)
            self._accounts = self.get_organization_accounts()
            logger.info(f'Found {len(self._accounts)} accounts')
            click.echo(f' {len(self.accounts)} collected')
        elif self._metadata_source == 'dummy':
            click.echo('Notice: Dummy account mapping will be created')
        else:
            print('Unsupported selection')
            return False

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
        accounts_sql = list()
        for account in self.accounts:
            acc = account.copy()
            account_name = acc.pop('account_name').replace("'", "''")
            accounts_sql.append(
                """ROW ('{account_id}', '{account_name}:{account_id}', '{parent_account_id}', '{account_status}', '{account_email}')""".format(account_name=account_name, **acc))
        # Fill in TPLs
        columns_tpl = {
            'athena_view_name': name,
            'rows': ','.join(accounts_sql)
        }
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query
