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
            for table_map in self.raw.get('PhysicalTableMap').values():
                _datasources.append(table_map.get('RelationalTable').get('DataSourceArn').split('/')[-1])
        except Exception as e:
            logger.debug(e, stack_info=True)
        return sorted(list(set(_datasources)))

    @property
    def schemas (self) -> list:
        schemas = []
        try:
            for table_map in self.raw.get('PhysicalTableMap').values():
                schema = table_map.get('RelationalTable', {}).get('Schema', None)
                if schema:
                    schemas.append(schema)
        except Exception as e:
            logger.debug(e, stack_info=True)
        return sorted(list(set(schemas)))
