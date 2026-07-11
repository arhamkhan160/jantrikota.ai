"""
ml/trainer.py
Thin wrapper around FLAML AutoML.

FLAML owns everything the old hand-rolled pipeline did: model search, hyperparameter
tuning, preprocessing, and elimination all happen inside `automl.fit()`. We only:
  1. split a holdout,
  2. let FLAML pick the best model,
  3. score that model on the holdout with friendly metrics,
  4. persist the fitted AutoML object (it is itself a picklable estimator with .predict).
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score,
)
from flaml import AutoML

from core.config import settings
from core.constants import TaskType
from core.logger import get_logger
from ml.export.exporter import ModelExporter

logger = get_logger(__name__)


def _classification_metrics(y_true, y_pred, y_proba) -> dict[str, float]:
    m = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_score": float(f1_score(y_true, y_pred, average="weighted")),
    }
    # roc_auc only makes sense for binary targets with probability output
    try:
        if y_proba is not None and len(np.unique(y_true)) == 2:
            m["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
    except Exception as e:  # noqa: BLE001 - metric is best-effort, never fail training on it
        logger.warning(f"roc_auc skipped: {e}")
    return m


def _regression_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def train(df, target_column: str, task_type: TaskType, job_id: str,
          *, time_budget: int | None = None) -> dict:
    """(df, target, task) -> best-model result dict. FLAML owns the ML inside .fit()."""
    X = df.drop(columns=[target_column])
    y = df[target_column]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=settings.RANDOM_STATE
    )

    task = "classification" if task_type == TaskType.CLASSIFICATION else "regression"
    metric = "accuracy" if task == "classification" else "rmse"

    automl = AutoML()
    automl.fit(
        X_train=X_tr, y_train=y_tr,
        task=task, metric=metric,
        time_budget=time_budget or settings.TIME_BUDGET_SECONDS,
        verbose=1,
    )

    y_pred = automl.predict(X_te)
    if task == "classification":
        y_proba = automl.predict_proba(X_te) if hasattr(automl, "predict_proba") else None
        best_metrics = _classification_metrics(y_te, y_pred, y_proba)
    else:
        best_metrics = _regression_metrics(y_te, y_pred)

    best_name = automl.best_estimator

    # Leaderboard: FLAML tracks the best loss it found per estimator family.
    all_results = []
    for name, loss in (automl.best_loss_per_estimator or {}).items():
        if loss is None or (isinstance(loss, float) and np.isinf(loss)):
            continue
        all_results.append({
            "model_name": name,
            "is_best": name == best_name,
            "metrics": best_metrics if name == best_name else {"flaml_loss": float(loss)},
        })
    if not all_results:  # single-estimator run
        all_results = [{"model_name": best_name, "metrics": best_metrics, "is_best": True}]

    # Persist the fitted AutoML object — it has .predict for inference (M6).
    model_path = ModelExporter().save(automl, job_id, best_name)
    logger.info(f"Best model '{best_name}' | metrics={best_metrics} | saved={model_path}")

    return {
        "best_model": best_name,
        "best_metrics": best_metrics,
        "all_results": all_results,
        "model_path": model_path,
    }
