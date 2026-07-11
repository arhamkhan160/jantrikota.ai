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


class DatasetValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {}
