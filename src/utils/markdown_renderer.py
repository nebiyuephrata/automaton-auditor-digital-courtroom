from src.state import AuditReport


def render_audit_report(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# Automaton Auditor Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append(f"Overall Score: **{report.overall_score:.2f}/5.00**")
    lines.append("")
    lines.append("## Criterion Breakdown")

    for criterion in report.criteria:
        lines.append("")
        lines.append(f"### {criterion.dimension_name} ({criterion.dimension_id})")
        lines.append(f"Final Score: **{criterion.final_score}/5**")
        for opinion in criterion.judge_opinions:
            lines.append(
                f"- {opinion.judge}: {opinion.score}/5 | {opinion.argument} | Evidence: {', '.join(opinion.cited_evidence)}"
            )
        if criterion.dissent_summary:
            lines.append(f"- Dissent: {criterion.dissent_summary}")
        lines.append(f"- Remediation: {criterion.remediation}")

    lines.append("")
    lines.append("## Remediation Plan")
    lines.append(report.remediation_plan)
    lines.append("")
    return "\n".join(lines)
