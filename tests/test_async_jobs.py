import tempfile
import time

from src.service.async_jobs import AuditJobManager
from src.service.audit_store import AuditStore


def test_audit_store_update_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
            status="queued",
        )
        store.update_status(run_id, "running")
        assert store.get_run(run_id)["status"] == "running"


def test_job_manager_completes_run(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        manager = AuditJobManager(store=store, max_workers=1)

        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
            status="queued",
        )

        def fake_run_audit(**kwargs):
            return {
                "rendered_markdown": "# done",
                "final_report": {"overall_score": 4.2},
                "errors": [],
            }

        monkeypatch.setattr("src.service.async_jobs.run_audit", fake_run_audit)
        manager.submit(
            run_id=run_id,
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
        )

        for _ in range(100):
            record = store.get_run(run_id)
            if record["status"] == "completed":
                break
            time.sleep(0.01)

        assert store.get_run(run_id)["status"] == "completed"
        result = store.get_result(run_id)
        assert result["rendered_markdown"] == "# done"


def test_job_manager_cancel_marks_run_canceled(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        manager = AuditJobManager(store=store, max_workers=1)

        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
            status="queued",
        )

        def slow_run_audit(**kwargs):
            time.sleep(0.1)
            return {
                "rendered_markdown": "# done",
                "final_report": {"overall_score": 4.2},
                "errors": [],
            }

        monkeypatch.setattr("src.service.async_jobs.run_audit", slow_run_audit)
        manager.submit(
            run_id=run_id,
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
        )
        assert manager.cancel(run_id) is True

        for _ in range(200):
            status = store.get_run(run_id)["status"]
            if status == "canceled":
                break
            time.sleep(0.01)

        assert store.get_run(run_id)["status"] == "canceled"


def test_job_manager_cancel_unknown_run_returns_false() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        manager = AuditJobManager(store=store, max_workers=1)
        assert manager.cancel("missing") is False
