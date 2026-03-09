from __future__ import annotations

from enum import Enum
from typing import TypedDict


class OperationStatus(Enum):
    CONTINUE = 1
    STOP = 2
    

type op_result = dict[str, list[op_result] | str | op_result]


class OperationResult(TypedDict):
    status: OperationStatus
    output: op_result | None
