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

## Run Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Test

```bash
uv run pytest
```
