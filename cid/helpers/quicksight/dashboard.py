import click
import json
import logging
import os
from typing import Dict

from cid.helpers.quicksight.resource import CidQsResource
from cid.utils import is_unattendent_mode


logger = logging.getLogger(__name__)

class Dashboard(CidQsResource):
    def __init__(self, raw: dict) -> None:
        super().__init__(raw)
        # Initialize properties
        self.datasets: Dict[str, str] = {}
        self._status = str()
        self.status_detail = str()
        # Source template in origin account
        self.sourceTemplate = dict()
        # Locally saved deployment
        self.localConfig = dict()

    @property
    def id(self) -> str:
        return self.get_property('DashboardId')

    @property
    def version(self) -> dict:
        return self.get_property('Version')

    @property
    def latest(self) -> bool:
        return self.latest_version == self.deployed_version

    @property
    def latest_version(self) -> int:
        return int(self.sourceTemplate.get('Version', dict()).get('VersionNumber', -1))
    
    @property
    def deployed_arn(self) -> str:
        return self.version.get('SourceEntityArn')
    
    @property
    def deployed_version(self) -> int:
        try:
            return int(self.deployed_arn.split('/')[-1])
        except Exception as e:
            logger.debug(e, stack_info=True)
            return 0
 
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
            elif self.deployed_arn and self.sourceTemplate.get('Arn') and not self.deployed_arn.startswith(self.sourceTemplate.get('Arn')):
                self._status = 'legacy'
            else:
                if self.latest_version > self.deployed_version:
                    self._status = f'update available {self.deployed_version}->{self.latest_version}'
                elif self.latest:
                    self._status = 'up to date'
        return self._status

    @property
    def templateId(self) -> str:
        if 'SourceEntityArn' not in self.version:
            return ''
        arn = self.version.get('SourceEntityArn')
        if ":template/" not in arn:
            return ''
        return str(arn.split('/')[1])

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
        if self.localConfig:
            print(f"  Local config: {self.localConfig.get('SourceEntity').get('SourceTemplate').get('Name')}")
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
