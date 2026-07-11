"""
api/v1/endpoints/dataset.py
POST /api/v1/dataset/upload — Upload a dataset file.
GET  /api/v1/dataset/{dataset_id}/validate — Validate uploaded dataset.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from schemas.dataset import (
    DatasetUploadResponse, DatasetValidationResult,
    DatasetSearchHit, DatasetDetail, ColumnInfo, FetchRequest,
)
from services.dataset_service import DatasetService
from services.column_explainer import explain as explain_columns
from integrations import sources_registry as registry

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


@router.get("/search", response_model=list[DatasetSearchHit], summary="Search datasets (ranked)")
def search_datasets(
    q: str = Query(..., description="Query matched + ranked against dataset names"),
    sources: str = Query("openml", description="Comma list: openml,hf,kaggle"),
    limit: int = Query(10, ge=1, le=50),
) -> list[DatasetSearchHit]:
    """Ranked top-N across sources. Columns/explanations are deferred to /detail on click."""
    src_list = [s.strip() for s in sources.split(",") if s.strip()]
    return [DatasetSearchHit(**h) for h in registry.search(q, limit, src_list)]


@router.get("/detail", response_model=DatasetDetail, summary="Dataset detail (on click)")
def dataset_detail(
    ref: str = Query(..., description="Dataset ref 'source:id', e.g. 'openml:61'"),
) -> DatasetDetail:
    """Metadata only (no full download): description + columns + optional LLM prose."""
    try:
        d = registry.detail(ref)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Detail failed for '{ref}': {e}")

    prose = explain_columns(d["name"], d.get("description"), [c["name"] for c in d["columns"]])
    columns = [ColumnInfo(**{**c, "explanation": prose.get(c["name"]) or c.get("explanation")})
               for c in d["columns"]]
    return DatasetDetail(
        ref=d["ref"], source=d["source"], name=d["name"],
        description=d.get("description"), target=d.get("target"), columns=columns,
    )


@router.post("/fetch", response_model=DatasetUploadResponse, summary="Fetch a dataset by ref")
def fetch_dataset(body: FetchRequest) -> DatasetUploadResponse:
    """Download a dataset ('source:id') into local storage. OpenML carries a target."""
    try:
        df, target = registry.fetch(body.ref)
    except Exception as e:  # network / auth / unknown ref
        raise HTTPException(status_code=502, detail=f"Fetch failed for '{body.ref}': {e}")
    name = body.ref.replace("/", "_").replace(":", "_")
    return _svc.save_dataframe(df, name, suggested_target=target)


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
