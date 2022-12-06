import logging

from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)


class Dataset(CidQsResource):

    @property
    def id(self) -> str:
        return self.get_property('DataSetId')

    @property
    def columns(self) -> list:
        return self.get_property('OutputColumns')

    @property
    def datasources(self) -> list:
        _datasources = []
        try:
            for table_map in self.raw.get('PhysicalTableMap', {}).values():
                ds = table_map.get('RelationalTable', {}).get(
                    'DataSourceArn', '').split('/')[-1]
                if ds:
                    _datasources.append(ds)
        except Exception as e:
            logger.debug(e, exc_info=True)
        return sorted(list(set(_datasources)))

    @property
    def schemas(self) -> list:
        schemas = []
        try:
            for table_map in self.get_property('PhysicalTableMap').values():
                schema = table_map.get(
                    'RelationalTable', {}).get('Schema', None)
                if schema:
                    schemas.append(schema)
        except Exception as e:
            logger.debug(e, exc_info=True)
        return sorted(list(set(schemas)))
