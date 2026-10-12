# app/agents/base.py

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):

    name: str
    version: str
    description: str
    capabilities: list[str]

    @abstractmethod
    async def run(self, input: str, **kwargs: Any) -> Any:
        ...