from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    langchain_tracing_v2: bool
    langchain_api_key: str
    langchain_project: str
    judge_provider: str
    judge_model: str


def load_settings() -> Settings:
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    return Settings(
        langchain_tracing_v2=tracing_flag,
        langchain_api_key=os.getenv("LANGCHAIN_API_KEY", ""),
        langchain_project=os.getenv("LANGCHAIN_PROJECT", "automaton-auditor"),
        judge_provider=os.getenv("JUDGE_PROVIDER", "openai"),
        judge_model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
    )


def apply_runtime_settings(settings: Settings) -> None:
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.langchain_tracing_v2 else "false"
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["JUDGE_PROVIDER"] = settings.judge_provider
    os.environ["JUDGE_MODEL"] = settings.judge_model
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
