# Implements generic Plugin class to load plugins

import json, yaml
from pkg_resources import (
    resource_exists,
    resource_string,
    resource_listdir,
    resource_isdir,
    resource_stream,
    resource_filename,
)
import logging

logger = logging.getLogger(__name__)

class Plugin():

    def __init__(self, name):
        logger.debug(f'Initializing plugin {name}')
        self.resources = {}
        self.name = name
        pkg_resources_db_directory = 'data'
        for pkg_resource in resource_listdir(self.name,pkg_resources_db_directory):
            if not resource_isdir(self.name, f'data/{pkg_resource}'):
                logger.debug(f'Located data file: {pkg_resource}')
                ext = pkg_resource.rsplit('.', -1)[-1].lower()
                content = None
                if ext == 'json':
                    content = json.loads(resource_string(self.name, f'data/{pkg_resource}'))
                    logger.debug(f'Loaded {pkg_resource} as JSON')
                elif ext in ['yaml', 'yml']:
                    with resource_stream(self.name, f'data/{pkg_resource}') as yaml_stream:
                        content = yaml.load(yaml_stream, Loader=yaml.SafeLoader)
                        logger.debug(f'Loaded {pkg_resource} as YAML')
                if content is None:
                    logger.info(f'Unsupported file type: {pkg_resource}')
                    continue
                # If plugin has resources defined in different files,
                # they will be merged into one dict
                resource_kind = pkg_resource.rsplit('.', -1)[0]
                supported_resource_kinds = ['dashboards', 'views', 'datasets']
                if resource_kind in supported_resource_kinds:
                    self.resources.update({
                        resource_kind: content
                    })
                    logger.info(f'Loaded {resource_kind} from {pkg_resource}')
                # If plugin has resources defined in one file,
                # simply add it to resources dict
                else:
                    self.resources.update(content)
                # Add plugin name to every resource
                for v in self.resources.values():
                    for item in v.values():
                        if item is not None:
                            item.update({'providedBy': self.name})
                            item.update({'source': resource_filename(self.name, f'data/{pkg_resource}')})
        logger.debug(f'Plugin {self.name} initialized')
    
    def provides(self) -> dict:
        logger.debug(f'Provides: {self.resources}')
        return self.resources

    def get_resource(self, resource_name) -> str:
        _resource = f'data/{resource_name}'
        if resource_exists(self.name, _resource):
            logger.info(f'Resource {resource_name} found')
            _content = resource_string(self.name, _resource).decode("utf-8")
            logger.debug(f'Resource {resource_name} content: {_content}')
            return _content
        return None
