# 📘 AutoML Agent

### Natural-Language-Driven Machine Learning Pipeline

Describe an ML problem in plain English → the system finds a dataset (or you upload one) → an **interactive validation agent** cleans it *with you in the loop* → an existing AutoML library trains and picks the best model → you get a live inference endpoint.

---

## 🎯 What this project actually is

The ML is a **solved commodity**. Libraries already train many models and return the best (FLAML, PyCaret) and already do automated feature engineering (featuretools). We do **not** re-implement any of that.

**Our product = the translator + conductor + validation agent** — the judgment those libraries don't have:

1. **Translate** free-text query → a precise ML task spec.
2. **Validate** the dataset through a stateful **LLM + user + statistics** loop (the differentiator).
3. **Conduct** the AutoML library, then **serve** the result as an API.

> If you strip the language + validation layers, this is "a nicer UI over PyCaret." Those two layers are the only part that is genuinely ours. That is where the effort goes.

---

## 🧩 The spine: Task Spec

Everything hangs on one contract. NLP layer produces it; validation + AutoML layers consume it.

```json
{
  "task": "regression",          // or "classification"
  "target": "price",             // column to predict
  "metric": "rmse",              // rmse | accuracy | f1 | roc_auc
  "dataset_id": "openml:42165"   // resolved dataset reference
}
```

Build this schema **first**. It is the interface between every half of the system.

---

## 🔄 System flow

```
User query (natural language)
      ↓
NLP layer  → produces Task Spec (task, target, metric)
      ↓
Dataset layer
   ├─ Upload: user provides CSV                    (Phase 1)
   └─ Fetch:  search OpenML / HuggingFace → user picks   (Phase 3)
      ↓
╔══════════════════════════════════════════════════════╗
║  VALIDATION AGENT  (LangGraph — stateful loop)        ║
║  profile → LLM proposes → STATS gate → ask user →     ║
║  apply → re-profile → … until clean                   ║
╚══════════════════════════════════════════════════════╝
      ↓
Clean dataframe + Task Spec  →  AutoML library
                                (FLAML/PyCaret owns training,
                                 feature engineering, tuning)
      ↓
Best model + metrics
      ↓
Persist model  →  serve /predict endpoint
```

Training jobs run in the background; the client polls `/status/{job_id}`.

---

## 🧠 The Validation Agent (LangGraph)

This is the one subsystem that genuinely needs a state-machine framework, because it has **cycles + human-in-the-loop + conditional branching** — exactly what LangGraph is for. Everything else in the app stays plain Python functions.

### The iron rule

> **LLM proposes. Statistics gate. User confirms. Nothing is dropped or altered on name-meaning alone.**

The LLM never edits the dataframe directly. It reads a **statistical profile** and *suggests* actions. Every suggestion carries hard numbers, and destructive actions require the stats to agree **and** the user to approve.

Why this rule exists — the trap: ice-cream-sales and shark-attacks are *correlated* (both driven by summer heat). For a **prediction** task that correlation makes shark-attacks a *useful predictor*. An LLM dropping it because it's "semantically unrelated" would delete real signal. So relevance is decided by **correlation / mutual information / model importance on the data**, not by what a column *sounds* like.

### Graph shape

```
        ┌─────────────┐
        │   PROFILE   │  compute per-column stats:
        │  (stats)    │  dtype, missing %, cardinality,
        └──────┬──────┘  corr-to-target, mutual info,
               │         leakage check, duplicate/constant
               ▼
        ┌─────────────┐
        │  LLM REVIEW │  reads profile + column names,
        │  (propose)  │  proposes actions WITH evidence:
        └──────┬──────┘  [{col, action, reason, stat}]
               │
               ▼
        ┌─────────────┐   stats disagree → reject proposal,
        │  STATS GATE │──▶ log, keep column
        │  (verify)   │   (e.g. "drop" but importance high)
        └──────┬──────┘
               │ passes gate
               ▼
        ┌─────────────┐   confident + low-risk → auto-apply
        │  DECIDE     │──────────────┐
        └──────┬──────┘              │
               │ ambiguous / risky   │
               ▼                     │
        ┌─────────────┐ interrupt    │
        │  ASK USER   │  (wait for   │
        │ (human loop)│   answer)    │
        └──────┬──────┘              │
               ▼                     ▼
        ┌───────────────────────────────┐
        │           APPLY               │  mutate dataframe
        └──────────────┬────────────────┘
                       ▼
                 re-PROFILE ──▶ loop until no actions remain
                       ▼
                 ┌───────────┐
                 │  CLEAN ✓  │  emit validated dataframe
                 └───────────┘
```

### Nodes

| Node | Does | Owner |
|---|---|---|
| **profile** | pure stats: missing %, cardinality, corr-to-target, mutual info, target leakage, constant/duplicate cols | pandas / sklearn — no LLM |
| **llm_review** | reads the profile, proposes `[{col, action, reason, evidence}]` | LLM, structured output |
| **stats_gate** | rejects any proposal the numbers don't support (e.g. "drop" a high-importance col) | pure code — the safety rail |
| **decide** | confident + low-risk → auto-apply; ambiguous/destructive → route to user | conditional edge |
| **ask_user** | `interrupt()` — surface proposal + evidence, wait for answer | LangGraph human-in-the-loop |
| **apply** | mutate dataframe per approved actions | pure code |
| **loop** | re-profile; exit when no actions remain or user says done | graph edge |

Actions the agent can propose: `drop_column`, `impute_missing`, `cast_type`, `flag_leakage`, `flag_confounder`, `handle_outliers`, `encode`. Each returns the stat that justifies it.

### State (what flows through the graph)

```python
class ValidationState(TypedDict):
    df: pd.DataFrame
    spec: TaskSpec
    profile: dict            # latest stats snapshot
    proposals: list[dict]    # LLM suggestions + evidence
    applied: list[dict]      # audit trail of every change
    pending_question: dict | None   # set when waiting on user
    done: bool
```

The `applied` list is the audit trail — every mutation, with its statistical justification and who approved it. Nothing changes without a recorded reason.

---

## 🧱 What WE build vs what LIBRARIES own

| Concern | Owner | Notes |
|---|---|---|
| Model training & selection | **Library** (FLAML / PyCaret) | includes subset→eliminate→shortlist→full-train — don't hand-roll |
| Preprocessing / encoding / scaling | **Library** | sklearn pipelines inside the AutoML lib |
| Statistical feature scoring | **Library / sklearn** | corr, mutual info, importances — feeds the validation agent |
| Automated feature engineering | **Library** (featuretools) | optional, add later |
| Hyperparameter tuning | **Library** | inside FLAML |
| NL query → Task Spec | **Us** | LLM, structured output |
| **Validation agent (loop)** | **Us** (LangGraph) | LLM proposes · stats gate · user confirms |
| Dataset search & schema understanding | **Us** | relevance + target resolution |
| Job orchestration, persistence, serving | **Us** | FastAPI glue — plain functions |

---

## 🗂️ Dataset sources (fetch path)

Start with **OpenML** — it labels the target column in metadata, so target resolution is free.

| Source | Why | Watch out |
|---|---|---|
| **OpenML** | built for ML, target labeled, clean API | start here |
| HuggingFace Datasets | huge, searchable, permissive licenses | schema unknown → target resolution needed |
| Kaggle | biggest catalog | auth + redistribution ToS, large downloads |

Skip scraping random sources — licensing and quality hell.

---

## 🛠️ Tech Stack

**Backend:** FastAPI, Uvicorn
**Validation agent:** **LangGraph** — stateful loop with human-in-the-loop interrupts
**LLM calls:** LangChain *only as the LLM/structured-output client the graph uses* (or raw provider SDK) — not as the app framework
**AutoML:** FLAML (start here) or PyCaret — owns training + tuning + preprocessing
**Data / stats:** pandas, numpy, scikit-learn (correlation, mutual info, importances)
**Dataset fetch:** `openml`, HuggingFace `datasets`
**Feature engineering (optional, later):** featuretools
**Serialization:** joblib

> Scoped deliberately: LangGraph lives **only** in the validation subsystem, where the loop actually exists. The rest of the app (query parsing, job orchestration, serving) is plain FastAPI + Python functions — no graph, no chains. Don't spread the framework past the subsystem that needs it.
>
> Dropped from the original plan: spaCy, transformers pipeline, hand-wired XGBoost/LightGBM/CatBoost, multiprocessing, Dask, Optuna. The AutoML library covers what those were for. Add back only when it measurably falls short.

---

## 📡 API Design

| Method | Route | Purpose |
|---|---|---|
| POST | `/query` | free-text → Task Spec (+ dataset suggestions on fetch path) |
| POST | `/upload-dataset` | upload CSV, returns `dataset_id` |
| GET | `/datasets/search?q=` | search OpenML/HF, return descriptions to pick from |
| POST | `/validate/start` | begin the validation-agent run, returns `validation_id` |
| GET | `/validate/{id}` | current state — clean, or a pending question for the user |
| POST | `/validate/{id}/answer` | user answers the agent's question → graph resumes |
| POST | `/start-pipeline` | validated Task Spec → starts background training job, returns `job_id` |
| GET | `/status/{job_id}` | training progress |
| GET | `/results/{job_id}` | best model + metrics |
| GET | `/download-model/{job_id}` | download `.pkl` |
| POST | `/predict` | run inference with the trained model |

`/query`
```json
{ "query": "predict house prices from this data" }
```

`/validate/{id}` when the agent needs you (human-in-the-loop):
```json
{
  "status": "awaiting_user",
  "question": "Column 'agent_id' has 0.99 correlation with 'price' — likely target leakage. Drop it?",
  "evidence": { "corr_to_target": 0.99, "mutual_info": 0.95 },
  "options": ["drop", "keep"]
}
```

`/start-pipeline` (validated Task Spec)
```json
{ "task": "regression", "target": "price", "metric": "rmse", "dataset_id": "openml:42165" }
```

---

## 🏗️ Project Structure

```
automl-agent/
├── app/
│   ├── main.py
│   ├── core/           # config, logger, constants
│   ├── api/v1/         # endpoints + router
│   ├── schemas/        # Task Spec + request/response models  ← build first
│   ├── services/       # orchestration (the conductor) — plain functions
│   ├── ml/             # thin wrappers around FLAML/PyCaret — NOT reimplementations
│   ├── validation/     # ← LangGraph agent: graph.py, nodes.py, profiler.py, state.py
│   ├── integrations/   # OpenML / HF / LLM clients
│   ├── utils/
│   └── workers/        # background training-job runner
├── models/             # saved models
├── datasets/           # uploaded/fetched data
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 🚀 Build order (generate gradually)

Each phase runs end-to-end before the next starts. Don't build ahead.

### Phase 0 — Skeleton *(done)*
FastAPI app, config, logger, health route, Docker. → `main.py` already runs.

### Phase 1 — Spine + upload + train
Proof the core idea works, **zero external deps**, data you control.
- `schemas/` — Task Spec model
- `POST /upload-dataset` (CSV → dataframe, save)
- `POST /start-pipeline` → hand dataframe + Task Spec to **FLAML** → best model
- background job + `/status` + `/results` + `/download-model`
- **Manual** Task Spec (user sends `target` + `task` — no NLP, no validation agent yet)

✅ End of Phase 1: upload CSV → get best model. A working product.

### Phase 2 — NLP layer
- `POST /query` → LLM structured output → Task Spec
- resolve `target` against real dataframe columns; flag if ambiguous

### Phase 3 — Validation Agent (LangGraph) ⭐ the core feature
Build the graph in `app/validation/`:
1. `profiler.py` — pure-stats profile (no LLM). **Build + test this first** — it's the safety rail everything else trusts.
2. `state.py` — `ValidationState`.
3. `nodes.py` — `profile`, `llm_review`, `stats_gate`, `decide`, `ask_user`, `apply`.
4. `graph.py` — wire nodes, conditional edges, `interrupt()` for the user question, loop-back edge.
5. Endpoints: `/validate/start`, `/validate/{id}`, `/validate/{id}/answer` (resume the interrupted graph).
- Persist graph state (LangGraph checkpointer) so a run survives across the request/answer round-trip.

### Phase 4 — Dataset fetch
- `GET /datasets/search` over **OpenML** first (target pre-labeled) → user picks → `dataset_id` flows into validation + training.
- add HuggingFace source after OpenML works.

### Phase 5 — Serving + polish
- `POST /predict` against the saved model.
- input validation, error handling when training explodes.

### Later (only if measured need)
featuretools for auto features · Redis+Celery for multi-worker jobs · MLflow tracking · UI dashboard.

> Storage defaults: Phase 1 training jobs = in-memory dict + FastAPI `BackgroundTasks`. Phase 3 validation state = LangGraph's in-memory checkpointer. Both are the lazy-correct single-worker choice. Swap to Redis/Postgres checkpointer only when you run multiple workers.

---

## 🐳 Run

```bash
# Docker
docker-compose up --build      # → http://localhost:8000/docs

# Local
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## ⚙️ Environment

```
APP_ENV=development
LOG_LEVEL=info
MODEL_DIR=./models
DATASET_DIR=./datasets
LLM_API_KEY=            # NLP layer (Phase 2) + validation agent (Phase 3)
```

---

## ⚠️ Real risks

- **Statistical gate must be right.** The whole "no dropping on vibes" guarantee rests on `profiler.py` + `stats_gate`. If the stats are wrong, the LLM's mistakes pass through. This is why the profiler is built and tested first, before any LLM node.
- **NL → target column** reliability — hard part. OpenML's labeled targets sidestep it on the fetch path.
- **Dataset search relevance** — "house prices" must surface housing data. Semantic search (embeddings) is its own subsystem; Phase 4.
- **Training latency** — fetched datasets can be large. Background jobs from day one (Phase 1).
```
