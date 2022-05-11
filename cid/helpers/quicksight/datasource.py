import logging

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)

class Datasource(CidQsResource):

    @property
    def AthenaParameters(self) -> dict:
        return self.parameters.get('AthenaParameters', {})

    @property
    def id(self) -> str:
        return self.get_property('DataSourceId')

    @property
    def parameters(self) -> dict:
        return self.get_property('DataSourceParameters') or {}

    @property
    def status(self) -> str:
        return self.get_property('Status')

    @property
    def type(self) -> str:
        return self.get_property('Type')
