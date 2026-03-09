from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from src.resources.messaging import group_messaging

if TYPE_CHECKING:
    from src.model.agent import Agent
    from src.model.resource import Resource

class Group:
    
    def __init__(self, uuid : str, name : str):
        self.uuid = uuid
        self.name = name
        self.members : list['Agent'] = []
        self.messaging_resource : Optional['Resource[Any]'] = group_messaging(group=self)
        
    def add_member(self, agent : 'Agent'):
        if agent not in self.members:
            self.members.append(agent)
            agent.data.post(agent, {"path": f"groups/{self.name}-{self.uuid}/messaging", "resource": self.messaging_resource})
            
ADMIN = Group(uuid="admin", name="Admin")
