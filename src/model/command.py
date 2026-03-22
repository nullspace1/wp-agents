from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Any

    from model.enums import OperationType


class Command(TypedDict):
    resource: str
    operation: OperationType
    parameters: dict[str, Any]
