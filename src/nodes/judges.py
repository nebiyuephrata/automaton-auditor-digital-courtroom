from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, List, Protocol

from src.state import AgentState, JudicialOpinion
from src.utils.retry_logic import retry


class StructuredJudge(Protocol):
    def invoke(self, payload: Dict) -> JudicialOpinion:
        ...


class LLMProtocol(Protocol):
    def with_structured_output(self, schema):
        ...


def _load_chat_model() -> Any | None:
    provider = os.getenv("JUDGE_PROVIDER", "openai").lower()
    model_name = os.getenv("JUDGE_MODEL", "gpt-4o-mini")

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            return None
        if not os.getenv("ANTHROPIC_API_KEY"):
            return None
        return ChatAnthropic(model=model_name, temperature=0)

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return ChatOpenAI(model=model_name, temperature=0)


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


@dataclass
class ProviderBackedJudgeLLM:
    persona: str
    model: Any
    structured_model: Any | None = None

    def with_structured_output(self, schema):
        self.structured_model = self.model.with_structured_output(schema)
        return self

    def invoke(self, payload: Dict) -> JudicialOpinion:
        if self.structured_model is None:
            raise RuntimeError("Structured output is not bound for provider-backed judge.")

        prompt = (
            f"Criterion ID: {payload['criterion']['id']}\n"
            f"Criterion Name: {payload['criterion'].get('name', '')}\n"
            f"Judicial Logic: {payload.get('judicial_logic', '')}\n\n"
            f"Evidence:\n{payload['evidence_text']}\n\n"
            f"Return a strictly valid JudicialOpinion."
        )
        result = self.structured_model.invoke(
            [
                {"role": "system", "content": payload["system_prompt"]},
                {"role": "user", "content": prompt},
            ]
        )
        if isinstance(result, JudicialOpinion):
            return result
        if isinstance(result, dict):
            return JudicialOpinion.model_validate(result)
        raise ValueError("Provider judge returned non-parseable output.")


class _JudgeBase:
    judge_name: str
    prompt_file: str

    def __init__(self, llm: LLMProtocol | None = None) -> None:
        self.llm = llm or self._build_default_llm()
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
                "judicial_logic": criterion.get("judicial_logic", ""),
            }
            opinion = retry(lambda: self._invoke_strict(structured, payload), attempts=3)
            opinions.append(opinion)

        return {"opinions": opinions}

    def _invoke_strict(self, structured: StructuredJudge, payload: Dict[str, Any]) -> JudicialOpinion:
        opinion = structured.invoke(payload)
        if not isinstance(opinion, JudicialOpinion):
            raise ValueError("Judge output failed schema validation.")
        if opinion.judge != self.judge_name:
            raise ValueError(
                f"Judge identity mismatch. Expected {self.judge_name}, got {opinion.judge}."
            )
        if opinion.criterion_id != payload["criterion"]["id"]:
            raise ValueError(
                "Judge output criterion_id mismatch for strict structured output enforcement."
            )
        return opinion

    def _build_default_llm(self) -> LLMProtocol:
        model = _load_chat_model()
        if model is not None:
            return ProviderBackedJudgeLLM(persona=self.judge_name, model=model)
        return DeterministicJudgeLLM(self.judge_name)

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
