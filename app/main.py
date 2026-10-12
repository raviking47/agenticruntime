# app/main.py

import logging
import os

from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path

from app.agents.register import register_agents
from app.routes.agent import router as agent_router

load_dotenv(Path(__file__).with_name(".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


app = FastAPI(title="Agentic Runtime")

register_agents()
app.include_router(agent_router)
