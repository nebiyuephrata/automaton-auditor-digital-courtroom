from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Any, Dict

from src.service.audit_runner import run_audit
from src.service.audit_store import AuditStore


class AuditJobManager:
    def __init__(self, store: AuditStore, max_workers: int = 2) -> None:
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="audit-job")
        self._futures: Dict[str, object] = {}
        self._lock = threading.Lock()

    def submit(self, run_id: str, repo_url: str, pdf_path: str, rubric_path: str, output_path: str | None) -> None:
        self.store.update_status(run_id, "queued")

        def _task() -> None:
            self.store.update_status(run_id, "running")
            try:
                result = run_audit(
                    repo_url=repo_url,
                    pdf_path=pdf_path,
                    rubric_path=rubric_path,
                    output_path=output_path,
                )
                self.store.complete_run(
                    run_id=run_id,
                    final_report=result.get("final_report"),
                    rendered_markdown=result.get("rendered_markdown", ""),
                    errors=result.get("errors", []),
                )
            except Exception as exc:  # pragma: no cover - thread failure path
                self.store.complete_run(
                    run_id=run_id,
                    final_report=None,
                    rendered_markdown="",
                    errors=[str(exc)],
                )

        future = self.executor.submit(_task)
        with self._lock:
            self._futures[run_id] = future

    def is_active(self, run_id: str) -> bool:
        with self._lock:
            future = self._futures.get(run_id)
        if future is None:
            return False
        return not future.done()
