from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
import json
from typing import TYPE_CHECKING, Any, Mapping, Sequence, TypeAlias, TypedDict, cast

from model.resource_types import ResourceViewDict

if TYPE_CHECKING:
    from model.agent import Agent


class OperationStatus(Enum):
    CONTINUE = 1
    STOP = 2
    FAIL = 3


JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonLike: TypeAlias = JsonPrimitive | Mapping[str, "JsonLike"] | Sequence["JsonLike"] | ResourceViewDict


class AgentViewable(ABC):
    
    @abstractmethod
    def view(self, agent : Agent) -> JsonLike:
        pass


class AgentViewableValue(AgentViewable):

    def __init__(self, value: Any) -> None:
        self.value = value

    def view(self, agent: Agent) -> JsonLike:
        return cast(JsonLike, json.loads(json.dumps(self.value, default=str)))


class OperationResult(TypedDict):
    status: OperationStatus
    output: AgentViewable
