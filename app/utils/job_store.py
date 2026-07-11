"""
utils/job_store.py
In-memory job tracking store.

Stores pipeline job state keyed by job_id.
Thread-safe for single-process use.
TODO: Replace with Redis when scaling to multiple workers.
"""

import threading
from datetime import datetime, UTC
from typing import Any


class JobStore:
    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str, initial: dict) -> dict:
        with self._lock:
            self._store[job_id] = initial
        return initial

    def update(self, job_id: str, updates: dict) -> bool:
        with self._lock:
            if job_id not in self._store:
                return False
            self._store[job_id].update(updates)
            return True

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            return self._store.get(job_id)

    def all_jobs(self) -> list[dict]:
        with self._lock:
            return list(self._store.values())

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return bool(self._store.pop(job_id, None))


# Global singleton
job_store = JobStore()
