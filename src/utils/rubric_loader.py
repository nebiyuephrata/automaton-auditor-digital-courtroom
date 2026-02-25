import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_RUBRIC_PRESET = "industry_iso_soc2"
PRESET_DIR = Path("rubrics/defaults")


def load_rubric(path: str) -> Dict[str, Any]:
    rubric_path = Path(path)
    with rubric_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_rubric_presets() -> List[Dict[str, Any]]:
    presets: List[Dict[str, Any]] = []
    if not PRESET_DIR.exists():
        return presets

    for path in sorted(PRESET_DIR.glob("*.json")):
        payload = load_rubric(str(path))
        meta = payload.get("rubric_metadata", {})
        presets.append(
            {
                "id": path.stem,
                "name": meta.get("name", path.stem),
                "description": meta.get("description", ""),
                "path": str(path),
                "framework": meta.get("framework", "general"),
                "standard": meta.get("standard", "custom"),
            }
        )
    return presets


def resolve_rubric_path(
    rubric_path: str | None = None, rubric_preset: str | None = None
) -> str:
    if rubric_path and Path(rubric_path).exists():
        return rubric_path

    preset_id = rubric_preset or DEFAULT_RUBRIC_PRESET
    preset_path = PRESET_DIR / f"{preset_id}.json"
    if preset_path.exists():
        return str(preset_path)

    if rubric_path:
        return rubric_path
    return "rubric.json"


def rubric_dimensions(
    rubric_path: str | None = None, rubric_preset: str | None = None
) -> List[Dict[str, Any]]:
    resolved = resolve_rubric_path(rubric_path=rubric_path, rubric_preset=rubric_preset)
    return load_rubric(resolved).get("dimensions", [])
