from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict

from src.service.audit_runner import run_audit
from src.service.audit_store import AuditStore
from src.state import RuntimeLLMConfig


class AuditJobManager:
    def __init__(self, store: AuditStore, max_workers: int = 2) -> None:
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="audit-job")
        self._futures: Dict[str, object] = {}
        self._cancel_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        run_id: str,
        repo_url: str,
        pdf_path: str,
        rubric_path: str,
        output_path: str | None,
        rubric_preset: str | None = None,
        runtime_config: RuntimeLLMConfig | None = None,
    ) -> None:
        self.store.update_status(run_id, "queued")
        cancel_event = threading.Event()

        def _task() -> None:
            if cancel_event.is_set():
                self.store.complete_run(
                    run_id=run_id,
                    final_report=None,
                    rendered_markdown="",
                    errors=[],
                    status_override="canceled",
                )
                return

            self.store.update_status(run_id, "running")
            try:
                result = run_audit(
                    repo_url=repo_url,
                    pdf_path=pdf_path,
                    rubric_path=rubric_path,
                    rubric_preset=rubric_preset,
                    runtime_config=runtime_config,
                    output_path=output_path,
                )
                self.store.complete_run(
                    run_id=run_id,
                    final_report=result.get("final_report"),
                    rendered_markdown=result.get("rendered_markdown", ""),
                    errors=[] if cancel_event.is_set() else result.get("errors", []),
                    status_override="canceled" if cancel_event.is_set() else None,
                )
            except Exception as exc:  # pragma: no cover - thread failure path
                self.store.complete_run(
                    run_id=run_id,
                    final_report=None,
                    rendered_markdown="",
                    errors=[str(exc)],
                )
            finally:
                with self._lock:
                    self._futures.pop(run_id, None)
                    self._cancel_events.pop(run_id, None)

        future = self.executor.submit(_task)
        with self._lock:
            self._futures[run_id] = future
            self._cancel_events[run_id] = cancel_event

    def cancel(self, run_id: str) -> bool:
        with self._lock:
            future = self._futures.get(run_id)
            cancel_event = self._cancel_events.get(run_id)

        if cancel_event is None:
            return False

        cancel_event.set()
        if future is not None and future.cancel():
            self.store.complete_run(
                run_id=run_id,
                final_report=None,
                rendered_markdown="",
                errors=[],
                status_override="canceled",
            )
            return True

        record = self.store.get_run(run_id)
        if record.get("status") in {"queued", "running"}:
            self.store.update_status(run_id, "cancel_requested")
            return True
        return False

    def shutdown(self, wait: bool = False) -> None:
        self.executor.shutdown(wait=wait, cancel_futures=True)

    def is_active(self, run_id: str) -> bool:
        with self._lock:
            future = self._futures.get(run_id)
        if future is None:
            return False
        return not future.done()
