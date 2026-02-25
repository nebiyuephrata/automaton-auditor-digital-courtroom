import operator
from typing import Any, Dict, List, get_type_hints

from src.state import AgentState, Evidence, JudicialOpinion


def _reducer_for(field: str):
    hints = get_type_hints(AgentState, include_extras=True)
    reducer = hints[field].__metadata__[0]
    return reducer


def test_evidences_reducer_merges_without_overwrite() -> None:
    reducer = _reducer_for("evidences")
    left: Dict[str, List[Evidence]] = {
        "repo": [
            Evidence(
                goal="g1",
                found=True,
                content="a",
                location="src/state.py",
                rationale="exists",
                confidence=1.0,
            )
        ]
    }
    right: Dict[str, List[Evidence]] = {
        "docs": [
            Evidence(
                goal="g2",
                found=True,
                content="b",
                location="README.md",
                rationale="exists",
                confidence=0.9,
            )
        ]
    }

    merged = reducer(left, right)

    assert reducer is operator.ior
    assert set(merged.keys()) == {"repo", "docs"}


def test_opinions_reducer_appends() -> None:
    reducer = _reducer_for("opinions")
    left = [
        JudicialOpinion(
            judge="Prosecutor",
            criterion_id="arch",
            score=1,
            argument="linear",
            cited_evidence=["src/graph.py"],
        )
    ]
    right = [
        JudicialOpinion(
            judge="Defense",
            criterion_id="arch",
            score=3,
            argument="effort exists",
            cited_evidence=["README.md"],
        )
    ]

    merged = reducer(left, right)

    assert reducer is operator.add
    assert len(merged) == 2
    assert merged[0].judge == "Prosecutor"
    assert merged[1].judge == "Defense"
