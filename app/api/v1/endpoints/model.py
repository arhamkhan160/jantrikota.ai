"""
api/v1/endpoints/model.py
GET /api/v1/model/download/{job_id} — Download trained model file.
GET /api/v1/model/list             — List all saved models.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from utils.job_store import job_store
from ml.export.exporter import ModelExporter

router = APIRouter(prefix="/model", tags=["Model"])
_exporter = ModelExporter()


@router.get("/download/{job_id}", summary="Download trained model (.joblib)")
def download_model(job_id: str) -> FileResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    model_path = job.get("model_path")
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Model file not available.")

    filename = os.path.basename(model_path)
    return FileResponse(
        path=model_path,
        media_type="application/octet-stream",
        filename=filename,
    )


@router.get("/list", summary="List all saved models")
def list_models() -> list[str]:
    return _exporter.list_models()
