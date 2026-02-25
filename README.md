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
- `GET /api/audits`
- `GET /api/audits/{run_id}`
- `GET /api/audits/{run_id}/result`

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

## Test

```bash
uv run pytest
```
