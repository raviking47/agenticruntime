import json
import logging
import re

from app.engine.workflow import WorkflowEngine
from app.templates.builtin_tools import reset_search_budget, set_search_budget

logger = logging.getLogger(__name__)


class AgentRuntime:
    def __init__(self, workflow: WorkflowEngine):
        self.workflow = workflow

    async def execute(self, task: str) -> dict:
        # 1. Plan, check tools, create missing tools, and create the agent.
        definition = await self.workflow.prepare(task)

        # 4. Instantiate the agent from its registered factory.
        if definition.factory is None:
            raise ValueError(f"Agent {definition.name} has no factory")

        if {"web_search", "write_file"}.issubset(definition.capabilities):
            return await self._execute_research_file_task(task, definition)

        agent = definition.factory()

        # 5. Execute the task.
        search_budget_token = set_search_budget(1)
        try:
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": task,
                        }
                    ]
                },
                config={"recursion_limit": 6},
            )
        except Exception:
            logger.exception("Generated agent failed while executing task")
            raise
        finally:
            reset_search_budget(search_budget_token)

        # 6. Extract the final response.
        messages = result["messages"]
        final_message = messages[-1]

        return {
            "agent": definition.name,
            "version": definition.version,
            "result": final_message.content,
        }

    async def _execute_research_file_task(self, task: str, definition) -> dict:
        """Run search → summarize → write without a repeating tool loop."""
        tools = self.workflow.templates.tool_registry
        search_result = await tools.get("web_search").ainvoke({"query": task})

        filename_match = re.search(
            r"(?:to|into|in)\s+([\w./-]+\.(?:txt|md|json))",
            task,
            flags=re.IGNORECASE,
        )
        if filename_match is None:
            raise ValueError("File task must include a .txt, .md, or .json filename")
        filename = filename_match.group(1)

        summary = await self.workflow.planner.model.ainvoke([
            (
                "system",
                "Summarize the supplied search result exactly as requested. "
                "Include source URLs. Do not search again and return only the file content.",
            ),
            ("human", f"Task: {task}\nSearch result: {search_result}"),
        ])
        content = summary.content
        await tools.get("write_file").ainvoke({
            "filename": filename,
            "content": content,
        })

        return {
            "agent": definition.name,
            "version": definition.version,
            "result": json.dumps({"file": filename, "content": content}),
        }
