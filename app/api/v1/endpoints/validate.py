"""
api/v1/endpoints/validate.py
POST /api/v1/validate/start        — begin the validation-agent run
GET  /api/v1/validate/{id}         — current state (clean, or a pending question)
POST /api/v1/validate/{id}/answer  — answer the agent's question; graph resumes
"""

import uuid

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from schemas.validation import (
    ValidationStartRequest, ValidationAnswerRequest, ValidationResponse,
)
from services.dataset_service import DatasetService
from validation import store
from validation.graph import get_graph

router = APIRouter(prefix="/validate", tags=["Validation"])
_ds = DatasetService()


def _config(validation_id: str) -> dict:
    return {"configurable": {"thread_id": validation_id}}


def _response(validation_id: str, result: dict) -> ValidationResponse:
    interrupts = result.get("__interrupt__")
    if interrupts:
        return ValidationResponse(
            validation_id=validation_id,
            status="awaiting_user",
            question=interrupts[0].value,
            applied=result.get("applied", []),
        )
    return ValidationResponse(
        validation_id=validation_id,
        status="clean",
        applied=result.get("applied", []),
    )


@router.post("/start", response_model=ValidationResponse, summary="Start validation agent")
def start(body: ValidationStartRequest) -> ValidationResponse:
    try:
        df = _ds.load_dataset(body.dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{body.dataset_id}' not found.")
    if body.target not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target '{body.target}' not in dataset.")

    validation_id = str(uuid.uuid4())
    store.put(validation_id, df)
    try:
        result = get_graph().invoke(
            {"run_id": validation_id, "target": body.target, "applied": [], "iterations": 0},
            _config(validation_id),
        )
    except RuntimeError as e:  # LLM not configured
        raise HTTPException(status_code=503, detail=str(e))
    return _response(validation_id, result)


@router.post("/{validation_id}/answer", response_model=ValidationResponse, summary="Answer + resume")
def answer(validation_id: str, body: ValidationAnswerRequest) -> ValidationResponse:
    result = get_graph().invoke(Command(resume=body.decisions), _config(validation_id))
    return _response(validation_id, result)


@router.get("/{validation_id}", response_model=ValidationResponse, summary="Validation state")
def status(validation_id: str) -> ValidationResponse:
    snap = get_graph().get_state(_config(validation_id))
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Validation run not found.")
    for task in snap.tasks:
        if task.interrupts:
            return ValidationResponse(
                validation_id=validation_id,
                status="awaiting_user",
                question=task.interrupts[0].value,
                applied=snap.values.get("applied", []),
            )
    return ValidationResponse(
        validation_id=validation_id,
        status="clean",
        applied=snap.values.get("applied", []),
    )
