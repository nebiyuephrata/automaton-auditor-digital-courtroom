from collections import defaultdict
from statistics import mean
from typing import Dict, List, Literal

from src.state import AgentState, AuditReport, CriterionResult, Evidence, JudicialOpinion
from src.utils.markdown_renderer import render_audit_report


def resolve_criterion(
    dimension: Dict,
    opinions: List[JudicialOpinion],
    evidence_index: Dict[str, Evidence],
) -> CriterionResult:
    scores = [op.score for op in opinions]
    if not scores:
        raise ValueError(f"No opinions provided for criterion {dimension['id']}")

    prosecutor = next((op for op in opinions if op.judge == "Prosecutor"), None)
    defense = next((op for op in opinions if op.judge == "Defense"), None)
    techlead = next((op for op in opinions if op.judge == "TechLead"), None)

    final_score = round(mean(scores))

    security_vulnerability = any(
        "security" in op.argument.lower()
        or "unsafe shell" in op.argument.lower()
        or "command injection" in op.argument.lower()
        for op in opinions
    )
    if security_vulnerability:
        final_score = min(final_score, 3)

    if defense and _hallucinated_claim(defense, evidence_index):
        final_score = min(final_score, 2)

    is_architecture_criterion = "architecture" in dimension["name"].lower()
    if is_architecture_criterion and techlead:
        final_score = max(1, min(5, round((final_score + 2 * techlead.score) / 3)))

    structural_fraud = any(
        "orchestration fraud" in op.argument.lower() or "linear" in op.argument.lower()
        for op in opinions
    )
    if structural_fraud and is_architecture_criterion:
        final_score = 1

    variance = max(scores) - min(scores)
    dissent_summary = None
    if variance > 2:
        if techlead:
            final_score = techlead.score
        dissent_summary = (
            "High variance triggered deterministic re-evaluation; "
            "TechLead practicality and verified evidence were prioritized."
        )

    remediation = _build_remediation(dimension["id"], prosecutor, defense, techlead)

    return CriterionResult(
        dimension_id=dimension["id"],
        dimension_name=dimension["name"],
        final_score=max(1, min(5, final_score)),
        judge_opinions=opinions,
        dissent_summary=dissent_summary,
        remediation=remediation,
    )


def _hallucinated_claim(defense: JudicialOpinion, evidence_index: Dict[str, Evidence]) -> bool:
    if not defense.cited_evidence:
        return True
    for citation in defense.cited_evidence:
        if citation in evidence_index:
            return False
    return True


def _build_remediation(
    criterion_id: str,
    prosecutor: JudicialOpinion | None,
    defense: JudicialOpinion | None,
    techlead: JudicialOpinion | None,
) -> str:
    remediations = {
        "langgraph_architecture": "Refactor src/graph.py to enforce dual fan-out/fan-in and add deterministic error routing.",
        "state_management": "Strengthen src/state.py with explicit reducers and immutable merge-safe state channels.",
        "forensic_accuracy": "Replace any heuristic checks in src/tools with AST-backed structural evidence capture.",
        "judicial_nuance": "Ensure src/nodes/judges.py returns schema-bound JudicialOpinion objects with retries.",
        "synthesis_engine": "Keep src/nodes/justice.py deterministic and prohibit LLM calls in final verdict logic.",
    }
    return remediations.get(
        criterion_id,
        "Apply file-level fixes aligned to cited evidence and rerun governance audit.",
    )


class ChiefJusticeNode:
    def __call__(self, state: AgentState) -> Dict[str, object]:
        dimensions = state.get("rubric_dimensions", [])
        opinions = state.get("opinions", [])
        evidences = state.get("evidences", {})

        evidence_index: Dict[str, Evidence] = {}
        for bucket_name, bucket in evidences.items():
            for evidence in bucket:
                evidence_index[f"{bucket_name}:{evidence.goal}"] = evidence

        grouped: Dict[str, List[JudicialOpinion]] = defaultdict(list)
        for opinion in opinions:
            grouped[opinion.criterion_id].append(opinion)

        results: List[CriterionResult] = []
        for dimension in dimensions:
            result = resolve_criterion(dimension, grouped.get(dimension["id"], []), evidence_index)
            results.append(result)

        overall = mean([result.final_score for result in results]) if results else 0.0
        maturity, maturity_rationale = derive_governance_maturity(overall, results)
        report = AuditReport(
            repo_url=state.get("repo_url", ""),
            executive_summary=(
                "Deterministic constitutional synthesis completed across forensic, judicial, "
                "and architectural criteria."
            ),
            overall_score=overall,
            governance_maturity=maturity,
            governance_maturity_rationale=maturity_rationale,
            criteria=results,
            remediation_plan="\n".join(f"- {res.remediation}" for res in results),
        )
        markdown = render_audit_report(report)

        return {
            "final_report": report,
            "rendered_markdown": markdown,
        }


def derive_governance_maturity(
    overall_score: float, criteria: List[CriterionResult]
) -> tuple[Literal["Emergent", "Developing", "Governed", "Constitutional"], str]:
    if overall_score < 2.0:
        band: Literal["Emergent", "Developing", "Governed", "Constitutional"] = "Emergent"
    elif overall_score < 3.0:
        band = "Developing"
    elif overall_score < 4.2:
        band = "Governed"
    else:
        band = "Constitutional"

    architecture = next((c for c in criteria if c.dimension_id == "langgraph_architecture"), None)
    judicial = next((c for c in criteria if c.dimension_id == "judicial_nuance"), None)
    synthesis = next((c for c in criteria if c.dimension_id == "synthesis_engine"), None)

    if architecture and architecture.final_score <= 2:
        band = _downgrade_maturity(band)
    if judicial and judicial.final_score <= 2:
        band = _downgrade_maturity(band)
    if synthesis and synthesis.final_score <= 2:
        band = _downgrade_maturity(band)

    dissent_count = sum(1 for c in criteria if c.dissent_summary)
    rationale = (
        f"Band derived from overall score {overall_score:.2f} with {dissent_count} dissent-triggered "
        "re-evaluations and constitutional guardrail penalties applied to critical dimensions."
    )
    return band, rationale


def _downgrade_maturity(
    band: Literal["Emergent", "Developing", "Governed", "Constitutional"]
) -> Literal["Emergent", "Developing", "Governed", "Constitutional"]:
    order = ["Emergent", "Developing", "Governed", "Constitutional"]
    idx = order.index(band)
    if idx == 0:
        return band
    return order[idx - 1]  # type: ignore[return-value]
