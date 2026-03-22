from __future__ import annotations

from typing import TYPE_CHECKING

from model.auth import generate_auth_key
from model.resource import KeySet, Resource
from model.operation import Operation
from model.parameter import ParameterTemplate
from model.operation_result import AgentViewableValue, AgentState

if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.operation_result import OperationResult
    from model.types import ResourceKeyPair


def post(resource: Resource[None], agent: 'Agent', params: dict[str, Any]) -> OperationResult:
    message = params.get("message", "")
    return {
        "status": AgentState.STOP,
        "output": AgentViewableValue({
            "message": "Message sent to user.",
            "response": message,
        })
    }

def send_agent_reply(
    owner: 'Agent',
) -> ResourceKeyPair:
    authentication_key = generate_auth_key()
    return KeySet(post=authentication_key), Resource[None](
        owner=owner,
        group=None,
        name=f"agent_response",
        description=f"Return a response to the user.",
        auth_keys=KeySet(post=authentication_key),
        data=None,
        post_op=Operation['None'](
            operation=post,
            param_templates=[
                ParameterTemplate("message", "The message to send to the agent",  converter=str, required=True),
            ],
            description="Send a message to the user and stops the agent's execution."
        )
    )
    return authentication_key, resource
