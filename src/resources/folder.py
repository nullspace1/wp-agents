from __future__ import annotations

from typing import Any, TYPE_CHECKING, cast

from model.resource import Resource
from model.permission_level import PermissionLevel
from model.group import Group
from model.operation import Operation
from model.parameter import ParameterTemplate
from model.enums import OperationType
from model.operation_result import AgentViewableValue, OperationResult, OperationStatus
from model.resource_types import ResourceViewDict

if TYPE_CHECKING:
    from model.agent import Agent


def sanitize_path(path: str) -> list[str]:
    parts = path.split("/")
    parts = [p.strip() for p in parts if p.strip()]
    return parts

def view_resource(resource: Resource[Any], agent: Agent) -> ResourceViewDict:
    return resource.view_direct(agent)

def get(resource : Resource[list[Resource[Any]]], agent : Agent, params : dict[str, Any]) -> OperationResult:
    path_str = params.get("path", "")
    path = sanitize_path(path_str) if path_str else []
    
    if not path:
        if resource.data:
            visible_resources = [r for r in resource.data if r.verify(agent, OperationType.GET)]
            contents = ",\n".join([str(r.view(agent)) for r in visible_resources])
            return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"contents": contents})}
        return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"contents": "empty"})}
    
    target_name = path[0]
    
    target_resource = None
    if resource.data:
        for r in resource.data:
            if view_resource(r, agent).get("name") == target_name:
                target_resource = r
                break
    
    if not target_resource:
        resource_view = view_resource(resource, agent)
        raise ValueError(f"Resource '{target_name}' not found in folder '{resource_view['name']}'")
    
    if len(path) > 1:
        target_view = view_resource(target_resource, agent)
        if target_view["type"] != "folder":
            raise ValueError(f"Resource '{target_name}' is not a folder, cannot navigate further")
        remaining_path = "/".join(path[1:])
        return target_resource.get(agent, {"path": remaining_path})
    else:
        return {"status": OperationStatus.CONTINUE, "output": target_resource}
    
def delete(resource : Resource[list[Resource[Any]]], agent : Agent, params : dict[str, Any]) -> OperationResult:
    path_str = params.get("path", "")
    path = sanitize_path(path_str) if path_str else []
    
    if not path:
        resource.data = []
        return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"status": "folder cleared"})}
    
    target_name = path[0]
    
    target_resource = None
    if resource.data:
        for r in resource.data:
            if view_resource(r, agent).get("name") == target_name:
                target_resource = r
                break
    
    if not target_resource:
        resource_view = view_resource(resource, agent)
        raise ValueError(f"Resource '{target_name}' not found in folder '{resource_view['name']}'")
    
    if len(path) > 1:
        target_view = view_resource(target_resource, agent)
        if target_view["type"] != "folder":
            raise ValueError(f"Resource '{target_name}' is not a folder, cannot navigate further")
        remaining_path = "/".join(path[1:])
        return target_resource.delete(agent, {"path": remaining_path})
    else:
        resource.data.remove(target_resource)
        resource_view = view_resource(resource, agent)
        return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"status": f"Resource '{target_name}' deleted from folder '{resource_view['name']}'"})}

def post(resource : Resource[list[Resource[Any]]], agent : Agent, params : dict[str, Any]) -> OperationResult:
    new_resource : Resource[Any] | None = cast(Resource[Any] | None, params.get("resource"))
    path_str = params.get("path", "")
    path = sanitize_path(path_str) if path_str else []

    if not new_resource and not path:
        raise ValueError("No resource provided to add to folder and no path to create one")

    if not resource.data:
        resource.data = []

    if not path and new_resource:
        resource.data.append(new_resource)
        new_view = view_resource(new_resource, agent)
        resource_view = view_resource(resource, agent)
        return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"status": f"Resource '{new_view['name']}' added to folder '{resource_view['name']}'"})}

    if new_resource:
        new_view = view_resource(new_resource, agent)
        folder_path = path[:-1] if path and path[-1] == new_view["name"] else path
    else:
        folder_path = path[:-1]
    current_folder = resource

    for segment in folder_path:
        if not current_folder.data:
            current_folder.data = []

        next_resource = None
        for child in current_folder.data:
            child_view = view_resource(child, agent)
            if child_view["name"] == segment:
                next_resource = child
                break

        if not next_resource:
            agent_group = agent.groups[0] if agent.groups else None
            resource_view = view_resource(resource, agent)
            user_permissions = resource_view["permissions"]["user"]
            group_permissions = resource_view["permissions"]["group"]
            other_permissions = resource_view["permissions"]["other"]
            next_resource = folder(
                agent=agent,
                group=agent_group,
                folder_name=segment,
                description=f"A folder resource named {segment} that can contain other resources",
                user_permissions=PermissionLevel(
                    get="get" in user_permissions,
                    post="post" in user_permissions,
                    patch="patch" in user_permissions,
                    delete="delete" in user_permissions,
                ),
                group_permissions=PermissionLevel(
                    get="get" in group_permissions,
                    post="post" in group_permissions,
                    patch="patch" in group_permissions,
                    delete="delete" in group_permissions,
                ),
                other_permissions=PermissionLevel(
                    get="get" in other_permissions,
                    post="post" in other_permissions,
                    patch="patch" in other_permissions,
                    delete="delete" in other_permissions,
                )
            )
            current_folder.data.append(next_resource)

        next_view = view_resource(next_resource, agent)
        if next_view["type"] != "folder":
            raise ValueError(f"Resource '{segment}' is not a folder, cannot navigate further")

        current_folder = cast(Resource[list[Resource[Any]]], next_resource)

    if not current_folder.data:
        current_folder.data = []

    if not new_resource:
        folder_name = path[-1]
        agent_group = agent.groups[0] if agent.groups else None
        new_resource = folder(
            agent=agent,
            group=agent_group,
            folder_name=folder_name,
            description=f"A folder resource named {folder_name} that can contain other resources",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )

    current_folder.data.append(new_resource)
    new_view = view_resource(new_resource, agent)
    current_view = view_resource(current_folder, agent)
    return {"status": OperationStatus.CONTINUE, "output": AgentViewableValue({"status": f"Resource '{new_view['name']}' added to folder '{current_view['name']}'"})}


def folder(
    agent : Agent,
    group : Group | None, 
    folder_name : str,
    description : str,
    user_permissions : PermissionLevel, 
    group_permissions : PermissionLevel, 
    other_permissions : PermissionLevel,
    ) -> Resource[list[Resource[Any]]]: 
    return Resource(
        owner=agent,
        group=group,
        type="folder",
        name=folder_name,
        description=description,
        user_permissions=user_permissions,
        group_permissions=group_permissions,
        other_permissions=other_permissions,
        data=[],
        get_op=Operation[list[Resource[Any]]](
            operation=get,
            param_templates=[ParameterTemplate("path", "Path to navigate within the folder", str, required=False)],
            description="Get a resource from the folder by path"
        ),
        delete_op=Operation[list[Resource[Any]]](
            operation=delete,
            param_templates=[ParameterTemplate("path", "Path to navigate within the folder", str, required=False)],
            description="Delete a resource from the folder by path"
        ),
        post_op=Operation[list[Resource[Any]]](
            operation=post,
            param_templates=[
                ParameterTemplate("path", "Path to navigate within the folder", str, required=False),
                ParameterTemplate("resource", "The resource to add to the folder", Resource, required=False)
            ],
            description="Add a resource to the folder at the specified path"
        )
    )