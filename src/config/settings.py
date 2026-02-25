from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    langchain_tracing_v2: bool
    langchain_api_key: str
    langchain_project: str
    judge_provider: str
    judge_model: str
    vision_provider: str
    vision_model: str
    api_auth_key: str
    api_rate_limit_per_minute: int


def load_settings() -> Settings:
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    return Settings(
        langchain_tracing_v2=tracing_flag,
        langchain_api_key=os.getenv("LANGCHAIN_API_KEY", ""),
        langchain_project=os.getenv("LANGCHAIN_PROJECT", "automaton-auditor"),
        judge_provider=os.getenv("JUDGE_PROVIDER", "openai"),
        judge_model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
        vision_provider=os.getenv("VISION_PROVIDER", "openai"),
        vision_model=os.getenv("VISION_MODEL", "gpt-4o-mini"),
        api_auth_key=os.getenv("API_AUTH_KEY", ""),
        api_rate_limit_per_minute=_int_env("API_RATE_LIMIT_PER_MINUTE", 60, min_value=1),
    )


def apply_runtime_settings(settings: Settings) -> None:
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.langchain_tracing_v2 else "false"
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["JUDGE_PROVIDER"] = settings.judge_provider
    os.environ["JUDGE_MODEL"] = settings.judge_model
    os.environ["VISION_PROVIDER"] = settings.vision_provider
    os.environ["VISION_MODEL"] = settings.vision_model
    os.environ["API_RATE_LIMIT_PER_MINUTE"] = str(settings.api_rate_limit_per_minute)
    if settings.api_auth_key:
        os.environ["API_AUTH_KEY"] = settings.api_auth_key


def _int_env(name: str, default: int, min_value: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(min_value, parsed)
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
