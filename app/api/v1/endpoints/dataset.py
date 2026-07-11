"""
api/v1/endpoints/dataset.py
POST /api/v1/dataset/upload — Upload a dataset file.
GET  /api/v1/dataset/{dataset_id}/validate — Validate uploaded dataset.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from schemas.dataset import (
    DatasetUploadResponse, DatasetValidationResult,
    DatasetSearchHit, OpenMLFetchRequest,
)
from services.dataset_service import DatasetService
from integrations import openml as openml_int

router = APIRouter(prefix="/dataset", tags=["Dataset"])
_svc = DatasetService()


@router.post("/upload", response_model=DatasetUploadResponse, summary="Upload a dataset file")
async def upload_dataset(file: UploadFile = File(...)) -> DatasetUploadResponse:
    """
    Accepts a CSV, Excel, or JSON file. Returns dataset metadata and column info.
    """
    content = await file.read()
    try:
        return _svc.save_upload(content, file.filename or "upload", file.content_type or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=list[DatasetSearchHit], summary="Search OpenML datasets")
def search_datasets(
    q: str = Query(..., description="Substring to match against dataset names"),
    limit: int = Query(10, ge=1, le=50),
) -> list[DatasetSearchHit]:
    return [DatasetSearchHit(**h) for h in openml_int.search(q, limit)]


@router.post("/fetch", response_model=DatasetUploadResponse, summary="Fetch an OpenML dataset")
def fetch_dataset(body: OpenMLFetchRequest) -> DatasetUploadResponse:
    """Download an OpenML dataset into local storage; target comes pre-labeled."""
    try:
        df, target = openml_int.fetch(body.openml_id)
    except Exception as e:  # network / unknown id
        raise HTTPException(status_code=502, detail=f"OpenML fetch failed: {e}")
    return _svc.save_dataframe(df, f"openml_{body.openml_id}", suggested_target=target)


@router.get(
    "/{dataset_id}/validate",
    response_model=DatasetValidationResult,
    summary="Validate a dataset against a target column",
)
def validate_dataset(
    dataset_id: str,
    target_column: str = Query(..., description="Column to use as label/target"),
) -> DatasetValidationResult:
    try:
        df = _svc.load_dataset(dataset_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _svc.validate(df, target_column)
