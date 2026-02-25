from src.nodes.justice import resolve_criterion
from src.state import Evidence, JudicialOpinion


def test_security_override_caps_score() -> None:
    dimension = {"id": "sandbox_safety", "name": "Sandbox Safety"}
    opinions = [
        JudicialOpinion(
            judge="Prosecutor",
            criterion_id="sandbox_safety",
            score=5,
            argument="Security issue: unsafe shell execution path used",
            cited_evidence=["repo:Safe Tool Engineering"],
        ),
        JudicialOpinion(
            judge="Defense",
            criterion_id="sandbox_safety",
            score=5,
            argument="Effort is high",
            cited_evidence=["repo:Safe Tool Engineering"],
        ),
        JudicialOpinion(
            judge="TechLead",
            criterion_id="sandbox_safety",
            score=5,
            argument="Operationally acceptable",
            cited_evidence=["repo:Safe Tool Engineering"],
        ),
    ]
    evidence_index = {
        "repo:Safe Tool Engineering": Evidence(
            goal="Safe Tool Engineering",
            found=False,
            content="unsafe shell execution",
            location="src/tools/repo_tools.py",
            rationale="unsafe",
            confidence=1.0,
        )
    }

    result = resolve_criterion(dimension, opinions, evidence_index)
    assert result.final_score <= 3


def test_fact_supremacy_rejects_hallucinated_defense() -> None:
    dimension = {"id": "citation_integrity", "name": "Citation Integrity"}
    opinions = [
        JudicialOpinion(
            judge="Prosecutor",
            criterion_id="citation_integrity",
            score=2,
            argument="Missing file claim verified",
            cited_evidence=["docs:Host Analysis Accuracy"],
        ),
        JudicialOpinion(
            judge="Defense",
            criterion_id="citation_integrity",
            score=5,
            argument="Everything is present",
            cited_evidence=["fake:evidence"],
        ),
        JudicialOpinion(
            judge="TechLead",
            criterion_id="citation_integrity",
            score=3,
            argument="Mixed quality",
            cited_evidence=["docs:Host Analysis Accuracy"],
        ),
    ]
    evidence_index = {
        "docs:Host Analysis Accuracy": Evidence(
            goal="Host Analysis Accuracy",
            found=False,
            content="missing path",
            location="report",
            rationale="hallucinated",
            confidence=1.0,
        )
    }

    result = resolve_criterion(dimension, opinions, evidence_index)
    assert result.final_score <= 3


def test_variance_rule_generates_dissent() -> None:
    dimension = {"id": "judicial_nuance", "name": "Judicial Nuance"}
    opinions = [
        JudicialOpinion(
            judge="Prosecutor",
            criterion_id="judicial_nuance",
            score=1,
            argument="Hallucination liability",
            cited_evidence=["repo:Structured Output"],
        ),
        JudicialOpinion(
            judge="Defense",
            criterion_id="judicial_nuance",
            score=5,
            argument="Role separation successful",
            cited_evidence=["repo:Structured Output"],
        ),
        JudicialOpinion(
            judge="TechLead",
            criterion_id="judicial_nuance",
            score=3,
            argument="Needs stricter schemas",
            cited_evidence=["repo:Structured Output"],
        ),
    ]
    evidence_index = {
        "repo:Structured Output": Evidence(
            goal="Structured Output",
            found=True,
            content="with_structured_output",
            location="src/nodes/judges.py",
            rationale="schema bound",
            confidence=1.0,
        )
    }

    result = resolve_criterion(dimension, opinions, evidence_index)
    assert result.dissent_summary is not None
    assert result.final_score == 3
