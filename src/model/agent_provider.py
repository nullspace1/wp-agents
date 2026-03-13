from __future__ import annotations

from abc import ABC, abstractmethod


class AgentProvider(ABC):
    @abstractmethod
    def send_message(self, message: str) -> str:
        pass

    @abstractmethod
    def count_tokens(self, message: str) -> int:
        pass
