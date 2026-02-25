from typing import Dict, List


def build_targeted_context(rubric_dimensions: List[Dict], target_artifact: str) -> List[Dict]:
    return [
        dimension
        for dimension in rubric_dimensions
        if dimension.get("target_artifact") in {target_artifact, "all"}
    ]
