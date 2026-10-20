# app/registry_instance.py

from app.registry import AgentRegistry
from app.registry_store import YamlRegistry
from app.runtime_store import RuntimeStore

registry_catalog = YamlRegistry()
runtime_store = RuntimeStore()
agent_registry = AgentRegistry(registry_catalog, runtime_store)
