"""
schemas/dataset.py
Pydantic schemas for dataset upload and validation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    upload_time: datetime
    suggested_target: str | None = None   # set when fetched from OpenML (target is labeled)


class DatasetValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {}


class DatasetSearchHit(BaseModel):
    openml_id: int
    name: str
    confidence: float = 0.0          # ranking score (semantic, else lexical)
    rows: int | None = None
    features: int | None = None


class ColumnInfo(BaseModel):
    name: str
    type: str | None = None
    n_missing: int | None = None
    n_distinct: int | None = None
    explanation: str | None = None   # LLM prose when a key is configured


class DatasetDetail(BaseModel):
    openml_id: int
    name: str
    description: str | None = None
    target: str | None = None
    columns: list[ColumnInfo]


class OpenMLFetchRequest(BaseModel):
    openml_id: int
