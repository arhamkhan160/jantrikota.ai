"""
schemas/pipeline.py
Pydantic schemas for pipeline lifecycle endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
from core.constants import JobStatus, TaskType


class PipelineStartRequest(BaseModel):
    dataset_id: str = Field(..., description="ID returned from /upload-dataset")
    target_column: str = Field(..., description="Name of the target/label column")
    task_type: TaskType | None = None   # auto-detected if None
    query: str | None = None            # optionally pass original NL query


class PipelineStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=100.0)
    current_stage: str = ""
    started_at: datetime
    updated_at: datetime
    error: str | None = None


class ModelResult(BaseModel):
    model_name: str
    metrics: dict[str, float]
    is_best: bool = False


class PipelineResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    task_type: TaskType
    target_column: str
    best_model: str
    best_metrics: dict[str, float]
    all_results: list[ModelResult]
    model_path: str | None = None
    completed_at: datetime | None = None
