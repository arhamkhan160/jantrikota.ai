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
    rows: int | None = None
    features: int | None = None


class OpenMLFetchRequest(BaseModel):
    openml_id: int
