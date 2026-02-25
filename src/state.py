import operator
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    goal: str = Field(description="Forensic goal being tested")
    found: bool = Field(description="Whether the artifact or pattern was found")
    content: Optional[str] = Field(default=None, description="Raw captured details")
    location: str = Field(description="File path, image path, or commit hash")
    rationale: str = Field(description="Why this evidence supports the finding")
    confidence: float = Field(ge=0.0, le=1.0)


class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5)
    argument: str
    cited_evidence: List[str] = Field(default_factory=list)


class CriterionResult(BaseModel):
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = Field(default=None)
    remediation: str


class AuditReport(BaseModel):
    repo_url: str
    executive_summary: str
    overall_score: float
    governance_maturity: Literal[
        "Emergent",
        "Developing",
        "Governed",
        "Constitutional",
    ]
    governance_maturity_rationale: str
    criteria: List[CriterionResult]
    remediation_plan: str


class RuntimeLLMConfig(BaseModel):
    judge_provider: str = "openai"
    judge_model: str = "gpt-4o-mini"
    vision_provider: str = "openai"
    vision_model: str = "gpt-4o-mini"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None


class AgentState(TypedDict, total=False):
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict]
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    runtime_config: RuntimeLLMConfig
    final_report: AuditReport
    errors: Annotated[List[str], operator.add]
