from dataclasses import dataclass
from typing import Dict

import pytest

from src.nodes.judges import ProsecutorNode
from src.state import Evidence, JudicialOpinion


@dataclass
class FakeStructuredLLM:
    called_with_schema: bool = False

    def with_structured_output(self, schema):
        self.called_with_schema = schema is JudicialOpinion
        return self

    def invoke(self, payload: Dict) -> JudicialOpinion:
        return JudicialOpinion(
            judge="Prosecutor",
            criterion_id=payload["criterion"]["id"],
            score=2,
            argument="Structured output returned",
            cited_evidence=["repo:Graph Wiring"],
        )


@dataclass
class FlakyStructuredLLM:
    attempts: int = 0

    def with_structured_output(self, schema):
        return self

    def invoke(self, payload: Dict) -> JudicialOpinion:
        self.attempts += 1
        if self.attempts < 3:
            return JudicialOpinion(
                judge="Defense",
                criterion_id=payload["criterion"]["id"],
                score=2,
                argument="Wrong judge on purpose",
                cited_evidence=["repo:Graph Wiring"],
            )
        return JudicialOpinion(
            judge="Prosecutor",
            criterion_id=payload["criterion"]["id"],
            score=2,
            argument="Recovered after retries",
            cited_evidence=["repo:Graph Wiring"],
        )


@dataclass
class AlwaysBrokenStructuredLLM:
    def with_structured_output(self, schema):
        return self

    def invoke(self, payload: Dict):
        return {"invalid": "payload"}


def test_judge_uses_structured_output_binding() -> None:
    llm = FakeStructuredLLM()
    node = ProsecutorNode(llm=llm)
    state = {
        "rubric_dimensions": [{"id": "langgraph_architecture", "name": "LangGraph Architecture"}],
        "evidences": {
            "repo": [
                Evidence(
                    goal="Graph Wiring",
                    found=True,
                    content="fan-out",
                    location="src/graph.py",
                    rationale="parallel",
                    confidence=1.0,
                )
            ]
        },
    }

    result = node(state)

    assert llm.called_with_schema is True
    assert "opinions" in result
    assert len(result["opinions"]) == 1
    assert isinstance(result["opinions"][0], JudicialOpinion)


def test_judge_retries_until_identity_matches() -> None:
    llm = FlakyStructuredLLM()
    node = ProsecutorNode(llm=llm)
    state = {
        "rubric_dimensions": [{"id": "langgraph_architecture", "name": "LangGraph Architecture"}],
        "evidences": {
            "repo": [
                Evidence(
                    goal="Graph Wiring",
                    found=True,
                    content="fan-out",
                    location="src/graph.py",
                    rationale="parallel",
                    confidence=1.0,
                )
            ]
        },
    }

    result = node(state)

    assert llm.attempts == 3
    assert result["opinions"][0].judge == "Prosecutor"


def test_judge_raises_when_schema_never_recovers() -> None:
    llm = AlwaysBrokenStructuredLLM()
    node = ProsecutorNode(llm=llm)
    state = {
        "rubric_dimensions": [{"id": "langgraph_architecture", "name": "LangGraph Architecture"}],
        "evidences": {
            "repo": [
                Evidence(
                    goal="Graph Wiring",
                    found=True,
                    content="fan-out",
                    location="src/graph.py",
                    rationale="parallel",
                    confidence=1.0,
                )
            ]
        },
    }

    with pytest.raises(ValueError):
        node(state)
