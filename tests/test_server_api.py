import tempfile

from fastapi.testclient import TestClient

import src.server as server
from src.service.async_jobs import AuditJobManager
from src.service.audit_store import AuditStore
from src.service.security import SecurityConfig, SlidingWindowRateLimiter


class ImmediateJobManager:
    def __init__(self, store: AuditStore) -> None:
        self.store = store

    def submit(self, run_id: str, repo_url: str, pdf_path: str, rubric_path: str, output_path: str | None) -> None:
        self.store.complete_run(
            run_id=run_id,
            final_report={"overall_score": 4.0},
            rendered_markdown="# done",
            errors=[],
        )

    def cancel(self, run_id: str) -> bool:
        record = self.store.get_run(run_id)
        if record["status"] in {"queued", "running", "cancel_requested"}:
            self.store.complete_run(
                run_id=run_id,
                final_report=None,
                rendered_markdown="",
                errors=[],
                status_override="canceled",
            )
            return True
        return False

    def shutdown(self, wait: bool = False) -> None:
        return None


def _configure_test_runtime(monkeypatch):
    temp_dir = tempfile.TemporaryDirectory()
    store = AuditStore(root_dir=temp_dir.name)

    monkeypatch.setattr(server, "store", store)
    monkeypatch.setattr(server, "job_manager", ImmediateJobManager(store))
    monkeypatch.setattr(server, "security_config", SecurityConfig(api_auth_key="test-key", rate_limit_per_minute=60))
    monkeypatch.setattr(server, "rate_limiter", SlidingWindowRateLimiter(limit_per_minute=60))

    client = TestClient(server.app)
    return client, store, temp_dir


def test_health_endpoint() -> None:
    client = TestClient(server.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_required_for_audit_routes(monkeypatch) -> None:
    client, _store, temp_dir = _configure_test_runtime(monkeypatch)
    try:
        response = client.get("/api/audits")
        assert response.status_code == 401

        response_ok = client.get("/api/audits", headers={"x-api-key": "test-key"})
        assert response_ok.status_code == 200
    finally:
        temp_dir.cleanup()


def test_auth_returns_503_when_not_configured(monkeypatch) -> None:
    temp_dir = tempfile.TemporaryDirectory()
    store = AuditStore(root_dir=temp_dir.name)
    monkeypatch.setattr(server, "store", store)
    monkeypatch.setattr(server, "job_manager", ImmediateJobManager(store))
    monkeypatch.setattr(server, "security_config", SecurityConfig(api_auth_key="", rate_limit_per_minute=60))
    monkeypatch.setattr(server, "rate_limiter", SlidingWindowRateLimiter(limit_per_minute=60))

    client = TestClient(server.app)
    try:
        response = client.get("/api/audits", headers={"x-api-key": "anything"})
        assert response.status_code == 503
    finally:
        temp_dir.cleanup()


def test_rate_limiter_blocks_excess_requests(monkeypatch) -> None:
    client, _store, temp_dir = _configure_test_runtime(monkeypatch)
    monkeypatch.setattr(server, "rate_limiter", SlidingWindowRateLimiter(limit_per_minute=1))

    try:
        first = client.get("/api/audits", headers={"x-api-key": "test-key"})
        second = client.get("/api/audits", headers={"x-api-key": "test-key"})

        assert first.status_code == 200
        assert second.status_code == 429
    finally:
        temp_dir.cleanup()


def test_run_async_creates_completed_record_with_immediate_manager(monkeypatch) -> None:
    client, _store, temp_dir = _configure_test_runtime(monkeypatch)
    try:
        response = client.post(
            "/api/audits/run-async",
            headers={"x-api-key": "test-key"},
            json={
                "repo_url": "https://example.com/repo.git",
                "pdf_path": "reports/final_report.pdf",
                "rubric_path": "rubric.json",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"

        result = client.get(
            f"/api/audits/{payload['run_id']}/result",
            headers={"x-api-key": "test-key"},
        )
        assert result.status_code == 200
        assert result.json()["rendered_markdown"] == "# done"
    finally:
        temp_dir.cleanup()


def test_result_endpoint_returns_409_for_non_terminal_runs(monkeypatch) -> None:
    client, store, temp_dir = _configure_test_runtime(monkeypatch)
    try:
        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
            status="queued",
        )

        response = client.get(f"/api/audits/{run_id}/result", headers={"x-api-key": "test-key"})
        assert response.status_code == 409
    finally:
        temp_dir.cleanup()


def test_cancel_endpoint_returns_404_for_unknown_run(monkeypatch) -> None:
    client, _store, temp_dir = _configure_test_runtime(monkeypatch)
    try:
        response = client.post("/api/audits/missing/cancel", headers={"x-api-key": "test-key"})
        assert response.status_code == 404
    finally:
        temp_dir.cleanup()


def test_cancel_endpoint_can_cancel_queued_run(monkeypatch) -> None:
    client, store, temp_dir = _configure_test_runtime(monkeypatch)
    try:
        run_id = store.create_run(
            repo_url="https://example.com/repo.git",
            pdf_path="reports/final_report.pdf",
            rubric_path="rubric.json",
            output_path=None,
            status="queued",
        )
        response = client.post(f"/api/audits/{run_id}/cancel", headers={"x-api-key": "test-key"})
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"
    finally:
        temp_dir.cleanup()
