import json
from pathlib import Path
from typing import Any, Dict, List


def load_rubric(path: str = "rubric.json") -> Dict[str, Any]:
    rubric_path = Path(path)
    with rubric_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rubric_dimensions(path: str = "rubric.json") -> List[Dict[str, Any]]:
    return load_rubric(path).get("dimensions", [])
