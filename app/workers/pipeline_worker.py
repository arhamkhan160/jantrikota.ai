"""
workers/pipeline_worker.py
Background thread worker for running the ML pipeline asynchronously.

Keeps FastAPI responsive while training is in progress.
Each job spins up a daemon thread that calls PipelineService.run().
"""

import threading
from core.logger import get_logger
from services.pipeline_service import PipelineService

logger = get_logger(__name__)

_service = PipelineService()


def run_pipeline_in_background(job_id: str, df, target_column: str, task_type) -> None:
    """
    Spawns a daemon thread to execute the pipeline.
    The job_store is updated by PipelineService throughout execution.
    """
    def _worker():
        logger.info(f"Background worker started for job {job_id}")
        _service.run(
            job_id=job_id,
            df=df,
            target_column=target_column,
            task_type=task_type,
        )
        logger.info(f"Background worker finished for job {job_id}")

    t = threading.Thread(target=_worker, daemon=True, name=f"pipeline-{job_id}")
    t.start()
    logger.info(f"Pipeline thread started: {t.name}")
