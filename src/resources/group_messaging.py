from __future__ import annotations

import datetime
from typing import Any, TYPE_CHECKING

from src.model.resource import Resource
from src.model.permission_level import PermissionLevel
from src.model.operation import Operation
from src.model.parameter import ParameterTemplate
from src.model.operation_result import OperationResult, OperationStatus

if TYPE_CHECKING:
    from src.model.agent import Agent
    from src.model.group import Group


class MessagingData:
    """Data structure to hold group reference and messages"""
    def __init__(self, group: 'Group'):
        self.group = group
        self.messages: list[dict[str, Any]] = []


def get(resource: Resource[MessagingData], agent: Agent, params: dict[str, Any] | None = None) -> OperationResult:
    """Get all views from each group member"""
    if not resource.data or not resource.data.group:
        return {"status": OperationStatus.CONTINUE, "output": {"members": []}}
    
    member_info: list[dict[str, Any]] = []
    for member in resource.data.group.members:
        member_info.append({
                "name": member.name,
                "description": member.description
            })

    return {"status": OperationStatus.CONTINUE, "output": {"agents": member_info}}


def post(resource: Resource[MessagingData], agent: Agent, params: dict[str, Any]) -> OperationResult: 
    """Post a message to a specific agent in the group"""
    uuid = params.get("uuid", "")
    message = params.get("message", "")
    is_async = params.get("async", False)
    
    if not resource.data or not resource.data.group:
        raise ValueError("Messaging resource not properly initialized")
    
    target_agent = None
    for member in resource.data.group.members:
        if member.uuid == uuid:
            target_agent = member
            break
    
    if not target_agent:
        raise ValueError(f"Agent with uuid '{uuid}' not found in group '{resource.data.group.name}'")
    
    # Send the message to the target agent
    response = "" if is_async else target_agent.message(message)
    
    # Log the message exchange
    msg_entry = {
        "from": agent.name,
        "from_uuid": agent.uuid,
        "to": target_agent.name,
        "to_uuid": target_agent.uuid,
        "message": message,
        "response": response if not is_async else "[async - no response]",
        "timestamp": datetime.datetime.now().isoformat()
    }
   
    resource.data.messages.append(msg_entry)
    
    result = {
        "status": "message sent",
        "to": target_agent.name,
        "to_uuid": target_agent.uuid,
        "message": message,
        "timestamp": msg_entry["timestamp"]
    }
    
    if not is_async:
        result["response"] = response
    
    return {"status": OperationStatus.CONTINUE, "output": result}


def group_messaging(group: 'Group') -> Resource[MessagingData]:
    """Create a group messaging resource"""
    return Resource[MessagingData](
        owner=None,
        group=group,
        type="group_messaging",
        name=f"{group.name}_messaging",
        description=f"Inter-agent messaging for group {group.name}: {group.description}",
        user_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        group_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
        other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        data=MessagingData(group),
        get_op=Operation[MessagingData](
            operation=get,
            param_templates=[],
            description="Get all views from each group member"
        ),
        post_op=Operation[MessagingData](
            operation=post,
            param_templates=[
                ParameterTemplate("uuid", "The UUID of the agent to send the message to", str, required=True),
                ParameterTemplate("message", "The message to send to the agent", str, required=True),
                ParameterTemplate("async", "Whether to send asynchronously without waiting for response", bool, required=False)
            ],
            description="Send a message to a specific agent"
        )
    )
