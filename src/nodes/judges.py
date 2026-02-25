from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Protocol

from src.state import AgentState, JudicialOpinion
from src.utils.retry_logic import retry


class StructuredJudge(Protocol):
    def invoke(self, payload: Dict) -> JudicialOpinion:
        ...


class LLMProtocol(Protocol):
    def with_structured_output(self, schema):
        ...


@dataclass
class DeterministicJudgeLLM:
    persona: str

    def with_structured_output(self, schema):
        return self

    def invoke(self, payload: Dict) -> JudicialOpinion:
        criterion = payload["criterion"]
        evidence_text = payload["evidence_text"]
        cid = criterion["id"]

        has_linear = "linear" in evidence_text.lower() and "fan-out" not in evidence_text.lower()
        has_security = "os.system" in evidence_text.lower()

        if self.persona == "Prosecutor":
            score = 1 if (has_linear or has_security) else 3
            argument = "Critical gaps detected in orchestration or safety checks."
        elif self.persona == "Defense":
            score = 4 if not has_security else 2
            argument = "Evidence shows implementation effort with partial compliance."
        else:
            score = 2 if has_linear else 4
            argument = "Technical viability depends on deterministic wiring and safety controls."

        return JudicialOpinion(
            judge=self.persona,
            criterion_id=cid,
            score=score,
            argument=argument,
            cited_evidence=["repo:Graph Wiring", "repo:Typed State Enforcement"],
        )


class _JudgeBase:
    judge_name: str
    prompt_file: str

    def __init__(self, llm: LLMProtocol | None = None) -> None:
        self.llm = llm or DeterministicJudgeLLM(self.judge_name)
        self.system_prompt = self._load_prompt(self.prompt_file)

    def __call__(self, state: AgentState) -> Dict[str, List[JudicialOpinion]]:
        structured: StructuredJudge = self.llm.with_structured_output(JudicialOpinion)
        dimensions = state.get("rubric_dimensions", [])
        evidence_text = _flatten_evidence(state)

        opinions: List[JudicialOpinion] = []
        for criterion in dimensions:
            payload = {
                "criterion": criterion,
                "evidence_text": evidence_text,
                "system_prompt": self.system_prompt,
            }
            opinion = retry(lambda: structured.invoke(payload), attempts=3)
            opinions.append(opinion)

        return {"opinions": opinions}

    @staticmethod
    def _load_prompt(filename: str) -> str:
        prompt_path = Path("src") / "prompts" / filename
        return prompt_path.read_text(encoding="utf-8").strip()


def _flatten_evidence(state: AgentState) -> str:
    bits: List[str] = []
    for bucket in state.get("evidences", {}).values():
        for evidence in bucket:
            bits.append(
                f"{evidence.goal}|{evidence.location}|{evidence.rationale}|{evidence.content or ''}"
            )
    return "\n".join(bits)


class ProsecutorNode(_JudgeBase):
    judge_name = "Prosecutor"
    prompt_file = "prosecutor.txt"


class DefenseNode(_JudgeBase):
    judge_name = "Defense"
    prompt_file = "defense.txt"


class TechLeadNode(_JudgeBase):
    judge_name = "TechLead"
    prompt_file = "techlead.txt"
