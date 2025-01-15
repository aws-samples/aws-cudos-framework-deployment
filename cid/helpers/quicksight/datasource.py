import logging

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)

class Datasource(CidQsResource):

    @property
    def AthenaParameters(self) -> dict:
        return self.parameters.get('AthenaParameters', {})

    @property
    def role_name(self) -> dict:
        role_arn = self.parameters.get('AthenaParameters', {}).get('RoleArn')
        if not role_arn:
            return None
        return role_arn.split('/')[-1]

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

    @property
    def is_healthy(self) -> bool:
        return self.status not in ['CREATION_IN_PROGRESS', 'CREATION_FAILED']

    @property
    def error_info(self) -> bool:
        """ returns a dict  {'Type': '...', 'Message': '...'} or empty dict """
        return self.get_property('ErrorInfo') or {}