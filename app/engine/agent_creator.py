import re
from app.engine.schemas import AgentSpec
from app.tools.tool_registry import ToolRegistry


class AgentCreator:
    def __init__(
        self,
        model,
        tool_registry: ToolRegistry,
    ):
        self.model = model
        self.tool_registry = tool_registry

        self.planner = model.with_structured_output(AgentSpec)

    async def plan(self, task: str) -> AgentSpec:
        available_tools = self.tool_registry.describe()

        return await self.planner.ainvoke([
            (
                "system",
                """
                You are an internal agent designer.

                Design an agent to complete the user's task using
                only the registered tools listed below.

                Rules:
                - Select only tools that are actually available.
                - Select the minimum tools needed.
                - Never invent tool names.
                - If a required capability is missing, request an approved
                  tool template instead of inventing implementation code.
                - Match the task to tool capabilities, not just tool names.
                - For tasks that create or update a file, select write_file.
                - For tasks that require internet information, select web_search.
                - Give the agent reusable, role-oriented instructions. The user
                  task is supplied at runtime; never embed a product, company,
                  framework, filename, or other one-off task detail in the role.
                - Choose a reusable work_key such as research, file_operations,
                  or reporting; do not create a one-off role for every task.
                - Do not request shell access or arbitrary code execution.

                Approved tool templates that may be requested when missing:
                - web_search: public web search

                Available tools:
                """,
            ),
            (
                "human",
                f"""
                Task:
                {task}

                Available tool definitions:
                {available_tools}
                """,
            ),
        ])
