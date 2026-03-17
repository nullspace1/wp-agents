from __future__ import annotations

import datetime
import json
import re
from typing import TYPE_CHECKING
import uuid

from model.enums import OperationType
from model.api import API
from model.group import ADMIN
from model.operation_result import OperationStatus
from model.response import Response
from resources.agent_reply import send_agent_reply
from resources.scanner import scanner
from resources.text import text

if TYPE_CHECKING:
    from typing import Any
    from model.agent_provider import AgentProvider
    from model.auth import AuthenticationKey
    from model.auth import KeySet
    from model.operation_result import Json, OperationResult
    from model.group import Group
    from model.resource import Resource, ResourceKeyPair

class Agent:
    
    def __init__(self, name : str, 
                 description : str, 
                 provider : AgentProvider, 
                 initial_context : str = "", 
                 tool_usage_instructions : str | None = None,
                 token_limit : int = 3000,
                 groups : list[Group] | None = None,
                 mounted_resources : list[Resource[Any]] | None = None):
        
        self.__uuid__ : str = str(uuid.uuid4())
        self.__name__ : str = name
        self.__description__ : str = description
        self.__groups__ : list[Group] = groups or []
        self.__provider__ : AgentProvider = provider
        self.__information__ : Resource[str]
        self.__initial_context__ : str = initial_context
        self.__current_conversation__ = ""
        self.__token_limit__ = token_limit
        self.__tool_usage_instructions__ = (
            tool_usage_instructions or
            'Your last line must be a command in this exact format:\n\n'
            '    <operation_type> <api_name>/<resource_path> <json_encoded_parameters>\n\n'
            'Use one of: get, post, patch, delete. '
            'Parameters must be a JSON object; use {{}} when empty. '
            'Example: post <api_name>/agent_response {{"message": "Hello, how can I help you?"}}'
        )
        self.__local_api__ : API = API(f'agent-{self.__name__}-{self.__uuid__}', f"Local API for agent {self.__name__}", [])
        self.__auth_keys__ : dict[Resource[Any], KeySet] = {}
        self.__apis__ = set([self.__local_api__])
        self.__conversation__ : str = ""

        for group in self.__groups__:
            try:
                self.add_api(group.api)
            except ValueError:
                pass
            
        self.__setup__(mounted_resources)

    def message(self, message: str) -> str:

        if (len(self.__current_conversation__) == 0):
            self.__current_conversation__ = self.__build_prompt__()
            
        elif (self.__provider__.count_tokens(self.__current_conversation__) > self.__token_limit__):
            self.__summarize_conversation__()
           
        self.__current_conversation__ += f"\n[User]: {message}"

        response = self.__run_operation_chain__(self.__current_conversation__)
        
        self.__current_conversation__ += f"\n[{self.get_full_name()}]: {response}"
        
        return response

    def add_api(self, api: API):
        if api.name in [existing_api.name for existing_api in self.__apis__]:
            raise ValueError(f"API with name '{api.name}' is already mounted.")
        self.__apis__.add(api)
    
    def mount_locally(self, resource_key_pair: ResourceKeyPair[Any]):
        key_set, resource = resource_key_pair
        self.__auth_keys__[resource] = key_set
        self.__local_api__.mount(resource)
        
    def add_keys_for_resource(self, resource: Resource[Any], key_set: KeySet):
        self.__auth_keys__[resource] = key_set

    def is_admin(self) -> bool:
        return any(group == ADMIN for group in self.__groups__)
    
    def get_auth_key(self, resource : Resource[Any], operation : OperationType) -> AuthenticationKey | None:
        key_set = self.__auth_keys__.get(resource)
        if not key_set:
            return None
        return key_set.get(operation)
    
    def get_full_name(self) -> str:
        return f"{self.__name__} ({self.__uuid__})"
    
    def __setup__(self, mounted_resources: list[Resource[Any]] | None = None):
        self.mount_locally(send_agent_reply(owner=self))
        self.mount_locally(scanner(self, self.__local_api__))
        
    def __summarize_conversation__(self):
        summary_prompt = f"Summarize the following conversation between the user and the agent in a concise manner, keeping all important details and information. The summary should be as short as possible while still retaining the key points of the conversation. Conversation: {self.__current_conversation__}"
        summary_response = self.__run_operation_chain__(summary_prompt)
        self.__current_conversation__ = self.__build_prompt__() + f"\n\nSummary of previous conversation: {summary_response}"

    def __save_thought__(self, reasoning: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.mount_locally(text(
            owner=self,
            name=f"thoughts/{timestamp}",
            description=f"Thought recorded at {timestamp}",
            content=reasoning
        ))
        
    def __run_operation_chain__(self, prompt: str) -> str:

        while True:
            raw_response = self.__provider__.send_message(prompt)
            parsed_response: Response
            parsed_response, reasoning = self.__parse_response__(raw_response)
            if reasoning:
                self.__save_thought__(reasoning)
            
            result : OperationResult = self.__execute__(
                parsed_response.resource,
                parsed_response.operation,
                parsed_response.parameters,
            )

            if result["status"] == OperationStatus.STOP:
                output_view = result["output"].view(self)
                return self.__format_output__(output_view)

            if result["status"] == OperationStatus.FAIL:
                raise RuntimeError(self.__format_output__(result["output"].view(self)))

            self.__conversation__ += (
                f"\n[Agent]: {raw_response}"
                f"\n[Operation result]: {self.__format_output__(result['output'].view(self))}"
            )

    def __build_prompt__(self) -> str:
        return self.__initial_context__ + "\n\n" + "You are agent " + self.get_full_name() + "." + self.__tool_usage_instructions__ + "\n\n" + "Agent's data:\n" + str(self.__view_root__()) + "\n\n"
                 
    _COMMAND_RE = re.compile(
        r'(get|post|patch|delete)\s+(\S+)\s+(\{.*\})\s*$',
        re.IGNORECASE | re.DOTALL,
    )

    def __parse_response__(self, response: str) -> tuple[Response, str]:
        match = self._COMMAND_RE.search(response)
        if not match:
            raise ValueError(f"Invalid response format (no valid command found at end): {response}")
        reasoning = response[:match.start()].strip()
        parsed_response = Response(
            resource=match.group(2),
            operation=OperationType(match.group(1).lower()),
            parameters=json.loads(match.group(3))
        )
        return parsed_response, reasoning

    def __view_root__(self) -> Json:
        available_apis : list[str] = sorted(api.name for api in self.__apis__ if api != self.__local_api__) 
        return {
            "available_external_apis": available_apis,
            "local_api": self.__local_api__.search(self, "", depth=0),
        }
    
    def __execute__(self, resource_identifier: str, operation_type : OperationType, parameters: dict[str, Any]) -> OperationResult:
        api_name, separator, resource_path = resource_identifier.partition("/")

        if not separator or not resource_path:
            raise ValueError(
                "Resource name must include the API name in the format '<api_name>/<resource_path>'."
            )

        api = next((api for api in self.__apis__ if api.name == api_name), None)
        
        if not api:
            raise ValueError(f"API not found: {api_name}")
        
        resource = api.get(self, resource_path)
        
        if not resource:
            raise ValueError(f"Resource not found: {resource_path} in API {api_name}")
        
        if operation_type == OperationType.GET:
            return resource.get(self, parameters)
        elif operation_type == OperationType.POST:
            return resource.post(self, parameters)
        elif operation_type == OperationType.PATCH:
            return resource.patch(self, parameters)
        elif operation_type == OperationType.DELETE:
            return resource.delete(self, parameters)

        raise ValueError(f"Unsupported operation type: {operation_type}")
    
    def __format_output__(self, output: Any, indent: int = 2) -> str:
        return json.dumps(output, indent=indent, default=str)

        