"""
api/v1/endpoints/query.py
POST /api/v1/query — free-text ML request -> TaskSpec.

Resolves the target against the uploaded dataset's columns. If the target is
ambiguous, the response carries `ambiguous=true` + `candidates` for the client
to disambiguate before calling /pipeline/start.
"""

from fastapi import APIRouter, HTTPException

from schemas.query import QueryRequest, TaskSpec
from services.dataset_service import DatasetService
from services.spec_builder import build_spec

router = APIRouter(prefix="/query", tags=["Query"])
_dataset_svc = DatasetService()


@router.post("", response_model=TaskSpec, summary="Parse a natural-language ML request")
def parse_query(body: QueryRequest) -> TaskSpec:
    try:
        df = _dataset_svc.load_dataset(body.dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{body.dataset_id}' not found.")

    try:
        return build_spec(body.query, df.columns.tolist(), dataset_id=body.dataset_id)
    except RuntimeError as e:  # LLM not configured
        raise HTTPException(status_code=503, detail=str(e))
