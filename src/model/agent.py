from __future__ import annotations

import datetime
import json
import re
from typing import TYPE_CHECKING, Callable
import uuid

from errors.api import APINotFoundError
from errors.command_parsing import CommandParsingError
from errors.resource import ResourceNotFoundError
from model.enums import OperationType
from model.api import API
from model.events import AgentMessageEventData, EventEmitter, EventListener, ScheduledOperationEventData, agent_message_event, scheduled_operation_event
from model.group import ADMIN
from model.operation_result import AgentViewableValue, AgentState
from model.command import Command
from model.types import  ResourceKeyPair
from model.message import Message
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
    from model.resource import Resource
    

class Agent:
    
    def __init__(self, 
                 name : str, 
                 description : str, 
                 provider : AgentProvider, 
                 token_limit : int = 3000,
                 error_handler : Callable[[Agent,Json], AgentState] | None = None,
                 groups : list[Group] | None = None,
                 initial_context : str = "", 
                 tool_usage_instructions : str | None = None,
                 summarize_prompt: str | None = None):
        
        self.__uuid__ : str = str(uuid.uuid4())
        self.__name__ : str = name
        self.__description__ : str = description
        self.__groups__ : list[Group] = groups or []
        self.__provider__ : AgentProvider = provider
        self.__initial_context__ : str = initial_context
        self.__token_limit__ : int = token_limit
        self.__local_api__ : API = API(f'agent-{self.__name__.replace(" ", "-")}-{self.__uuid__}', f"Local API for agent {self.__name__}", [])
        self.__tool_usage_instructions__ : str = (
            tool_usage_instructions or
            'Your last line must be a command in this exact format:\n\n'
            '    <operation_type> <api_name>/<resource_path> <json_encoded_parameters>\n\n'
            'Use one of: get, post, patch, delete. '
            'Parameters must be a JSON object; use {{}} when empty. '
            f'Example: post {self.__local_api__.name}/agent_response {{"message": "Hello, how can I help you?"}}'
            'You will be returned control back after executing the command, except for commands that return control to the user (e.g. sending a message to the user), which will stop your execution'
        )
        self.__auth_keys__ : dict[Resource[Any], KeySet] = {}
        self.__apis__ : set[API] = set([self.__local_api__])
        self.__conversation__ : list[Message] = []
        self.__message_event_emitter__ : EventEmitter[AgentMessageEventData] = EventEmitter()
        self.__operation_event_emitter__ : EventEmitter[ScheduledOperationEventData] = EventEmitter()
        self._COMMAND_RE = re.compile(
        r'(get|post|patch|delete)\s+(\S+)\s+(\{.*\})\s*$',
        re.IGNORECASE | re.DOTALL,
    )
        
        for group in self.__groups__:
            try:
                self.add_api(group.api)
            except ValueError:
                pass
            
        self.__setup__()

        self.__summarize_prompt_template__ : str = (
            summarize_prompt or
            "Summarize the following conversation between the user and the agent in a concise manner, keeping all important details and information. The summary should be as short as possible while still retaining the key points of the conversation. Conversation: \n\n {conversation}"
        )
        
        self.__error_handler__ : Callable[[Agent,Json], AgentState] | None = error_handler

    def message(self, message: str) -> Json:

        if (len(self.__conversation__) == 0):
            self.__conversation__ = [self.__build_prompt__()]
            
        elif (self.__provider__.count_tokens(self.__conversation__) > self.__token_limit__):
            self.__summarize_conversation__()
           
        self.__append_to_conversation__(Message(role="user", content=message))

        self.__run_operation_chain__(self.__conversation__)
        
        return self.__conversation__[-1].content if self.__conversation__ else ""

    def add_api(self, api: API):
        if api.name in [existing_api.name for existing_api in self.__apis__]:
            raise ValueError(f"API with name '{api.name}' is already mounted.")
        self.__apis__.add(api)
    
    def add_to_local_api(self, resource_key_pair: ResourceKeyPair):
        key_set, resource = resource_key_pair
        self.__auth_keys__[resource] = key_set
        self.__local_api__.mount(resource)
        
    def add_keys_for_resource(self, resource: Resource[Any], key_set: KeySet):
        self.__auth_keys__[resource] = key_set

    def is_admin(self) -> bool:
        return any(group == ADMIN for group in self.__groups__)
    
    def get_auth_key(self, resource : Resource[Any], operation : OperationType) -> AuthenticationKey | None:
        key_set : KeySet | None = self.__auth_keys__.get(resource)
        if not key_set:
            return None
        return key_set.get(operation)
    
    def get_full_name(self) -> str:
        return f"{self.__name__} ({self.__uuid__})"
    
    def kill(self) -> None:
        self.__conversation__ = []
        raise SystemExit("Agent has been killed.")
    
    def add_scheduled_operation_listener(self, listener: EventListener[ScheduledOperationEventData]):
        self.__operation_event_emitter__.add_listener(listener)
        
    def add_message_listener(self, listener: EventListener[AgentMessageEventData]):
        self.__message_event_emitter__.add_listener(listener)
    
    def __append_to_conversation__(self, message: Message) -> None:
        self.__conversation__.append(message)
        self.__message_event_emitter__.emit(agent_message_event(self, message))
        
    def __setup__(self) -> None:
        self.add_to_local_api(send_agent_reply(owner=self))
        self.add_to_local_api(scanner(self, self.__local_api__))
        self.add_to_local_api(text(owner=self, name="agent_preloaded_text", description="All text written here will be guaranteed to be available even after summarizing the conversation. Use this to store important information.", content=""))
            
    def __summarize_conversation__(self) -> None:
        summary_response = self.__run_operation_chain__([Message(role="system", content=self.__tool_usage_instructions__),Message(role="system", content=self.__summarize_prompt_template__)])
        self.__conversation__ = [self.__build_prompt__(), Message(role="system", content=f"Summary of previous conversation: {summary_response}")]

    def __save_thought__(self, reasoning: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.add_to_local_api(text(
            owner=self,
            name=f"thoughts/{timestamp}",
            description=f"Thought recorded at {timestamp}",
            content=reasoning
        ))
        
    def __run_operation_chain__(self, conversation: list[Message]) -> None:

        while True:
            
            raw_response = self.__provider__.send_message(conversation)
            parsed_command: Command
            parsed_command, reasoning = self.__parse_response__(raw_response)
            
            if reasoning:
                self.__save_thought__(reasoning)
            
            result : OperationResult = self.__execute__(
                    parsed_command
                )
            
            self.__append_to_conversation__(Message(role="agent", content=raw_response))
            
            if result["status"] == AgentState.CONTINUE:
                self.__append_to_conversation__(Message(role="system", content=result["output"].view(self) or {"message": "No response from operation."}))
                
            elif result["status"] == AgentState.STOP:
                output_view = result["output"].view(self)
                self.__append_to_conversation__(Message(role="system", content=output_view or {"message": "No response from operation."}))
                return

            elif result["status"] == AgentState.FAIL:
                if self.__error_handler__:
                    error : Json | None = result["output"].view(self)
                    if not error:
                        error = {"error": "Unknown error occurred."}
                    error_status = self.__error_handler__(self, error)
                    if error_status == AgentState.STOP:
                        self.__append_to_conversation__( Message(role="system", content={"message": "Error occurred during operation execution. Returning control to user.", "error": error}))
                    elif error_status == AgentState.CONTINUE:
                        self.__append_to_conversation__( Message(role="system", content={"message": "Error occurred during operation execution. Continue with the next command.", "error": error}))
                    elif error_status == AgentState.FAIL:
                        self.__append_to_conversation__( Message(role="system", content={"message": "Error occurred during operation execution. Stopping agent execution.", "error": error}))
                        raise ValueError(f"Invalid status returned by error handler: {error_status}")
                return
            
            self.__append_to_conversation__(Message(role="system",
                                                    content={"message": "API Updates after operation execution:", "updates": self.__get_api_updates__()}))
                
    def __build_prompt__(self) -> Message:
        return  Message(
            role="system", content=self.__initial_context__ + "\n\n" + "You are agent " + self.get_full_name() + "." + self.__tool_usage_instructions__ + "\n\n" + "Overview of available resources:\n" + str(self.__view_root__()))
                 
    def __parse_response__(self, response: str) -> tuple[Command, str]:
        match = self._COMMAND_RE.search(response)
        if not match:
            raise ValueError(f"Invalid response format (no valid command found at end): {response}")
        reasoning = response[:match.start()].strip()
        parsed_response = Command(
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
    
    def __execute__(self, parsed_command: Command) -> OperationResult:
       
        try:
            resource : Resource[Any] | None = self.__find_resource__(parsed_command["resource"])
        except (APINotFoundError, ResourceNotFoundError, CommandParsingError) as e:
            self.__operation_event_emitter__.emit(scheduled_operation_event(
                resource=None,
                resource_name=parsed_command["resource"],
                operation_type=parsed_command["operation"],
                parameters=parsed_command["parameters"],
                agent=self,
                timestamp=datetime.datetime.now(),
                exception= e
            ))
            return {
                "status": AgentState.FAIL,
                "output": AgentViewableValue({"message": "Error occurred while finding resource","error": str(e)})
            }
        
        self.__operation_event_emitter__.emit(scheduled_operation_event(
            resource=resource,
            resource_name=parsed_command["resource"],
            operation_type=parsed_command["operation"],
            parameters=parsed_command["parameters"],
            agent=self,
            timestamp=datetime.datetime.now()
        ))
        
        if parsed_command["operation"] == OperationType.GET:
            return resource.get(self, parsed_command["parameters"])
        elif parsed_command["operation"] == OperationType.POST:
            return resource.post(self, parsed_command["parameters"])
        elif parsed_command["operation"] == OperationType.PATCH:
            return resource.patch(self, parsed_command["parameters"])
        elif parsed_command["operation"] == OperationType.DELETE:
            return resource.delete(self, parsed_command["parameters"])
        
        raise ValueError(f"Unsupported operation type: {parsed_command['operation']}")
    
    def __find_resource__(self, resource_identifier: str) -> Resource[Any]:
        api_name, separator, resource_path = resource_identifier.partition("/")

        if not separator or not resource_path:
            raise CommandParsingError(
                "Resource name must include the API name in the format '<api_name>/<resource_path>'."
            )

        api = next((api for api in self.__apis__ if api.name == api_name), None)
        
        if not api:
            raise APINotFoundError(f"API not found: {api_name}")
        
        resource = api.get(self, resource_path)
        
        if not resource:
            raise ResourceNotFoundError(f"Resource not found: {resource_path} in API {api_name}")

        return resource
    
    def __get_api_updates__(self) -> Json:
        updated_resources : list[Json] = []
        for api in self.__apis__:
            for resource in api.get_updates():
                view : Json | None  = resource.view(self)
                if view:
                    updated_resources.append(view)
        return updated_resources