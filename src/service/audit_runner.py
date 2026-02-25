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
    effective_runtime = runtime_config or RuntimeLLMConfig(
        judge_provider=settings.judge_provider,
        judge_model=settings.judge_model,
        vision_provider=settings.vision_provider,
        vision_model=settings.vision_model,
        openai_api_key=settings.openai_api_key or None,
        anthropic_api_key=settings.anthropic_api_key or None,
        ollama_base_url=settings.ollama_base_url or None,
    )
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
