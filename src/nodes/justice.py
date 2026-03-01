from collections import defaultdict
from statistics import mean
from typing import Dict, List, Literal

from src.state import (
    AgentState,
    AuditReport,
    CriterionResult,
    Evidence,
    ImprovementAction,
    JudicialOpinion,
)
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

    defense_hallucinated = bool(defense and _hallucinated_claim(defense, evidence_index))
    if defense_hallucinated:
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
            f"score spread={min(scores)}-{max(scores)} (delta={variance}). "
            "TechLead practicality and verified evidence were prioritized."
        )

    remediation = _build_remediation(dimension["id"], prosecutor, defense, techlead)
    recommended_changes = _recommended_file_changes(dimension["id"])
    detailed_improvements = _build_detailed_improvements(
        dimension_name=dimension["name"],
        final_score=max(1, min(5, final_score)),
        opinions=opinions,
        recommended_changes=recommended_changes,
        variance=variance,
        defense_hallucinated=defense_hallucinated,
        security_vulnerability=security_vulnerability,
        evidence_index=evidence_index,
    )
    evidence_linked_files = _evidence_linked_target_files(opinions, evidence_index)
    if evidence_linked_files:
        remediation = (
            f"{remediation} Prioritize evidence-linked fixes in: {', '.join(evidence_linked_files)}."
        )

    return CriterionResult(
        dimension_id=dimension["id"],
        dimension_name=dimension["name"],
        final_score=max(1, min(5, final_score)),
        judge_opinions=opinions,
        dissent_summary=dissent_summary,
        remediation=remediation,
        recommended_changes=recommended_changes,
        detailed_improvements=detailed_improvements,
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
        "detective_layer_implementation": "Harden detective forensics with AST-backed checks, chunk-indexed PDF evidence, and confidence-calibrated Evidence payloads.",
        "graph_orchestration_architecture": "Refactor graph wiring to preserve dual fan-out/fan-in orchestration and deterministic conditional failure routing.",
        "judicial_persona_differentiation_structured_output": "Strengthen persona separation and schema-bound judicial outputs with explicit retry/failure handling.",
        "chief_justice_synthesis_engine": "Keep Chief Justice synthesis deterministic while surfacing dissent and high-variance rationale in final report outputs.",
        "generated_audit_report_artifacts": "Generate and persist complete self/peer markdown audit artifacts for each rubric criterion with file-level actions.",
    }
    return remediations.get(
        criterion_id,
        "Apply file-level fixes aligned to cited evidence and rerun governance audit.",
    )


def _recommended_file_changes(criterion_id: str) -> List[str]:
    recommendations = {
        "detective_layer_implementation": [
            "Change src/tools/ast_analysis.py: expand graph/state forensic checks with stronger typed findings.",
            "Change src/tools/doc_tools.py: improve chunk-index retrieval and targeted evidence extraction.",
            "Change src/tools/pdf_image_tools.py: keep multimodal path and deterministic heuristic fallback aligned.",
        ],
        "graph_orchestration_architecture": [
            "Change src/graph.py: enforce START detective fan-out and explicit judge fan-out/fan-in wiring.",
            "Change src/nodes/aggregator.py: keep strict fan-in validation before judicial dispatch.",
        ],
        "judicial_persona_differentiation_structured_output": [
            "Change src/nodes/judges.py: preserve strict judge identity and criterion_id validation for each opinion.",
            "Change src/prompts/prosecutor.txt, src/prompts/defense.txt, src/prompts/techlead.txt: sharpen role boundaries.",
        ],
        "chief_justice_synthesis_engine": [
            "Change src/nodes/justice.py: keep final arbitration deterministic and non-LLM.",
            "Change src/utils/markdown_renderer.py: expose criterion-level dissent and remediation decisions clearly.",
        ],
        "generated_audit_report_artifacts": [
            "Change src/service/audit_runner.py: persist markdown output to audit/report_onself_generated by default.",
            "Change frontend/src/App.tsx: render rubric scorecards with direct file-change recommendations.",
            "Change audit/report_onself_generated/*.md, audit/report_onpeer_generated/*.md, audit/report_bypeer_received/*.md: keep complete AuditReport-shaped markdown artifacts.",
        ],
    }
    return recommendations.get(
        criterion_id,
        ["Change relevant source files and tests based on cited evidence before rerunning the audit."],
    )


def _build_detailed_improvements(
    dimension_name: str,
    final_score: int,
    opinions: List[JudicialOpinion],
    recommended_changes: List[str],
    variance: int,
    defense_hallucinated: bool,
    security_vulnerability: bool,
    evidence_index: Dict[str, Evidence],
) -> List[ImprovementAction]:
    actions: List[ImprovementAction] = []
    priority: Literal["P0", "P1", "P2"] = "P2"
    if final_score <= 2:
        priority = "P0"
    elif final_score <= 3:
        priority = "P1"

    judge_findings = " | ".join(f"{op.judge}: {op.argument}" for op in opinions)
    actions.append(
        ImprovementAction(
            priority=priority,
            action=f"Close {dimension_name} gaps identified by the judicial panel.",
            rationale=(
                f"Current criterion score is {final_score}/5. Execute fixes directly tied to judge findings: "
                f"{judge_findings}"
            ),
        )
    )

    target_files = [
        change.split(":", 1)[0].replace("Change ", "").strip()
        for change in recommended_changes
        if ":" in change and change.startswith("Change ")
    ]
    actions.append(
        ImprovementAction(
            priority=priority,
            action="Implement the prescribed file-level changes and rerun this criterion.",
            rationale="Deterministic synthesis requires concrete code/document updates before score recovery.",
            target_files=target_files,
        )
    )

    if variance > 2:
        actions.append(
            ImprovementAction(
                priority="P1",
                action="Run a judge-alignment review for scoring divergence.",
                rationale=(
                    "Judge score variance exceeded 2 points. Align rubric interpretation and evidence thresholds "
                    "to reduce contradictory outcomes."
                ),
            )
        )

    if defense_hallucinated:
        actions.append(
            ImprovementAction(
                priority="P0",
                action="Enforce citation verification before accepting defense claims.",
                rationale=(
                    "Defense arguments cited unverifiable evidence. Add strict evidence cross-checks to block "
                    "hallucinated acceptance paths."
                ),
            )
        )

    if security_vulnerability:
        actions.append(
            ImprovementAction(
                priority="P0",
                action="Patch security-sensitive execution paths before feature work.",
                rationale=(
                    "Security-risk language was detected in judicial reasoning; remediation must precede "
                    "non-security enhancements."
                ),
            )
        )

    actions.extend(_evidence_linked_improvements(dimension_name, opinions, evidence_index))
    return actions


def _evidence_linked_target_files(
    opinions: List[JudicialOpinion], evidence_index: Dict[str, Evidence]
) -> List[str]:
    files: list[str] = []
    for opinion in opinions:
        for citation in opinion.cited_evidence:
            evidence = evidence_index.get(citation)
            if evidence and evidence.location:
                files.append(evidence.location)
    return sorted(set(files))


def _evidence_linked_improvements(
    dimension_name: str,
    opinions: List[JudicialOpinion],
    evidence_index: Dict[str, Evidence],
) -> List[ImprovementAction]:
    target_files = _evidence_linked_target_files(opinions, evidence_index)
    if not target_files:
        return []
    return [
        ImprovementAction(
            priority="P1",
            action=f"Apply evidence-linked remediation for {dimension_name}.",
            rationale=(
                "Target files are derived from cited judicial evidence to keep corrective actions "
                "directly traceable to forensic findings."
            ),
            target_files=target_files,
        )
    ]


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
        remediation_lines: List[str] = []
        for res in results:
            remediation_lines.append(f"- {res.remediation}")
            for item in res.detailed_improvements:
                remediation_lines.append(f"  - [{item.priority}] {item.action}")
                if item.target_files:
                    remediation_lines.append(f"    - Targets: {', '.join(item.target_files)}")
        dissenting = [r for r in results if r.dissent_summary]
        if dissenting:
            remediation_lines.append("- Dissent and variance follow-ups:")
            for res in dissenting:
                remediation_lines.append(
                    f"  - {res.dimension_name}: {res.dissent_summary}"
                )

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
            remediation_plan="\n".join(remediation_lines),
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
