"""
schemas/agent.py
Request/response models for the supervisor-agent endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field


class AgentStartRequest(BaseModel):
    query: str = Field(..., description="Plain-English ML request")
    sources: list[str] = Field(default_factory=lambda: ["openml"],
                               description="Dataset sources to search: openml, hf, kaggle")


class AgentAnswerRequest(BaseModel):
    value: dict[str, Any] = Field(
        ..., description="Answer to the agent's question, e.g. {'ref':'openml:61'} or {'target':'price'}"
    )


class AgentResponse(BaseModel):
    agent_id: str
    status: str = Field(..., description="awaiting | done | no_datasets")
    question: dict | None = Field(default=None, description="Pending question when awaiting")
    report: dict | None = Field(default=None, description="Final report when done")
