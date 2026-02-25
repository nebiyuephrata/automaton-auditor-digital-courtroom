from pathlib import Path
import re
from typing import Dict, List

from pypdf import PdfReader

from src.state import Evidence


KEYWORDS = [
    "Dialectical Synthesis",
    "Fan-In",
    "Fan-Out",
    "Metacognition",
    "State Synchronization",
]


def ingest_pdf(path: str, chunk_size: int = 1200) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(path)
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not text.strip():
        return []
    return [text[idx : idx + chunk_size] for idx in range(0, len(text), chunk_size)]


def build_chunk_index(chunks: List[str]) -> List[Dict[str, object]]:
    index: List[Dict[str, object]] = []
    cursor = 0
    for chunk_id, text in enumerate(chunks):
        start = cursor
        end = cursor + len(text)
        index.append(
            {
                "chunk_id": chunk_id,
                "start": start,
                "end": end,
                "text": text,
            }
        )
        cursor = end
    return index


def query_chunk_index(
    chunk_index: List[Dict[str, object]], query: str, top_k: int = 3
) -> List[Dict[str, object]]:
    query_tokens = {token.lower() for token in re.findall(r"\w+", query)}
    if not query_tokens or top_k <= 0:
        return []

    scored: List[tuple[int, Dict[str, object]]] = []
    for item in chunk_index:
        text = str(item.get("text", ""))
        tokens = {token.lower() for token in re.findall(r"\w+", text)}
        overlap = len(query_tokens.intersection(tokens))
        if overlap > 0:
            scored.append((overlap, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def query_pdf_chunks(
    path: str, query: str, chunk_size: int = 1200, top_k: int = 3
) -> List[Evidence]:
    chunks = ingest_pdf(path, chunk_size=chunk_size)
    index = build_chunk_index(chunks)
    matches = query_chunk_index(index, query=query, top_k=top_k)

    if not matches:
        return [
            Evidence(
                goal="Targeted PDF Query",
                found=False,
                content=query,
                location=path,
                rationale="No chunk matched the provided query tokens.",
                confidence=0.8,
            )
        ]

    evidences: List[Evidence] = []
    for item in matches:
        evidences.append(
            Evidence(
                goal="Targeted PDF Query",
                found=True,
                content=str(item.get("text", ""))[:800],
                location=f"{path}::chunk:{item.get('chunk_id')}",
                rationale=f"Matched query '{query}' in indexed chunk range.",
                confidence=0.85,
            )
        )
    return evidences


def keyword_depth_analysis(chunks: List[str]) -> List[Evidence]:
    joined = "\n".join(chunks)
    evidences: List[Evidence] = []
    for term in KEYWORDS:
        count = joined.lower().count(term.lower())
        evidences.append(
            Evidence(
                goal=f"Keyword Depth: {term}",
                found=count > 0,
                content=f"count={count}",
                location="pdf::content",
                rationale="Checks conceptual depth claims against report text.",
                confidence=0.85,
            )
        )
    return evidences


def extract_file_paths(text: str) -> List[str]:
    return sorted(set(re.findall(r"\b(?:src|tests|docs|audit|reports)/[\w./-]+", text)))


def path_mention_evidence(report_text: str) -> List[Evidence]:
    mentioned = extract_file_paths(report_text)
    evidences: List[Evidence] = []
    for path in mentioned:
        evidences.append(
            Evidence(
                goal="Mentioned Path",
                found=True,
                content=path,
                location="pdf::path-mention",
                rationale="Path mentioned in report for later repo cross-reference.",
                confidence=0.9,
            )
        )
    return evidences


def cross_reference_paths(report_text: str, existing_paths: List[str]) -> List[Evidence]:
    mentioned = extract_file_paths(report_text)
    existing_set = set(existing_paths)
    evidences: List[Evidence] = []

    for path in mentioned:
        verified = path in existing_set
        evidences.append(
            Evidence(
                goal="Host Analysis Accuracy",
                found=verified,
                content=path,
                location=path,
                rationale=(
                    "Path exists in repository; claim is verifiable."
                    if verified
                    else "Path cited in report is missing from repository; hallucination risk."
                ),
                confidence=0.95,
            )
        )

    return evidences


def analyze_document(path: str, existing_paths: List[str] | None = None) -> List[Evidence]:
    try:
        chunks = ingest_pdf(path)
    except Exception as exc:
        return [
            Evidence(
                goal="Document Parsing",
                found=False,
                content=str(exc),
                location=path,
                rationale="Document analysis failed before forensic extraction.",
                confidence=1.0,
            )
        ]

    report_text = "\n".join(chunks)
    results = keyword_depth_analysis(chunks) + path_mention_evidence(report_text)
    if existing_paths is not None:
        results.extend(cross_reference_paths(report_text, existing_paths))
    return results
