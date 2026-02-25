import argparse
import json
from pathlib import Path

from src.config.logging_config import configure_logging
from src.config.settings import apply_runtime_settings, load_settings
from src.graph import create_graph
from src.utils.rubric_loader import rubric_dimensions


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Automaton Auditor Digital Courtroom")
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--rubric-path", default="rubric.json")
    parser.add_argument(
        "--output",
        default="audit/report_onself_generated/final_audit_report.md",
    )
    args = parser.parse_args()

    configure_logging()
    apply_runtime_settings(load_settings())

    app = create_graph()
    state = {
        "repo_url": args.repo_url,
        "pdf_path": args.pdf_path,
        "rubric_dimensions": rubric_dimensions(args.rubric_path),
        "evidences": {},
        "opinions": [],
        "errors": [],
    }

    result = app.invoke(state)
    rendered = result.get("rendered_markdown", "")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")

    if "final_report" in result:
        json_path = output.with_suffix(".json")
        json_path.write_text(result["final_report"].model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
