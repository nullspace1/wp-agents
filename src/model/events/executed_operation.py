from __future__ import annotations

import datetime
from typing import Any, TypedDict, TYPE_CHECKING, Generic
from ..enums import OperationType
from ..typebar import D
from .events import Event

if TYPE_CHECKING:
    from ..agent import Agent
    from ..operation import Operation
    from ..operation_result import AgentState
    from ..resource import Resource


class ExecutedOperationEventData(TypedDict, Generic[D]):
    resource: 'Resource[D]'
    resource_name: str
    operation: 'Operation[D]'
    operation_type: OperationType
    status: 'AgentState'
    output: Any
    parameters: dict[str, Any]
    agent: 'Agent'
    exception: Exception | None
    timestamp: datetime.datetime


def executed_operation_event(
    resource: "Resource[D]",
    resource_name: str,
    operation: "Operation[D]",
    operation_type: OperationType,
    status: "AgentState",
    output: Any,
    parameters: dict[str, Any],
    agent: "Agent",
    exception: Exception | None = None,
    timestamp: datetime.datetime | None = None,
):
    return Event[ExecutedOperationEventData[D]](
        event_data={
            "resource": resource,
            "resource_name": resource_name,
            "operation": operation,
            "operation_type": operation_type,
            "status": status,
            "output": output,
            "parameters": parameters,
            "agent": agent,
            "exception": exception,
            "timestamp": timestamp or datetime.datetime.now(),
        },
        to_string=lambda event: f"{event['resource']} {event['operation']} {event['operation_type']} {event['status']} {event['output']} {event['agent']} {event['timestamp']}",
    )
