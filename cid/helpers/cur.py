import json
import logging

from cid.base import CidBase
from cid.helpers import Athena, Glue
from cid.utils import get_parameter, get_parameters
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)


class CUR(CidBase):
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
        'line_item_resource_id',
       #'line_item_resource_id',
        'line_item_unblended_cost',
        'line_item_usage_account_id',
        'line_item_usage_amount',
        'line_item_usage_end_date',
        'line_item_usage_start_date',
        'line_item_usage_type',
        'pricing_term',
        'pricing_unit',
       # 'product_database_engine',
       # 'product_deployment_option',
       # 'product_from_location',
       # 'product_group',
       # 'product_instance_type',
       # 'product_instance_type_family',
       # 'product_operating_system',
       # 'product_product_family',
       # 'product_product_name',
       # 'product_region',
       # 'product_servicecode',
       # 'product_storage',
       # 'product_to_location',
       # 'product_volume_api_name',
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
    _tableName = None
    _metadata = None
    _clients = dict()
    _hasResourceIDs = None
    _hasSavingsPlans = None
    _hasReservations = None
    _configured = None
    _status = str()


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
        return self._clients.get('athena')

    @property
    def glue(self) -> Glue:
        if not self._clients.get('glue'):
            self._clients['glue'] = Glue(self.session)
        return self._clients.get('glue')

    @glue.setter
    def glue(self, client) -> Glue:
        if not self._clients.get('glue'):
            self._clients['glue'] = client
        return self._clients.get('glue')

    @property
    def configured(self) -> bool:
        """ Check if AWS Data Catalog and Athena database exist """
        if self._configured is None:
            if self.athena.CatalogName and self.athena.DatabaseName:
                self._configured = True
            else:
                self._configured = False
        return self._configured

    @property
    def tableName(self) -> str:
        if self.metadata is None:
            raise CidCritical('Error: Cannot detect any CUR table. Hint: Check if AWS Lake Formation is activated on your account, verify that the LakeFormationEnabled parameter is set to yes on the deployment stack')
        return self.metadata.get('Name')

    @property
    def hasResourceIDs(self) -> bool:
        if self._configured and self._hasResourceIDs is None:
            self._hasResourceIDs = 'line_item_resource_id' in self.fields
        return self._hasResourceIDs

    @property
    def hasReservations(self) -> bool:
        if self._configured and self._hasReservations is None:
            logger.debug(f'{self.ri_required_columns}: {[c in self.fields for c in self.ri_required_columns]}')
            self._hasReservations=all([c in self.fields for c in self.ri_required_columns])
            logger.info(f'Reserved Instances: {self._hasReservations}')
        return self._hasReservations

    @property
    def hasSavingsPlans(self) -> bool:
        if self._configured and self._hasSavingsPlans is None:
            logger.debug(f'{self.sp_required_columns}: {[c in self.fields for c in self.sp_required_columns]}')
            self._hasSavingsPlans=all([c in self.fields for c in self.sp_required_columns])
            logger.info(f'Savings Plans: {self._hasSavingsPlans}')
        return self._hasSavingsPlans

    def get_type_of_column(self, column: str):
        """ Return an Athena type of a given non existent CUR column """
        if column.startswith('cost_category_') or column.startswith('resource_tags_'):
            return 'STRING'
        for ending in ['_cost', '_factor', '_quantity', '_fee', '_amount', '_discount']:
            if column.endswith(ending):
                return 'DOUBLE'
        if column.endswith('_date') and not column.endswith('_to_date'):
            return 'TIMESTAMP'
        SPECIAL = {
            "reservation_amortized_upfront_cost_for_usage": "DOUBLE",
            "reservation_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_recurring_fee_for_usage": "DOUBLE",
            "reservation_unused_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_upfront_value": "DOUBLE",
            "reservation_net_amortized_upfront_cost_for_usage": "DOUBLE",
            "reservation_net_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_net_recurring_fee_for_usage": "DOUBLE",
            "reservation_net_unused_amortized_upfront_fee_for_billing_period": "DOUBLE",
            "reservation_net_upfront_value": "DOUBLE",
            "savings_plan_total_commitment_to_date": "DOUBLE",
            "savings_plan_savings_plan_rate": "DOUBLE",
            "savings_plan_used_commitment": "DOUBLE",
            "savings_plan_amortized_upfront_commitment_for_billing_period": "DOUBLE",
            "savings_plan_net_amortized_upfront_commitment_for_billing_period": "DOUBLE",
            "savings_plan_recurring_commitment_for_billing_period": "DOUBLE",
        }
        return SPECIAL.get(column, 'STRING')

    def ensure_column(self, column: str, column_type: str=None):
        """ Ensure column is in the cur. If it is not there - add column """
        column = column.lower()
        if column in [col.get('Name', '').lower() for col in self.metadata.get('Columns', [])]:
            return

        crawler_name = self.metadata.get('Parameters', {}).get('UPDATED_BY_CRAWLER')
        if crawler_name:
            # Check Crawler Behavior - if it does not have a Configuration/CrawlerOutput/TablesAddOrUpdateBehavior == MergeNewColumns, it will override columns
            config = json.loads(self.glue.get_crawler(crawler_name).get('Configuration', '{}'))
            add_or_update = config.get('CrawlerOutput', {}).get('Tables', {}).get('AddOrUpdateBehavior')
            if add_or_update != 'MergeNewColumns':
                raise CidCritical(f'Column {column} is not found in CUR. And we were unable to add it as crawler {crawler_name} is configured to override columns.')

        column_type = column_type or self.get_type_of_column(column)
        try:
            self.athena.query(f'ALTER TABLE {self._tableName} ADD COLUMNS ({column} {column_type})')
        except (self.athena.client.exceptions.ClientError, CidCritical) as exc:
            raise CidCritical(f'Column {column} is not found in CUR and we were unable to add it. Please check FAQ.') from exc
        self._metadata = self.athena.get_table_metadata(self._tableName) # refresh table metadata
        logger.critical(f"Column '{column}' was added to CUR ({self._tableName}). Please make sure crawler do not override that columns. Crawler='{crawler_name}'")

    def table_is_cur(self, table: dict=None, name: str=None, return_reason: bool=False) -> bool:
        """ return True if table metadata fits CUR definition. """
        try:
            table = table or self.athena.get_table_metadata(name)
        except Exception as exc:
            logger.debug(exc)
            return False if not return_reason else (False, f'cannot get table {name}. {exc}.')

        table_name = table.get('Name')
        columns = [cols.get('Name') for cols in table.get('Columns')]
        missing_columns = [col for col in self.cur_minimal_required_columns if col not in columns]
        if missing_columns:
            return False if not return_reason else (False, f"Table {table_name} does not contain columns: {','.join(missing_columns)}. You can try ALTER TABLE {table_name} ADD COLUMNS (missing_column string).")

        return True if not return_reason else (True, 'all good')

    @property
    def metadata(self) -> dict:
        if self._metadata:
            return self._metadata

        if get_parameters().get('cur-table-name'):
            self._tableName = get_parameters().get('cur-table-name')
            try:
                self._metadata = self.athena.get_table_metadata(self._tableName)
            except self.athena.client.exceptions.ResourceNotFoundException as exc:
                raise CidCritical('Provided cur-table-name "{self._tableName}" is not found. Please make sure the table exists.') from exc
            res, message = self.table_is_cur(table=self._metadata, return_reason=True)
            if not res:
                raise CidCritical(f'Table {self._tableName} does not look like CUR. {message}')
        else:
            # Look all tables and filter ones with CUR fields
            all_tables = self.athena.list_table_metadata()
            if not all_tables:
                raise CidCritical(
                    f'No tables found in Athena Database {self.athena.DatabaseName} in {self.athena.region}.'
                    f' (Hint: If you see tables in this Database, please check AWS Lake Formation permissions)'
                )
            cur_tables = [tab for tab in all_tables if self.table_is_cur(table=tab)]

            if not cur_tables:
                raise CidCritical(f'CUR table not found. (scanned {len(all_tables)} tables in Athena Database {self.athena.DatabaseName} in {self.athena.region}). But none has required fields: {self.cur_minimal_required_columns}.')
            if len(cur_tables) == 1:
                self._metadata = cur_tables[0]
                self._tableName = self._metadata.get('Name')
                logger.info('1 CUR table found: %s', self._tableName)
            elif len(cur_tables) > 1:
                self._tableName =  get_parameter(
                    param_name='cur-table-name',
                    message="Multiple CUR tables found, please select one",
                    choices=sorted([v.get('Name') for v in cur_tables], reverse=True),
                )
                self._metadata = self.athena.get_table_metadata(self._tableName)
        return self._metadata

    @property
    def fields(self) -> list:
        return [v.get('Name') for v in self.metadata.get('Columns', list())]

    @property
    def tag_and_cost_category_fields(self) -> list:
        """ Returns all tags and cost category fields. """
        return [field for field in self.fields if field.startswith('resource_tags_user_') or field.startswith('cost_category_')]
