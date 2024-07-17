import re
import logging

logger = logging.getLogger(__name__)

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