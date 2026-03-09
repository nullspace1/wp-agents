from __future__ import annotations

from typing import Any, TYPE_CHECKING, TypeVar, cast

from src.model.resource import Resource, op_result
from src.model.permission_level import PermissionLevel
from src.model.operation import Operation
from src.model.parameter import ParameterTemplate
from src.model.group import Group

if TYPE_CHECKING:
    from src.model.agent import Agent


T = TypeVar("T")


def get(resource: Resource[list[T]], agent: Agent, params: dict[str, Any] | None = None) -> op_result:
    index = (params or {}).get("index")

    if index is None:
        return {"items": cast(Any, resource.data)}

    if not isinstance(index, int):
        raise ValueError("Parameter index must be of type int.")

    if index < 0 or index >= len(resource.data):
        raise IndexError("Index out of range.")

    return {"item": cast(Any, resource.data[index])}


def post(resource: Resource[list[T]], agent: Agent, params: dict[str, Any]) -> op_result:
    value = cast(T, params.get("value"))
    resource.data.append(value)
    return {"status": "item appended"}


def patch(resource: Resource[list[T]], agent: Agent, params: dict[str, Any]) -> op_result:
    index = params.get("index")
    value = cast(T, params.get("value"))

    if not isinstance(index, int):
        raise ValueError("Parameter index must be of type int.")

    if index < 0 or index > len(resource.data):
        raise IndexError("Index out of range.")

    resource.data.insert(index, value)
    return {"status": "item inserted"}


def delete(resource: Resource[list[T]], agent: Agent, params: dict[str, Any] | None = None) -> op_result:
    index = (params or {}).get("index")

    if not isinstance(index, int):
        raise ValueError("Parameter index must be of type int.")

    if index < 0 or index >= len(resource.data):
        raise IndexError("Index out of range.")

    resource.data.pop(index)
    return {"status": "item deleted"}


def list_resource(
    agent: Agent,
    group: Group | None,
    resource_name: str,
    description: str,
    user_permissions: PermissionLevel,
    group_permissions: PermissionLevel,
    other_permissions: PermissionLevel,
    initial_data: list[T] | None = None,
) -> Resource[list[T]]:
    return Resource[list[T]](
        owner=agent,
        group=group,
        type="list",
        name=resource_name,
        description=description,
        user_permissions=user_permissions,
        group_permissions=group_permissions,
        other_permissions=other_permissions,
        data=initial_data or [],
        get_op=Operation[list[T]](
            operation=get,
            param_templates=[
                ParameterTemplate("index", "Optional index to fetch", int, required=False),
            ],
            description="Get an item by optional index or return the full list",
        ),
        post_op=Operation[list[T]](
            operation=post,
            param_templates=[
                ParameterTemplate("value", "Value to append", object, required=True),
            ],
            description="Append a value to the list",
        ),
        patch_op=Operation[list[T]](
            operation=patch,
            param_templates=[
                ParameterTemplate("index", "Index to insert into", int, required=True),
                ParameterTemplate("value", "Value to insert", object, required=True),
            ],
            description="Insert a value at the given index",
        ),
        delete_op=Operation[list[T]](
            operation=delete,
            param_templates=[
                ParameterTemplate("index", "Index to delete", int, required=True),
            ],
            description="Delete the value at the given index",
        ),
    )
