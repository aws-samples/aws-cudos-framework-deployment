import json
import questionary
from cid.helpers import Athena

class CUR:
    requiredColumns = [
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
    _tableName = None
    _metadata = None
    _clients = dict()
    _hasResourceIDs = None
    _hasSavingsPlans = None
    _hasReservations = None
    _configured = None
    _status = str()
    

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
            print('Error: CUR not detected')
            exit(1)
        return self.metadata.get('Name')

    @property
    def hasResourceIDs(self) -> bool:
        if self._configured and self._hasResourceIDs is None:
            self._hasResourceIDs = 'line_item_resource_id' in self.fields
        return self._hasResourceIDs

    @property
    def hasReservations(self) -> bool:
        if self._configured and self._hasReservations is None:
            kwargs = {
                'cur_table_name': self._tableName
            }
            self._hasReservations = bool(len(self.athena.execute_ahq('hasReservations', **kwargs)))
        return self._hasReservations

    @property
    def hasSavingsPlans(self) -> bool:
        if self._configured and self._hasSavingsPlans is None:
            kwargs = {
                'cur_table_name': self._tableName
            }
            self._hasSavingsPlans = bool(len(self.athena.execute_ahq('hasSavingsPlans', **kwargs)))
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
                    if not all([c in columns for c in self.requiredColumns]):
                        tables.remove(table)
                if len(tables) == 1:
                    self._metadata = tables[0]
                    self._tableName = self._metadata.get('Name')
                elif len(tables) > 1:
                    self._tableName=questionary.select(
                        "Multiple CUR tables found, please select one",
                        choices=[v.get('Name') for v in tables]
                    ).ask()
                    self._metadata = self.athena.get_table_metadata(self._tableName)
            except Exception as e:
                # For other errors dump the message
                print(json.dumps(e, indent=4, sort_keys=True, default=str))

        return self._metadata

    @property
    def fields(self) -> list:
        return [v.get('Name') for v in self.metadata.get('Columns', list())]
