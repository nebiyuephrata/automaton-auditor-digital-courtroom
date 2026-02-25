from src.tools.ast_analysis import (
    detect_graph_edge_patterns,
    detect_stategraph_instantiation,
    parse_class_inheritance,
)


def test_state_file_declares_pydantic_and_typeddict() -> None:
    inheritance = parse_class_inheritance("src/state.py")
    base_sets = list(inheritance.values())
    assert any("BaseModel" in bases for bases in base_sets)
    assert any("TypedDict" in bases for bases in base_sets)


def test_graph_contains_stategraph_and_parallel_patterns() -> None:
    assert detect_stategraph_instantiation("src/graph.py") is True
    patterns = detect_graph_edge_patterns("src/graph.py")
    assert patterns["has_fan_out"] is True
    assert patterns["has_fan_in"] is True
    assert patterns["conditional_edges"] >= 1
    edges = set(patterns["edges"])
    assert ("judge_dispatch", "prosecutor") in edges
    assert ("judge_dispatch", "defense") in edges
    assert ("judge_dispatch", "techlead") in edges
