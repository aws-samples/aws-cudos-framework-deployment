""" Glue Helper
"""
import yaml
import logging

from cid.base import CidBase

logger = logging.getLogger(__name__)


class Glue(CidBase):

    def __init__(self, session):
        super().__init__(session)
        self.client = self.session.client('glue', region_name=self.region)

    def create_or_update_table(self, view_name: str, definition: dict) -> None:
        """create_or_update_table"""
        definition = yaml.safe_load(definition)
        logger.debug(definition)
        try:
            self.client.create_table(**definition)
            logger.info('table updated')
            logger.info(f'Table "{view_name}" created')
        except self.client.exceptions.AlreadyExistsException:
            logger.info(f'Glue table "{view_name}" exists')
            self.client.update_table(**definition)
            logger.info(f'Table "{view_name}" updated')
        except self.client.exceptions.ClientError:
            logger.error(definition)
            raise

    def get_table(self, name, catalog, database):
        """Get table"""
        return self.client.get_table(
            CatalogId=catalog,
            DatabaseName=database,
            Name=name,
        )['Table']

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

    def create_or_update_crawler(self, crawler_definition) -> None:
        """Create or update crawler. Also start it if not running."""
        logger.debug("updating crawler")
        logger.debug(crawler_definition)
        try:
            self.client.create_crawler(**crawler_definition)
            logger.info(f'Created crawler')
        except self.client.exceptions.AlreadyExistsException:
            logger.info(f'Updating crawler')
            self.client.update_crawler(**crawler_definition)
        except self.client.exceptions.ClientError:
            logger.error(crawler_definition)
            raise

        crawler_name = crawler_definition['Name']
        try:
            self.client.start_crawler(Name=crawler_name)
            logger.critical(f'Started crawler {crawler_name}')
        except self.client.exceptions.ClientError as exc:
            if 'Cannot update Crawler while running' in str(exc):
                logger.info(f"Crawler is already running.")
            else:
                raise

    def get_crawler(self, name: str):
        """ GetCrawler """
        return self.client.get_crawler(Name=name)['Crawler']
