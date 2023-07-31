import json
import logging

from cid.base import CidBase
from cid.helpers import Athena
from cid.utils import get_parameter, get_parameters
from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)


class CUR(CidBase):
    curRequiredColumns = [
        'identity_line_item_id',
        'identity_time_interval',
        'bill_invoice_id',
        'bill_billing_entity',
        'bill_bill_type',
        'bill_payer_account_id',
        'bill_billing_period_start_date',
        'bill_billing_period_end_date',
        'line_item_usage_account_id',
        'line_item_line_item_type',
        'line_item_usage_start_date',
        'line_item_usage_end_date',
        'line_item_product_code',
        'line_item_usage_type',
        'line_item_operation',
    ]
    riRequiredColumns = [
        'reservation_reservation_a_r_n',
        'reservation_effective_cost',
        'reservation_start_time',
        'reservation_end_time',
        'pricing_lease_contract_length',
        'pricing_offering_class',
        'pricing_purchase_option'
    ]
    spRequiredColumns = [
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
    def configured(self) -> bool:
        """ Check if AWS Datacalog and Athena database exist """
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
            logger.debug(f'{self.riRequiredColumns}: {[c in self.fields for c in self.riRequiredColumns]}')
            self._hasReservations=all([c in self.fields for c in self.riRequiredColumns])
            logger.info(f'Reserved Instances: {self._hasReservations}')
        return self._hasReservations

    @property
    def hasSavingsPlans(self) -> bool:
        if self._configured and self._hasSavingsPlans is None:
            logger.debug(f'{self.spRequiredColumns}: {[c in self.fields for c in self.spRequiredColumns]}')
            self._hasSavingsPlans=all([c in self.fields for c in self.spRequiredColumns])
            logger.info(f'Savings Plans: {self._hasSavingsPlans}')
        return self._hasSavingsPlans


    def table_is_cur(self, table: dict=None, name: str=None) -> bool:
        """ return True if table metadata fits CUR definition. """
        try:
            table = table or self.athena.get_table_metadata(name)
        except Exception as exc:
            logger.debug(exc)
            return False

        if table.get('TableType') not in ['EXTERNAL_TABLE', 'VIRTUAL_VIEW']:
            return False
        columns = [cols.get('Name') for cols in table.get('Columns')]
        if not all(cols in columns for cols in self.curRequiredColumns):
            return False
        return True

    @property
    def metadata(self) -> dict:
        if self._metadata:
            return self._metadata

        if get_parameters().get('cur-table-name'):
            self._tableName = get_parameters().get('cur-table-name')
            self._metadata = self.athena.get_table_metadata(self._tableName)
            if not self.table_is_cur(table=self._metadata):
                raise CidCritical(f'Table {self._tableName} does not looks like CUR. Please check that the table exist and have fields: {self.curRequiredColumns}.')
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
                raise CidCritical(f'CUR table not found. (scanned {len(all_tables)} tables in Athena Database {self.athena.DatabaseName} in {self.athena.region}). But none has required fields: {self.curRequiredColumns}.')
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
