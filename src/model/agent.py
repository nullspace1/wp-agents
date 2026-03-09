from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
import uuid

from model.message import Message
from resources.agent_response import agent_response
from src.model.group import Group
from src.model.permission_level import PermissionLevel
from src.resources.folder import folder
from src.resources.list import list_resource

if TYPE_CHECKING:
    from src.model.resource import Resource


class Agent:
    
    def __init__(self, name : str, description : str, groups : list[Group] | None = None,mounted_resources : list[Resource[Any]] | None = None):
        
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.groups = groups or []
        self.provider : AgentProvider | None = None
        self.context_resources: Resource[list[str]]
        self.message_history: Resource[list[Message]]
        
        self.data = folder(
            agent=self,
            group=None,
            folder_name=f"{self.name}_data",
            description=f"Data folder for agent {self.name}",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
            
        self.__setup__(mounted_resources)
            
    def message(self, message: str, agent : Agent | None = None) -> str:
        return ""

    
    def mount(self, path: str, resource: Resource[Any]):
        self.data.post(self, {
            "path": path,
            "resource": resource
        })
    
    def __setup__(self, mounted_resources: list[Resource[Any]] | None = None):
        groups_folder = folder(
            agent=self,
            group=None,
            folder_name="groups",
            description="Folder containing all the available groups of agents to communicate with",
            user_permissions=PermissionLevel(get=True, post=False, patch=False, delete=False),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
        self.context_resources = list_resource(
            agent=self,
            group=None,
            resource_name="context_resources",
            description="Resource paths whose metadata is exposed when receiving a message",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            initial_data=[],
        )
        self.message_history = list_resource(
            agent=self,
            group=None,
            resource_name="message_history",
            description="History of messages sent to this agent",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            initial_data=[],
        )
        self.response  = agent_response(self) 

        self.mount("", groups_folder)
        self.mount("", self.context_resources)
        self.mount("", self.message_history)
        self.mount("", self.response)
        
        for resource in mounted_resources or []:
            self.mount("", resource)
        
        for group in self.groups:
            group.add_member(self)

        

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
        