"""Creates runtime tools and agents from approved templates."""

import re
from typing import Any
from uuid import uuid4

from app.agents.models import AgentDefinition
from app.engine.schemas import AgentSpec, ToolRequest
from app.registry import AgentRegistry
from app.registry_instance import agent_registry as default_agent_registry
from app.runtime_store import RuntimeStore
from app.templates.agent_template import AgentTemplate
from app.templates.tool_template import ToolTemplate
from app.tools.tool_registry import ToolRegistry


class TemplateCreateEngine:
    def __init__(
        self,
        model,
        tool_registry: ToolRegistry,
        agent_registry: AgentRegistry | None = None,
        store: RuntimeStore | None = None,
    ):
        self.model = model
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry or default_agent_registry
        self.store = store or tool_registry.store
        self.tool_templates: dict[str, ToolTemplate] = {}

    def register_tool_template(self, template: ToolTemplate) -> None:
        self.tool_templates[template.name] = template

    @staticmethod
    def _role_instructions(work_key: str, capabilities: list[str]) -> str:
        capability_text = ", ".join(capabilities) or "the registered tools"
        return (
            f"You are a reusable {work_key} agent. Work from the user's current "
            f"request at runtime using only these capabilities: {capability_text}. "
            "Do not assume a particular product, framework, filename, or topic "
            "from an earlier request. Complete the current request and return "
            "the result clearly."
        )

    def create_tool(self, request: ToolRequest):
        if self.tool_registry.has(request.name):
            return self.tool_registry.get(request.name)

        template = self.tool_templates.get(request.template)
        if template is None:
            raise ValueError(
                f"No approved tool template exists for '{request.template}'"
            )

        tool = template.create()
        if tool.name != request.name:
            raise ValueError(
                f"Template '{request.template}' creates '{tool.name}', "
                f"not '{request.name}'"
            )

        self.tool_registry.register(
            tool,
            capabilities=template.capabilities,
            template=request.template,
            function_key=template.key,
        )
        return tool

    def restore_tools(self) -> None:
        """Rebuild persisted tools from their registered templates."""
        if self.store is None:
            return
        for record in self.store.tools():
            if self.tool_registry.has(record["name"]):
                continue
            template = self.tool_templates.get(record["template"])
            if template is not None:
                if record["function_key"] != template.key:
                    raise ValueError(
                        f"Persisted function '{record['function_key']}' does not "
                        f"match template '{template.key}'"
                    )
                self.tool_registry.register(
                    template.create(),
                    capabilities=record["capabilities"],
                    template=record["template"],
                    function_key=record["function_key"],
                    arguments=record["arguments"],
                )

    def create_agent(self, spec: AgentSpec, tools: list[Any]) -> AgentDefinition:
        if not tools:
            raise ValueError("Cannot create an agent without tools")

        work_key = re.sub(r"[^a-z0-9_]+", "_", spec.work_key.lower()).strip("_") or "general"
        if "web_search" in spec.tool_names:
            work_key = "research"
        elif {"read_file", "write_file"}.intersection(spec.tool_names):
            work_key = "file_operations"
        existing = self.agent_registry.get_work_agent(work_key)
        if existing is not None:
            required = set(spec.tool_names)
            current = set(existing.capabilities)
            selected_capabilities = list(dict.fromkeys(existing.capabilities + spec.tool_names))
            role_instructions = self._role_instructions(work_key, selected_capabilities)
            if required.issubset(current):
                selected_tools = self.tool_registry.get_many(selected_capabilities)
                template = AgentTemplate(
                    name=existing.name,
                    description=f"Reusable {work_key} agent",
                    instructions=role_instructions,
                    capabilities=selected_capabilities,
                    version=existing.version,
                )
                existing.description = template.description
                existing.factory = lambda template=template, tools=selected_tools: template.create(
                    self.model, tools
                )
                self.agent_registry.update(existing, instructions=role_instructions)
                return existing

            # Upgrade the persistent work agent when a later requirement needs
            # capabilities that the role did not previously have.
            selected_tools = self.tool_registry.get_many(selected_capabilities)
            template = AgentTemplate(
                name=existing.name,
                description=f"Reusable {work_key} agent",
                instructions=role_instructions,
                capabilities=selected_capabilities,
                version=existing.version,
            )
            existing.description = template.description
            existing.capabilities = template.capabilities
            existing.factory = lambda template=template, tools=selected_tools: template.create(
                self.model, tools
            )
            self.agent_registry.update(existing, instructions=template.instructions)
            return existing

        name = f"{work_key}_agent"
        if name in self.agent_registry.agents:
            name = f"{name}_{uuid4().hex[:8]}"
        role_instructions = self._role_instructions(work_key, list(spec.tool_names))
        template = AgentTemplate(
            name=name,
            description=f"Reusable {work_key} agent",
            instructions=role_instructions,
            capabilities=list(spec.tool_names),
        )

        def factory():
            return template.create(self.model, tools)

        definition = AgentDefinition(
            name=template.name,
            version=template.version,
            description=template.description,
            capabilities=template.capabilities,
            work_key=work_key,
            source="dynamic",
            factory=factory,
        )
        self.agent_registry.register(definition, instructions=role_instructions)
        return definition

    def restore_agents(self) -> None:
        """Rebuild persisted agents after persisted tools are restored."""
        if self.store is None:
            return
        for record in self.store.agents():
            if record["name"] in self.agent_registry.agents:
                continue
            tools = self.tool_registry.get_many(record["capabilities"])
            work_key = record.get("work_key", "general")
            role_instructions = self._role_instructions(work_key, record["capabilities"])
            template = AgentTemplate(
                name=record["name"],
                description=f"Reusable {work_key} agent",
                instructions=role_instructions,
                capabilities=record["capabilities"],
                version=record["version"],
            )
            definition = AgentDefinition(
                name=template.name,
                version=template.version,
                description=template.description,
                capabilities=template.capabilities,
                work_key=work_key,
                source="restored",
                factory=lambda template=template, tools=tools: template.create(self.model, tools),
            )
            self.agent_registry.register(definition, instructions=template.instructions)
