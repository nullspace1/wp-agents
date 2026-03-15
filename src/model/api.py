from typing import Any

from model.agent import Agent
from model.operation_result import AgentViewable, JsonLike
from model.resource import Resource

class APINode:
    
    def __init__(self, name : str, children : list['APINode'], is_resource : bool):
        self.name = name
        self.children = children
        self.is_resource = is_resource

class API(AgentViewable):
    
    def __init__(self, name : str, description : str, resources : list[Resource[Any]]):
        self.name : str = name
        self.description : str = description
        self.resources : set[Resource[Any]] = set(resources)
        self.path_graph : APINode = APINode('', [], False)
        
    def mount(self,agent : Agent, resource: Resource[Any]):
        self.resources.add(resource)
        self.__update_path_graph__(agent, resource)

    def get(self, agent : Agent, path : str) -> Resource[Any]:
        for resource in self.resources:
            view : JsonLike | None = resource.view(agent)
            if view and view['name'] == path:
                return resource
        raise ValueError(f"Resource {path} not found in API {self.name} or agent {agent.get_full_name()} does not have access to it.")

    def search(self, agent : Agent, query : str, depth : int = 0, root_node : APINode | None = None) -> JsonLike:
        
        root : APINode = root_node if root_node else self.path_graph 
         
        node : APINode | None = self.__find_node__(root, query)
        
        if not node:
            return None
        
        if node.is_resource:
            return self.get(agent, query).view(agent)
        else:
            data : list[JsonLike] = []
            for child in node.children:
                
                if child.is_resource:
                        data.append(self.get(agent, f"{query}/{child.name}").view(agent))
                     
                if len(child.children) == 0:
                    if depth == 0:
                        data.append({
                            "name": child.name,
                            "description": f"Contains {len(child.children)} sub-resources"
                        })
                    else:
                        data.append(self.search(agent, child.name, depth - 1, child))
                    
            return data
    
    def __update_path_graph__(self, agent: Agent, resource: Resource[Any]):
        
        resource_view : JsonLike | None = resource.view(agent)
        
        if not resource_view:
            raise ValueError(f"Agent {agent.get_full_name()} does not have access to resource and cannot mount it on API {self.name}")
        
        split_path : list[str] = resource_view['name'].split('/')
        
        current_node = self.path_graph
        
        for part in split_path:
            found_node = None
            for child in current_node.children:
                if child.name == part:
                    found_node = child
                    break
            if not found_node:
                found_node = APINode(part, [],False)
                current_node.children.append(found_node)
            current_node = found_node
        
        current_node.is_resource = True
        
    def __find_node__(self,root_node : APINode, query : str) -> APINode | None:
        split_query : list[str] = query.split('/')
        current_node = root_node
        
        for part in split_query:
            found_node = None
            for child in current_node.children:
                if child.name == part:
                    found_node = child
                    break
            if not found_node:
                return None
            current_node = found_node
        return current_node
        
        
    def view(self, agent : Agent) -> JsonLike:
        return {
            "name": self.name,
            "description": self.description,
            "root_resources": self.search(agent, "", depth=0) 
        }

class Browser:
    
    def __init__(self):
        self.api : dict[str, API] = {}
        
    def mount_api(self, name: str, api: API):
        self.api[name] = api
