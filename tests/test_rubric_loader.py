from src.utils.rubric_loader import (
    DEFAULT_RUBRIC_PRESET,
    list_rubric_presets,
    resolve_rubric_path,
    rubric_dimensions,
)


def test_list_rubric_presets_contains_default() -> None:
    presets = list_rubric_presets()
    preset_ids = {preset["id"] for preset in presets}
    assert DEFAULT_RUBRIC_PRESET in preset_ids


def test_resolve_rubric_path_uses_preset_when_path_missing() -> None:
    resolved = resolve_rubric_path(rubric_path="missing_rubric.json", rubric_preset=DEFAULT_RUBRIC_PRESET)
    assert resolved.endswith(f"{DEFAULT_RUBRIC_PRESET}.json")


def test_rubric_dimensions_load_from_preset() -> None:
    dimensions = rubric_dimensions(rubric_path="missing_rubric.json", rubric_preset=DEFAULT_RUBRIC_PRESET)
    assert len(dimensions) > 0
    assert all("id" in dim for dim in dimensions)
