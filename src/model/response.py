from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from model.enums import OperationType


@dataclass(slots=True)
class Response:
    resource: str
    operation: OperationType
    parameters: dict[str, Any]
