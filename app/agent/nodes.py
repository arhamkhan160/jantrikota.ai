"""
agent/nodes.py
Supervisor-agent nodes. Each node calls an existing service as a "tool":
  search  -> sources_registry.search
  choose  -> interrupt (user picks a dataset)
  fetch   -> sources_registry.fetch + dataset_service.save_dataframe
  resolve -> spec_builder.build_spec (+ interrupt if target ambiguous)
  train   -> profiler + ml.trainer.train, recorded in job_store (so /predict works)
"""

import uuid
from datetime import datetime, UTC

from langgraph.types import interrupt

from core.constants import TaskType, JobStatus
from core.logger import get_logger
from integrations import sources_registry as registry
from services.dataset_service import DatasetService
from services.spec_builder import build_spec
from validation.profiler import profile as compute_profile, infer_task
from ml.trainer import train as train_model
from utils.job_store import job_store

logger = get_logger(__name__)
_ds = DatasetService()
_DEFAULT_METRIC = {TaskType.CLASSIFICATION: "accuracy", TaskType.REGRESSION: "rmse"}


def search_node(state: dict) -> dict:
    hits = registry.search(state["query"], 10, state.get("sources") or ["openml"])
    return {"candidates": hits}


def choose_node(state: dict) -> dict:
    cands = state.get("candidates", [])
    if not cands:
        return {"report": {"status": "no_datasets", "message": "No datasets found for the query."}}
    pick = interrupt({
        "type": "choose_dataset",
        "message": "Pick a dataset by ref.",
        "candidates": cands,
    })
    ref = pick.get("ref") if isinstance(pick, dict) else pick
    return {"chosen_ref": ref}


def route_after_choose(state: dict) -> str:
    if state.get("report", {}).get("status") == "no_datasets":
        return "end"
    return "fetch"


def fetch_node(state: dict) -> dict:
    df, target = registry.fetch(state["chosen_ref"])
    name = state["chosen_ref"].replace("/", "_").replace(":", "_")
    resp = _ds.save_dataframe(df, name, suggested_target=target)
    return {"dataset_id": resp.dataset_id, "suggested_target": target}


def resolve_target_node(state: dict) -> dict:
    df = _ds.load_dataset(state["dataset_id"])
    cols = df.columns.tolist()

    suggested = state.get("suggested_target")
    if suggested and suggested in cols:
        chosen = suggested
    else:
        spec = build_spec(state["query"], cols, dataset_id=state["dataset_id"])
        if spec.ambiguous:
            ans = interrupt({
                "type": "confirm_target",
                "message": "Which column should be predicted?",
                "candidates": spec.candidates or cols,
            })
            chosen = ans.get("target") if isinstance(ans, dict) else ans
        else:
            chosen = spec.target

    task = infer_task(df[chosen])
    return {"target": chosen, "task": task.value, "metric": _DEFAULT_METRIC[task]}


def train_node(state: dict) -> dict:
    df = _ds.load_dataset(state["dataset_id"])
    target = state["target"]
    task = TaskType(state["task"])

    # Surface leakage suspects in the report (agent doesn't auto-drop — that's the
    # interactive validation agent's job; here we just flag for the user).
    prof = compute_profile(df, target)
    flags = [c for c, s in prof["columns"].items() if s.get("leakage_suspect")]

    job_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    job_store.create(job_id, {
        "job_id": job_id, "status": JobStatus.RUNNING, "progress": 0.0,
        "current_stage": "agent-train", "started_at": now, "updated_at": now,
        "error": None, "dataset_id": state["dataset_id"], "target_column": target,
    })
    result = train_model(df, target, task, job_id)
    job_store.update(job_id, {
        "status": JobStatus.COMPLETED, "progress": 100.0, "current_stage": "Done",
        "updated_at": datetime.now(UTC), "completed_at": datetime.now(UTC),
        "best_model": result["best_model"], "best_metrics": result["best_metrics"],
        "all_results": result["all_results"], "model_path": result["model_path"],
        "task_type": task, "target_column": target,
    })

    report = {
        "status": "done",
        "ref": state["chosen_ref"],
        "dataset_id": state["dataset_id"],
        "target": target,
        "task": task.value,
        "metric": state["metric"],
        "leakage_flags": flags,
        "best_model": result["best_model"],
        "best_metrics": result["best_metrics"],
        "job_id": job_id,
    }
    logger.info(f"agent done: best={result['best_model']} flags={flags}")
    return {"job_id": job_id, "data_flags": flags, "report": report}
