import json
import logging
from typing import Dict

import importlib.resources as pkg_resources

from cid.base import CidBase
from cid.exceptions import CidError

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

    def create_database(self, name: str, catalog_id: str) -> None:
        """Create a new AWS Glue database"""
        try:
            self.client.create_database(
                CatalogId=catalog_id,
                DatabaseInput={
                    "Name": name,
                },
            )
        except self.client.exceptions.AlreadyExistsException as ex:
            logger.debug(ex, exc_info=True)
            logger.info("Database %s cannot be created in %s: %s", name, catalog_id, ex)
            raise CidError() from ex

    def create_crawler(self, name: str, role_arn: str, database_name: str, processed_cur_path: Dict[str, str]) -> None:
        """Create new crawler"""
        configuration = pkg_resources.read_text("cid.builtin.core.data.glue", "crawler_configuration.json")
        try:
            self.client.create_crawler(
                Name=name,
                Role=role_arn,
                DatabaseName=database_name,
                Description="A recurring crawler that keeps your CUR table in Athena up-to-date.",
                Targets={
                    "S3Targets": [
                        {
                            "Path": f"s3://{processed_cur_path['Bucket']}/{processed_cur_path['Path']}/",
                            "Exclusions": [
                                "**.json",
                                "**.yml",
                                "**.sql",
                                "**.csv",
                                "**.csv.metadata",
                                "**.gz",
                                "**.zip",
                                "**/cost_and_usage_data_status/*",
                                "aws-programmatic-access-test-object",
                            ],
                        },
                    ],
                },
                Schedule="cron(0 2 * * ? *)",
                SchemaChangePolicy={"DeleteBehavior": "LOG"},
                RecrawlPolicy={"RecrawlBehavior": "CRAWL_EVERYTHING"},
                Configuration=configuration,
            )
        except self.client.exceptions.AlreadyExistsException as ex:
            raise CidError(f'Crawler {name} already exists') from ex
