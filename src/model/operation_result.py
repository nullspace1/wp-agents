from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from model.agent import Agent
    from model.types import Json


class OperationStatus(Enum):
    CONTINUE = 1
    STOP = 2
    FAIL = 3

class AgentViewable(ABC):
    
    @abstractmethod
    def view(self, agent : Agent) -> Json | None:
        pass

class AgentViewableValue(AgentViewable):

    def __init__(self, value: Json) -> None:
        self.value = value

    def view(self, agent: Agent) -> Json | None:
        return self.value

class OperationResult(TypedDict):
    status: OperationStatus
    output: AgentViewable
