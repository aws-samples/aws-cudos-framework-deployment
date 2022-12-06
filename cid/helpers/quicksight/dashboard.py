import click
import json
import logging
import os
from typing import Dict

from cid.helpers.quicksight.resource import CidQsResource
from cid.helpers.quicksight.template import Template as CidQsTemplate
from cid.utils import is_unattendent_mode


logger = logging.getLogger(__name__)


class Dashboard(CidQsResource):
    def __init__(self, raw: dict) -> None:
        super().__init__(raw)
        # Initialize properties
        self.datasets: Dict[str, str] = {}
        # Deployed template
        self._deployedTemplate: CidQsTemplate = None
        self._status = str()
        self.status_detail = str()
        # Source template in origin account
        self.sourceTemplate: CidQsTemplate = None

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
        print('\nDashboard status:')
        print(f"  Name (id): {self.name} ({self.id})")
        print(f"  Status: {self.status}")
        print(f"  Health: {'healthy' if self.health else 'unhealthy'}")
        if self.status_detail:
            print(f"  Status detail: {self.status_detail}")
        if self.latest:
            print(f"  Version: {self.deployed_version}")
        else:
            print(f"  Version (deployed, latest): {self.deployed_version}, {self.latest_version}")
        if self.datasets:
            print(f"  Datasets: {', '.join(sorted(self.datasets.keys()))}")
        print('\n')
        if click.confirm('Display dashboard raw data?'):
            print(json.dumps(self.raw, indent=4, sort_keys=True, default=str))
    
    def display_url(self, url_template: str, launch: bool = False, **kwargs) -> None:
        url = url_template.format(dashboard_id=self.id, **kwargs)
        print(f"#######\n####### {self.name} is available at: " + url + "\n#######")
        _supported_env = os.environ.get('AWS_EXECUTION_ENV') not in ['CloudShell', 'AWS_Lambda']
        if _supported_env and not is_unattendent_mode() and launch and click.confirm('Do you wish to open it in your browser?'):
            click.launch(url)
