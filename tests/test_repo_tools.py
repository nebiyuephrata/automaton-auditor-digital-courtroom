from pathlib import Path
import tempfile

from src.tools.repo_tools import analyze_graph_structure, clone_repo, extract_git_history
from src.tools.sandbox import run_command


def _init_local_repo(path: str) -> None:
    run_command(["git", "init"], cwd=path)
    run_command(["git", "config", "user.email", "test@example.com"], cwd=path)
    run_command(["git", "config", "user.name", "tester"], cwd=path)

    file_path = Path(path) / "README.md"
    file_path.write_text("seed\n", encoding="utf-8")
    run_command(["git", "add", "README.md"], cwd=path)
    run_command(["git", "commit", "-m", "init"], cwd=path)


def test_clone_repo_uses_sandboxed_git_clone() -> None:
    with tempfile.TemporaryDirectory() as source:
        _init_local_repo(source)
        cloned = clone_repo(source)
        try:
            assert (Path(cloned.worktree) / "README.md").exists()
        finally:
            cloned.cleanup()


def test_extract_git_history_returns_structured_evidence() -> None:
    with tempfile.TemporaryDirectory() as source:
        _init_local_repo(source)
        evidences = extract_git_history(source)
    assert len(evidences) == 1
    assert evidences[0].goal == "Git Forensic Analysis"
    assert evidences[0].location.endswith("::git-log")


def test_analyze_graph_structure_detects_missing_graph() -> None:
    with tempfile.TemporaryDirectory() as repo:
        Path(repo, "src").mkdir(parents=True, exist_ok=True)
        Path(repo, "src", "state.py").write_text("", encoding="utf-8")
        findings = analyze_graph_structure(repo)

    graph_finding = [e for e in findings if e.goal == "Graph Wiring"]
    assert graph_finding
    assert graph_finding[0].found is False
