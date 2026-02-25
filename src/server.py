from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config.settings import load_settings
from src.service.async_jobs import AuditJobManager
from src.service.audit_runner import run_audit
from src.service.audit_store import AuditStore
from src.service.security import SecurityConfig, SlidingWindowRateLimiter, is_api_key_valid


class AuditRunRequest(BaseModel):
    repo_url: str = Field(min_length=1)
    pdf_path: str = Field(min_length=1)
    rubric_path: str = Field(default="rubric.json", min_length=1)
    output_path: str | None = Field(default=None)


class AuditRunResponse(BaseModel):
    run_id: str
    rendered_markdown: str
    final_report: dict | None = None
    errors: list[str] = Field(default_factory=list)


class AuditRunRecordResponse(BaseModel):
    run_id: str
    created_at: str
    repo_url: str
    pdf_path: str
    rubric_path: str
    output_path: str | None = None
    status: str
    overall_score: float | None = None
    errors: list[str] = Field(default_factory=list)


app = FastAPI(title="Automaton Auditor API", version="0.1.0")
store = AuditStore()
job_manager = AuditJobManager(store)
settings = load_settings()
security_config = SecurityConfig(
    api_auth_key=settings.api_auth_key,
    rate_limit_per_minute=settings.api_rate_limit_per_minute,
)
rate_limiter = SlidingWindowRateLimiter(security_config.rate_limit_per_minute)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def enforce_api_auth(x_api_key: str | None = Header(default=None)) -> None:
    if not is_api_key_valid(x_api_key, security_config.api_auth_key):
        raise HTTPException(status_code=401, detail="Unauthorized")


def enforce_rate_limit(
    request: Request,
    response: Response,
    x_api_key: str | None = Header(default=None),
) -> None:
    caller = x_api_key or (request.client.host if request.client else "unknown")
    allowed, retry_after = rate_limiter.allow(caller)
    if not allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.post("/api/audits/run", response_model=AuditRunResponse)
def run_audit_endpoint(
    request: AuditRunRequest,
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> AuditRunResponse:
    run_id = store.create_run(
        repo_url=request.repo_url,
        pdf_path=request.pdf_path,
        rubric_path=request.rubric_path,
        output_path=request.output_path,
    )
    try:
        result = run_audit(
            repo_url=request.repo_url,
            pdf_path=request.pdf_path,
            rubric_path=request.rubric_path,
            output_path=request.output_path,
        )
    except Exception as exc:
        store.complete_run(run_id, final_report=None, rendered_markdown="", errors=[str(exc)])
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {exc}") from exc

    store.complete_run(
        run_id=run_id,
        final_report=result.get("final_report"),
        rendered_markdown=result.get("rendered_markdown", ""),
        errors=result.get("errors", []),
    )

    return AuditRunResponse(
        run_id=run_id,
        rendered_markdown=result.get("rendered_markdown", ""),
        final_report=result.get("final_report"),
        errors=result.get("errors", []),
    )


@app.post("/api/audits/run-async", response_model=AuditRunRecordResponse)
def run_audit_async_endpoint(
    request: AuditRunRequest,
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> AuditRunRecordResponse:
    run_id = store.create_run(
        repo_url=request.repo_url,
        pdf_path=request.pdf_path,
        rubric_path=request.rubric_path,
        output_path=request.output_path,
        status="queued",
    )
    job_manager.submit(
        run_id=run_id,
        repo_url=request.repo_url,
        pdf_path=request.pdf_path,
        rubric_path=request.rubric_path,
        output_path=request.output_path,
    )
    return AuditRunRecordResponse(**store.get_run(run_id))


@app.get("/api/audits", response_model=list[AuditRunRecordResponse])
def list_audits_endpoint(
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> list[AuditRunRecordResponse]:
    records = store.list_runs()
    return [AuditRunRecordResponse(**record) for record in records]


@app.get("/api/audits/{run_id}", response_model=AuditRunRecordResponse)
def get_audit_endpoint(
    run_id: str,
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> AuditRunRecordResponse:
    try:
        record = store.get_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found") from exc
    return AuditRunRecordResponse(**record)


@app.get("/api/audits/{run_id}/result")
def get_audit_result_endpoint(
    run_id: str,
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> dict:
    try:
        return store.get_result(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Result for run {run_id} not found") from exc


@app.post("/api/audits/{run_id}/cancel", response_model=AuditRunRecordResponse)
def cancel_audit_endpoint(
    run_id: str,
    _auth: None = Depends(enforce_api_auth),
    _rate: None = Depends(enforce_rate_limit),
) -> AuditRunRecordResponse:
    try:
        store.get_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found") from exc

    if not job_manager.cancel(run_id):
        raise HTTPException(status_code=409, detail="Run is not cancelable")
    return AuditRunRecordResponse(**store.get_run(run_id))
