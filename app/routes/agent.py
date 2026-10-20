import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.registry_instance import agent_registry
from app.templates.builtin_tools import reset_search_budget, set_search_budget

router = APIRouter()
logger = logging.getLogger(__name__)


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)


@router.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str, request: AgentRequest):
    logger.info("Request received: agent=%s message_length=%d", agent_name, len(request.message))
    try:
        definition = agent_registry.get_agent(agent_name)
        logger.info("Running agent: %s (version %s)", definition.name, definition.version)
    except ValueError as exc:
        logger.warning("Agent not found: %s", agent_name)
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not definition.enabled:
        raise HTTPException(status_code=403, detail="Agent is disabled")
    if definition.factory is None:
        raise HTTPException(status_code=503, detail="Agent has no factory")

    try:
        agent = definition.factory()
        logger.info("Agent initialized: agent=%s version=%s", definition.name, definition.version)
    except Exception as exc:
        logger.exception("Could not initialize agent: %s", definition.name)
        raise HTTPException(status_code=503, detail="Agent is unavailable") from exc

    try:
        logger.info("Invoking agent: agent=%s", definition.name)
        if hasattr(agent, "run"):
            result = await agent.run(request.message)
        else:
            search_budget_token = set_search_budget(1)
            try:
                result_data = await agent.ainvoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": request.message,
                            }
                        ]
                    },
                    config={"recursion_limit": 6},
                )
            finally:
                reset_search_budget(search_budget_token)
            result = result_data["messages"][-1].content
        logger.info("Agent completed: agent=%s result_type=%s", definition.name, type(result).__name__)
    except Exception as exc:
        logger.exception("Agent execution failed: %s", definition.name)
        raise HTTPException(status_code=500, detail="Agent execution failed") from exc

    return {"agent": definition.name, "version": definition.version, "result": result}
