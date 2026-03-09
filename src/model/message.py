from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.model.agent import Agent


class Message:
    
    def __init__(self, agent: 'Agent', content: str, timestamp: datetime.datetime | None = None):
        self.agent = agent
        self.content = content
        self.timestamp = timestamp or datetime.datetime.now()
        
    def __str__(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent.name}: {self.content}"
