from src.tools.ast_analysis import detect_graph_edge_patterns


def test_detectives_fanout_and_aggregation_fanin_are_wired() -> None:
    patterns = detect_graph_edge_patterns("src/graph.py")
    edges = set(patterns["edges"])

    assert ("__start__", "repo_investigator") in edges or ("START", "repo_investigator") in edges
    assert ("__start__", "doc_analyst") in edges or ("START", "doc_analyst") in edges
    assert ("__start__", "vision_inspector") in edges or ("START", "vision_inspector") in edges

    assert ("repo_investigator", "evidence_aggregator") in edges
    assert ("doc_analyst", "evidence_aggregator") in edges
    assert ("vision_inspector", "evidence_aggregator") in edges

    assert patterns["has_fan_out"] is True
    assert patterns["has_fan_in"] is True
    assert patterns["conditional_edges"] >= 1
