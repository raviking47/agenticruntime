from app.agents.models import AgentDefinition
from app.registry_store import YamlRegistry
from app.runtime_store import RuntimeStore

class AgentRegistry:
    def __init__(self, catalog: YamlRegistry | None = None, store: RuntimeStore | None = None):
        self.agents: dict[str, AgentDefinition] = {}
        self.catalog = catalog or YamlRegistry()
        self.store = store

    def register(self, agent_definition: AgentDefinition, *, instructions: str = "") -> None:
        if not agent_definition.name or not agent_definition.name.strip():
            raise ValueError("Agent name must not be empty.")
        if agent_definition.name in self.agents:
            raise ValueError(f"Agent with name {agent_definition.name} is already registered.")
        self.agents[agent_definition.name] = agent_definition
        self.catalog.register_agent(agent_definition)
        if self.store is not None:
            self.store.save_agent(
                name=agent_definition.name,
                version=agent_definition.version,
                description=agent_definition.description,
                instructions=instructions,
                capabilities=agent_definition.capabilities,
                work_key=agent_definition.work_key,
            )

    def get_agent(self, name: str) -> AgentDefinition:
        if name not in self.agents:
            raise ValueError(f"Agent with name {name} is not registered.")
        return self.agents[name]

    # Keep the short spelling used by the HTTP layer and make the registry API
    # convenient for callers without breaking the explicit get_agent method.
    get = get_agent

    def list_agents(self) -> list[str]:
        return list(self.agents.keys())

    def list(self) -> list[AgentDefinition]:
        """Return registered definitions in registration order."""
        return list(self.agents.values())

    def find_work_agent(self, work_key: str, capabilities: list[str]) -> AgentDefinition | None:
        required = set(capabilities)
        for definition in self.agents.values():
            if definition.work_key == work_key and required.issubset(definition.capabilities):
                return definition
        return None

    def get_work_agent(self, work_key: str) -> AgentDefinition | None:
        for definition in self.agents.values():
            if definition.work_key == work_key:
                return definition
        return None

    def update(self, agent_definition: AgentDefinition, *, instructions: str = "") -> None:
        if agent_definition.name not in self.agents:
            raise ValueError(f"Agent with name {agent_definition.name} is not registered.")
        self.agents[agent_definition.name] = agent_definition
        self.catalog.register_agent(agent_definition)
        if self.store is not None:
            self.store.save_agent(
                name=agent_definition.name,
                version=agent_definition.version,
                description=agent_definition.description,
                instructions=instructions,
                capabilities=agent_definition.capabilities,
                work_key=agent_definition.work_key,
            )

    def unregister(self, name: str) -> None:
        if name not in self.agents:
            raise ValueError(f"Agent with name {name} is not registered.")
        del self.agents[name]
