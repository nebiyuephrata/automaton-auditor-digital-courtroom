# Automaton Auditor Architecture

## 1. System Goal
Automaton Auditor is a constitutional governance swarm that audits AI-code repositories and supporting documentation using a strict digital-courtroom model.

Core invariant:

`START -> Detectives (parallel) -> EvidenceAggregator (fan-in) -> Judges (parallel) -> ChiefJustice (deterministic) -> END`

## 2. What Is Implemented

### 2.1 Typed State + Contracts
Implemented in `src/state.py`:
- `Evidence` (Pydantic)
- `JudicialOpinion` (Pydantic)
- `CriterionResult` (Pydantic)
- `AuditReport` (Pydantic)
- `AgentState` (TypedDict)

Reducers:
- `evidences`: `operator.ior`
- `opinions`: `operator.add`
- `errors`: `operator.add`

### 2.2 Detective Layer (Forensics)
Implemented in:
- `src/tools/repo_tools.py`
- `src/tools/ast_analysis.py`
- `src/tools/doc_tools.py`
- `src/tools/pdf_image_tools.py`
- `src/nodes/detectives.py`

Capabilities:
- Sandboxed git clone with `tempfile` + `subprocess.run`
- Git history extraction
- AST-based graph/state structure checks
- PDF ingestion and concept/path analysis
- PDF image extraction + diagram flow analysis
  - multimodal structured classification when provider available
  - deterministic heuristic fallback when unavailable

### 2.3 Judicial Layer
Implemented in `src/nodes/judges.py`:
- Parallel judge personas: Prosecutor, Defense, TechLead
- `.with_structured_output(JudicialOpinion)` enforcement
- Retry behavior on invalid/mismatched outputs
- Provider-backed execution (OpenAI/Anthropic) with deterministic fallback

### 2.4 Deterministic Chief Justice
Implemented in `src/nodes/justice.py`:
- Security override
- Fact supremacy against hallucinated defense claims
- Functionality weighting for architecture via TechLead
- Structural fraud override
- Variance-triggered dissent/re-evaluation
- Deterministic governance maturity banding:
  - `Emergent`
  - `Developing`
  - `Governed`
  - `Constitutional`

### 2.5 Graph Orchestration
Implemented in `src/graph.py`:
- Detectives fan-out from `START`
- Fan-in at `EvidenceAggregator`
- Judges fan-out via `judge_dispatch`
- Fan-in at `ChiefJustice`
- Conditional error routing

### 2.6 Runtime and Delivery Surfaces
- CLI: `src/cli.py`
- API: `src/server.py`
- Shared runner service: `src/service/audit_runner.py`
- Async job manager: `src/service/async_jobs.py`
- Persistent run ledger: `src/service/audit_store.py`
- Security controls: `src/service/security.py`
- Frontend operator console: `frontend/`

API endpoints:
- `POST /api/audits/run`
- `POST /api/audits/run-async`
- `POST /api/audits/{run_id}/cancel`
- `GET /api/audits`
- `GET /api/audits/{run_id}`
- `GET /api/audits/{run_id}/result`

### 2.7 Security + Parallel Safety
Implemented controls:
- API key auth (`x-api-key`)
- Sliding-window rate limiting
- Non-terminal result fetch protection (`409`)
- Async cancellation with explicit statuses (`queued`, `running`, `cancel_requested`, `completed`, `failed`, `canceled`)
- Thread-safe run store and limiter
- Reducer-based parallel merge safety

### 2.8 CI/CD
Implemented workflow: `.github/workflows/ci.yml`
- Backend compile check and tests
- Frontend build check
- Triggered on PR and `main` push

## 3. Evidence of Governance Maturity
The platform currently demonstrates:
- Constitutional enforcement via rubric-driven judicial/synthesis flow
- Deterministic arbitration in Chief Justice
- Governance maturity scoring (band + rationale)
- Architecture self-verification (AST and graph pattern checks)
- Hallucination resistance (claim cross-reference + fact supremacy)
- Parallel safety enforcement (reducers + fan-in/fan-out structure)

## 4. Current Gaps (Honest Status)
1. Full online dependency/test execution is environment-dependent.
- In offline/sandboxed environments, `uv sync` and full pytest cannot run without package access.

2. Multimodal vision quality depends on configured provider keys/models.
- Fallback is deterministic but less semantically rich than live multimodal parsing.

3. No persistent relational datastore.
- Run history currently stored as JSON files under `audit/.runs/`.

## 5. Next Implementations (Priority)
1. `feat(api): add WebSocket/SSE live run events`
- Replace polling loop with server-pushed progress updates.

2. `feat(governance): criterion-level evidence confidence calibration`
- Penalize low-confidence evidence during synthesis.

3. `feat(ops): move run ledger to SQLite`
- Better indexing, history queries, and consistency under concurrency.

4. `feat(security): scoped API tokens and audit trail`
- Per-client keys, rotation, and endpoint-level authorization logs.

5. `feat(quality): add integration tests for server endpoints`
- FastAPI route tests for auth, rate limits, async lifecycle, cancellation, and result semantics.

## 6. Deliverables Mapping (Week 2 Challenge)
Implemented and aligned:
- Typed state + reducers
- Sandboxed forensic tooling
- Parallel detective and judge orchestration
- Deterministic synthesis engine
- Rubric-driven governance logic
- Markdown audit report rendering
- API + frontend operator workflow
- CI workflow

Operational outputs expected at runtime:
- `audit/report_onself_generated/`
- `audit/report_onpeer_generated/`
- `audit/report_bypeer_received/`
- `reports/final_report.pdf`
