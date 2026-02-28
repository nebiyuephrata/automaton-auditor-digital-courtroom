import argparse
import json
from pathlib import Path

from src.config.logging_config import configure_logging
from src.service.audit_runner import run_audit
from src.state import RuntimeLLMConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Automaton Auditor Digital Courtroom")
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--rubric-path", default="rubric.json")
    parser.add_argument("--rubric-preset", default=None)
    parser.add_argument("--judge-provider", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--vision-provider", default=None)
    parser.add_argument("--vision-model", default=None)
    parser.add_argument("--openai-api-key", default=None)
    parser.add_argument("--anthropic-api-key", default=None)
    parser.add_argument("--openrouter-api-key", default=None)
    parser.add_argument("--openrouter-base-url", default=None)
    parser.add_argument("--ollama-base-url", default=None)
    parser.add_argument(
        "--output",
        default="audit/report_onself_generated/final_audit_report.md",
    )
    args = parser.parse_args()

    configure_logging()
    runtime_config = None
    if any(
        [
            args.judge_provider,
            args.judge_model,
            args.vision_provider,
            args.vision_model,
            args.openai_api_key,
            args.anthropic_api_key,
            args.openrouter_api_key,
            args.openrouter_base_url,
            args.ollama_base_url,
        ]
    ):
        runtime_config = RuntimeLLMConfig(
            judge_provider=args.judge_provider or "openai",
            judge_model=args.judge_model or "gpt-4o-mini",
            vision_provider=args.vision_provider or "openai",
            vision_model=args.vision_model or "gpt-4o-mini",
            openai_api_key=args.openai_api_key,
            anthropic_api_key=args.anthropic_api_key,
            openrouter_api_key=args.openrouter_api_key,
            openrouter_base_url=args.openrouter_base_url,
            ollama_base_url=args.ollama_base_url,
        )
    result = run_audit(
        repo_url=args.repo_url,
        pdf_path=args.pdf_path,
        rubric_path=args.rubric_path,
        rubric_preset=args.rubric_preset,
        runtime_config=runtime_config,
        output_path=args.output,
    )
    rendered = result.get("rendered_markdown", "")

    if "final_report" in result:
        output = Path(args.output)
        json_path = output.with_suffix(".json")
        json_path.write_text(json.dumps(result["final_report"], indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
