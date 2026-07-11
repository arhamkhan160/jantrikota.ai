"""
ml/export/exporter.py
Saves trained models to disk and loads them for inference.
"""

import os
import joblib
from pathlib import Path
from datetime import datetime
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class ModelExporter:
    def __init__(self, model_dir: str | None = None):
        self.model_dir = Path(model_dir or settings.MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save(self, model, job_id: str, model_name: str) -> str:
        """Save model to disk. Returns the file path."""
        filename = f"{job_id}__{model_name.replace(' ', '_')}.joblib"
        path = self.model_dir / filename
        joblib.dump(model, path)
        logger.info(f"Model saved: {path}")
        return str(path)

    def load(self, path: str):
        """Load a model from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        logger.info(f"Loading model from: {path}")
        return joblib.load(path)

    def list_models(self) -> list[str]:
        return [str(p) for p in self.model_dir.glob("*.joblib")]
