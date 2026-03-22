from __future__ import annotations

from typing import TYPE_CHECKING

from model.auth import KeySet, generate_auth_key
from model.api import API
from model.operation import Operation
from model.operation_result import AgentViewableValue, AgentState
from model.parameter import ParameterTemplate
from model.resource import Resource

if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.operation_result import Json, OperationResult
    from model.types import ResourceKeyPair

def get(resource : Resource[API], agent : Agent, params : dict[str, Any]) -> OperationResult:
    search_query : str  = params.get("search") or ""
    depth : int = params.get("depth") or 0
    resources : Json = resource.data.search(agent, search_query, depth)
    return {
        "status": AgentState.CONTINUE,
        "output": AgentViewableValue(resources)
    }
    
def scanner(
    owner: Agent,
    api : API
) -> ResourceKeyPair:
    keyset = KeySet(get=generate_auth_key())
    return keyset, Resource[API](
        owner=owner,
        group=None,
        name="scanner",
        description=f"Resource scanner for listing and filtering resources in the {api.name} API that are visible to the agent.",
        auth_keys=keyset,
        data=api,
        get_op=Operation[API](
            operation=get,
            param_templates=[
                ParameterTemplate("search", "Search query to filter resources by name",  converter=str, required=False),
                ParameterTemplate("depth", "Depth for recursive search (0 for no recursion)",  converter=int, required=False),
            ],
            description="List all resources in the API that are visible to the agent and filter them by name"
        )
    )