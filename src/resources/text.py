from __future__ import annotations

from typing import Any

from src.model.resource import Resource
from src.model.permission_level import PermissionLevel
from src.model.operation import Operation
from src.model.parameter import ParameterTemplate
from src.model.agent import Agent
from src.model.group import Group
from src.model.operation_result import OperationResult, OperationStatus


def get(resource : Resource[str], agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
    return {"status": OperationStatus.CONTINUE, "output": {"content": resource.data or ""}}

def patch(resource : Resource[str], agent : Agent, params : dict[str, Any]) -> OperationResult:
    if not resource.data:
        resource.data = ""
    resource.data = params.get("content", "")
    return {"status": OperationStatus.CONTINUE, "output": {"content": resource.data or ""}}

def delete(resource : Resource[str], agent : Agent, params : dict[str, Any]) -> OperationResult:
    resource.data = ""
    return {"status": OperationStatus.CONTINUE, "output": {"status": "content deleted"}}


def text(
    agent : Agent,
    group : Group | None, 
    user_permissions : PermissionLevel, 
    group_permissions : PermissionLevel, 
    other_permissions : PermissionLevel,
    text_summary : str,
    text : str
    ) -> Resource[str]:
    return Resource[str](
        owner=agent,
        group=group,
        type="text",
        name="text",
        description=text_summary,
        user_permissions=user_permissions,
        group_permissions=group_permissions,
        other_permissions=other_permissions,
        data=text,
        get_op=Operation[str](
            operation=get,
            param_templates=[],
            description="Retrieve the text content"
        ),
        patch_op=Operation[str](
            operation=patch,
            param_templates=[
                ParameterTemplate("content", "The text content to store", str, required=True)],
            description="Update the text content"
        ),
        delete_op=Operation[str](
            operation=delete,
            param_templates=[],
            description="Delete the text content"
        )
    )