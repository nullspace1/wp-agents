from __future__ import annotations

from typing import TYPE_CHECKING, Any

from model.api import API
from model.resource import Resource

if TYPE_CHECKING:
    from model.agent import Agent

class Group:
    
    def __init__(self, uuid : str, name : str, description : str, api : API):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.members : list[Agent] = []
        self.api : API = api

    def add_member(self, agent: 'Agent') -> None:
        if agent in self.members:
            return
        self.members.append(agent)
        agent.add_api(self.api)
        
    def add_resource(self,agent: Agent, resource: Resource[Any]):
        self.api.mount(agent, resource)
            
ADMIN = Group(uuid="admin", name="Admin", description="The admin group for the system. Has access to all resources", api=API("admin", "Admin API with access to all resources", []))
