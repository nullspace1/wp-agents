from __future__ import annotations

from typing import TYPE_CHECKING, cast

from model.auth import KeySet, generate_auth_key
from model.operation import Operation
from model.operation_result import AgentViewableValue, AgentState
from model.parameter import ParameterTemplate
from model.resource import Resource

if TYPE_CHECKING:
    from typing import Any
    from model.agent import Agent
    from model.operation_result import OperationResult
    from model.types import ResourceKeyPair


def get(resource : Resource[str], agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
    return {
        "status": AgentState.CONTINUE,
        "output": AgentViewableValue(resource.data)
    }
    
def post(resource : Resource[str], agent : Agent, params : dict[str, Any]) -> OperationResult:
    new_content : str = cast(str,params.get("content"))
    resource.data = new_content
    return {
            "status": AgentState.CONTINUE,
            "output": AgentViewableValue({
                "message": "Text resource updated successfully."
            })
    }
  
def text(
    owner: Agent,
    name: str,
    description: str,
    content: str
) -> ResourceKeyPair:
    authentication_key = KeySet(get=generate_auth_key(), post=generate_auth_key())
    return authentication_key, Resource[str](
        owner=owner,
        group=None,
        name=name,
        description=description,
        auth_keys=authentication_key,
        data=content,
        get_op=Operation[str](
            operation=get,
            param_templates=[],
            description="View the content of the text resource"
        ),
        post_op=Operation[str](
            operation=post,
            param_templates=[
                ParameterTemplate("content", "The new content for the text resource",  converter=str, required=True),
            ],
            description="Update the content of the text resource"
        )
    )