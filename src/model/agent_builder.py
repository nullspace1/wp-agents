from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from model.agent import Agent
    from model.agent_provider import AgentProvider
    from model.group import Group
    from model.resource import Resource


class AgentBuilder:
    def __init__(self):
        self.provider: AgentProvider
        self.groups: list[Group] = []
        self.mounts: list[Resource[Any]] = []
        self.description: str
        self.initial_context: str = ""
        self.tool_usage_instructions: str | None = None
        self.token_limit: int = 3000

    def with_provider(self, provider: AgentProvider) -> "AgentBuilder":
        self.provider = provider
        return self

    def with_groups(self, groups: list[Group]) -> "AgentBuilder":
        self.groups = groups
        return self

    def with_mounted_resources(self, resources: list[Resource[Any]]) -> "AgentBuilder":
        self.mounts = resources
        return self

    def with_description(self, description: str) -> "AgentBuilder":
        self.description = description
        return self

    def with_initial_context(self, initial_context: str) -> "AgentBuilder":
        self.initial_context = initial_context
        return self

    def with_tool_usage_instructions(self, tool_usage_instructions: str | None) -> "AgentBuilder":
        self.tool_usage_instructions = tool_usage_instructions
        return self

    def with_token_limit(self, token_limit: int) -> "AgentBuilder":
        self.token_limit = token_limit
        return self

    def with_name(self, name: str) -> "AgentBuilder":
        self.name = name
        return self

    def build(self) -> "Agent":
        from model.agent import Agent

        return Agent(
            name=self.name,
            provider=self.provider,
            description=self.description,
            initial_context=self.initial_context,
            tool_usage_instructions=self.tool_usage_instructions,
            token_limit=self.token_limit,
            groups=self.groups,
            mounted_resources=self.mounts,
        )
