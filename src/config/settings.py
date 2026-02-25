from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    langchain_tracing_v2: bool
    langchain_api_key: str
    langchain_project: str


def load_settings() -> Settings:
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    return Settings(
        langchain_tracing_v2=tracing_flag,
        langchain_api_key=os.getenv("LANGCHAIN_API_KEY", ""),
        langchain_project=os.getenv("LANGCHAIN_PROJECT", "automaton-auditor"),
    )
