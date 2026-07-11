"""
schemas/query.py
Task Spec — the contract between the NLP layer and the training pipeline.

The NLP layer (services/spec_builder.py) produces a TaskSpec from a free-text
query + the dataset's columns. TaskSpec.target maps to the pipeline's
target_column; TaskSpec.task maps to task_type.
"""

from pydantic import BaseModel, Field

from core.constants import TaskType


class QueryRequest(BaseModel):
    query: str = Field(..., description="Plain-English description of the ML problem")
    dataset_id: str = Field(..., description="Dataset to resolve the target column against")


class TaskSpec(BaseModel):
    task: TaskType
    target: str = Field(..., description="Column to predict (resolved against real columns)")
    metric: str = Field(..., description="rmse | accuracy | f1 | roc_auc")
    dataset_id: str | None = None
    ambiguous: bool = Field(
        default=False,
        description="True when the target could not be confidently matched to a column",
    )
    candidates: list[str] = Field(
        default_factory=list,
        description="Possible target columns when ambiguous — client should ask the user",
    )
