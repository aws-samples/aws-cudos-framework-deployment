import click
import json
import logging
from typing import Dict

from cid.helpers.quicksight.resource import CidQsResource
from cid.helpers.quicksight.definition import Definition as CidQsDefinition
from cid.helpers.quicksight.template import Template as CidQsTemplate
from cid.utils import cid_print, get_yesno_parameter
from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)


class Dashboard(CidQsResource):
    def __init__(self, raw: dict, qs=None) -> None:
        super().__init__(raw)
        # Initialize properties
        self.datasets: Dict[str, str] = {}
        # Deployed template
        self._deployedTemplate: CidQsTemplate = None
        self._deployedDefinition: CidQsDefinition = None
        self._status = str()
        self.status_detail = str()
        # Source template in origin account
        self.sourceTemplate: CidQsTemplate = None
        self.sourceDefinition: CidQsDefinition = None
        self.qs = qs

    @property
    def id(self) -> str:
        return self.get_property('DashboardId')

    @property
    def version(self) -> dict:
        return self.get_property('Version')

    @property
    def deployedTemplate(self) -> CidQsTemplate:
        return self._deployedTemplate

    @deployedTemplate.setter
    def deployedTemplate(self, template: CidQsTemplate) -> None:
        self._deployedTemplate = template

    @property
    def deployedDefinition(self) -> CidQsTemplate:
        return self._deployedDefinition

    @deployedDefinition.setter
    def deployedDefinition(self, definition: CidQsDefinition) -> None:
        self._deployedDefinition = definition

    @property
    def template_id(self) -> str:
        if isinstance(self.deployedTemplate, CidQsTemplate):
            return self.deployedTemplate.id
        return None

    @property
    def template_arn(self) -> str:
        if isinstance(self.deployedTemplate, CidQsTemplate):
            return self.deployedTemplate.arn
        return None

    @property
    def deployed_cid_version(self) -> int:
        if isinstance(self.deployedTemplate, CidQsTemplate):
            return self.deployedTemplate.cid_version
        elif isinstance(self.deployedDefinition, CidQsDefinition):
            return self.deployedDefinition.cid_version
        else:
            return None

    @property
    def latest(self) -> bool:
        return self.latest_available_cid_version == self.deployed_cid_version

    @property
    def health(self) -> bool:
        return self.status not in ['broken']
    
    @property
    def origin_type(self) -> str:
        if self.deployedTemplate is not None:
            return "TEMPLATE"
        elif self.deployedDefinition is not None:
            return "DEFINITION"
        else:
            return "UNKNOWN"
    

    @property
    def cid_version(self) -> int:
        if self.origin_type == "TEMPLATE":
            return self.deployedTemplate.cid_version
        elif self.origin_type == "DEFINITION":
            return self.deployedDefinition.cid_version
        else:
            return None
    
    @property
    def latest_available_cid_version(self) -> int:
        if self.origin_type == "TEMPLATE":
            return self.sourceTemplate.cid_version
        elif self.origin_type == "DEFINITION":
            return self.sourceDefinition.cid_version
        else:
            return None


    @property
    def status(self) -> str:
        if not self._status:
            # Deployment failed
            if self.version.get('Status') not in ['CREATION_SUCCESSFUL']:
                self._status = 'broken'
                self.status_detail = f"{self.version.get('Status')}: {self.version.get('Errors')}"
            # Not discovered yet
            elif not self.definition:
                self._status = 'undiscovered'
            # Missing dataset
            elif not self.datasets or (len(set(self.datasets)) < len(set(self.definition.get('dependsOn').get('datasets')))):
                self.status_detail = 'missing dataset(s)'
                self._status = 'broken'
                logger.info(f"Found datasets: {self.datasets}")
                logger.info(f"Required datasets: {self.definition.get('dependsOn').get('datasets')}")
            # Source Template has changed
            elif self.deployedTemplate and self.sourceTemplate and self.deployedTemplate.arn and self.sourceTemplate.arn and not self.deployedTemplate.arn.startswith(self.sourceTemplate.arn):
                self._status = 'legacy'
            elif not self.latest_available_cid_version or not self.deployed_cid_version:
                self._status = 'undetermined'
            else:
                if self.latest_available_cid_version > self.deployed_cid_version:
                    self._status = f'update available {self.deployed_cid_version}->{self.latest_available_cid_version}'
                elif self.latest:
                    self._status = 'up to date'
        return self._status

    def display_status(self) -> None:
        """Display status of dashboard"""

        cid_print('\n<BOLD>Dashboard status:<END>')
        cid_print(f"  <BOLD>Id:<END>        {self.id}")
        cid_print(f"  <BOLD>Name:<END>      {self.name}")
        cid_print(f"  <BOLD>Health:<END>    {'<GREEN>healthy<END>' if self.health else '<RED>unhealthy<END>'}")
        cid_print(f"  <BOLD>Status:<END>    {'<GREEN>' + self.status + '<END>' if self.health else '<RED>' + self.status + '<END>'}")

        if self.status_detail:
            cid_print(f"  <BOLD>Status detail:<END> {self.status_detail}")

        if not self.cid_version:
            logger.debug("The cid version of the deployed dashboard could not be retrieved")

        if not self.latest_available_cid_version:
            logger.debug("The latest version of the dashboard could not be retrieved")
            cid_print(f"  <BOLD>Version:<END>   <YELLOW>{self.cid_version or 'N/A'}<END> (unable to find latest)")
        else:
            if self.latest:
                cid_print(f"  <BOLD>Version:<END>   <GREEN>{self.cid_version or 'N/A'}<END> (latest)")
            else:
                logger.debug("An update is available")
                cid_print(f"  <BOLD>Version:<END>   <YELLOW>{self.cid_version or 'N/A'} --> {self.latest_available_cid_version or 'N/A'}<END>")

        cid_print('  <BOLD>Owners:<END>')
        try:
            permissions = self.qs.get_dashboard_permissions(self.id)
            for permission in permissions:
                if 'quicksight:UpdateDashboardPermissions' in permission["Actions"]:
                    cid_print('    ' + permission["Principal"].split('user/default/')[-1])
        except Exception as exc:
            if "AccessDenied" in str(exc):
                cid_print('     <RED>AccessDenied<END>')

        if self.datasets:
            cid_print(f"  <BOLD>Datasets:<END>")
            for dataset_name, dataset_id in  sorted(self.datasets.items()):
                status = self.qs.get_dataset_last_ingestion(dataset_id) or '<BLUE>DIRECT<END>' #todo fix this Blue using dataset import type.
                cid_print(f'    {dataset_name: <36} ({dataset_id: <36}) {status}')

    def display_url(self, url_template: str, launch: bool = False, **kwargs) -> None:
        url = url_template.format(dashboard_id=self.id, **kwargs)
        print(f"#######\n####### {self.name} is available at: " + url + "\n#######")

    def refresh_datasets(self) -> None:
        """Refresh datasets of dashboard"""
        if self.datasets:
            cid_print(f"  <BOLD>Refreshing Datasets:<END>")
            for dataset_name, dataset_id in  sorted(self.datasets.items()):
                mode, status = self.qs.refresh_dataset(dataset_id)
                cid_print(f'    {dataset_name: <36} ({dataset_id: <36}) Refresh Status: {status} Mode: {mode}')
