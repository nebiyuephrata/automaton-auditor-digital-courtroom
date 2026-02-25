import tempfile

from src.service.audit_store import AuditStore


def test_audit_store_run_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path="audit/out.md",
        )

        created = store.get_run(run_id)
        assert created["status"] == "running"

        store.complete_run(
            run_id=run_id,
            final_report={"overall_score": 4.0},
            rendered_markdown="# report",
            errors=[],
        )

        updated = store.get_run(run_id)
        assert updated["status"] == "completed"
        assert updated["overall_score"] == 4.0

        result = store.get_result(run_id)
        assert result["rendered_markdown"] == "# report"
        assert result["errors"] == []


def test_audit_store_marks_failed_when_errors_present() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(root_dir=tmp)
        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
        )

        store.complete_run(
            run_id=run_id,
            final_report=None,
            rendered_markdown="",
            errors=["failure"],
        )

        record = store.get_run(run_id)
        assert record["status"] == "failed"
        assert record["errors"] == ["failure"]
