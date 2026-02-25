from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.service.audit_runner import run_audit


class AuditRunRequest(BaseModel):
    repo_url: str = Field(min_length=1)
    pdf_path: str = Field(min_length=1)
    rubric_path: str = Field(default="rubric.json", min_length=1)
    output_path: str | None = Field(default=None)


class AuditRunResponse(BaseModel):
    rendered_markdown: str
    final_report: dict | None = None
    errors: list[str] = Field(default_factory=list)


app = FastAPI(title="Automaton Auditor API", version="0.1.0")

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


@app.post("/api/audits/run", response_model=AuditRunResponse)
def run_audit_endpoint(request: AuditRunRequest) -> AuditRunResponse:
    try:
        result = run_audit(
            repo_url=request.repo_url,
            pdf_path=request.pdf_path,
            rubric_path=request.rubric_path,
            output_path=request.output_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {exc}") from exc

    return AuditRunResponse(
        rendered_markdown=result.get("rendered_markdown", ""),
        final_report=result.get("final_report"),
        errors=result.get("errors", []),
    )
