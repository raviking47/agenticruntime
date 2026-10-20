"""Requirement workflow: plan, check, create, register, and execute."""

from app.engine.agent_creator import AgentCreator
from app.engine.template_create_engine import TemplateCreateEngine


class WorkflowEngine:
    def __init__(self, planner: AgentCreator, templates: TemplateCreateEngine):
        self.planner = planner
        self.templates = templates

    async def prepare(self, requirement: str):
        spec = await self.planner.plan(requirement)

        for request in spec.tool_requests:
            self.templates.create_tool(request)
            if request.name not in spec.tool_names:
                spec.tool_names.append(request.name)

        if not spec.tool_names:
            raise ValueError("The requirement needs at least one registered tool")

        tools = self.planner.tool_registry.get_many(spec.tool_names)
        return self.templates.create_agent(spec, tools)
