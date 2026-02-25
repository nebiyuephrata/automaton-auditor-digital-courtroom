# Automaton Auditor - Digital Courtroom

Production-grade autonomous governance swarm for forensic repository auditing.

## Architecture Invariants

`START -> Detectives (parallel) -> EvidenceAggregator -> Judges (parallel) -> ChiefJustice (deterministic) -> END`

## Setup

```bash
uv sync
cp .env.example .env
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

Security:
- All `/api/audits/*` endpoints require `x-api-key` header matching `API_AUTH_KEY`.
- Sliding-window rate limit is enforced per caller via `API_RATE_LIMIT_PER_MINUTE`.
- If `API_AUTH_KEY` is not configured, audit endpoints return `503` by design.

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
