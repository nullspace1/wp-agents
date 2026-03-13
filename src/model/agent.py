from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import datetime
import json
import re
from typing import Any, TYPE_CHECKING, cast
import uuid

from model.enums import OperationType
from model.group import ADMIN
from model.message import Message
from model.operation_result import OperationResult, OperationStatus
from resources.text import text
from resources.agent_response import send_agent_reply
from model.permission_level import PermissionLevel
from resources.folder import folder
from resources.list import list_resource

if TYPE_CHECKING:
    from model.resource import Resource
    from model.group import Group
    

class Agent:
    
    def __init__(self, name : str, description : str, provider : AgentProvider, initial_context : str = "", token_limit : int = 3000, groups : list[Group] | None = None,mounted_resources : list[Resource[Any]] | None = None):
        
        self.uuid : str = str(uuid.uuid4())
        self.name : str = name
        self.description : str = description
        self.groups : list[Group] = groups or []
        self.provider : AgentProvider = provider
        self.information : Resource[str]
        self.message_history: Resource[list[Message]]
        self.initial_context : str = initial_context
        self.current_conversation = ""
        self.token_limit = token_limit
        self.tool_usage_instructions = (
            'You may reason freely before issuing a command, but your reply MUST end with a command on its own line '
            'using EXACTLY the following format:\n\n'
            '    <operation_type> <resource_name> <json_encoded_parameters>\n\n'
            '- operation_type: one of "get", "post", "patch", or "delete".\n'
            '- resource_name: the exact name of a resource available through the agent\'s mounted resources. You may access resources nested within other resources by looking them with "/" separators.\n'
            '- json_encoded_parameters: a JSON-encoded dictionary of parameters. '
            'Use {{}} if no parameters are needed.\n\n'
            'The LAST line of every reply MUST be a valid command in this format. '
            'Any text before it is treated as reasoning and stored as a text resource in the agent\'s data folder under the thoughts folder. '
            'Example — to reply to the user with "Hello, how can I help you?": '
            'post agent_response {{"message": "Hello, how can I help you?"}}'
        )
        
        self.data = folder(
            agent=self,
            group=None,
            folder_name=f"{self.name}_data",
            description=f"Data folder for agent {self.name}",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
            
        self.__setup__(mounted_resources)
            
    def message(self, message: str, agent : Agent | None = None) -> str:
        self.message_history.data.append(Message(user="user", content=message))
        self.current_conversation += f"\n[User]: {message}"

        if (self.provider.count_tokens(self.current_conversation) > self.token_limit):
            self.__summarize_conversation__()

        response = self.__run_operation_chain__(self.current_conversation)
        self.message_history.data.append(Message(user=agent.name if agent else self.name, content=response))
        self.current_conversation += f"\n[{self.name}]: {response}"
        return response

    
    def mount(self, path: str, resource: Resource[Any]):
        self.data.post(self, {
            "path": path,
            "resource": resource
        })
        
    def unmount(self, path: str, resource: Resource[Any]):
        self.data.delete(self, {
            "path": path,
            "resource": resource
        })
        
    def is_admin(self) -> bool:
        return any(group == ADMIN for group in self.groups)
    
    def __setup__(self, mounted_resources: list[Resource[Any]] | None = None):
        groups_folder = folder(
            agent=self,
            group=None,
            folder_name="groups",
            description="Folder containing all the available groups of agents to communicate with",
            user_permissions=PermissionLevel(get=True, post=False, patch=False, delete=False),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
        self.message_history = list_resource(
            agent=self,
            group=None,
            resource_name="message_history",
            description="History of messages sent to this agent",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            initial_data=[],
        )
        self.information = text(
            agent=self,
            group=None,
            text="",
            resource_name="information",
            description="A text resource that can be used to store any information this agent wants to keep track of. This can be used by the agent to keep track of important details, such as the user's preferences, or to store any other relevant information that the agent may want to refer to later.",
            user_permissions=PermissionLevel(get=True, post=True, patch=True, delete=True),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )
        self.agent_reply  = send_agent_reply(self)
        
        thoughts_folder = folder(
            agent=self,
            group=None,
            folder_name="thoughts",
            description="Folder containing this agent's reasoning steps, each stored as a text resource",
            user_permissions=PermissionLevel(get=True, post=False, patch=False, delete=False),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
        )

        self.mount("", groups_folder)
        self.mount("", thoughts_folder)
        self.mount("", self.message_history)
        self.mount("", self.agent_reply)
        for resource in mounted_resources or []:
            self.mount("", resource)
        
        for group in self.groups:
            group.add_member(self)
            
    def __summarize_conversation__(self):
        summary_prompt = f"Summarize the following conversation between the user and the agent in a concise manner, keeping all important details and information. The summary should be as short as possible while still retaining the key points of the conversation. Conversation: {self.current_conversation}"

        summary_response = self.__run_operation_chain__(summary_prompt)
        self.current_conversation = f"Summary of previous conversation: {summary_response}"

    def __save_thought__(self, reasoning: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        thought = text(
            agent=self,
            group=None,
            resource_name=f"thought_{timestamp}",
            description=f"Reasoning captured at {timestamp}",
            user_permissions=PermissionLevel(get=True, post=False, patch=False, delete=False),
            group_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            other_permissions=PermissionLevel(get=False, post=False, patch=False, delete=False),
            text=reasoning,
        )
        self.data.post(self, {"path": "thoughts", "resource": thought})

    def __run_operation_chain__(self, prompt: str) -> str:
        conversation = self.__build_prompt__(prompt)

        while True:
            raw_response = self.provider.send_message(conversation)
            match = self._COMMAND_RE.search(raw_response)
            if not match:
                raise ValueError(f"Invalid response format (no valid command found at end): {raw_response}")
            reasoning = raw_response[:match.start()].strip()
            if reasoning:
                self.__save_thought__(reasoning)
            response = self.__parse_response__(raw_response)
            
            result = self.__execute__(response.resource, response.operation, response.parameters)

            if result["status"] == OperationStatus.STOP:
                output = result["output"]
                if isinstance(output, dict):
                    output_dict = cast(dict[str, Any], output)
                    response_message = output_dict.get("response")
                    if isinstance(response_message, str):
                        return response_message
                return json.dumps(output, default=str)

            if result["status"] == OperationStatus.FAIL:
                raise RuntimeError(json.dumps(result["output"], default=str))

            conversation += (
                f"\n[Agent]: {raw_response}"
                f"\n[Operation result]: {json.dumps(result['output'], default=str)}"
            )

    def __build_prompt__(self, prompt: str) -> str:
        return self.initial_context + "\n\n" + "You are agent " + self.name + "." + self.tool_usage_instructions + "\n\n" + "Agent's data:\n" + self.__view_root__() + "\n\n" + prompt
                 
    _COMMAND_RE = re.compile(
        r'(get|post|patch|delete)\s+(\S+)\s+(\{.*\})\s*$',
        re.IGNORECASE | re.DOTALL,
    )

    def __parse_response__(self, response: str) -> Response:
        match = self._COMMAND_RE.search(response)
        if not match:
            raise ValueError(f"Invalid response format (no valid command found at end): {response}")
        return Response(
            resource=match.group(2),
            operation=OperationType(match.group(1).lower()),
            parameters=json.loads(match.group(3))
        )

    def __view_root__(self):
        return json.dumps([d.view(agent=self) for d in self.data.data], indent=2, default=str)
    
    def __execute__(self, resource_path: str, operation_type : OperationType, parameters: dict[str, Any]) -> OperationResult:
        
        print(f"Executing operation: {operation_type} on resource path: {resource_path} with parameters: {parameters}")
        
        resource : Resource[Any] = self.data.get(self, {"path": resource_path})["output"]
             
        if operation_type == OperationType.GET:
            return resource.get(self, parameters)
        elif operation_type == OperationType.POST:
            return resource.post(self, parameters)
        elif operation_type == OperationType.PATCH:
            return resource.patch(self, parameters)
        elif operation_type == OperationType.DELETE:
            return resource.delete(self, parameters)

        raise ValueError(f"Unsupported operation type: {operation_type}")
        
        
class AgentProvider(ABC):
    
    @abstractmethod
    def send_message(self, message : str) -> str:
        pass
    
    @abstractmethod
    def count_tokens(self, message : str) -> int:
        pass
    
    
@dataclass(slots=True)
class Response:
    resource : str
    operation : OperationType
    parameters: dict[str, Any]
        
        
class AgentBuilder:
    
    def __init__(self):
        self.provider : AgentProvider
        self.groups : list[Group] = []
        self.mounts : list[Resource[Any]] = []
        self.description : str
    
    def with_provider(self, provider : AgentProvider) -> 'AgentBuilder':
        self.provider = provider
        return self
    
    def with_groups(self, groups : list[Group]) -> 'AgentBuilder':
        self.groups = groups
        return self
    
    def with_mounted_resources(self, resources : list[Resource[Any]]) -> 'AgentBuilder':
        self.mounts = resources
        return self
    
    def with_description(self, description : str) -> 'AgentBuilder':
        self.description = description
        return self
    
    def with_name(self, name : str) -> 'AgentBuilder':
        self.name = name
        return self

    def build(self) -> Agent:
        agent = Agent(
            name=self.name,
            provider=self.provider,
            description=self.description,
            groups=self.groups,
            mounted_resources=self.mounts
        )
        return agent
        