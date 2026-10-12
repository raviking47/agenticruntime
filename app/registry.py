from app.agents.models import AgentDefinition

class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, AgentDefinition] = {}

    def register(self, agent_definition: AgentDefinition) -> None:
        if not agent_definition.name or not agent_definition.name.strip():
            raise ValueError("Agent name must not be empty.")
        if agent_definition.name in self.agents:
            raise ValueError(f"Agent with name {agent_definition.name} is already registered.")
        self.agents[agent_definition.name] = agent_definition

    def get_agent(self, name: str) -> AgentDefinition:
        if name not in self.agents:
            raise ValueError(f"Agent with name {name} is not registered.")
        return self.agents[name]

    # Keep the short spelling used by the HTTP layer and make the registry API
    # convenient for callers without breaking the explicit get_agent method.
    get = get_agent

    def list_agents(self) -> list[str]:
        return list(self.agents.keys())

    def unregister(self, name: str) -> None:
        if name not in self.agents:
            raise ValueError(f"Agent with name {name} is not registered.")
        del self.agents[name]
