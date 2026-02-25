from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


@dataclass(frozen=True)
class AuditRunRecord:
    run_id: str
    created_at: str
    repo_url: str
    pdf_path: str
    rubric_path: str
    output_path: str | None
    status: str
    overall_score: float | None
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "repo_url": self.repo_url,
            "pdf_path": self.pdf_path,
            "rubric_path": self.rubric_path,
            "output_path": self.output_path,
            "status": self.status,
            "overall_score": self.overall_score,
            "errors": self.errors,
        }


class AuditStore:
    def __init__(self, root_dir: str = "audit/.runs") -> None:
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def create_run(
        self,
        repo_url: str,
        pdf_path: str,
        rubric_path: str,
        output_path: str | None,
    ) -> str:
        run_id = uuid4().hex
        record = AuditRunRecord(
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            repo_url=repo_url,
            pdf_path=pdf_path,
            rubric_path=rubric_path,
            output_path=output_path,
            status="running",
            overall_score=None,
            errors=[],
        )
        self._write_json(self._record_path(run_id), record.to_dict())
        return run_id

    def complete_run(
        self,
        run_id: str,
        final_report: Dict[str, Any] | None,
        rendered_markdown: str,
        errors: List[str],
    ) -> None:
        record = self.get_run(run_id)
        status = "failed" if errors else "completed"
        overall_score = None
        if final_report is not None:
            overall_score = final_report.get("overall_score")

        updated = {**record, "status": status, "overall_score": overall_score, "errors": errors}
        self._write_json(self._record_path(run_id), updated)

        payload = {
            "run_id": run_id,
            "rendered_markdown": rendered_markdown,
            "final_report": final_report,
            "errors": errors,
        }
        self._write_json(self._result_path(run_id), payload)

    def list_runs(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for path in sorted(self.root.glob("*.record.json"), reverse=True):
            records.append(self._read_json(path))
        return records

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._read_json(self._record_path(run_id))

    def get_result(self, run_id: str) -> Dict[str, Any]:
        return self._read_json(self._result_path(run_id))

    def _record_path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.record.json"

    def _result_path(self, run_id: str) -> Path:
        return self.root / f"{run_id}.result.json"

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(path)
        return json.loads(path.read_text(encoding="utf-8"))
