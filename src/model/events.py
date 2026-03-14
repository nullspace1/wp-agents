from __future__ import annotations

from abc import ABC, abstractmethod
import datetime
from typing import Any, Generic, TYPE_CHECKING
from model.enums import OperationType
from model.operation import Operation
from model.operation_result import OperationStatus
from model.types import D

if TYPE_CHECKING:
    from model.resource import Resource
    from model.agent import Agent

class Event(Generic[D]):
    
    def __init__(self, resource : Resource[D], operation : Operation[D], operation_type : OperationType, status : OperationStatus, output : Any, parameters : dict[str, Any], agent : 'Agent', exception : Exception | None = None, timestamp : datetime.datetime | None = None):
        self.resource = resource
        self.operation = operation
        self.operation_type = operation_type
        self.status = status
        self.parameters = parameters
        self.agent = agent
        self.output = output
        self.timestamp = timestamp or datetime.datetime.now()
        self.exception = exception
        
    def __str__(self) -> str:
        resource_view = self.resource.retrieve_agent_view(self.agent)
        return f"{self.timestamp.isoformat()} - {self.agent.name} performed {self.operation_type.name} on {resource_view['name']} with status {self.status.name}. Parameters: {self.parameters}. Output: {self.output}"


class EventListener(ABC, Generic[D]):
    
    @abstractmethod
    def notify(self, event : Event[D]):
        pass

class EventEmitter(Generic[D]):
    
    def __init__(self):
        self.listeners : dict[tuple[Resource[D], list[OperationType]], list[EventListener[D]]] = {}
        
    def emit(self, event : Event[D]):
        for (resource, operations), listeners in self.listeners.items():
            if resource == event.resource and event.operation_type in operations:
                for listener in listeners:
                    listener.notify(event)
        if self != GLOBAL_EMITTER:
            GLOBAL_EMITTER.emit(event)
            
    def add_listener(self, listener : EventListener[D], resource : Resource[D], operations : list[OperationType] | None = None):
        if operations is None:
            operations = [OperationType.GET, OperationType.POST, OperationType.PATCH, OperationType.DELETE]
        self.listeners.setdefault((resource, operations), []).append(listener)
        
        
GLOBAL_EMITTER = EventEmitter[Any]()
    