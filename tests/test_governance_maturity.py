from src.nodes.justice import derive_governance_maturity
from src.state import CriterionResult, JudicialOpinion


def _criterion(cid: str, score: int, dissent: bool = False) -> CriterionResult:
    return CriterionResult(
        dimension_id=cid,
        dimension_name=cid,
        final_score=score,
        judge_opinions=[
            JudicialOpinion(
                judge="Prosecutor",
                criterion_id=cid,
                score=score,
                argument="a",
                cited_evidence=["repo:x"],
            )
        ],
        dissent_summary="dissent" if dissent else None,
        remediation="fix",
    )


def test_maturity_band_constitutional_without_penalties() -> None:
    criteria = [_criterion("langgraph_architecture", 5), _criterion("judicial_nuance", 5), _criterion("synthesis_engine", 5)]
    band, rationale = derive_governance_maturity(4.6, criteria)
    assert band == "Constitutional"
    assert "overall score 4.60" in rationale


def test_maturity_downgrades_on_critical_dimension_failures() -> None:
    criteria = [_criterion("langgraph_architecture", 2), _criterion("judicial_nuance", 2), _criterion("synthesis_engine", 2)]
    band, _ = derive_governance_maturity(4.6, criteria)
    assert band == "Developing"
