from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING,  TypeAlias, TypedDict, TypeGuard

if TYPE_CHECKING:
    from model.agent import Agent


class OperationStatus(Enum):
    CONTINUE = 1
    STOP = 2
    FAIL = 3


JsonPrimitive: TypeAlias = str | int | float | bool

Json: TypeAlias = (
    JsonPrimitive
    | list[str]
    | list['Json']
    | dict[str, 'Json']
    | dict[str, str]
    | dict[str, dict[str,str]]
    | dict[str, list[str]]
    | dict[str, JsonPrimitive]
    | dict[str, list[JsonPrimitive]]
    | dict[str, str | int]
)

JsonDict = dict[str, Json]

class NamedJsonDict(TypedDict):
    name: str


def has_name(value: JsonDict | None) -> TypeGuard[NamedJsonDict]:
    return value is not None and isinstance(value.get("name"), str)


def get_name(value: JsonDict | None) -> str | None:
    if has_name(value):
        return value["name"]
    return None

class AgentViewable(ABC):
    
    @abstractmethod
    def view(self, agent : Agent) -> JsonDict | None:
        pass
    
    @abstractmethod
    def get_property(self,agent : Agent, key : str) -> Json | None:
        pass

class AgentViewableValue(AgentViewable):

    def __init__(self, value: JsonDict) -> None:
        self.value = value

    def view(self, agent: Agent) -> JsonDict | None:
        return self.value
    
    def get_property(self, agent: Agent, key: str) -> Json | None:
        value = self.view(agent)
        if value:
            return value.get(key)


class OperationResult(TypedDict):
    status: OperationStatus
    output: AgentViewable
