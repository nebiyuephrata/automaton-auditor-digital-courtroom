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
