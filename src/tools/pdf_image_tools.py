import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Literal

from pypdf import PdfReader
from pydantic import BaseModel

from src.state import Evidence, RuntimeLLMConfig


def extract_images_from_pdf(path: str, output_dir: str) -> List[str]:
    reader = PdfReader(path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    extracted: List[str] = []
    image_index = 0
    for page in reader.pages:
        resources = page.get("/Resources")
        if not resources:
            continue
        x_object = resources.get("/XObject") if hasattr(resources, "get") else None
        if not x_object:
            continue

        x_object = x_object.get_object()
        for obj in x_object.values():
            obj_data = obj.get_object()
            if obj_data.get("/Subtype") == "/Image":
                ext = ".bin"
                filt = obj_data.get("/Filter")
                if filt == "/DCTDecode":
                    ext = ".jpg"
                elif filt == "/FlateDecode":
                    ext = ".png"

                image_path = output / f"image_{image_index}{ext}"
                image_path.write_bytes(obj_data.get_data())
                extracted.append(str(image_path))
                image_index += 1

    return extracted


def classify_diagram(image_path: str) -> Evidence:
    name = Path(image_path).name.lower()
    if "graph" in name or "langgraph" in name:
        classification = "stategraph"
        rationale = "Filename indicates graph/state machine visualization."
        confidence = 0.8
    elif "arch" in name:
        classification = "architecture_diagram"
        rationale = "Filename indicates architecture depiction."
        confidence = 0.75
    else:
        classification = "generic_diagram"
        rationale = "Could not confirm explicit StateGraph flow from filename only."
        confidence = 0.55

    return Evidence(
        goal="Swarm Visual Classification",
        found=True,
        content=classification,
        location=image_path,
        rationale=rationale,
        confidence=confidence,
    )


class DiagramFlowAssessment(BaseModel):
    classification: Literal["stategraph", "sequence", "generic", "unknown"]
    has_required_flow: bool
    rationale: str
    confidence: float


def classify_diagram_flow(
    image_path: str, runtime_config: RuntimeLLMConfig | None = None
) -> Evidence:
    model = _load_vision_model(runtime_config=runtime_config)
    if model is None:
        assessment = _heuristic_flow_assessment(image_path)
        return _assessment_to_evidence(image_path, assessment, "heuristic")

    prompt = (
        "Classify this diagram as one of: stategraph, sequence, generic, unknown. "
        "Then determine if it explicitly shows the required flow: "
        "Detectives (Parallel) -> Evidence Aggregation -> Judges (Parallel) -> Chief Justice."
    )
    try:
        assessment = _analyze_with_model(model, image_path, prompt)
        return _assessment_to_evidence(image_path, assessment, "multimodal")
    except Exception as exc:
        fallback = _heuristic_flow_assessment(image_path)
        fallback.rationale = (
            f"Multimodal analysis failed ({exc}); heuristic fallback used. {fallback.rationale}"
        )
        return _assessment_to_evidence(image_path, fallback, "fallback")


def analyze_pdf_diagrams(
    pdf_path: str, runtime_config: RuntimeLLMConfig | None = None
) -> List[Evidence]:
    try:
        with tempfile.TemporaryDirectory(prefix="vision-audit-") as tmp_dir:
            extracted = extract_images_from_pdf(pdf_path, tmp_dir)
            if not extracted:
                return [
                    Evidence(
                        goal="Swarm Visual Flow Analysis",
                        found=False,
                        content=None,
                        location=pdf_path,
                        rationale="No extractable images were found in the PDF for vision analysis.",
                        confidence=0.95,
                    )
                ]
            return [classify_diagram_flow(image_path, runtime_config) for image_path in extracted]
    except Exception as exc:
        return [
            Evidence(
                goal="Swarm Visual Flow Analysis",
                found=False,
                content=str(exc),
                location=pdf_path,
                rationale="Vision analysis failed while parsing or extracting PDF images.",
                confidence=1.0,
            )
        ]


def _load_vision_model(runtime_config: RuntimeLLMConfig | None = None) -> Any | None:
    runtime_config = runtime_config or RuntimeLLMConfig()
    provider = runtime_config.vision_provider.lower()
    model_name = runtime_config.vision_model

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            return None
        if not runtime_config.anthropic_api_key:
            return None
        return ChatAnthropic(
            model=model_name,
            temperature=0,
            api_key=runtime_config.anthropic_api_key,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            return None
        return ChatOllama(
            model=model_name,
            temperature=0,
            base_url=runtime_config.ollama_base_url or "http://localhost:11434",
        )

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None
    if not runtime_config.openai_api_key:
        return None
    return ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=runtime_config.openai_api_key,
    )


def _analyze_with_model(model: Any, image_path: str, prompt: str) -> DiagramFlowAssessment:
    structured = model.with_structured_output(DiagramFlowAssessment)
    image_url = Path(image_path).resolve().as_uri()
    message_payload = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]
    result = structured.invoke(message_payload)
    if isinstance(result, DiagramFlowAssessment):
        return result
    if isinstance(result, dict):
        return DiagramFlowAssessment.model_validate(result)
    raise ValueError("Invalid structured output from vision model.")


def _heuristic_flow_assessment(image_path: str) -> DiagramFlowAssessment:
    name = Path(image_path).name.lower()
    if "langgraph" in name or "state" in name:
        classification = "stategraph"
        has_required_flow = True
        rationale = "Filename suggests state graph diagram aligned to orchestration flow."
        confidence = 0.72
    elif "sequence" in name:
        classification = "sequence"
        has_required_flow = False
        rationale = "Sequence diagram does not prove required fan-out/fan-in architecture."
        confidence = 0.66
    elif "arch" in name or "diagram" in name:
        classification = "generic"
        has_required_flow = False
        rationale = "Generic architecture image naming lacks explicit parallel flow guarantees."
        confidence = 0.62
    else:
        classification = "unknown"
        has_required_flow = False
        rationale = "Unable to classify diagram type without multimodal model support."
        confidence = 0.5

    return DiagramFlowAssessment(
        classification=classification,
        has_required_flow=has_required_flow,
        rationale=rationale,
        confidence=confidence,
    )


def _assessment_to_evidence(
    image_path: str, assessment: DiagramFlowAssessment, mode: str
) -> Evidence:
    payload: Dict[str, object] = {
        "mode": mode,
        "classification": assessment.classification,
        "has_required_flow": assessment.has_required_flow,
    }
    return Evidence(
        goal="Swarm Visual Flow Analysis",
        found=assessment.has_required_flow,
        content=json.dumps(payload),
        location=image_path,
        rationale=assessment.rationale,
        confidence=max(0.0, min(1.0, assessment.confidence)),
    )
