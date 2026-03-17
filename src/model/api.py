from __future__ import annotations

from typing import TYPE_CHECKING

from model.operation_result import AgentViewable
 
if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.resource import Resource
    from model.types import Json, JsonDict

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
        self.__path_graph__ : APINode = APINode('', [], False)

    def mount(self, resource: Resource[Any]) -> None:
        self.resources.add(resource)

    def get(self, agent : Agent, path : str) -> Resource[Any] | None:
        self.__build_path_graph__(agent)
        for resource in self.resources:
            view  = resource.view(agent)
            if view and view["name"] == path:
                return resource
    def search(self, agent : Agent, query : str, depth : int = 0, root_node : APINode | None = None) -> Json:
        self.__build_path_graph__(agent)
        
        root : APINode = root_node if root_node else self.__path_graph__
         
        node : APINode | None = self.__find_node__(root, query)
        
        if not node:
            return {}
        
        if node.is_resource:
            res = self.get(agent, query)
            view = res.view(agent) if res else None
            return view if view else {}
        else:
            visible_children = [c for c in node.children if self.__has_visible_resource__(agent, c)]
            
            if depth == 0:
                data : Json = {
                    "name": node.name,
                    "description": f"This path contains {len(visible_children)} sub-resources"
                }     
            else:
                search_result = [self.search(agent, f"{node.name}/{c.name}", depth - 1, c) for c in visible_children]
                data : Json = search_result
                
            return data
        
    def view(self, agent : Agent) -> JsonDict | None:
        return {
            "name": self.name,
            "description": self.description,
            "root_resources": self.search(agent, "", depth=0) or []
        }
        
    def get_property(self,  agent: Agent, key: str) -> Json | None:
        value = self.view(agent)
        if value:
            return value.get(key)
        
    def __has_visible_resource__(self, agent: Agent, node: APINode) -> bool:
        count = 0
        for r in self.resources:
            view = r.view(agent)
            if view and view["name"] == node.name:
                count += 1
        return count > 0


    def __build_path_graph__(self, agent: Agent) -> None:
        root = APINode('', [], False)
        for resource in self.resources:
            view = resource.view(agent)
            if not view:
                continue
            name = view["name"]
            split_path : list[str] = name.split('/')
            current_node = root
            for part in split_path:
                found_node = None
                for child in current_node.children:
                    if child.name == part:
                        found_node = child
                        break
                if not found_node:
                    found_node = APINode(part, [], False)
                    current_node.children.append(found_node)
                current_node = found_node
            current_node.is_resource = True
        self.__path_graph__ = root
        self.__graph_dirty__ = False
        
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