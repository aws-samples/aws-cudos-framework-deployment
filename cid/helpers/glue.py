import json
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class Glue(CidBase):

    def __init__(self, session):
        super().__init__(session)
        # QuickSight client
        self.client = self.session.client('glue', region_name=self.region)


    def create_or_update_table(self, view_name: str, view_query: str) -> None:
        table = json.loads(view_query)
        try:
            self.client.create_table(**table)
        except self.client.exceptions.AlreadyExistsException:
            logger.info(f'Glue table "{view_name}" exists')
            self.client.update_table(**table)

    def delete_table(self, name, catalog, database):
        """ Delete an AWS Glue table """
        try:
            return self.client.delete_table(
                CatalogId=catalog,
                DatabaseName=database,
                Name=name,
            )
        except self.client.exceptions.EntityNotFoundException:
            return True
