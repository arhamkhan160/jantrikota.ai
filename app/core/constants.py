"""
core/constants.py
Enums, literals, and shared constants.
"""

from enum import Enum


class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Metric key names
CLASSIFICATION_METRICS = ["accuracy", "f1_score", "roc_auc"]
REGRESSION_METRICS = ["rmse", "mae", "r2"]

# Allowed upload MIME types
ALLOWED_UPLOAD_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
    "application/octet-stream",  # fallback
}

MAX_UPLOAD_SIZE_MB = 100
