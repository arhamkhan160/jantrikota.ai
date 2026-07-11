"""
api/v1/endpoints/predict.py
POST /api/v1/predict — run inference with a job's trained model.
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

from core.constants import JobStatus
from ml.export.exporter import ModelExporter
from schemas.predict import PredictRequest, PredictResponse
from utils.job_store import job_store

router = APIRouter(prefix="/predict", tags=["Predict"])
_exporter = ModelExporter()


def _json_safe(v):
    return v.item() if hasattr(v, "item") else v


@router.post("", response_model=PredictResponse, summary="Predict with a trained model")
def predict(body: PredictRequest) -> PredictResponse:
    job = job_store.get(body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.get("status") != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Model not ready for this job.")
    path = job.get("model_path")
    if not path:
        raise HTTPException(status_code=404, detail="No model file for this job.")

    model = _exporter.load(path)
    X = pd.DataFrame([body.features])
    try:
        pred = model.predict(X)
    except Exception as e:  # feature mismatch / bad input at inference boundary
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    return PredictResponse(job_id=body.job_id, prediction=_json_safe(pred[0]))
