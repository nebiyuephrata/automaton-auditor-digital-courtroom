from collections import defaultdict
from statistics import mean
from typing import Dict, List

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
        "security" in op.argument.lower() or "os.system" in op.argument.lower() for op in opinions
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
        report = AuditReport(
            repo_url=state.get("repo_url", ""),
            executive_summary=(
                "Deterministic constitutional synthesis completed across forensic, judicial, "
                "and architectural criteria."
            ),
            overall_score=overall,
            criteria=results,
            remediation_plan="\n".join(f"- {res.remediation}" for res in results),
        )
        markdown = render_audit_report(report)

        return {
            "final_report": report,
            "rendered_markdown": markdown,
        }
