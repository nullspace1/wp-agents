from typing import Any

from model.agent import Agent
from model.auth import KeySet, generate_auth_key
from model.api import API
from model.operation import Operation
from model.operation_result import AgentViewableValue, JsonLike, OperationResult, OperationStatus
from model.parameter import ParameterTemplate
from model.resource import Resource, ResourceKeyPair


def get(resource : Resource[API], agent : Agent, params : dict[str, Any]) -> OperationResult:
    search_query : str  = params.get("search") or ""
    resources : JsonLike = resource.data.search(agent, search_query)
    return {
        "status": OperationStatus.CONTINUE,
        "output": AgentViewableValue(resources)
    }
    
def scanner(
    owner: Agent,
    api : API
) -> ResourceKeyPair[API]:
    keyset = KeySet(get=generate_auth_key())
    return keyset, Resource[API](
        owner=owner,
        group=None,
        name="scanner",
        description=f"Resource scanner for listing and filtering resources in the {api.name} API",
        auth_keys=keyset,
        data=api,
        get_op=Operation[API](
            operation=get,
            param_templates=[
                ParameterTemplate("search", "Search query to filter resources by name", str, required=False),
                ParameterTemplate("depth", "Depth for recursive search (0 for no recursion)", int, required=False),
            ],
            description="List all resources in the API and filter them by name"
        )
    )