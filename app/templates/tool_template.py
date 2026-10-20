from dataclasses import dataclass
from typing import Any, Callable

from langchain_core.tools import BaseTool, StructuredTool


@dataclass(frozen=True)
class ToolTemplate:
    """Blueprint for a tool backed by an approved application function."""

    name: str
    description: str
    capabilities: list[str]
    function: Callable[..., Any] | BaseTool
    function_key: str | None = None

    @property
    def key(self) -> str:
        if self.function_key:
            return self.function_key

        function = self.function
        if isinstance(function, BaseTool):
            function = getattr(function, "func", None) or getattr(function, "coroutine", None)
        module = getattr(function, "__module__", "runtime")
        qualified_name = getattr(function, "__qualname__", self.name)
        return f"{module}:{qualified_name}"

    def create(self) -> BaseTool:
        if isinstance(self.function, BaseTool):
            return self.function

        return StructuredTool.from_function(
            func=self.function,
            name=self.name,
            description=self.description,
        )
