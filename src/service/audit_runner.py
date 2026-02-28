from pathlib import Path
from typing import Any, Dict

from src.config.settings import load_settings
from src.graph import create_graph
from src.state import RuntimeLLMConfig
from src.utils.rubric_loader import resolve_rubric_path, rubric_dimensions


def run_audit(
    repo_url: str,
    pdf_path: str,
    rubric_path: str = "rubric.json",
    rubric_preset: str | None = None,
    runtime_config: RuntimeLLMConfig | None = None,
    output_path: str | None = None,
) -> Dict[str, Any]:
    app = create_graph()
    resolved_rubric_path = resolve_rubric_path(rubric_path=rubric_path, rubric_preset=rubric_preset)
    settings = load_settings()
    default_runtime = RuntimeLLMConfig(
        judge_provider=settings.judge_provider,
        judge_model=settings.judge_model,
        vision_provider=settings.vision_provider,
        vision_model=settings.vision_model,
        openai_api_key=settings.openai_api_key or None,
        anthropic_api_key=settings.anthropic_api_key or None,
        openrouter_api_key=settings.openrouter_api_key or None,
        openrouter_base_url=settings.openrouter_base_url or None,
        ollama_base_url=settings.ollama_base_url or None,
    )
    effective_runtime = _merge_runtime_config(default_runtime, runtime_config)
    state = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": rubric_dimensions(
            rubric_path=resolved_rubric_path,
            rubric_preset=rubric_preset,
        ),
        "runtime_config": effective_runtime,
        "evidences": {},
        "opinions": [],
        "errors": [],
    }

    result = app.invoke(state)
    markdown = result.get("rendered_markdown", "")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")

    response: Dict[str, Any] = {"rendered_markdown": markdown}
    if "final_report" in result:
        response["final_report"] = result["final_report"].model_dump()
    if "errors" in result:
        response["errors"] = result.get("errors", [])
    return response


def _merge_runtime_config(
    defaults: RuntimeLLMConfig, runtime_config: RuntimeLLMConfig | None
) -> RuntimeLLMConfig:
    if runtime_config is None:
        return defaults
    return RuntimeLLMConfig(
        judge_provider=runtime_config.judge_provider or defaults.judge_provider,
        judge_model=runtime_config.judge_model or defaults.judge_model,
        vision_provider=runtime_config.vision_provider or defaults.vision_provider,
        vision_model=runtime_config.vision_model or defaults.vision_model,
        openai_api_key=runtime_config.openai_api_key or defaults.openai_api_key,
        anthropic_api_key=runtime_config.anthropic_api_key or defaults.anthropic_api_key,
        openrouter_api_key=runtime_config.openrouter_api_key or defaults.openrouter_api_key,
        openrouter_base_url=runtime_config.openrouter_base_url or defaults.openrouter_base_url,
        ollama_base_url=runtime_config.ollama_base_url or defaults.ollama_base_url,
    )
