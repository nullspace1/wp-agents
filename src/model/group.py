from __future__ import annotations

from typing import TYPE_CHECKING

from model.api import API
from model.types import ResourceKeyPair

if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.resource import Resource

class Group:
    
    def __init__(self, uuid : str, name : str, description : str, api : API, auth_keys : list[ResourceKeyPair]):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.members : list[Agent] = []
        self.api : API = api
        self.keypairs : list[ResourceKeyPair] = auth_keys
        
    def add_member(self, agent: 'Agent') -> None:
        if agent in self.members:
            return
        self.members.append(agent)
        agent.add_api(self.api)
        for (key, resource) in self.keypairs:
            agent.add_keys_for_resource(resource, key)
        
    def add_resource(self,agent: Agent, resource: Resource[Any]):
        if agent not in self.members:
            raise Exception("Agent not in group")
        self.api.mount(resource)
            
ADMIN = Group(uuid="admin", name="Admin", description="The admin group for the system. Has access to all resources", api=API("admin", "Admin API with access to all resources", []), auth_keys=[])
