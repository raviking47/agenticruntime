# app/agents/register.py

import logging

from app.registry_instance import agent_registry
from app.agents.models import AgentDefinition
from app.agents.file_agent import FileAgent

logger = logging.getLogger(__name__)


def register_agents():
    if FileAgent.name in agent_registry.agents:
        logger.debug("Agent already registered: %s", FileAgent.name)
        return

    logger.info("Registering agent: %s version=%s", FileAgent.name, FileAgent.version)
    agent_registry.register(
        AgentDefinition(
            name=FileAgent.name,
            version=FileAgent.version,
            description=FileAgent.description,
            capabilities=FileAgent.capabilities,
            factory=FileAgent,
        )
    )
