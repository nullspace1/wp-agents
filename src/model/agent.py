from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
import uuid

from src.model.group import Group
from src.model.permission_level import PermissionLevel
from src.resources.folder import folder

if TYPE_CHECKING:
    from src.model.resource import Resource


class Agent:
    
    def __init__(self, name : str, description : str, groups : list[Group] | None = None,mounted_resources : list[Resource[Any]] | None = None):
        
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.groups = groups or []
        self.provider : AgentProvider | None = None
        
        self.data = folder(
            agent=self,
            group=None,
            folder_name=f"{self.name}_data",
            description=f"Data folder for agent {self.name}",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
        
        for resource in mounted_resources or []:
            self.mount("", resource)
        
        for group in self.groups:
            group.add_member(self)
            
        self.__setup()
            
    def message(self, message : str) -> str:
        ## TODO - implement message sending to provider and receiving response
        return ""
    
    def mount(self, path: str, resource: Resource[Any]):
        self.data.post(self, {
            "path": path,
            "resource": resource
        })
    
    def __setup(self):
        groups_folder = folder(
            agent=self,
            group=None,
            folder_name="groups",
            description="Folder containing group messaging resources",
            user_permissions=PermissionLevel(get=True, post=False, patch=False, delete=False),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
        self.mount("", groups_folder)
            

        

class AgentProvider(ABC):
    
    @abstractmethod
    def send_message(self, message : str) -> str:
        pass
    
    
class AgentBuilder:
    
    def __init__(self):
        self.provider : AgentProvider | None = None
        self.groups : list[Group] = []
        self.api_resource : Resource[Any] | None = None
        self.mounts : list[Resource[Any]] = []
        self.description : str = ""
    
    def with_provider(self, provider : AgentProvider) -> 'AgentBuilder':
        self.provider = provider
        return self
    
    def with_groups(self, groups : list[Group]) -> 'AgentBuilder':
        self.groups = groups
        return self
    
    def with_mounted_resources(self, resources : list[Resource[Any]]) -> 'AgentBuilder':
        self.mounts = resources
        return self
    
    def with_description(self, description : str) -> 'AgentBuilder':
        self.description = description
        return self

    def build(self, name : str) -> Agent:
        agent = Agent(
            name=name,
            description=self.description,
            groups=self.groups,
            mounted_resources=self.mounts
        )
        agent.provider = self.provider
        return agent
        