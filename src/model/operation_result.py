from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias, TypedDict

if TYPE_CHECKING:
    from model.agent import Agent


class OperationStatus(Enum):
    CONTINUE = 1
    STOP = 2
    FAIL = 3


class ResourceViewDict(TypedDict):
    name: str
    created_at: str
    description: str
    operations: dict[str, str]
    operation_timestamps: dict[str, str]
    last_error: str


JsonPrimitive: TypeAlias = str | int | float | bool

Json: TypeAlias = (
    JsonPrimitive
    | list[str]
    | list['Json']
    | dict[str, 'Json']
    | dict[str, dict[str,'Json']]
    | dict[str, 'Json']
    | dict[str, list[JsonPrimitive]]
    | dict[str, str | int]
    | ResourceViewDict
)

JsonDict: TypeAlias = dict[str, Json]

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
