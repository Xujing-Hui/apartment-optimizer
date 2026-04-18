"""Dijkstra shortest paths (min-heap). Non-negative edge weights only."""

import heapq
from typing import Any, Dict, List, Optional, Tuple

# Adjacency: list of (neighbor_id, weight, mode)
Graph = Dict[str, List[Tuple[str, float, str]]]


def dijkstra(graph: Graph, source: str):
    """Shortest paths from source to all nodes.

    Args:
        graph: dict[node_id, list[tuple[neighbor_id, weight, mode]]]
        source: starting node ID

    Returns:
        dist: dict node -> shortest distance (inf if unreachable)
        prev: dict node -> previous node on shortest path from source
    """
    dist = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    heap = [(0, source)]
    visited = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, w, _mode in graph.get(u, []):
            if v in visited:
                continue
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    return dist, prev


def reconstruct_path(prev: Dict[str, Any], source: str, target: str) -> List[str]:
    """Shortest path source -> target as list of node ids, or [] if unreachable."""
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        if cur == source:
            break
        cur = prev.get(cur)
    else:
        return []
    path.reverse()
    return path


def lookup_edge(graph: Graph, u: str, v: str) -> Optional[Tuple[float, str]]:
    """Return (weight, mode) for edge u→v, or None if absent."""
    for nb, w, mode in graph.get(u, []):
        if nb == v:
            return (w, mode)
    return None


def path_leg_breakdown(graph: Graph, path: List[str]) -> List[Dict[str, Any]]:
    """Per consecutive pair on path: from, to, minutes, mode."""
    legs: List[Dict[str, Any]] = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        meta = lookup_edge(graph, a, b)
        if meta is None:
            legs.append(
                {
                    "from": a,
                    "to": b,
                    "minutes": None,
                    "mode": "unknown",
                }
            )
        else:
            w, mode = meta
            legs.append(
                {
                    "from": a,
                    "to": b,
                    "minutes": w,
                    "mode": mode,
                }
            )
    return legs
