import os

from src.config.settings import load_settings


def test_load_settings_invalid_rate_limit_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "abc")
    settings = load_settings()
    assert settings.api_rate_limit_per_minute == 60


def test_load_settings_rate_limit_clamped_to_min(monkeypatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "0")
    settings = load_settings()
    assert settings.api_rate_limit_per_minute == 1


def test_load_settings_reads_dotenv_when_env_is_unset(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("LANGCHAIN_API_KEY=test_key_from_dotenv\n", encoding="utf-8")
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    settings = load_settings()
    assert settings.langchain_api_key == "test_key_from_dotenv"


def test_load_settings_openrouter_fields(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    settings = load_settings()
    assert settings.openrouter_api_key == "or-key"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
