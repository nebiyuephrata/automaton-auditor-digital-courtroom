from typing import Dict, List

from src.state import AgentState
from src.tools.doc_tools import cross_reference_paths


class EvidenceAggregator:
    def __call__(self, state: AgentState) -> Dict[str, object]:
        evidences = state.get("evidences", {})
        missing: List[str] = []
        for bucket in ("repo", "docs", "vision"):
            if bucket not in evidences:
                missing.append(f"missing_evidence_bucket:{bucket}")

        if missing:
            return {"errors": missing}

        existing_paths: List[str] = []
        for evidence in evidences.get("repo", []):
            if evidence.goal == "Repository File Inventory" and evidence.content:
                existing_paths = [
                    line.strip() for line in evidence.content.splitlines() if line.strip()
                ]
                break

        report_text = "\n".join(
            ev.content or "" for ev in evidences.get("docs", []) if ev.goal == "Mentioned Path"
        )
        cross_refs = cross_reference_paths(report_text, existing_paths)

        return {"errors": [], "evidences": {"crossref": cross_refs}}
