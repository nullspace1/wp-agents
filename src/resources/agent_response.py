from __future__ import annotations

from typing import Any, TYPE_CHECKING

from src.model.resource import Resource
from src.model.permission_level import PermissionLevel
from src.model.operation import Operation
from src.model.parameter import ParameterTemplate
from src.model.operation_result import OperationResult, OperationStatus

if TYPE_CHECKING:
    from src.model.agent import Agent


def post(resource: Resource['Agent'], agent: 'Agent', params: dict[str, Any]) -> OperationResult:
    """Send a message to the agent and receive a final response"""
    message = params.get("message", "")
    
    if not resource.data:
        raise ValueError("Agent resource not properly initialized")
    
    response = resource.data.message(message, agent)
    
    return {
        "status": OperationStatus.STOP,
        "output": {
            "response": response,
        }
    }


def agent_response(
    owner: 'Agent',
) -> Resource['Agent']:
    return Resource['Agent'](
        owner=owner,
        group=None,
        type="agent_response",
        name=f"agent_response",
        description=f"Allows the agent to return a response. Using this resource will stop the current operation chain and return the provided response to the caller.",
        user_permissions=PermissionLevel(get=False, post=True, patch=False, delete=False),
        group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        data=owner,
        post_op=Operation['Agent'](
            operation=post,
            param_templates=[
                ParameterTemplate("message", "The message to send to the agent", str, required=True),
            ],
            description="Send a message to the agent and receive a final response"
        )
    )
