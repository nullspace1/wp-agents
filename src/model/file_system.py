
from typing import Any, cast
from typing import TYPE_CHECKING

from resources.folder import sanitize_path

if TYPE_CHECKING:
    from model.resource import Resource
    from model.agent import Agent

class FileSystem:
    
    def __init__(self, root_resources : list[Resource[Any]]):
        self.root = root_resources

    def mount(self, resource: Resource[Any]) -> None:
        self.root.append(resource)

    def get_resource(self,agent: Agent, path: str) -> Resource[Any]:
        
        if not path:
            raise ValueError("Path cannot be empty")
        
        path_parts : list[str] = sanitize_path(path)
    
        
        return self.__get_resource__(agent, self.root, path_parts)
        
    def __get_resource__(self, agent: Agent, resource_list: list[Resource[Any]], path_parts: list[str]) -> Resource[Any]:
        
        target_resource = None
        
        for r in resource_list:
            if r.retrieve_agent_view(agent).get("name") == path_parts[0]:
                target_resource = r
                break
        
        if not target_resource:
            raise ValueError(f"Resource '{path_parts[0]}' not found")
        
        if len(path_parts) == 1:
            return target_resource
        else:
            if target_resource.retrieve_agent_view(agent).get("type") == "folder":
                folder_target_resource = cast(Resource[list[Resource[Any]]], target_resource)
                return self.__get_resource__(agent, folder_target_resource.data if folder_target_resource.data else [], path_parts[1:])
            else:
                raise ValueError(f"Resource '{path_parts[0]}' is not a folder, cannot navigate further")
        