import click
import json
import logging
from typing import Dict

from cid.helpers.quicksight.resource import CidQsResource
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
        self._status = str()
        self.status_detail = str()
        # Source template in origin account
        self.sourceTemplate: CidQsTemplate = None
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
    def deployed_version(self) -> int:
        if isinstance(self.deployedTemplate, CidQsTemplate):
            return self.deployedTemplate.version
        else:
            return -1

    @property
    def latest(self) -> bool:
        return self.latest_version == self.deployed_version

    @property
    def latest_version(self) -> int:
        if isinstance(self.sourceTemplate, CidQsTemplate):
            return self.sourceTemplate.version
        else:
            return -1

    @property
    def health(self) -> bool:
        return self.status not in ['broken']

    @property
    def status(self) -> str:
        if not self._status:
            # Deployment failed
            if self.version.get('Status') not in ['CREATION_SUCCESSFUL']:
                self._status = 'broken'
                self.status_detail = f"{self.version.get('Status')}: {self.version.get('Errors')}"
            # Not dicovered yet
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
            else:
                if self.latest_version > self.deployed_version:
                    self._status = f'update available {self.deployed_version}->{self.latest_version}'
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

        cid_version = "N/A"
        cid_version_latest =  "N/A"

        try:
            cid_version = self.deployedTemplate.cid_version
        except ValueError:
            logger.debug("The cid version of the deployed dashboard could not be retrieved")

        try:
            if isinstance(self.sourceTemplate, CidQsTemplate):
                cid_version_latest = self.sourceTemplate.cid_version
        except ValueError:
            logger.debug("The latest version of the dashboard could not be retrieved")

        if self.latest:
            cid_print(f"  <BOLD>Version:<END>   <GREEN>{cid_version}<END> (latest)")
            cid_print(f"  <BOLD>VersionId:<END> <GREEN>{self.deployed_version}<END> (latest)")
        else:
            logger.debug("An update is available")
            cid_print(f"  <BOLD>Version:<END>   <YELLOW>{str(cid_version): <8} --> {str(cid_version_latest): <8}<END>")
            cid_print(f"  <BOLD>VersionId:<END> <YELLOW>{str(self.deployed_version): <8} --> {str(self.latest_version): <8}<END>")

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
                status = self.qs.get_dataset_last_ingestion(dataset_id) or '<BLUE>DIRECT<END>'
                cid_print(f'    {dataset_name: <36} ({dataset_id: <36}) {status}')

        print('\n')
        if get_yesno_parameter('display-raw', 'Display dashboard raw data?', default='yes'):
            print(json.dumps(self.raw, indent=4, sort_keys=True, default=str))

    def display_url(self, url_template: str, launch: bool = False, **kwargs) -> None:
        url = url_template.format(dashboard_id=self.id, **kwargs)
        print(f"#######\n####### {self.name} is available at: " + url + "\n#######")
