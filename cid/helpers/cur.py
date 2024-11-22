""" Manage AWS CUR
"""
import json
import logging
from abc import abstractmethod

from cid.base import CidBase
from cid.utils import get_parameter, get_parameters, set_parameters, cid_print
from cid.exceptions import CidCritical
from cid.helpers.cur_proxy import ProxyView

from tqdm import tqdm

logger = logging.getLogger(__name__)


class AbstractCUR(CidBase):
    """ Manage AWS CUR
    """
    # Must be both CUR1 and 2 compatible
    cur_minimal_required_columns = [
        'bill_bill_type',
        'bill_billing_entity',
        'bill_billing_period_end_date',
        'bill_billing_period_start_date',
        'bill_invoice_id',
        'bill_payer_account_id',
        'identity_line_item_id',
        'identity_time_interval',
        'line_item_legal_entity',
        'line_item_line_item_description',
        'line_item_line_item_type',
        'line_item_operation',
        'line_item_product_code',
        'line_item_unblended_cost',
        'line_item_usage_account_id',
        'line_item_usage_amount',
        'line_item_usage_end_date',
        'line_item_usage_start_date',
        'line_item_usage_type',
        'pricing_term',
        'pricing_unit',
    ]
    ri_required_columns = [
        'reservation_reservation_a_r_n',
        'reservation_effective_cost',
        'reservation_start_time',
        'reservation_end_time',
        'pricing_lease_contract_length',
        'pricing_offering_class',
        'pricing_purchase_option'
    ]
    sp_required_columns = [
        'savings_plan_savings_plan_a_r_n',
        'savings_plan_savings_plan_effective_cost',
        'savings_plan_start_time',
        'savings_plan_end_time',
        'savings_plan_purchase_term',
        'savings_plan_offering_type',
        'savings_plan_payment_option'
    ]
    _metadata = None
    _database = None

    def __init__(self, athena, glue):
        self.athena = athena
        self.glue = glue
        self.proxy = None

    @property
    def database(self) -> str:
        """get Athena database of CUR """
        if self.metadata is None: # Need explicit call of metadata. Do not remove this line
            raise CidCritical('Error: Cannot detect any CUR table. Hint: Check if AWS Lake Formation is activated on your account, verify that the LakeFormationEnabled parameter is set to yes on the deployment stack')
        return self._database

    @property
    def table_name(self) -> str:
        """ Get Athena table name """
        if self.metadata is None: # Need explicit call of metadata. Do not remove this line
            raise CidCritical('Error: Cannot detect any CUR table. Hint: Check if AWS Lake Formation is activated on your account, verify that the LakeFormationEnabled parameter is set to yes on the deployment stack')
        return self.metadata.get('Name')

    @property
    def has_resource_ids(self) -> bool:
        """ Return True if CUR has resource ids """
        return 'line_item_resource_id' in self.fields

    @property
    def has_reservations(self) -> bool:
        """ Return True if CUR has reservation fields """
        return all(col in self.fields for col in self.ri_required_columns)

    @property
    def has_savings_plans(self) -> bool:
        """ Return True if CUR has savings plan """
        return all(col in self.fields for col in self.sp_required_columns)

    @property
    def version(self) -> str:
        """ Return version of CUR """
        return '2' if 'bill_payer_account_name' in self.fields else '1'

    def get_type_of_column(self, column: str, version=None):
        """ Return an Athena type of a given non existent CUR column """
        if column.startswith('cost_category_') or column.startswith('resource_tags_'):
            return 'STRING'
        for ending in ['_cost', '_factor', '_quantity', '_fee', '_amount', '_discount', '_usage', '_usage_ratio']:
            if column.endswith(ending):
                return 'DOUBLE'
        if column.endswith('_date') and not column.endswith('_to_date'):
            return 'TIMESTAMP'
        if column.endswith('_time') and (version or self.version) == '2':
            return 'STRING' # yes, they are string
        special_cases = {
            "cost_category": "MAP",
            "discount": "MAP",
            "product": "MAP",
            "resource_tags": "MAP",
            "reservation_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_unused_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_upfront_value": "DOUBLE",
            "reservation_net_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_net_unused_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_net_upfront_value": "DOUBLE",
            "savings_plan_total_commitment_to_date": "DOUBLE",
            "savings_plan_savings_plan_rate": "DOUBLE",
            "savings_plan_used_commitment": "DOUBLE",
            "savings_plan_amortized_upfront_commitment_for_billing_period": "DOUBLE",
            "savings_plan_net_amortized_upfront_commitment_for_billing_period": "DOUBLE",
            "savings_plan_recurring_commitment_for_billing_period": "DOUBLE",
        }
        return special_cases.get(column, 'STRING')

    def column_exists(self, column:  str):
        return column.lower() in [col.lower() for col in self.fields]

    def ensure_columns(self, columns):
        if not isinstance(columns, list):
            logger.debug(f'{columns} must be list')
            return
        for column in columns:
            self.ensure_column(column)

    @abstractmethod
    def ensure_column(self, column: str, column_type: str=None):
        """ Ensure column is in the cur. If it is not there - add column """
        pass

    def table_is_cur(self, table: dict=None, name: str=None, return_reason: bool=False) -> bool:
        """ return cur version if table metadata fits CUR definition. """
        try:
            table = table or self.athena.get_table_metadata(name)
        except Exception as exc: #pylint: disable=broad-exception-caught
            logger.warning(exc)
            return False if not return_reason else (False, f'cannot get table {name}. {exc}.')

        table_name = table.get('Name')
        columns = [col.get('Name') for col in table.get('Columns')]
        missing_columns = [col for col in self.cur_minimal_required_columns if col not in columns]
        logger.debug(f'missing_columns={missing_columns}')
        if missing_columns:
            return False if not return_reason else (False, f"Table {table_name} does not contain columns: {','.join(missing_columns)}. You can try ALTER TABLE {table_name} ADD COLUMNS (missing_column string).")

        version = '1'
        if 'bill_payer_account_name' in columns:
            version = '2'
        return version if not return_reason else (True, 'all good')

    @property
    def fields(self) -> list:
        """get CUR fields """
        return [col.get('Name') for col in (self.metadata.get('Columns', []) + self.metadata.get('PartitionKeys', []))]

    @property
    def tag_and_cost_category_fields(self) -> list:
        """ Returns all tags and cost category fields. """
        if self.version == '1':
            return [field for field in self.fields if field.startswith('resource_tags_user_') or field.startswith('cost_category_')]
        elif self.version == '2':
            raise NotImplemented('Need to run a query to get all fields of resource_tags')
        else:
            raise NotImplemented('cur version not known')


class CUR(AbstractCUR):
    """This Class represents CUR table (1 or 2 versions)"""

    def __init__(self, athena, glue):
        super().__init__(athena, glue)

    @property
    def metadata(self) -> dict:
        """get Athena metadata for the table of CUR """
        if self._metadata:
            return self._metadata
        self._database, self._metadata = self.find_cur()
        # good place to set a database for athena
        return self._metadata

    def find_cur(self):
        """Choose CUR"""
        metadata = None
        cur_database = get_parameters().get('cur-database')
        if get_parameters().get('cur-table-name'):
            table_name = get_parameters().get('cur-table-name')
            try:
                metadata = self.athena.get_table_metadata(table_name, cur_database)
            except self.athena.client.exceptions.MetadataException as exc:
                raise CidCritical(f'Provided cur-table-name "{table_name}" in database "{cur_database or self.athena.DatabaseName}" is not found. Please make sure the table exists.') from exc
            res, message = self.table_is_cur(table=metadata, return_reason=True)
            if not res:
                raise CidCritical(f'Table {table_name} does not look like CUR. {message}')
            return cur_database or self.athena.DatabaseName, metadata

        all_cur_tables = []
        if cur_database:
            cur_databases = [cur_database]
        else:
            cur_databases = list(self.athena.list_databases()) # user have not provided the cur database
        for database in tqdm(cur_databases, desc='Fining CUR in Athena Databases'):
            try:
                tables = self.athena.find_tables_with_columns(
                    columns=self.cur_minimal_required_columns,
                    database_name=database,
                )
                all_cur_tables += [(database, table) for table in tables]
            except self.athena.client.exceptions.AccessDenied:
                logger.info(f'Cannot read from athena database {database}')

        if not all_cur_tables:
            # FIXME : distinguish a case where we have NONE tables in any database. This might be because
            raise CidCritical(
                f'CUR table not found in {self.athena.region}. We need a least one table with these columns: {self.cur_minimal_required_columns}.'
                 ' Please make sure you created cur and created Athena table, preferably with CID Cloud Formation stack.'
                 ' Also if you have AWS Lake Formation, the user running the tool might need additional permissions'
            )
        databases = set([database for database, _ in all_cur_tables])
        if len(databases) > 1:
            choices = dict(sorted([(f'{database}.{tab}', (database, tab)) for database, tab in all_cur_tables], reverse=True))
        else:
            choices = dict(sorted([(f'{tab}', (database, tab)) for database, tab in all_cur_tables], reverse=True))
        if not choices:
            choices['<CREATE CUR TABLE AND CRAWLER>'] = '<CREATE CUR TABLE AND CRAWLER>'
        answer =  get_parameter(
            param_name='cur-table-name-and-db',
            message="Please select CUR table",
            choices=choices,
        )
        if answer == '<CREATE CUR TABLE AND CRAWLER>':
            raise CidCritical('CUR creation was requested') # to be captured in common.py
        database, table = answer
        set_parameters({'cur-table-name': table,'cur-database': database, })
        return database, self.athena.get_table_metadata(table, database_name=database)

    def ensure_column(self, column: str, column_type: str=None):
        """ Ensure column is in the cur. If it is not there - add column """
        column = column.lower()
        column = column.split('[')[0]
        if self.column_exists(column):
            return
        logger.trace(f'trying to add to CUR following column: {column}')
        table_can_be_updated = False
        # Check Crawler Behavior - if it has a Configuration/CrawlerOutput/TablesAddOrUpdateBehavior != MergeNewColumns, it will override columns
        crawler_name = self.metadata.get('Parameters', {}).get('UPDATED_BY_CRAWLER')
        if crawler_name:
            try:
                crawler = self.glue.get_crawler(crawler_name)
                config = json.loads(crawler.get('Configuration', '{}'))
                add_or_update = config.get('CrawlerOutput', {}).get('Tables', {}).get('AddOrUpdateBehavior')
                if add_or_update == 'MergeNewColumns':
                    table_can_be_updated = True
            except self.glue.client.exceptions.ClientError as exc:
                logger.debug(f'Failed to get crawler info: {exc}')
        if table_can_be_updated:
            column_type = column_type or self.get_type_of_column(column)
            try:
                self.athena.query(f'ALTER TABLE {self.table_name} ADD COLUMNS ({column} {column_type})', database=self.database)
            except (self.athena.client.exceptions.ClientError, CidCritical) as exc:
                raise CidCritical(f'Column {column} is not found in CUR and we were unable to add it. Please check FAQ.') from exc
            # table takes time to update so just adding column to cached data
            self._metadata.get('Columns', []).append({'Name': column, 'Type': column_type})
            cid_print(f"Column '{column}' was added to CUR ({self.table_name}).")
            return

        # if table cannot be updated, check if it is ri/sp case - let's hope dashboard views can handle it:
        if column in self.sp_required_columns + self.ri_required_columns:
            logger.warn(f"Column '{column}' is not present in ({self.table_name}). Will try to continue without.")
            return

        # if a required column is not there and not ri/sp -> stop
        logger.warning(f"Column '{column}' is not in CUR ({self.table_name}).")



class ProxyCUR(AbstractCUR):
    """ Cur Proxy behaves as CUR (1 or 2) but actually is a proxy view in Athena
    """
    def __init__(self, cur, target_cur_version):
        self.proxy = []
        self.cur = cur
        self.target_cur_version = target_cur_version
        super().__init__(cur.athena, cur.glue)

    @property
    def database(self) -> str:
        return self.athena.DatabaseName # use CID database for proxy view

    @property
    def metadata(self) -> dict:
        """get Athena metadata for the view of CUR """
        if self._metadata:
            return self._metadata
        self.cur = CUR(self.athena, self.glue)
        if self.cur.version != self.target_cur_version:
            cid_print(f'CUR{self.cur.version} ({self.athena.DatabaseName}.{self.cur.table_name}) provided but {self.target_cur_version} is needed. CUR Proxy view will be used.')
        self.proxy = ProxyView(cur=self.cur, target_cur_version=self.target_cur_version)
        try:
            self._metadata = self.athena.get_table_metadata(self.proxy.name)
        except self.athena.client.exceptions.MetadataException: # if no table - create it
            self.proxy.create_or_update_view()
            self._metadata = self.athena.get_table_metadata(self.proxy.name)

        return self._metadata

    def ensure_columns(self, columns):
        if not self.metadata:# To make sure metadata exists
            raise RuntimeError('No metadata')
        if isinstance(columns, list):
            if all(self.proxy.column_surely_exist(col) for col in columns):
                return
            if self.cur.metadata.get('TableType') == 'EXTERNAL_TABLE':
                try:
                    equivalent_columns = sum([self.proxy.source_column_equivalents(col) for col in columns], [])
                    logger.trace(f'equivalent_columns = {dict(zip(columns,equivalent_columns))}')
                    self.cur.ensure_columns(list(set(equivalent_columns)))
                    # add field from underlying cur to the proxy
                    for item in self.cur._metadata.get('Columns', []):
                        for existing_item in self._metadata.get('Columns', []):
                            if item['Name'] == existing_item['Name']:
                                break
                        else: # if not found
                            self._metadata.get('Columns', []).append(item)
                except Exception as exc:
                    logger.exception(exc)
            for column in columns:
                self.proxy.fields_to_expose.append(column)
            self.proxy.create_or_update_view()
