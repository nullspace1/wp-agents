from __future__ import annotations

import datetime
from typing import Generic, TYPE_CHECKING

from model.auth import  KeySet
from model.enums import OperationType
from model.events import Event, EventEmitter
from model.types import D
from model.operation_result import AgentViewable, AgentViewableValue, OperationStatus

if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.group import Group
    from model.operation import Operation
    from model.operation_result import OperationResult
    from model.types import ResourceViewDict

class Resource(Generic[D], EventEmitter[D], AgentViewable):
    
    def __init__(self, 
                 owner : Agent | None, 
                 group : Group | None, 
                 name : str,
                 description : str,
                 data : D,
                 auth_keys : KeySet,
                 get_op : Operation[D] | None = None, 
                 post_op : Operation[D] | None = None,
                 patch_op : Operation[D] | None = None,
                 delete_op : Operation[D] | None = None,
                 created_at : datetime.datetime | None = None, 
                 ):
        super().__init__()
        self.__name__ : str = name
        self.__description__ : str = description
        self.__created_at__ : datetime.datetime = created_at or datetime.datetime.now()
        self.__owner__ : Agent | None = owner
        self.__group__ : Group | None = group
        self.__get_op__ : Operation[D] | None = get_op
        self.__post_op__ : Operation[D] | None = post_op
        self.__patch_op__ : Operation[D] | None = patch_op
        self.__delete_op__ : Operation[D] | None = delete_op
        self.__auth_keys__ : KeySet = auth_keys
        self.__last_operation_at__ : dict[str, datetime.datetime | str] = {
            "get": 'Never',
            "post": 'Never',
            "patch": 'Never',
            "delete": 'Never',
        }
        self.__last_error__ : str = "Never"
        self.data : D  = data
    
    def get(self, agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
        operation = self.__validate_operation_access__(self.__get_op__, OperationType.GET, agent)
        try:
            return self.__execute_operation__(OperationType.GET, operation, agent, params or {})
        except Exception as error:
            return self.__handle_operation_exception__(OperationType.GET, operation, params or {}, agent, error)
        
    def post(self, agent : Agent, params : dict[str, Any]) -> OperationResult:
        operation = self.__validate_operation_access__(self.__post_op__, OperationType.POST, agent)
        try:
            return self.__execute_operation__(OperationType.POST, operation, agent, params)
        except Exception as error:
            return self.__handle_operation_exception__(OperationType.POST, operation, params, agent, error)
            
    def patch(self, agent : Agent, params : dict[str, Any]) -> OperationResult:
        operation = self.__validate_operation_access__(self.__patch_op__, OperationType.PATCH, agent)
        try:
            return self.__execute_operation__(OperationType.PATCH, operation, agent, params)
        except Exception as error:
            return self.__handle_operation_exception__(OperationType.PATCH, operation, params, agent, error)
            
    def delete(self, agent : Agent, params : dict[str, Any] | None = None) -> OperationResult:
        operation = self.__validate_operation_access__(self.__delete_op__, OperationType.DELETE, agent)
        try:
            return self.__execute_operation__(OperationType.DELETE, operation, agent, params or {})
        except Exception as error:
            return self.__handle_operation_exception__(OperationType.DELETE, operation, params or {}, agent, error)
        
    def view(self, agent : Agent) -> ResourceViewDict | None:
        if not self.__has_any_key__(agent):
            return None
        value : ResourceViewDict = {
                "name": self.__name__,
                "created_at": self.__relative_time_ago__(self.__created_at__),
                "description": self.__description__,
                "operations": self.__options__(),
                "operation_timestamps": {
                    key: self.__relative_time_ago__(value)
                    for key, value in self.__last_operation_at__.items()
                },
                "last_error": self.__last_error__,
        }
        return value 

    def __execute_operation__(
        self,
        operation_type: OperationType,
        operation: Operation[D],
        agent: Agent,
        params: dict[str, Any],
    ) -> OperationResult:
        result = operation.execute(self, agent, params)
        self.__last_operation_at__[operation_type.value] = datetime.datetime.now()
        self.__last_error__ = ""
        self.emit(
            Event(
                self,
                self.__name__,
                operation,
                operation_type,
                result["status"],
                result["output"],
                params,
                agent
            )
        )
        return result

    def __validate_operation_access__(
        self,
        operation: Operation[D] | None,
        operation_type: OperationType,
        agent: Agent,
    ) -> Operation[D]:
        if not operation:
            raise NotImplementedError(f"{operation_type.name} operation is not implemented for this resource.")
        if not self.__verify_permissions__(agent, operation_type):
            raise PermissionError(f"You do not have permission to {operation_type.name} this file.")
        return operation

    def __handle_operation_exception__(
        self,
        operation_type: OperationType,
        operation: Operation[D],
        params: dict[str, Any],
        agent: Agent,
        error: Exception,
    ) -> OperationResult:
        self.__last_operation_at__[operation_type.value] = datetime.datetime.now()
        self.__last_error__ = str(error)
        wrapped_error = AgentViewableValue(
            {
                "exception": {
                    "type": type(error).__name__,
                    "message": str(error),
                }
            }
        )
        self.emit(
            Event(
                self,
                self.__name__,
                operation,
                operation_type,
                OperationStatus.FAIL,
                wrapped_error,
                params,
                agent,
                error,
            )
        )
        return {"status": OperationStatus.FAIL, "output": wrapped_error}

    def __has_any_key__(self, agent : Agent) -> bool:
        return any(self.__verify_permissions__(agent, op) for op in OperationType) if self.__auth_keys__ else True
    
    def __verify_permissions__(self, agent : Agent, operation : OperationType) -> bool:
        if agent.is_admin():
            return True
        return  agent.get_auth_key(self, operation) == self.__auth_keys__.get(operation)

    def __relative_time_ago__(self, timestamp: datetime.datetime | str) -> str:
        if isinstance(timestamp, str):
            return timestamp
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