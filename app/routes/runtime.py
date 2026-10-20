from typing import Any
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.registry import AgentRegistry
from app.registry_store import YamlRegistry
from app.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10_000)


def create_router(
    tool_registry: ToolRegistry,
    runtime: Any,
    agent_registry: AgentRegistry,
    registry_catalog: YamlRegistry,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    @router.get("/tools")
    async def list_tools():
        return {"tools": tool_registry.describe()}

    @router.get("/agents")
    async def list_agents():
        return {
            "agents": [
                {
                    "name": definition.name,
                    "version": definition.version,
                    "description": definition.description,
                    "capabilities": definition.capabilities,
                }
                for definition in agent_registry.list()
            ]
        }

    @router.get("/registry")
    async def registry():
        return registry_catalog.snapshot()

    @router.post("/tasks")
    async def execute_task(request: TaskRequest):
        try:
            return await runtime.execute(request.task)

        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        except Exception as exc:
            logger.exception("Task execution failed")
            raise HTTPException(
                status_code=500,
                detail="Task execution failed",
            ) from exc

    return router
