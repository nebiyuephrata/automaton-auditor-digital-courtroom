from pathlib import Path
from typing import Dict, List

from src.state import AgentState, Evidence
from src.tools.doc_tools import analyze_document
from src.tools.pdf_image_tools import analyze_pdf_diagrams
from src.tools.repo_tools import analyze_graph_structure, clone_repo, extract_git_history


class RepoInvestigator:
    def __call__(self, state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
        repo_url = state.get("repo_url", "")
        cloned = clone_repo(repo_url)
        try:
            evidences = extract_git_history(cloned.worktree)
            evidences.extend(analyze_graph_structure(cloned.worktree))
            paths = sorted(
                str(path.relative_to(cloned.worktree))
                for path in Path(cloned.worktree).rglob("*")
                if path.is_file()
            )
            evidences.append(
                Evidence(
                    goal="Repository File Inventory",
                    found=True,
                    content="\n".join(paths),
                    location=cloned.worktree,
                    rationale="Used for report cross-reference validation.",
                    confidence=0.98,
                )
            )
        finally:
            cloned.cleanup()

        return {"evidences": {"repo": evidences}}


class DocAnalyst:
    def __call__(self, state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
        pdf_path = state.get("pdf_path", "")
        evidences = analyze_document(pdf_path)
        return {"evidences": {"docs": evidences}}


class VisionInspector:
    def __call__(self, state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
        pdf_path = state.get("pdf_path", "")
        runtime_config = state.get("runtime_config")
        evidences = analyze_pdf_diagrams(pdf_path, runtime_config=runtime_config)
        return {"evidences": {"vision": evidences}}
