from src.nodes.detectives import DocAnalyst, RepoInvestigator, VisionInspector
from src.state import Evidence


def test_repo_investigator_returns_structured_evidence(monkeypatch) -> None:
    class _FakeClone:
        worktree = "/tmp/fake-repo"

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr("src.nodes.detectives.clone_repo", lambda _url: _FakeClone())
    monkeypatch.setattr(
        "src.nodes.detectives.extract_git_history",
        lambda _path: [
            Evidence(
                goal="Git Forensic Analysis",
                found=True,
                content="commit",
                location="/tmp/fake-repo::git-log",
                rationale="ok",
                confidence=1.0,
            )
        ],
    )
    monkeypatch.setattr(
        "src.nodes.detectives.analyze_graph_structure",
        lambda _path: [
            Evidence(
                goal="Graph Wiring",
                found=True,
                content="fan-out/fan-in",
                location="/tmp/fake-repo/src/graph.py",
                rationale="ok",
                confidence=1.0,
            )
        ],
    )
    monkeypatch.setattr("src.nodes.detectives.Path.rglob", lambda _self, _p: [])

    node = RepoInvestigator()
    result = node({"repo_url": "https://example.com/repo.git"})

    assert "evidences" in result
    assert "repo" in result["evidences"]
    assert all(isinstance(item, Evidence) for item in result["evidences"]["repo"])


def test_doc_analyst_returns_docs_bucket(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.nodes.detectives.analyze_document",
        lambda _pdf: [
            Evidence(
                goal="Keyword Depth: Metacognition",
                found=True,
                content="count=2",
                location="pdf::content",
                rationale="ok",
                confidence=0.9,
            )
        ],
    )

    node = DocAnalyst()
    result = node({"pdf_path": "reports/final_report.pdf"})

    assert "docs" in result["evidences"]
    assert result["evidences"]["docs"][0].goal.startswith("Keyword Depth")


def test_vision_inspector_returns_vision_bucket(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.nodes.detectives.analyze_pdf_diagrams",
        lambda _pdf: [
            Evidence(
                goal="Swarm Visual Flow Analysis",
                found=True,
                content='{"mode":"heuristic"}',
                location="/tmp/image_0.png",
                rationale="ok",
                confidence=0.8,
            )
        ],
    )

    node = VisionInspector()
    result = node({"pdf_path": "reports/final_report.pdf"})

    assert "vision" in result["evidences"]
    assert result["evidences"]["vision"][0].goal == "Swarm Visual Flow Analysis"
