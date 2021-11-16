# Implements generic Plugin class to load plugins

import json, yaml
from pkg_resources import (
    resource_exists,
    resource_string,
    resource_listdir,
    resource_isdir,
    resource_stream
)

class Plugin():

    def __init__(self, name):
        self.resources = {}
        self.name = name
        pkg_resources_db_directory = 'data'
        for pkg_resource in resource_listdir(self.name,pkg_resources_db_directory):
            if not resource_isdir(self.name, f'data/{pkg_resource}'):
                ext = pkg_resource.rsplit('.', -1)[-1].lower()
                if ext == 'json':
                    content = json.loads(resource_string(self.name, f'data/{pkg_resource}'))
                elif ext in ['yaml', 'yml']:
                    with resource_stream(self.name, f'data/{pkg_resource}') as yaml_stream:
                        content = yaml.load(yaml_stream, Loader=yaml.SafeLoader)
                if content is None:
                    continue
                resource_kind = pkg_resource.rsplit('.', -1)[0]
                supported_resource_kinds = ['dashboards', 'views', 'datasets']
                if resource_kind in supported_resource_kinds:
                    for item in content.values():
                        if item is not None:
                            item.update({'providedBy': self.name})
                    self.resources.update({
                        resource_kind: content
                    })
                else:
                    for v in content.values():
                        for item in v.values():
                            if item is not None:
                                item.update({'providedBy': self.name})
                    self.resources.update(content)
                
    def provides(self) -> dict:
        return self.resources
    
    def get_resource(self, resource_name) -> str:
        _resource = f'data/{resource_name}'
        if resource_exists(self.name, _resource):
            return resource_string(self.name, _resource).decode("utf-8")
        return None
