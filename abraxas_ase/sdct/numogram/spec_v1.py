from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


# Working theory graph; update via spec versioning.


@dataclass(frozen=True)
class NumogramGraph:
    nodes: Tuple[str, ...]
    edges: Tuple[Tuple[str, str], ...]


def build_default_graph_v1() -> NumogramGraph:
    nodes = tuple(sorted(("a", "b", "c", "d", "e", "f", "g")))
    edges = tuple(sorted({
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("c", "d"),
        ("c", "e"),
        ("d", "f"),
        ("e", "f"),
        ("f", "g"),
        ("g", "a"),
    }))
    return NumogramGraph(nodes=nodes, edges=edges)


def _neighbors(graph: NumogramGraph) -> dict[str, set[str]]:
    neighbors: dict[str, set[str]] = {n: set() for n in graph.nodes}
    for a, b in graph.edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    return neighbors


def validate_graph(graph: NumogramGraph) -> None:
    node_set = set(graph.nodes)
    if len(node_set) != len(graph.nodes):
        raise ValueError("Duplicate nodes in graph.")
    for a, b in graph.edges:
        if a not in node_set or b not in node_set:
            raise ValueError("Edge references unknown node.")
        if a == b:
            raise ValueError("Self-loops are not allowed.")
    if len(set(graph.edges)) != len(graph.edges):
        raise ValueError("Duplicate edges in graph.")
    neighbors = _neighbors(graph)
    if any(len(neigh) == 0 for neigh in neighbors.values()):
        raise ValueError("Graph contains isolated nodes.")
    # connectivity check (undirected)
    start = graph.nodes[0] if graph.nodes else None
    if start is None:
        raise ValueError("Graph must contain nodes.")
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        stack.extend(sorted(neighbors[node]))
    if visited != node_set:
        raise ValueError("Graph is disconnected.")
