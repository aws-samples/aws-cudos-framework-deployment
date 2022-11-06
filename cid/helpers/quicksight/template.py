import logging
from typing import Dict

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)


class Template(CidQsResource):

    @property
    def id(self) -> str:
        return self.get_property('TemplateId')

    @property
    def datasets(self) -> Dict[str, list]:
        _datasets = {}
        try:
            for ds in self.raw.get('Version').get('DataSetConfigurations'):
                _datasets.update({ds.get('Placeholder'): ds.get('DataSetSchema').get('ColumnSchemaList')})
        except Exception as e:
            logger.debug(e, exc_info = True)
        return _datasets

    @property
    def version(self) -> int:
        return self.raw.get('Version', dict()).get('VersionNumber', -1)
