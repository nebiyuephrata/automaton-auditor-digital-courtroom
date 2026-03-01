from src.state import AuditReport


def render_audit_report(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# Automaton Auditor Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append(f"Overall Score: **{report.overall_score:.2f}/5.00**")
    lines.append(f"Governance Maturity: **{report.governance_maturity}**")
    lines.append(f"Maturity Rationale: {report.governance_maturity_rationale}")
    lines.append("")
    lines.append("## Criterion Breakdown")

    for criterion in report.criteria:
        lines.append("")
        lines.append(f"### {criterion.dimension_name} ({criterion.dimension_id})")
        lines.append(f"Final Score: **{criterion.final_score}/5**")
        for opinion in criterion.judge_opinions:
            evidence = ", ".join(opinion.cited_evidence) if opinion.cited_evidence else "none"
            lines.append(
                f"- {opinion.judge}: {opinion.score}/5 | {opinion.argument} | Evidence: {evidence}"
            )
        if criterion.dissent_summary:
            lines.append(f"- Dissent / Variance: {criterion.dissent_summary}")
        lines.append(f"- Remediation: {criterion.remediation}")
        if criterion.recommended_changes:
            lines.append("- File Changes:")
            for change in criterion.recommended_changes:
                lines.append(f"  - {change}")
        if criterion.detailed_improvements:
            lines.append("- Detailed Improvements:")
            for item in criterion.detailed_improvements:
                files = f" | Targets: {', '.join(item.target_files)}" if item.target_files else ""
                lines.append(
                    f"  - [{item.priority}] {item.action} | Why: {item.rationale}{files}"
                )

    lines.append("")
    lines.append("## Remediation Plan")
    lines.append(report.remediation_plan)
    lines.append("")
    return "\n".join(lines)
