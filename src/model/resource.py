from __future__ import annotations

import datetime
from typing import Any, Generic, TYPE_CHECKING, cast

from model.enums import OperationType
from model.operation import Operation
from model.permission_level import PermissionLevel
from model.events import Event, EventEmitter
from model.types import D
from model.resource_types import ResourceViewDict
from model.operation_result import OperationResult, OperationStatus

if TYPE_CHECKING:
    from model.agent import Agent
    from model.group import Group

class Resource(Generic[D], EventEmitter[D]):
    
    def __init__(self, 
                 owner : Agent | None, 
                 group : Group | None, 
                 type : str,
                 name : str,
                 description : str,
                 user_permissions : PermissionLevel, 
                 group_permissions : PermissionLevel, 
                 other_permissions : PermissionLevel,
                 data : D,
                 get_op : Operation[D] | None = None, 
                 post_op : Operation[D] | None = None,
                 patch_op : Operation[D] | None = None,
                 delete_op : Operation[D] | None = None,
                 created_at : datetime.datetime | None = None, 
                 ):
        super().__init__()
        self.__name__ : str = name
        self.__description__ : str = description
        self.__type__ : str  = type
        self.__created_at__ : datetime.datetime = created_at or datetime.datetime.now()
        self.__owner__ : Agent | None = owner
        self.__group__ : Group | None = group
        self.__get_op__ : Operation[D] | None = get_op
        self.__post_op__ : Operation[D] | None = post_op
        self.__patch_op__ : Operation[D] | None = patch_op
        self.__delete_op__ : Operation[D] | None = delete_op
        self.__user_permissions__ : PermissionLevel = user_permissions
        self.__group_permissions__ : PermissionLevel = group_permissions
        self.__other_permissions__ : PermissionLevel = other_permissions
        self.__last_operation_at__ : dict[str, datetime.datetime | None] = {
            "get": None,
            "post": None,
            "patch": None,
            "delete": None,
        }
        self.__last_error__ : str | None = None
        self.data : D  = data
    
    def get(self, agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
        """Retrieve the full resource contents.
        
        Fetches the complete contents of the resource (e.g., file contents, collection tree).
        Requires GET permission. Emits a SUCCESS or FAILURE event upon completion.
        
        Args:
            agent: The agent performing the operation. Must have GET permission.
            params: Optional dictionary of parameters to pass to the operation handler.
        
        Returns:
            Any: The full resource contents, which can be of any type depending on the resource (e.g., string for file contents, list of child resources for a collection).
        
        Raises:
            PermissionError: If the user does not have GET permission on this resource.
            Exception: Any exception raised by the operation handler is re-raised after emitting a FAILURE event.
        """
        if not self.__get_op__:
            raise NotImplementedError("GET operation is not implemented for this resource.")
        if not self.__verify_permissions__(agent, OperationType.GET):
            raise PermissionError("You do not have permission to GET this file.")
        try: 
            result = self.__get_op__.execute(self, agent, params or {})
            self.__last_operation_at__["get"] = datetime.datetime.now()
            self.__last_error__ = None
            self.emit(Event(self, self.__get_op__, OperationType.GET, result["status"], result["output"], params or {}, agent))
            return result
        except Exception as e:
            self.__last_operation_at__["get"] = datetime.datetime.now()
            self.__last_error__ = str(e)
            error_output: dict[str, dict[str, str]] = {
                "exception": {
                    "type": type(e).__name__,
                    "message": str(e),
                }
            }
            self.emit(Event(self, self.__get_op__, OperationType.GET, OperationStatus.FAIL, error_output, params or {}, agent, e))
            return {"status": OperationStatus.FAIL, "output": cast(Any,error_output)}
            
    def post(self, agent : Agent, params : dict[str, Any]) -> OperationResult:
        """Add new content to the resource.
        
        Appends or adds new content to the resource (e.g., appending to a file or adding 
        a new resource to a collection). Requires POST permission. Emits a SUCCESS or FAILURE event upon completion.
        
        Args:
            agent: The agent performing the operation. Must have POST permission.
            params: Dictionary of parameters to pass to the operation handler (required).
        
        Returns:
            Describable: Result of the post operation, which can be of any type depending on the operation handler.
        
        Raises:
            PermissionError: If the user does not have POST permission on this resource.
            Exception: Any exception raised by the operation handler is re-raised after emitting a FAILURE event.
        """
        if not self.__post_op__:
            raise NotImplementedError("POST operation is not implemented for this resource.")
        if not self.__verify_permissions__(agent, OperationType.POST):
            raise PermissionError("You do not have permission to POST to this file.")
        try:
            result = self.__post_op__.execute(self, agent, params)
            self.__last_operation_at__["post"] = datetime.datetime.now()
            self.__last_error__ = None
            self.emit(Event(self, self.__post_op__, OperationType.POST, result["status"], result["output"], params, agent))
            return result
        except Exception as e:
            self.__last_operation_at__["post"] = datetime.datetime.now()
            self.__last_error__ = str(e)
            error_output: dict[str, dict[str, str]] = {
                "exception": {
                    "type": type(e).__name__,
                    "message": str(e),
                }
            }
            self.emit(Event(self, self.__post_op__, OperationType.POST, OperationStatus.FAIL, error_output, params, agent, e))
            return {"status": OperationStatus.FAIL, "output": cast(Any, error_output)}
            
    def patch(self, agent : Agent, params : dict[str, Any]) -> OperationResult:
        """Modify existing content in the resource.
        
        Updates or modifies existing content in the resource (e.g., updating file contents 
        or modifying a resource in a collection). Requires PATCH permission. Emits a SUCCESS or FAILURE event upon completion.
        
        Args:
            agent: The agent performing the operation. Must have PATCH permission.
            params: Dictionary of parameters to pass to the operation handler (required).
        
        Returns:
            Resource[D]: Result of the patch operation.
        
        Raises:
            PermissionError: If the user does not have PATCH permission on this resource.
            Exception: Any exception raised by the operation handler is re-raised after emitting a FAILURE event.
        """
        if not self.__patch_op__:
            raise NotImplementedError("PATCH operation is not implemented for this resource.")
        if not self.__verify_permissions__(agent, OperationType.PATCH):
            raise PermissionError("You do not have permission to PATCH this file.")
        try:
            result = self.__patch_op__.execute(self, agent, params)
            self.__last_operation_at__["patch"] = datetime.datetime.now()
            self.__last_error__ = None
            self.emit(Event(self, self.__patch_op__, OperationType.PATCH, result["status"], result["output"], params, agent))
            return result
        except Exception as e:
            self.__last_operation_at__["patch"] = datetime.datetime.now()
            self.__last_error__ = str(e)
            error_output: dict[str, dict[str, str]] = {
                "exception": {
                    "type": type(e).__name__,
                    "message": str(e),
                }
            }
            self.emit(Event(self, self.__patch_op__, OperationType.PATCH, OperationStatus.FAIL, error_output, params, agent, e))
            return {"status": OperationStatus.FAIL, "output": cast(Any, error_output)}
            
    def delete(self, agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
        """Remove content from the resource.
        
        Deletes or removes content from the resource (e.g., deleting a file or removing 
        a resource from a collection). Requires DELETE permission. Emits a SUCCESS or FAILURE event upon completion.
        
        Args:
            agent: The agent performing the operation. Must have DELETE permission.
            params: Optional dictionary of parameters to pass to the operation handler.
        
        Returns:
            Resource[Any]: Result of the delete operation, which can be of any type depending on the operation handler.
        
        Raises:
            PermissionError: If the user does not have DELETE permission on this resource.
            Exception: Any exception raised by the operation handler is re-raised after emitting a FAILURE event.
        """
        if not self.__delete_op__:
            raise NotImplementedError("DELETE operation is not implemented for this resource.")
        if not self.__verify_permissions__(agent, OperationType.DELETE):
            raise PermissionError("You do not have permission to DELETE this file.")
        try:
            result = self.__delete_op__.execute(self, agent, params or {})
            self.__last_operation_at__["delete"] = datetime.datetime.now()
            self.__last_error__ = None
            self.emit(Event(self, self.__delete_op__, OperationType.DELETE, result["status"], result["output"], params or {}, agent))
            return result
        except Exception as e:
            self.__last_operation_at__["delete"] = datetime.datetime.now()
            self.__last_error__ = str(e)
            error_output: dict[str, dict[str, str]] = {
                "exception": {
                    "type": type(e).__name__,
                    "message": str(e),
                }
            }
            self.emit(Event(self, self.__delete_op__, OperationType.DELETE, OperationStatus.FAIL, error_output, params or {}, agent, e))
            return {"status": OperationStatus.FAIL, "output": cast(Any, error_output)}
        
    def view(self, agent : Agent) -> ResourceViewDict:
        """View basic metadata about the resource.
        
        Provides a dictionary representation of the resource's metadata (e.g., name, type, description).
        Requires at least one of GET, POST, PATCH, or DELETE permissions. Emits a SUCCESS or FAILURE event upon completion.
        
        Args:
            agent: The agent performing the operation. Must have at least one of GET, POST, PATCH, or DELETE permissions.
        
        Returns:
            dict[str, Any]: A dictionary representation of the resource's metadata.
            
        Raises:
            PermissionError: If the user does not have at least one of GET, POST, PATCH, or DELETE permissions on this resource.
        """
        if not self.__has_any_permissions__(agent):
            raise PermissionError("You do not have permission to view this resource.")
        return {
                "name": self.__name__,
                "type": self.__type__,
                "author": self.__owner__.name if self.__owner__ else "None",
                "group": self.__group__.name if self.__group__ else "None",
                "created_at": self.__relative_time_ago__(self.__created_at__),
                "description": self.__description__,
                "operations": self.__options__(),
                "operation_timestamps": {
                    key: self.__relative_time_ago__(value) if value else None
                    for key, value in self.__last_operation_at__.items()
                },
                "last_error": self.__last_error__,
                "permissions": {
                    "user": self.__user_permissions__.get_permissions(),
                    "group": self.__group_permissions__.get_permissions(),
                    "other": self.__other_permissions__.get_permissions()
                    }
                }
    
    def verify(self, agent : Agent, operation : OperationType) -> bool:
        """Check if agent has permission for a specific operation on this resource. 
        

        Args:
            agent: The agent to check permissions for.
            operation: The operation type to verify (GET, POST, PATCH, DELETE).
        
        Returns:
            bool: True if the agent has permission for the operation, False otherwise.
        """
        return self.__verify_permissions__(agent, operation)
    
    def __verify_permissions__(self, agent : Agent, operation : OperationType) -> bool:
        if agent.is_admin():
            return True
        if agent == self.__owner__:
            return self.__user_permissions__.verify(operation)
        elif self.__group__ is not None and self.__group__ in agent.groups:
            return self.__group_permissions__.verify(operation)
        else:
            return self.__other_permissions__.verify(operation)

    def __has_any_permissions__(self, agent: Agent) -> bool:
        return any(
            self.__verify_permissions__(agent, operation)
            for operation in (
                OperationType.GET,
                OperationType.POST,
                OperationType.PATCH,
                OperationType.DELETE,
            )
        )

    def __relative_time_ago__(self, timestamp: datetime.datetime) -> str:
        now = datetime.datetime.now()
        delta = now - timestamp
        total_seconds = max(0, int(delta.total_seconds()))

        units: list[tuple[str, int]] = [
            ("year", 60 * 60 * 24 * 365),
            ("month", 60 * 60 * 24 * 30),
            ("day", 60 * 60 * 24),
            ("hour", 60 * 60),
            ("minute", 60),
            ("second", 1),
        ]

        for unit_name, unit_seconds in units:
            value = total_seconds // unit_seconds
            if value > 0:
                suffix = "" if value == 1 else "s"
                return f"{value} {unit_name}{suffix} ago"

        return "0 seconds ago"
    
    def __options__(self) -> dict[str, str]:
        """
        Provides a dictionary of available operations and their descriptions for this resource.
        """
        ops : dict[str, str] = {}
        if self.__get_op__:
            ops["get"] = self.__get_op__.description
        if self.__post_op__:
            ops["post"] = self.__post_op__.description
        if self.__patch_op__:
            ops["patch"] = self.__patch_op__.description
        if self.__delete_op__:
            ops["delete"] = self.__delete_op__.description
        return ops
        