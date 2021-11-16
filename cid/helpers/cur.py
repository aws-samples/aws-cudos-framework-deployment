import json
from cid.helpers import Athena

class CUR:
    defaults = {
        'TableName': 'customer_all'
    }
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
    def tableName(self):
        if self.metadata is None:
            print('Error: CUR not detected')
            exit(1)
        return self.metadata.get('Name')

    @property
    def hasResourceIDs(self):
        if self._configured and self._hasResourceIDs is None:
            self._hasResourceIDs = 'line_item_resource_id' in self.fields
        return self._hasResourceIDs

    @property
    def hasReservations(self):
        if self._configured and self._hasReservations is None:
            kwargs = {
                'cur_table_name': self._tableName
            }
            self._hasReservations = bool(len(self.athena.execute_ahq('hasReservations', **kwargs)))
        return self._hasReservations

    @property
    def hasSavingsPlans(self):
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
                # Look for default CUR table
                self._metadata = self.athena.get_table_metadata(self.defaults.get('TableName'))
                self._tableName = self.defaults.get('TableName')
            except self.athena.client.exceptions.MetadataException:
                # Look based on CUR Athena database name
                try:
                    tables = self.athena.list_table_metadata()
                    tables = [v for v in tables if v.get('TableType') == 'EXTERNAL_TABLE']
                    for table in tables:
                        if table.get('Name') in self.athena.DatabaseName:
                            self._metadata = self.athena.get_table_metadata(table.get('Name'))
                            self._tableName = table.get('Name')
                            break
                    # self._metadata = self.athena.get_table_metadata(self.athena._DatabaseName.rpartition('_')[2])
                    # self._tableName = self.athena._DatabaseName.rpartition('_')[2]
                except self.athena.client.exceptions.MetadataException:
                    # TODO: ask user
                    print('Error: CUR metadata not found')
            except Exception as e:
                # For other errors dump the message
                print(json.dumps(e, indent=4, sort_keys=True, default=str))

        return self._metadata

    @property
    def fields(self) -> list:
        return [v.get('Name') for v in self.metadata.get('Columns', list())]
