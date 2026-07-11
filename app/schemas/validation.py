"""
schemas/validation.py
Request/response models for the validation agent endpoints.
"""

from pydantic import BaseModel, Field


class ValidationStartRequest(BaseModel):
    dataset_id: str
    target: str = Field(..., description="Column to predict")


class ValidationAnswerRequest(BaseModel):
    decisions: dict[str, str] = Field(
        ..., description="{column: 'drop'|'keep'} — answers to the agent's drop proposals"
    )


class ValidationResponse(BaseModel):
    validation_id: str
    status: str = Field(..., description="awaiting_user | clean")
    question: dict | None = Field(default=None, description="Pending question when awaiting_user")
    applied: list[dict] = Field(default_factory=list, description="Audit trail of applied changes")
