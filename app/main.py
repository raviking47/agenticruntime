import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.agents.llm import get_model
from app.agents.register import register_agents
from app.engine.agent_creator import AgentCreator
from app.engine.runtime import AgentRuntime
from app.engine.template_create_engine import TemplateCreateEngine
from app.engine.workflow import WorkflowEngine
from app.routes.agent import router as agent_router
from app.routes.runtime import create_router as create_runtime_router
from app.tools.tool_registry import ToolRegistry
from app.registry_instance import agent_registry, registry_catalog, runtime_store
from app.templates.builtin_tools import read_file, web_search, write_file
from app.templates.tool_template import ToolTemplate

load_dotenv(Path(__file__).with_name(".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

app = FastAPI(title="Dynamic Agent Engine")

# LLM shared by the planner and task agents.
llm = get_model()

# Register available tools.
tool_registry = ToolRegistry(registry_catalog, runtime_store)
tool_registry.register(
    read_file,
    capabilities=["file.read"],
    template="file_read",
)
tool_registry.register(
    write_file,
    capabilities=["file.write"],
    template="file_write",
)

# There are no predefined agents; the workflow creates and restores agents.
register_agents()

# Construct the engine.
creator = AgentCreator(
    model=llm,
    tool_registry=tool_registry,
)

template_engine = TemplateCreateEngine(llm, tool_registry, agent_registry, runtime_store)
for template in (
    ToolTemplate(
        name="read_file",
        description="Read a UTF-8 text file from the workspace.",
        capabilities=["file.read"],
        function=read_file,
    ),
    ToolTemplate(
        name="write_file",
        description="Write text content to a file in the workspace.",
        capabilities=["file.write"],
        function=write_file,
    ),
    ToolTemplate(
        name="web_search",
        description="Search the public web and return relevant results.",
        capabilities=["web.search"],
        function=web_search,
    ),
):
    template_engine.register_tool_template(template)
template_engine.restore_tools()
template_engine.restore_agents()
workflow = WorkflowEngine(creator, template_engine)
runtime = AgentRuntime(workflow)

app.include_router(create_runtime_router(
    tool_registry=tool_registry,
    runtime=runtime,
    agent_registry=agent_registry,
    registry_catalog=registry_catalog,
))
app.include_router(agent_router)
