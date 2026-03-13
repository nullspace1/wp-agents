from __future__ import annotations

from typing import Any, TYPE_CHECKING

from model.resource import Resource
from model.permission_level import PermissionLevel
from model.operation import Operation
from model.parameter import ParameterTemplate
from model.operation_result import OperationResult, OperationStatus

if TYPE_CHECKING:
    from model.agent import Agent


def post(resource: Resource[None], agent: 'Agent', params: dict[str, Any]) -> OperationResult:
    """Send a message to the agent and receive a final response"""
    message = params.get("message", "")
    
    return {
        "status": OperationStatus.STOP,
        "output": {
            "response": message,
        }
    }


def send_agent_reply(
    owner: 'Agent',
) -> Resource[None]:
    return Resource[None](
        owner=owner,
        group=None,
        type="agent_response",
        name=f"agent_response",
        description=f"Allows the agent to return a response. Using this resource will stop the current operation chain and return the provided response to the caller.",
        user_permissions=PermissionLevel(get=False, post=True, patch=False, delete=False),
        group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        data=None,
        post_op=Operation['None'](
            operation=post,
            param_templates=[
                ParameterTemplate("message", "The message to send to the agent", str, required=True),
            ],
            description="Send a message to the agent and receive a final response"
        )
    )
