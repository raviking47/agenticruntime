from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class AgentDefinition:
    name: str
    version: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    work_key: str = "general"
    source: str = "application"

    factory: Callable[..., Any] | None = None

    enabled: bool = True

    
