from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent


@dataclass(frozen=True)
class AgentTemplate:
    """Blueprint for an agent created from a selected tool set."""

    name: str
    description: str
    instructions: str
    capabilities: list[str]
    version: str = "1.0.0"

    def create(self, model: Any, tools: list[Any]):
        return create_agent(
            model=model,
            tools=tools,
            system_prompt=(
                f"{self.instructions}\n\n"
                "Use each tool only when needed. Do not repeatedly retry a web "
                "search with slightly different queries. Use the returned "
                "results and complete the task. If search returns no results, "
                "continue and complete the task without searching again."
            ),
        )
