from __future__ import annotations

import pathlib
import sys
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from model.agent import Agent, AgentProvider


class FakeProvider(AgentProvider):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, message: str) -> str:
        self.messages.append(message)
        return 'post agent_response {"message": "ok"}'

    def count_tokens(self, message: str) -> int:
        return 0


class TestAgentPrompt(unittest.TestCase):
    def test_agent_prompt_includes_all_root_resource_names(self) -> None:
        provider = FakeProvider()
        agent = Agent(
            name="test-agent",
            description="agent used for prompt tests",
            provider=provider,
        )

        result = agent.message("hello")

        self.assertEqual(result, "ok")
        self.assertTrue(provider.messages)

        prompt_sent_to_provider = provider.messages[0]
        
        print(prompt_sent_to_provider)
        
        root_resource_names = [resource.view(agent)["name"] for resource in agent.data.data]

        for resource_name in root_resource_names:
            self.assertIn(resource_name, prompt_sent_to_provider)


if __name__ == "__main__":
    unittest.main()
