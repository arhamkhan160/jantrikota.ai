"""
services/dataset_service.py
Handles file upload, schema detection, and validation.
"""

import uuid
import os
import json
from pathlib import Path
from datetime import datetime, UTC

import pandas as pd

from core.config import settings
from core.logger import get_logger
from core.constants import ALLOWED_UPLOAD_TYPES, MAX_UPLOAD_SIZE_MB
from schemas.dataset import DatasetUploadResponse, DatasetValidationResult

logger = get_logger(__name__)

DATASET_DIR = Path(settings.DATASET_DIR)
DATASET_DIR.mkdir(parents=True, exist_ok=True)


class DatasetService:
    def save_upload(self, file_bytes: bytes, filename: str, content_type: str) -> DatasetUploadResponse:
        # Validation
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise ValueError(f"File size {size_mb:.1f} MB exceeds limit of {MAX_UPLOAD_SIZE_MB} MB.")

        dataset_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        save_path = DATASET_DIR / f"{dataset_id}{ext}"

        save_path.write_bytes(file_bytes)
        logger.info(f"Dataset saved: {save_path}")

        # Parse
        df = self._read_file(save_path, ext)

        # Save metadata sidecar
        meta = {
            "dataset_id": dataset_id,
            "filename": filename,
            "path": str(save_path),
            "rows": len(df),
            "columns": len(df.columns),
        }
        (DATASET_DIR / f"{dataset_id}.meta.json").write_text(json.dumps(meta))

        return DatasetUploadResponse(
            dataset_id=dataset_id,
            filename=filename,
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            missing_values={col: int(df[col].isnull().sum()) for col in df.columns},
            upload_time=datetime.now(UTC),
        )

    def load_dataset(self, dataset_id: str) -> pd.DataFrame:
        meta_path = DATASET_DIR / f"{dataset_id}.meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Dataset {dataset_id} not found.")

        meta = json.loads(meta_path.read_text())
        path = Path(meta["path"])
        ext = path.suffix.lower()
        return self._read_file(path, ext)

    def validate(self, df: pd.DataFrame, target_column: str) -> DatasetValidationResult:
        errors, warnings = [], []

        if target_column not in df.columns:
            errors.append(f"Target column '{target_column}' not found in dataset.")

        if len(df) < 50:
            warnings.append("Dataset has fewer than 50 rows. Results may be unreliable.")

        if df.isnull().mean().max() > 0.3:
            warnings.append("Some columns have >30% missing values.")

        return DatasetValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            summary={"rows": len(df), "columns": len(df.columns)},
        )

    @staticmethod
    def _read_file(path: Path, ext: str) -> pd.DataFrame:
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(path)
        elif ext == ".json":
            return pd.read_json(path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
