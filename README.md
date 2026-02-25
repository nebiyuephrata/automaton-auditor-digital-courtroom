# Automaton Auditor - Digital Courtroom

Production-grade autonomous governance swarm for forensic repository auditing.

Detailed architecture and implementation status:
- [docs/architecture.md](docs/architecture.md)

## Architecture Invariants

`START -> Detectives (parallel) -> EvidenceAggregator -> Judges (parallel) -> ChiefJustice (deterministic) -> END`

Constitutional architecture mapping (implemented):
- `START -> Detectives (parallel fan-out)` in [`src/graph.py`](src/graph.py) with:
  - `repo_investigator`
  - `doc_analyst`
  - `vision_inspector`
- `Fan-in synchronization` in [`src/nodes/aggregator.py`](src/nodes/aggregator.py) via `EvidenceAggregator`
- `Judges (parallel fan-out)` in [`src/graph.py`](src/graph.py) with:
  - `prosecutor`
  - `defense`
  - `techlead`
- `Deterministic arbitration` in [`src/nodes/justice.py`](src/nodes/justice.py) via pure Python `ChiefJusticeNode`
- `Typed merge-safe state` in [`src/state.py`](src/state.py):
  - Pydantic schemas (`Evidence`, `JudicialOpinion`, `CriterionResult`, `AuditReport`)
  - `AgentState` TypedDict
  - reducers: `operator.ior` (`evidences`), `operator.add` (`opinions`, `errors`)

Non-negotiable synthesis rule:
- Final synthesis is deterministic rule engine logic (not LLM summarization).
- Judge nodes may use structured LLM output, but arbitration remains pure Python.

## Setup

Requirements:
- Python `3.11+` (project tested on `3.12`)
- Node.js `18+` for frontend
- Linux/macOS shell environment (Windows users should run in WSL)

```bash
uv sync
cp .env.example .env
```

Dependency locking:
- `uv.lock` is committed and should be used for reproducible installs.
- Refresh lock after dependency changes:

```bash
uv lock
```

## Run CLI

```bash
uv run python src/cli.py --repo-url <repo_url> --pdf-path reports/interim_report.pdf
```

## Run API

```bash
uv run uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
```

API endpoints:
- `POST /api/audits/run`
- `POST /api/audits/run-async`
- `POST /api/audits/{run_id}/cancel`
- `GET /api/audits`
- `GET /api/audits/{run_id}`
- `GET /api/audits/{run_id}/result`
- `GET /api/runtime/options`

Security:
- All `/api/audits/*` endpoints require `x-api-key` header matching `API_AUTH_KEY`.
- Sliding-window rate limit is enforced per caller via `API_RATE_LIMIT_PER_MINUTE`.
- If `API_AUTH_KEY` is not configured, audit endpoints return `503` by design.

Governance scoring:
- Chief Justice computes deterministic `governance_maturity` bands:
  `Emergent`, `Developing`, `Governed`, `Constitutional`.
- Critical-dimension failures (`langgraph_architecture`, `judicial_nuance`, `synthesis_engine`)
  apply downgrade penalties.

Vision analysis:
- VisionInspector extracts images directly from the submitted PDF.
- It attempts multimodal structured classification of required courtroom flow.
- If no multimodal model is configured, it records heuristic analysis with explicit confidence.

PDF forensic query interface:
- `src/tools/doc_tools.py` provides a queryable chunk index:
  - `build_chunk_index`
  - `query_chunk_index`
  - `query_pdf_chunks`
- This supports targeted questions over extracted PDF chunks, not only batch analysis.

Runtime model switching:
- Request-level runtime config supports `openai`, `anthropic`, and `ollama`.
- Local model example: set provider to `ollama` and model to `llama3.1`.
- Optional per-run keys/URL are supported via `runtime_config`:
  - `openai_api_key`
  - `anthropic_api_key`
  - `ollama_base_url`

Default and optional rubrics:
- Use default preset rubric (`industry_iso_soc2`) when no local rubric path exists.
- Included preset library under `rubrics/defaults/`:
  - `industry_iso_soc2.json`
  - `python_fastapi_best_practices.json`
  - `typescript_react_best_practices.json`
- Frontend supports either preset selection or custom rubric path.

## Run Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The UI now supports:
- Launching an audit run
- Viewing persisted run history
- Loading prior run results
- Async run submission with status polling
- Active run cancellation and authenticated API calls

## CI

GitHub Actions workflow runs backend compile/tests and frontend production build on PRs and pushes to `main`.

## Test

```bash
uv run pytest
```
