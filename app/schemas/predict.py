"""
schemas/predict.py
Inference request/response for a trained model.
"""

from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    job_id: str = Field(..., description="Completed pipeline job whose model to use")
    features: dict[str, Any] = Field(..., description="One row: {column: value}")


class PredictResponse(BaseModel):
    job_id: str
    prediction: Any
