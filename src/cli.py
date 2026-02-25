import argparse
import json
from pathlib import Path

from src.config.logging_config import configure_logging
from src.service.audit_runner import run_audit


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
    result = run_audit(
        repo_url=args.repo_url,
        pdf_path=args.pdf_path,
        rubric_path=args.rubric_path,
        output_path=args.output,
    )
    rendered = result.get("rendered_markdown", "")

    if "final_report" in result:
        output = Path(args.output)
        json_path = output.with_suffix(".json")
        json_path.write_text(json.dumps(result["final_report"], indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
