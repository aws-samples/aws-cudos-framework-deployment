import logging

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)

class Dataset(CidQsResource):

    @property
    def id(self) -> str:
        return self.get_property('DataSetId')

    @property
    def datasources(self) -> list:
        _datasources = []
        try:
            for _,map in self.raw.get('PhysicalTableMap').items():
                _datasources.append(map.get('RelationalTable').get('DataSourceArn').split('/')[-1])
        except Exception as e:
            logger.debug(e, stack_info=True)
        return _datasources
