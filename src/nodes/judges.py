from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Protocol

from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool

from src.state import AgentState, JudicialOpinion, RuntimeLLMConfig
from src.utils.retry_logic import retry


class StructuredJudge(Protocol):
    def invoke(self, payload: Dict) -> JudicialOpinion:
        ...


class LLMProtocol(Protocol):
    def with_structured_output(self, schema):
        ...


def _load_chat_model(runtime_config: RuntimeLLMConfig | None = None) -> Any | None:
    runtime_config = runtime_config or RuntimeLLMConfig()
    provider = runtime_config.judge_provider.lower()
    model_name = runtime_config.judge_model

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            return None
        if not runtime_config.anthropic_api_key:
            return None
        return ChatAnthropic(
            model=model_name,
            temperature=0,
            api_key=runtime_config.anthropic_api_key,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            return None
        return ChatOllama(
            model=model_name,
            temperature=0,
            base_url=runtime_config.ollama_base_url or "http://localhost:11434",
        )

    if provider == "openrouter":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None
        if not runtime_config.openrouter_api_key:
            return None
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=runtime_config.openrouter_api_key,
            base_url=runtime_config.openrouter_base_url or "https://openrouter.ai/api/v1",
        )

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None
    if not runtime_config.openai_api_key:
        return None
    return ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=runtime_config.openai_api_key,
    )


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
        has_security = any(
            marker in evidence_text.lower()
            for marker in ("unsafe shell", "shell execution", "command injection")
        )

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

        tool_analysis = self._run_tool_call_cycle(payload)
        prompt = (
            f"Criterion ID: {payload['criterion']['id']}\n"
            f"Criterion Name: {payload['criterion'].get('name', '')}\n"
            f"Judicial Logic: {payload.get('judicial_logic', '')}\n\n"
            f"Evidence:\n{payload['evidence_text']}\n\n"
            f"Tool Analysis:\n{tool_analysis}\n\n"
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

    def _run_tool_call_cycle(self, payload: Dict[str, Any]) -> str:
        if not hasattr(self.model, "bind_tools"):
            return "Tool calls unavailable for this provider model."

        tools = _build_evidence_tools(payload.get("evidence_text", ""))
        if not tools:
            return "No tools available."

        tool_enabled_model = self.model.bind_tools(tools)
        tool_lookup = {tool.name: tool for tool in tools}

        messages: List[Any] = [
            {
                "role": "system",
                "content": (
                    "Use tools when needed to inspect evidence. "
                    "When done, provide a concise factual analysis summary only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Criterion: {payload['criterion']['id']} - {payload['criterion'].get('name', '')}\n"
                    f"Judicial Logic: {payload.get('judicial_logic', '')}\n"
                    "Investigate with tools before summarizing."
                ),
            },
        ]

        for _ in range(3):
            response = tool_enabled_model.invoke(messages)
            messages.append(response)
            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                content = getattr(response, "content", "")
                return str(content) if content else "Tool cycle completed without summary content."

            for call in tool_calls:
                name = call.get("name", "")
                args = call.get("args", {}) or {}
                tool = tool_lookup.get(name)
                if tool is None:
                    output = json.dumps({"error": f"unknown tool: {name}"})
                else:
                    try:
                        output = tool.invoke(args)
                    except Exception as exc:
                        output = json.dumps({"error": str(exc)})
                messages.append(
                    ToolMessage(
                        content=str(output),
                        tool_call_id=call.get("id", ""),
                    )
                )

        return "Tool cycle reached maximum iterations."


def _build_evidence_tools(evidence_text: str) -> List[StructuredTool]:
    lines = [line for line in evidence_text.splitlines() if line.strip()]

    def list_evidence_items() -> str:
        return json.dumps({"count": len(lines), "items": lines[:200]})

    def find_evidence(keyword: str) -> str:
        needle = keyword.lower().strip()
        matched = [line for line in lines if needle and needle in line.lower()]
        return json.dumps({"keyword": keyword, "count": len(matched), "items": matched[:50]})

    def summarize_evidence() -> str:
        by_prefix: Dict[str, int] = {}
        for line in lines:
            prefix = line.split("|", 1)[0]
            by_prefix[prefix] = by_prefix.get(prefix, 0) + 1
        return json.dumps({"total": len(lines), "by_goal": by_prefix})

    return [
        StructuredTool.from_function(
            func=list_evidence_items,
            name="list_evidence_items",
            description="Return available evidence lines for this criterion context.",
        ),
        StructuredTool.from_function(
            func=find_evidence,
            name="find_evidence",
            description="Search evidence lines by keyword and return matching lines.",
        ),
        StructuredTool.from_function(
            func=summarize_evidence,
            name="summarize_evidence",
            description="Return grouped evidence counts by evidence goal prefix.",
        ),
    ]


class _JudgeBase:
    judge_name: str
    prompt_file: str

    def __init__(self, llm: LLMProtocol | None = None) -> None:
        self.llm = llm
        self.system_prompt = self._load_prompt(self.prompt_file)

    def __call__(self, state: AgentState) -> Dict[str, List[JudicialOpinion]]:
        runtime_config = state.get("runtime_config", RuntimeLLMConfig())
        llm = self.llm or self._build_default_llm(runtime_config)
        structured: StructuredJudge = llm.with_structured_output(JudicialOpinion)
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

    def _build_default_llm(self, runtime_config: RuntimeLLMConfig) -> LLMProtocol:
        model = _load_chat_model(runtime_config)
        if model is not None:
            return ProviderBackedJudgeLLM(persona=self.judge_name, model=model)
        raise RuntimeError(
            "Failed to initialize provider-backed judge model for "
            f"provider={runtime_config.judge_provider} model={runtime_config.judge_model}. "
            "Check runtime provider configuration and credentials."
        )

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
