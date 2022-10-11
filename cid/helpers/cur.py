import json
import logging

from cid.base import CidBase
from cid.helpers import Athena
from cid.utils import get_parameter
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
            raise CidCritical('Error: CUR not detected')
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

    @property
    def metadata(self) -> dict:
        if not self._metadata:
            try:
                # Look other tables
                tables = self.athena.list_table_metadata()
                # Filter tables with type = 'EXTERNAL_TABLE'
                tables = [v for v in tables if v.get('TableType') == 'EXTERNAL_TABLE']
                # Filter tables having CUR structure
                for table in tables.copy():
                    columns = [c.get('Name') for c in table.get('Columns')]                    
                    if not all([c in columns for c in self.curRequiredColumns]):
                        tables.remove(table)
                # Sort tables by name (desc)
                tables.sort(key=lambda x: x.get('Name'), reverse=True)
                if len(tables) == 1:
                    self._metadata = tables[0]
                    self._tableName = self._metadata.get('Name')
                elif len(tables) > 1:
                    self._tableName =  get_parameter(
                        param_name='cur-table-name',
                        message="Multiple CUR tables found, please select one",
                        choices=[v.get('Name') for v in tables],
                    )
                    self._metadata = self.athena.get_table_metadata(self._tableName)
            except Exception as e:
                # For other errors dump the message
                print(json.dumps(e, indent=4, sort_keys=True, default=str))

        return self._metadata

    @property
    def fields(self) -> list:
        return [v.get('Name') for v in self.metadata.get('Columns', list())]
