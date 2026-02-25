from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Dict, List

from src.state import Evidence
from src.tools.ast_analysis import (
    detect_graph_edge_patterns,
    detect_stategraph_instantiation,
    parse_class_inheritance,
)
from src.tools.sandbox import run_command


@dataclass
class ClonedRepo:
    worktree: str
    _tmp: tempfile.TemporaryDirectory[str]

    def cleanup(self) -> None:
        self._tmp.cleanup()


def clone_repo(repo_url: str) -> ClonedRepo:
    tmp = tempfile.TemporaryDirectory(prefix="automaton-auditor-")
    target = Path(tmp.name) / "target"
    result = run_command(["git", "clone", repo_url, str(target)])
    if result.returncode != 0:
        tmp.cleanup()
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
    return ClonedRepo(worktree=str(target), _tmp=tmp)


def extract_git_history(repo_path: str) -> List[Evidence]:
    result = run_command(
        ["git", "log", "--pretty=format:%H|%cI|%s", "--reverse"], cwd=repo_path
    )
    if result.returncode != 0:
        return [
            Evidence(
                goal="Git Forensic Analysis",
                found=False,
                content=result.stderr,
                location=repo_path,
                rationale="Unable to extract git log; repository may be invalid.",
                confidence=1.0,
            )
        ]

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    progression_found = len(lines) > 3
    return [
        Evidence(
            goal="Git Forensic Analysis",
            found=progression_found,
            content="\n".join(lines),
            location=f"{repo_path}::git-log",
            rationale=(
                "Commit history is atomic and progressive."
                if progression_found
                else "Commit history is monolithic or too shallow."
            ),
            confidence=0.95,
        )
    ]


def analyze_graph_structure(repo_path: str) -> List[Evidence]:
    graph_file = Path(repo_path) / "src" / "graph.py"
    state_file = Path(repo_path) / "src" / "state.py"
    findings: List[Evidence] = []

    has_graph = graph_file.exists()
    has_state = state_file.exists()

    findings.append(
        Evidence(
            goal="State Structure",
            found=has_state,
            content="state.py exists" if has_state else None,
            location=str(state_file),
            rationale="Typed state must be explicitly defined.",
            confidence=1.0,
        )
    )

    if not has_graph:
        findings.append(
            Evidence(
                goal="Graph Wiring",
                found=False,
                content=None,
                location=str(graph_file),
                rationale="Graph file missing; cannot validate fan-out/fan-in architecture.",
                confidence=1.0,
            )
        )
        return findings

    inheritance: Dict[str, List[str]] = parse_class_inheritance(str(state_file)) if has_state else {}
    has_pydantic = any("BaseModel" in bases for bases in inheritance.values())
    has_typeddict = any("TypedDict" in bases for bases in inheritance.values())

    findings.append(
        Evidence(
            goal="Typed State Enforcement",
            found=has_pydantic and has_typeddict,
            content=str(inheritance),
            location=str(state_file),
            rationale="State schema must include BaseModel and TypedDict definitions.",
            confidence=0.95,
        )
    )

    patterns = detect_graph_edge_patterns(str(graph_file))
    has_state_graph = detect_stategraph_instantiation(str(graph_file))
    architecture_ok = (
        has_state_graph
        and patterns["has_fan_out"]
        and patterns["has_fan_in"]
        and patterns["conditional_edges"] > 0
    )

    findings.append(
        Evidence(
            goal="Graph Wiring",
            found=architecture_ok,
            content=str(patterns),
            location=str(graph_file),
            rationale=(
                "Graph uses StateGraph with fan-out, fan-in, and conditional edges."
                if architecture_ok
                else "Graph missing required wiring invariants."
            ),
            confidence=0.9,
        )
    )

    return findings
