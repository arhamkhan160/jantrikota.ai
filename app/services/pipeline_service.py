"""
services/pipeline_service.py
Orchestrates a single training job.

FLAML owns the ML (see ml/trainer.py). This service only wires job-state updates
and error handling around it. Called from the background worker.
"""

from datetime import datetime, UTC

from core.constants import TaskType, JobStatus
from core.logger import get_logger
from ml.trainer import train
from utils.job_store import job_store

logger = get_logger(__name__)


class PipelineService:
    def run(self, job_id: str, df, target_column: str, task_type: TaskType) -> None:
        try:
            self._update(job_id, JobStatus.RUNNING, 10, "Training (FLAML AutoML)")
            result = train(df, target_column, task_type, job_id)

            job_store.update(job_id, {
                "status": JobStatus.COMPLETED,
                "progress": 100.0,
                "current_stage": "Done",
                "updated_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC),
                "best_model": result["best_model"],
                "best_metrics": result["best_metrics"],
                "all_results": result["all_results"],
                "model_path": result["model_path"],
                "task_type": task_type,
                "target_column": target_column,
            })
            logger.info(f"Job {job_id} completed. Best model: {result['best_model']}")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            job_store.update(job_id, {
                "status": JobStatus.FAILED,
                "error": str(e),
                "updated_at": datetime.now(UTC),
            })

    def _update(self, job_id: str, status: JobStatus, progress: float, stage: str) -> None:
        job_store.update(job_id, {
            "status": status,
            "progress": progress,
            "current_stage": stage,
            "updated_at": datetime.now(UTC),
        })
        logger.info(f"[{job_id}] {stage} ({progress}%)")
