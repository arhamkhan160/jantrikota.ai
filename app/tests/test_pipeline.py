"""
tests/test_pipeline.py
Integration tests for dataset upload and pipeline start.
Uses a small synthetic CSV to exercise the full flow.
"""

import io
import csv
import time

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _make_csv(rows: int = 100) -> bytes:
    """Generate a tiny synthetic classification CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["feature_a", "feature_b", "feature_c", "label"])
    import random
    random.seed(42)
    for _ in range(rows):
        a = round(random.gauss(0, 1), 4)
        b = round(random.gauss(5, 2), 4)
        c = round(random.gauss(-1, 0.5), 4)
        label = 1 if a + b > 5 else 0
        writer.writerow([a, b, c, label])
    return buf.getvalue().encode()


def test_upload_dataset():
    csv_bytes = _make_csv(200)
    response = client.post(
        "/api/v1/dataset/upload",
        files={"file": ("test_data.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "dataset_id" in data
    assert data["rows"] == 200
    assert "label" in data["column_names"]


def test_full_pipeline():
    # 1. Upload
    csv_bytes = _make_csv(150)
    upload_resp = client.post(
        "/api/v1/dataset/upload",
        files={"file": ("pipeline_test.csv", csv_bytes, "text/csv")},
    )
    assert upload_resp.status_code == 200
    dataset_id = upload_resp.json()["dataset_id"]

    # 2. Start pipeline
    start_resp = client.post(
        "/api/v1/pipeline/start",
        json={"dataset_id": dataset_id, "target_column": "label"},
    )
    assert start_resp.status_code == 200
    job_id = start_resp.json()["job_id"]

    # 3. Poll status until done (max 60 seconds)
    for _ in range(30):
        status_resp = client.get(f"/api/v1/pipeline/status/{job_id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(2)

    # 4. Check results
    results_resp = client.get(f"/api/v1/pipeline/results/{job_id}")
    assert results_resp.status_code == 200
    data = results_resp.json()
    assert data["status"] == "completed"
    assert data["best_model"] != ""
    assert len(data["all_results"]) > 0
