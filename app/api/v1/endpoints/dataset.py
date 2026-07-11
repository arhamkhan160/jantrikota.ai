"""
api/v1/endpoints/dataset.py
POST /api/v1/dataset/upload — Upload a dataset file.
GET  /api/v1/dataset/{dataset_id}/validate — Validate uploaded dataset.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from schemas.dataset import DatasetUploadResponse, DatasetValidationResult
from services.dataset_service import DatasetService

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
