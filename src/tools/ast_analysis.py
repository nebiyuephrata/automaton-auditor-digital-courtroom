import ast
from pathlib import Path
from typing import Any, Dict, List


def parse_class_inheritance(py_file: str) -> Dict[str, List[str]]:
    source = Path(py_file).read_text(encoding="utf-8")
    tree = ast.parse(source)
    inheritance: Dict[str, List[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases: List[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            inheritance[node.name] = bases
    return inheritance


def detect_stategraph_instantiation(py_file: str) -> bool:
    source = Path(py_file).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "StateGraph":
                return True
    return False


def detect_graph_edge_patterns(py_file: str) -> Dict[str, Any]:
    source = Path(py_file).read_text(encoding="utf-8")
    tree = ast.parse(source)

    edges: list[tuple[str, str]] = []
    conditional_calls = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_edge" and len(node.args) >= 2:
                src = _extract_name(node.args[0])
                dst = _extract_name(node.args[1])
                edges.append((src, dst))
            elif node.func.attr == "add_conditional_edges":
                conditional_calls += 1

    outgoing: Dict[str, int] = {}
    incoming: Dict[str, int] = {}
    for src, dst in edges:
        outgoing[src] = outgoing.get(src, 0) + 1
        incoming[dst] = incoming.get(dst, 0) + 1

    fan_out_nodes = [node for node, count in outgoing.items() if count > 1]
    fan_in_nodes = [node for node, count in incoming.items() if count > 1]

    return {
        "edges": edges,
        "fan_out_nodes": fan_out_nodes,
        "fan_in_nodes": fan_in_nodes,
        "has_fan_out": len(fan_out_nodes) > 0,
        "has_fan_in": len(fan_in_nodes) > 0,
        "conditional_edges": conditional_calls,
    }


def _extract_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    return ast.dump(node)
