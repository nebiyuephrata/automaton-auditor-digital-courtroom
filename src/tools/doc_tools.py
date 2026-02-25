from pathlib import Path
import re
from typing import List

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
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not text.strip():
        return []
    return [text[idx : idx + chunk_size] for idx in range(0, len(text), chunk_size)]


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
    chunks = ingest_pdf(path)
    report_text = "\n".join(chunks)
    results = keyword_depth_analysis(chunks) + path_mention_evidence(report_text)
    if existing_paths is not None:
        results.extend(cross_reference_paths(report_text, existing_paths))
    return results
