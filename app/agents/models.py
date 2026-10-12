from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class AgentDefinition:
    name: str
    version: str
    description: str
    capabilities: list[str] = field(default_factory=list)

    factory: Callable[..., Any] | None = None

    enabled: bool = True

    
