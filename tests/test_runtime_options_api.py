import pytest


@pytest.mark.anyio
async def test_runtime_options_exposes_providers_and_presets() -> None:
    from src.server import runtime_options_endpoint

    payload = (await runtime_options_endpoint()).model_dump()
    assert "ollama" in payload["judge_providers"]
    assert "ollama" in payload["vision_providers"]
    assert payload["default_models"]["ollama"] == "llama3.1"
    assert len(payload["rubric_presets"]) > 0
