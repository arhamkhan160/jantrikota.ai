"""
api/v1/endpoints/pipeline.py
POST /api/v1/pipeline/start  — Start a pipeline job.
GET  /api/v1/pipeline/status/{job_id} — Get job status.
GET  /api/v1/pipeline/results/{job_id} — Get full results.
"""

import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException

from core.constants import JobStatus
from schemas.pipeline import PipelineStartRequest, PipelineStatusResponse, PipelineResultResponse, ModelResult
from services.dataset_service import DatasetService
from utils.job_store import job_store
from workers.pipeline_worker import run_pipeline_in_background

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])
_dataset_svc = DatasetService()


@router.post("/start", response_model=PipelineStatusResponse, summary="Start an ML pipeline job")
def start_pipeline(body: PipelineStartRequest) -> PipelineStatusResponse:
    # Load dataset
    try:
        df = _dataset_svc.load_dataset(body.dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{body.dataset_id}' not found.")

    # Validate target column
    if body.target_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Target column '{body.target_column}' not found in dataset.",
        )

    job_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    initial = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0.0,
        "current_stage": "Queued",
        "started_at": now,
        "updated_at": now,
        "error": None,
        "dataset_id": body.dataset_id,
        "target_column": body.target_column,
    }
    job_store.create(job_id, initial)

    # Determine task type (use body value or auto-detect later via NLP)
    task_type = body.task_type
    if task_type is None:
        # Simple heuristic: if target has few unique values → classification
        n_unique = df[body.target_column].nunique()
        from core.constants import TaskType
        task_type = TaskType.CLASSIFICATION if n_unique <= 20 else TaskType.REGRESSION

    run_pipeline_in_background(job_id, df, body.target_column, task_type)

    job = job_store.get(job_id)
    return PipelineStatusResponse(**job)


@router.get("/status/{job_id}", response_model=PipelineStatusResponse, summary="Get pipeline job status")
def get_status(job_id: str) -> PipelineStatusResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return PipelineStatusResponse(**job)


@router.get("/results/{job_id}", response_model=PipelineResultResponse, summary="Get pipeline results")
def get_results(job_id: str) -> PipelineResultResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed yet. Current status: {job['status']}",
        )

    all_results = [ModelResult(**r) for r in job.get("all_results", [])]

    return PipelineResultResponse(
        job_id=job_id,
        status=job["status"],
        task_type=job["task_type"],
        target_column=job["target_column"],
        best_model=job["best_model"],
        best_metrics=job["best_metrics"],
        all_results=all_results,
        model_path=job.get("model_path"),
        completed_at=job.get("completed_at"),
    )
