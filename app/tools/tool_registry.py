from langchain_core.tools import BaseTool
from app.registry_store import YamlRegistry
from app.runtime_store import RuntimeStore


def _function_key(tool: BaseTool) -> str:
    function = getattr(tool, "func", None) or getattr(tool, "coroutine", None)
    if function is None:
        return tool.name
    return f"{function.__module__}:{function.__qualname__}"


class ToolRegistry:
    def __init__(self, catalog: YamlRegistry | None = None, store: RuntimeStore | None = None):
        self._tools: dict[str, BaseTool] = {}
        self._capabilities: dict[str, list[str]] = {}
        self.catalog = catalog or YamlRegistry()
        self.store = store

    def register(self, tool: BaseTool, capabilities: list[str] | None = None, *,
                 template: str = "manual", function_key: str | None = None,
                 arguments: dict | None = None) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool
        tool_capabilities = capabilities or [tool.name]
        self._capabilities[tool.name] = tool_capabilities
        self.catalog.register_tool(tool.name, tool_capabilities)
        if self.store is not None:
            self.store.save_tool(
                name=tool.name,
                description=tool.description,
                capabilities=tool_capabilities,
                template=template,
                function_key=function_key or _function_key(tool),
                arguments=arguments,
            )

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)

        if tool is None:
            raise KeyError(f"Unknown tool: {name}")

        return tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def get_many(self, names: list[str]) -> list[BaseTool]:
        # Reject unknown tools instead of silently ignoring them.
        return [self.get(name) for name in names]

    def describe(self) -> list[dict[str, object]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "capabilities": self._capabilities[tool.name],
            }
            for tool in self._tools.values()
        ]

    def list_names(self) -> list[str]:
        return list(self._tools)
