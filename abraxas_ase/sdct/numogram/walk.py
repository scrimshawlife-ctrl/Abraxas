from __future__ import annotations

import hashlib
from typing import List

from .spec_v1 import NumogramGraph


def _sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _seed_bytes(event_key: str, date: str, signature: str) -> bytes:
    payload = f"{event_key}|{date}|{signature}".encode("utf-8")
    return _sha256_bytes(payload)


def walk(graph: NumogramGraph, event_key: str, date: str, signature: str, steps: int = 24) -> List[str]:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    nodes = list(graph.nodes)
    if not nodes:
        raise ValueError("graph must contain nodes")
    neighbors = {n: [] for n in nodes}
    for a, b in graph.edges:
        neighbors[a].append(b)
        neighbors[b].append(a)
    for node in neighbors:
        neighbors[node] = sorted(neighbors[node])
        if not neighbors[node]:
            raise ValueError("graph contains isolated node")

    digest = _seed_bytes(event_key, date, signature)
    idx = 0
    start_idx = digest[0] % len(nodes)
    current = nodes[start_idx]
    path = [current]
    for _ in range(steps - 1):
        neigh = neighbors[current]
        if idx >= len(digest):
            digest = _sha256_bytes(digest)
            idx = 0
        pick = digest[idx] % len(neigh)
        idx += 1
        current = neigh[pick]
        path.append(current)
    return path
