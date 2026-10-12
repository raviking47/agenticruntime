# app/agents/file_agent.py

import logging

from langchain.agents import create_agent
import os

from app.agents.llm import get_model


from app.agents.base import BaseAgent
from app.tools.files import tool_capabilities
capabilities = [
        "file.write",
        "text.generate",
        "text.summarize",
        "read.file",
        "delete.file",        
    ]

logger = logging.getLogger(__name__)

class FileAgent(BaseAgent):

    name = "file_agent"
    version = "1.0.0"
    description = "Creates and writes Howtext files."
    capabilities = capabilities


    def __init__(self):
        logger.info("Creating file agent")
        self.agent = create_agent(
            model=get_model(),
            tools=tool_capabilities(),
            system_prompt="""
            You are a file-writing agent.

            Generate text requested by the user
            and save it using the write_file tool.
            """,
        )
        logger.info("File agent created with %d tools", len(tool_capabilities()))


    async def run(self, input: str, **kwargs):
        logger.debug("File agent processing request: message_length=%d", len(input))
        result = await self.agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": input,
                }
            ]
        })

        response = result["messages"][-1].content
        print(f"File agent response: {response}")
        logger.debug("File agent response generated: response_length=%d", (response))
        logger.debug("File agent response generated: response_type=%s", type(response).__name__)
        return response
