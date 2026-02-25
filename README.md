# Automaton Auditor - Digital Courtroom

Production-grade autonomous governance swarm for forensic repository auditing.

## Architecture Invariants

`START -> Detectives (parallel) -> EvidenceAggregator -> Judges (parallel) -> ChiefJustice (deterministic) -> END`

## Setup

```bash
uv sync
cp .env.example .env
```

## Run

```bash
uv run python src/cli.py --repo-url <repo_url> --pdf-path reports/interim_report.pdf
```

## Test

```bash
uv run pytest
```
