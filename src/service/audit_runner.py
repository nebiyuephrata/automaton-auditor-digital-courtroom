from pathlib import Path
from typing import Any, Dict

from src.config.settings import apply_runtime_settings, load_settings
from src.graph import create_graph
from src.utils.rubric_loader import rubric_dimensions


def run_audit(
    repo_url: str,
    pdf_path: str,
    rubric_path: str = "rubric.json",
    output_path: str | None = None,
) -> Dict[str, Any]:
    apply_runtime_settings(load_settings())

    app = create_graph()
    state = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": rubric_dimensions(rubric_path),
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
