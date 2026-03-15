from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
import json
from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict, cast

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
    operation_timestamps: dict[str, str | None]
    last_error: str | None


JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonLike: TypeAlias = (
    JsonPrimitive
    | list['JsonLike']
    | dict[str, 'JsonLike']
    | ResourceViewDict
)

class AgentViewable(ABC):
    
    @abstractmethod
    def view(self, agent : Agent) -> JsonLike | None:
        pass


class AgentViewableValue(AgentViewable):

    def __init__(self, value: Any) -> None:
        self.value = value

    def view(self, agent: Agent) -> JsonLike:
        return cast(JsonLike, json.loads(json.dumps(self.value, default=str)))


class OperationResult(TypedDict):
    status: OperationStatus
    output: AgentViewable
