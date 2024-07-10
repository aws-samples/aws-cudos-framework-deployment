import logging
import re
from typing import Dict
from cid.helpers.quicksight.resource import CidQsResource

logger = logging.getLogger(__name__)

# TODO Move to its own module and re-use across Template and Definition modules
class CidVersion:
    
    def __init__(self, version):
        
        if isinstance(version, __class__):
            self.major, self.minor, self.build = version.major, version.minor, version.build 
        elif isinstance(version, str):
            self.major, self.minor, self.build = self._parse(version)
        else:
            raise TypeError(f'{version} must be {__class__} or str ')

    def __str__(self):
        return f'v{self.major}.{self.minor}.{self.build}'
    
    def _parse(self, str_version):
        
        version_pattern = re.compile(r"^[v|V](?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<build>[0-9]+)$")
        results = version_pattern.match(str_version)
        
        if not results:
            logger.debug(f'Could not find version pattern in provided string: {str_version}')
            raise ValueError(f'Could not find version pattern in provided string:{str_version}')
        
        major = int(results.group("major"))
        minor = int(results.group("minor"))
        build = int(results.group("build"))

        return major, minor, build
    
    def compatible_versions(self, _version) -> bool:
        """
            Return True when both version are on the same major branch
        """
                    
        return CidVersion(_version).major == self.major
    
    def __lt__(self, _version):
        return self._get_version_as_tuple() < CidVersion(_version)._get_version_as_tuple()

    def __le__(self, _version):
        return self._get_version_as_tuple() <= CidVersion(_version)._get_version_as_tuple()

    def __eq__(self, _version):
        return self._get_version_as_tuple() == CidVersion(_version)._get_version_as_tuple()

    def __ge__(self, _version):
        return self._get_version_as_tuple() >= CidVersion(_version)._get_version_as_tuple()

    def __gt__(self, _version):
        return self._get_version_as_tuple() > CidVersion(_version)._get_version_as_tuple()

    def __ne__(self, _version):
        return self._get_version_as_tuple() != CidVersion(_version)._get_version_as_tuple()

    def _get_version_as_tuple(self) -> tuple:
        return (self.major,self.minor,self.build)
    
# TODO: the type CidQSResource does not fully apply for a dashboard definition. Removing inheritance for the moment.
class Definition:

    def __init__(self, raw: dict) -> None:
        self.raw: dict = raw
        # Resolve version from definition contents
        self._raw_version = self.resolve_version(self.raw)
    
    @property
    def cid_version(self) -> CidVersion:
        # Resolve version from "About" sheet contents
        return CidVersion(self._raw_version)
    
    def resolve_version(self, raw: dict):
        about_content = [text_content["Content"] for sheet in raw["Sheets"] for text_content in sheet["TextBoxes"] if sheet["Name"] == "About"]
        if about_content:
            all_about_content = " | ".join(about_content)
            # find first string that looks like vx.y.z using a regular expression where x, y and z are numbers
            version_matches = re.findall(r"(v\d+?\.\d+?\.\d+?)", all_about_content)
            if version_matches:
                return version_matches[0]
        return None
        

