import csv
from pathlib import Path
import questionary
import click
from pkg_resources import resource_string
from string import Template
from cid.helpers import Athena, CUR

class AccountMap():
    defaults = {
        'AthenaTableName': 'acc_metadata_details'
    }
    _clients = dict()
    _accounts = list()
    mappings = {
        'account_map': {
            'metadata_fields': 'account_id, account_name'
        },
        'aws_accounts': {
            'metadata_fields': 'account_id, account_name, email',
            'cur_fields': 'bill_payer_account_id'
        }
    }

    def __init__(self, session=None) -> None:
        self.session = session

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
        if not self._accounts:
            # Ask user which method to use to retreive account list
            selection = list()
            account_map_sources = {
                'csv': 'CSV file (relative path required)',
                'organization': 'AWS Organizations (one time account listing)',
                'dummy': 'Dummy (creates dummy account mapping)'
            }
            for k,v in account_map_sources.items():
                selection.append(
                        questionary.Choice(
                            title=f'{v}',
                            value=k
                        )
                    )
            selected_source=questionary.select(
                "\nWhich method would you like to use for collecting an account list ?",
                choices=selection
            ).ask()

            # Collect account list from different sources of user choice
            if selected_source == 'csv':
                finished = False
                while not finished:
                    mapping_file = click.prompt("Enter file path", type=str)
                    finished = self.check_file_exists(mapping_file)
                    if not finished:
                        click.echo('File not found, ', nl=False)
                click.echo('\nCollecting account info...', nl=False)
                self._accounts = self.get_csv_accounts(mapping_file)
            elif selected_source == 'organization':
                click.echo('\nCollecting account info...', nl=False)
                self._accounts = self.get_organization_accounts()
            elif selected_source == 'dummy':
                click.echo('Notice: Dummy account mapping will be created')
            else:
                raise Exception('Unsupported selection')
            
            click.echo(f'collected accounts: {len(self._accounts)}')
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
    
    def create(self, map_name= str) -> bool:
        """Create account map"""
        
        print(f'\nCreating {map_name}...')
        try:
            # Autodiscover
            print('\tautodiscovering...', end='')
            accounts = self.athena.get_table_metadata(self.defaults.get('AthenaTableName')).get('Columns')
            field_found = [v.get('Name') for v in accounts]
            field_required = self.mappings.get(map_name).get('metadata_fields').replace(" ", "").split(',')
            # Check if we have all the required fields
            if all(v in field_found for v in field_required):
                self._AthenaTableName = self.defaults.get('AthenaTableName')
                # Query path
                view_definition = self.athena._resources.get('views').get(map_name, dict())
                view_file = view_definition.get('File')

                template = Template(resource_string(view_definition.get('providedBy'), f'data/queries/{view_file}').decode('utf-8'))

                # Fill in TPLs
                columns_tpl = dict()
                parameters = {
                    'metadata_table_name': self.defaults.get('AthenaTableName'),
                    'cur_table_name': self.cur.tableName
                }
                columns_tpl.update(**parameters)
                compiled_query = template.safe_substitute(columns_tpl)
                print('compiled view.')
            else:
                print('failed, continuing..')
                compiled_query = self.create_account_mapping_sql(map_name)
        except:
            print('failed, continuing..')
            compiled_query = self.create_account_mapping_sql(map_name)
        finally:
            # Execute query
            click.echo('\tcreating view...', nl=False)
            query_id = self.athena.execute_query(sql_query=compiled_query)
            # Get results as list
            response = self.athena.get_query_results(query_id)
            click.echo('done')


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


    def create_account_mapping_sql(self, mapping_name) -> str:
        """ Returns account mapping Athena query """
        
        template_str = '''CREATE OR REPLACE VIEW  ${athena_view_name} AS
            SELECT
                *
            FROM
                ( VALUES ${rows} )
            ignored_table_name (account_id, account_name, parent_account_id, account_status, account_email)
        '''
        # Wait for account list
        while not self.accounts:
            pass
        template = Template(template_str)
        accounts_sql = list()
        for account in self.accounts:
            accounts_sql.append(
                "ROW ('{account_id}', '{account_name}:{account_id}', '{parent_account_id}', '{account_status}', '{account_email}')".format(**account))
        
        # Fill in TPLs
        columns_tpl = dict()
        parameters = {
            'athena_view_name': mapping_name,
            'rows': ','.join(accounts_sql)
        }
        columns_tpl.update(**parameters)
        compiled_query = template.safe_substitute(columns_tpl)

        return compiled_query
