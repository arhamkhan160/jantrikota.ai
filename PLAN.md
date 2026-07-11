# 🗺️ Build Plan — jantrikota.ai (AutoML Agent)

Actionable checklist. Blueprint lives in [Readme.md](Readme.md). Rule: **each milestone RUNS end-to-end before the next starts.** Vertical slices, not horizontal layers. Tick the box only when its acceptance check passes.

Dependency order is strict, top to bottom. Don't build ahead. Don't install a dep before the milestone that needs it.

---

## Guiding cuts (ultra-lazy scope)

- **Upload-only until the whole loop works.** Dataset fetch (OpenML/HF) is the *last* milestone, not a foundation.
- **Manual Task Spec before NLP.** The pipeline runs on a hand-written JSON spec first. `/query` LLM parsing is a thin add-on bolted on after.
- **No `langgraph`/`langchain` until M4.** M1–M3 are plain FastAPI + FLAML + pandas.
- **In-memory storage until multi-worker is real.** Job dict + LangGraph in-memory checkpointer. No Redis/Postgres until you actually run >1 worker.
- Every non-trivial module ships with **one** runnable check (`assert`-based `demo()` or one `test_*.py`). No suites unless asked.

---

## M0 — Skeleton ✅ (verify, don't rebuild)

Already scaffolded. Confirm these run, then move on:
- [ ] `uvicorn app.main:app --reload` boots, `GET /health` → `{"status":"ok"}`
- [ ] `core/config.py` (settings), `core/logger.py`, `api/v1/router.py` exist and import clean
- [ ] `docker-compose up --build` serves `/docs`

**Acceptance:** `/docs` loads locally and in Docker.
**Deps:** `fastapi`, `uvicorn`, `pydantic-settings`.

---

## M1 — Spine + upload + train (the proof) ⭐

The whole point in one vertical slice. Manual spec, no NLP, no validation agent.

- [ ] `schemas/task_spec.py` — `TaskSpec` (task, target, metric, dataset_id) + request/response models. **Build first — it's the contract.**
- [ ] `services/dataset_store.py` — save uploaded CSV to `datasets/`, return `dataset_id`; load back as DataFrame.
- [ ] `api/v1/endpoints/dataset.py` — `POST /upload-dataset` → `dataset_id`.
- [ ] `ml/trainer.py` — thin wrapper: `(df, spec) → FLAML.fit → best model + metrics`. **Wrapper only, no hand-rolled training.**
- [ ] `services/jobs.py` — in-memory `{job_id: status/result}` + FastAPI `BackgroundTasks`. `# ponytail: in-memory dict, swap to Redis when multi-worker`.
- [ ] `api/v1/endpoints/pipeline.py` — `POST /start-pipeline` (spec → job), `GET /status/{id}`, `GET /results/{id}`, `GET /download-model/{id}`.
- [ ] one `test_trainer.py` — tiny CSV → asserts a model + metric come back.

**Acceptance:** upload a CSV, POST a manual spec, poll status, download a `.pkl`. Working product.
**Deps add:** `flaml[automl]`, `pandas`, `scikit-learn`, `joblib`, `python-multipart`.

---

## M2 — NLP layer (query → Task Spec)

Convenience over M1's manual spec. Thin.

- [ ] `integrations/llm.py` — one structured-output call. Raw provider SDK. `# ponytail: raw SDK, not LangChain — one call doesn't need a framework`.
- [ ] `services/spec_builder.py` — `query + column list → TaskSpec`; resolve `target` against real columns; return `ambiguous` flag if no confident match.
- [ ] `api/v1/endpoints/query.py` — `POST /query` → TaskSpec (or ambiguity for the client to resolve).
- [ ] one `test_spec_builder.py` — mock LLM, assert target resolves to a real column, assert ambiguous case flagged.

**Acceptance:** `POST /query {"query":"predict price"}` on an uploaded dataset returns a valid TaskSpec feeding straight into M1's `/start-pipeline`.
**Deps add:** provider SDK (`anthropic` or `openai`).

---

## M3 — Statistical profiler (the safety rail)

Built and tested **before any LLM touches the data**. Everything in M4 trusts this.

- [ ] `validation/profiler.py` — pure stats per column: dtype, missing %, cardinality, corr-to-target, mutual info, target-leakage flag, constant/duplicate detection. **No LLM.**
- [ ] `test_profiler.py` — synthetic frame with a known leaky column + a known useless column; assert the profiler flags exactly those. **This is the guarantee behind "no dropping on vibes" — test it hard.**

**Acceptance:** profiler correctly flags a planted leakage column and a constant column on synthetic data.
**Deps add:** none (pandas/sklearn already in).

---

## M4 — Validation Agent (LangGraph) ⭐ the core feature

The LLM + user + stats loop. Now the graph deps earn their place.

- [ ] `validation/state.py` — `ValidationState` (df, spec, profile, proposals, applied, pending_question, done).
- [ ] `validation/nodes.py`:
  - [ ] `profile` (calls M3 profiler)
  - [ ] `llm_review` (profile → `[{col, action, reason, evidence}]`)
  - [ ] `stats_gate` (reject any proposal the numbers don't support — pure code)
  - [ ] `decide` (confident+safe → auto-apply; risky/ambiguous → user)
  - [ ] `ask_user` (`interrupt()`)
  - [ ] `apply` (mutate df, append to `applied` audit trail)
- [ ] `validation/graph.py` — wire nodes, conditional edges, loop-back, checkpointer (in-memory).
- [ ] `api/v1/endpoints/validate.py` — `POST /validate/start`, `GET /validate/{id}`, `POST /validate/{id}/answer` (resume interrupted graph).
- [ ] `test_stats_gate.py` — assert a "drop high-importance column" proposal is **rejected** by the gate. The whole safety claim in one test.

**Acceptance:** run validation on a dataset with a leaky column → agent proposes drop *with evidence* → asks user → on "drop" re-profiles clean → hands validated df to `/start-pipeline`.
**Deps add:** `langgraph` (+ `langchain-core` / provider adapter only if the graph's LLM node needs it).

---

## M5 — Dataset fetch (last, optional)

Only after the full upload→validate→train loop is solid.

- [ ] `integrations/openml.py` — search + load by id (**target pre-labeled** → free target resolution).
- [ ] `api/v1/endpoints/dataset.py` — `GET /datasets/search?q=` → descriptions to pick from; picked id flows into validate + train.
- [ ] HuggingFace `datasets` source — **only after OpenML works.**

**Acceptance:** search "iris" → pick → validate → train, no upload.
**Deps add:** `openml`; later `datasets`.

---

## M6 — Serving + polish

- [ ] `api/v1/endpoints/predict.py` — `POST /predict` loads saved model, runs inference.
- [ ] input validation at the upload + predict boundaries (trust boundary — **not** lazy here).
- [ ] error handling when training explodes (job → `failed` with reason, never a hung status).

**Acceptance:** train → `/predict` with a feature row → prediction back. Bad input → clean 4xx, not a 500.

---

## Deferred — only when measured need says so

featuretools (auto feature synthesis) · Redis+Celery (multi-worker jobs) · Postgres checkpointer (durable validation runs) · MLflow (experiment tracking) · UI dashboard.

Each is an addition on top of a working system. None blocks anything above. Add when the simple version measurably hurts — not before.

---

## Dependency growth (keep the image lean)

```
M0:  fastapi uvicorn pydantic-settings
M1:  + flaml[automl] pandas scikit-learn joblib python-multipart
M2:  + anthropic|openai
M3:  + (none)
M4:  + langgraph (+ langchain-core if graph LLM node needs it)
M5:  + openml   (+ datasets later)
```

Pin nothing you don't use yet. `langgraph` never appears before M4.
