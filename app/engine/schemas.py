from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    name: str = Field(description="Stable name for the required tool")
    capability: str = Field(description="Capability provided by the tool")
    template: str = Field(
        description="Approved implementation template, for example web_search"
    )


class AgentSpec(BaseModel):
    work_key: str = Field(
        description="Reusable work role, for example research or file_operations",
    )

    name: str = Field(
        description="Short descriptive name for the internal agent"
    )

    description: str = Field(
        description="What the agent is designed to do"
    )

    instructions: str = Field(
        description="Instructions governing the agent's behavior"
    )

    tool_names: list[str] = Field(
        default_factory=list,
        description="Names of registered tools required by the agent"
    )

    tool_requests: list[ToolRequest] = Field(
        default_factory=list,
        description="Tools that must be created when they are not registered",
    )
