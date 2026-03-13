from __future__ import annotations

from typing import Any, TYPE_CHECKING

from model.agent_provider import AgentProvider

if TYPE_CHECKING:
    from model.agent import Agent
    from model.group import Group
    from model.resource import Resource


class AgentBuilder:
    def __init__(self):
        self.provider: AgentProvider
        self.groups: list[Group] = []
        self.mounts: list[Resource[Any]] = []
        self.description: str

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

    def with_name(self, name: str) -> "AgentBuilder":
        self.name = name
        return self

    def build(self) -> "Agent":
        from model.agent import Agent

        return Agent(
            name=self.name,
            provider=self.provider,
            description=self.description,
            groups=self.groups,
            mounted_resources=self.mounts,
        )
