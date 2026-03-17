from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, TypedDict

if TYPE_CHECKING:
    from typing import TypeAlias

D = TypeVar('D')


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