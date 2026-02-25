import json

from src.tools.pdf_image_tools import classify_diagram_flow


def test_classify_diagram_flow_uses_heuristic_when_model_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.tools.pdf_image_tools._load_vision_model", lambda runtime_config=None: None
    )
    evidence = classify_diagram_flow("/tmp/langgraph_visualization.png")

    assert evidence.goal == "Swarm Visual Flow Analysis"
    assert evidence.found is True
    payload = json.loads(evidence.content or "{}")
    assert payload.get("mode") == "heuristic"
    assert payload.get("has_required_flow") is True


def test_classify_diagram_flow_unknown_filename_defaults_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.tools.pdf_image_tools._load_vision_model", lambda runtime_config=None: None
    )
    evidence = classify_diagram_flow("/tmp/random_image.bin")

    assert evidence.found is False
    payload = json.loads(evidence.content or "{}")
    assert payload.get("classification") in {"unknown", "generic"}
