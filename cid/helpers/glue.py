import json
import logging

logger = logging.getLogger(__name__)


class Glue():

    def __init__(self, session):
        self.region = session.region_name

        # QuickSight client
        self.client = session.client('glue', region_name=self.region)


    def create_table(self, table: dict) -> dict:
        """ Creates an AWS Glue table """
        return self.client.create_table(**table)

    def ensure_glue_table_created(self, view_name: str, view_query: str) -> None:
        try:
            self.create_table(json.loads(view_query))
        except self.glue.client.exceptions.AlreadyExistsException:
            logger.info(f'Glue table "{view_name}" exists')
