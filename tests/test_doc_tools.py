from src.state import Evidence
from src.tools.doc_tools import (
    analyze_document,
    build_chunk_index,
    query_chunk_index,
    query_pdf_chunks,
)


def test_query_chunk_index_returns_ranked_matches() -> None:
    chunks = [
        "LangGraph fan-out and fan-in orchestration details.",
        "This paragraph discusses deployment notes only.",
        "Deterministic Chief Justice arbitration and dissent handling.",
    ]
    index = build_chunk_index(chunks)

    matches = query_chunk_index(index, query="fan-out dissent", top_k=2)

    assert len(matches) == 2
    assert any("fan-out" in str(item["text"]).lower() for item in matches)


def test_query_pdf_chunks_handles_no_match(monkeypatch) -> None:
    monkeypatch.setattr("src.tools.doc_tools.ingest_pdf", lambda _path, chunk_size=1200: ["alpha beta"])

    evidences = query_pdf_chunks("reports/final_report.pdf", query="nonexistent token")

    assert len(evidences) == 1
    assert isinstance(evidences[0], Evidence)
    assert evidences[0].found is False


def test_analyze_document_returns_parsing_error_evidence(monkeypatch) -> None:
    def _raise(_path, chunk_size=1200):
        raise ValueError("parse failed")

    monkeypatch.setattr("src.tools.doc_tools.ingest_pdf", _raise)

    evidences = analyze_document("missing.pdf")

    assert len(evidences) == 1
    assert evidences[0].goal == "Document Parsing"
    assert evidences[0].found is False
    assert "parse failed" in (evidences[0].content or "")
