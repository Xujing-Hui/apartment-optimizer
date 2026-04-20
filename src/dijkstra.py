"""
dijkstra.py
-----------
Shortest-path algorithms used by the Apartment Commute Optimizer.

Exports
-------
dijkstra(G, source)
    Single-source shortest paths using a binary min-heap.
    Time complexity  : O((V + E) log V)
    Space complexity : O(V)

bellman_ford(G, source)
    Single-source shortest paths using edge relaxation.
    Time complexity  : O(V × E)
    Space complexity : O(V)
    Used for: correctness verification against Dijkstra results.

reconstruct_path(prev, source, target)
    Trace the predecessor map to recover the actual shortest path.

Why Dijkstra over Bellman-Ford?
-------------------------------
All edge weights in our transit graph are non-negative (travel times
cannot be negative), so Dijkstra with a min-heap is both correct and
significantly faster than Bellman-Ford for this problem.
Bellman-Ford is retained solely as a cross-validation tool.
"""

import heapq
from typing import Optional


# ── Dijkstra (primary algorithm) ─────────────────────────────────────────────
def dijkstra(G: dict, source: str) -> tuple[dict, dict]:
    """
    Compute single-source shortest paths from *source* using Dijkstra's
    algorithm with a binary min-heap priority queue.

    Algorithm steps
    ---------------
    1. Initialise dist[v] = ∞ for all v; dist[source] = 0.
    2. Push (0, source) onto a min-heap.
    3. While the heap is non-empty:
         a. Pop (d, u) — the node with the smallest tentative distance.
         b. Skip u if already visited (lazy-deletion pattern).
         c. Mark u as visited.
         d. For each neighbour v of u with edge weight w:
              if d + w < dist[v]:
                  update dist[v] and prev[v], push (dist[v], v).
    4. Return dist and prev maps.

    Time complexity  : O((V + E) log V)  — V nodes, E edges
    Space complexity : O(V)

    Parameters
    ----------
    G      : adjacency list  {node_id: [(neighbour_id, weight), …]}
    source : starting node id

    Returns
    -------
    dist : dict[str, float]   shortest distance from source to every node
    prev : dict[str, str|None] predecessor map for path reconstruction
    """
    # Initialise
    dist: dict = {node: float("inf") for node in G}
    prev: dict = {node: None for node in G}
    dist[source] = 0.0

    # Min-heap entries: (distance, node_id)
    heap: list = [(0.0, source)]
    visited: set = set()

    while heap:
        d, u = heapq.heappop(heap)

        # Lazy deletion: skip stale entries
        if u in visited:
            continue
        visited.add(u)

        for v, w in G.get(u, []):
            # Ensure v is tracked even if it was not pre-seeded
            if v not in dist:
                dist[v] = float("inf")
                prev[v] = None

            relaxed = d + w
            if relaxed < dist[v]:
                dist[v] = relaxed
                prev[v] = u
                heapq.heappush(heap, (relaxed, v))

    return dist, prev


# ── Bellman-Ford (verification only) ─────────────────────────────────────────
def bellman_ford(G: dict, source: str) -> tuple[dict, dict]:
    """
    Compute single-source shortest paths using the Bellman-Ford algorithm.

    This implementation is used exclusively to cross-validate Dijkstra
    results.  It is considerably slower (O(V × E)) but handles negative
    edge weights and detects negative cycles.

    Algorithm steps
    ---------------
    1. Initialise dist[v] = ∞ for all v; dist[source] = 0.
    2. Repeat (|V| − 1) times:
         For every edge (u, v, w) in E:
             if dist[u] + w < dist[v]: relax.
    3. (Optional) Check for negative cycles — not present in our graph.

    Time complexity  : O(V × E)
    Space complexity : O(V)

    Parameters
    ----------
    G      : adjacency list  {node_id: [(neighbour_id, weight), …]}
    source : starting node id

    Returns
    -------
    dist : dict[str, float]
    prev : dict[str, str|None]
    """
    dist: dict = {node: float("inf") for node in G}
    prev: dict = {node: None for node in G}
    dist[source] = 0.0

    nodes = list(G.keys())
    V = len(nodes)

    # Build flat edge list for repeated relaxation
    edges: list[tuple[str, str, float]] = []
    for u, neighbours in G.items():
        for v, w in neighbours:
            edges.append((u, v, w))

    # Relax all edges V-1 times
    for _ in range(V - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] != float("inf") and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                updated = True
        # Early exit if no update occurred
        if not updated:
            break

    return dist, prev


# ── Path reconstruction ───────────────────────────────────────────────────────
def reconstruct_path(prev: dict, source: str,
                     target: str) -> Optional[list[str]]:
    """
    Trace the predecessor map *prev* to recover the shortest path
    from *source* to *target*.

    Parameters
    ----------
    prev   : predecessor map returned by dijkstra() or bellman_ford()
    source : start node id
    target : end node id

    Returns
    -------
    list[str]  if a path exists  (includes both source and target)
    None       if target is unreachable from source
    """
    path: list[str] = []
    current = target

    while current is not None:
        path.append(current)
        current = prev.get(current)

    path.reverse()

    # Validate: path must start at source
    if not path or path[0] != source:
        return None
    return path


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Small hand-crafted graph for unit testing
    # A -2-> B -3-> C   A -10-> C
    test_G = {
        "A": [("B", 2), ("C", 10)],
        "B": [("A", 2), ("C", 3)],
        "C": [("B", 3), ("A", 10)],
    }

    d_dijk, p_dijk = dijkstra(test_G, "A")
    d_bf,   p_bf   = bellman_ford(test_G, "A")

    print("=== Dijkstra results ===")
    for node, dist in sorted(d_dijk.items()):
        path = reconstruct_path(p_dijk, "A", node)
        print(f"  A → {node} : {dist}  path={path}")

    print("\n=== Bellman-Ford results ===")
    for node, dist in sorted(d_bf.items()):
        print(f"  A → {node} : {dist}")

    # Cross-validate
    assert d_dijk == d_bf, "Dijkstra and Bellman-Ford disagree!"
    print("\nCross-validation passed: Dijkstra == Bellman-Ford")

    # Known correct values for test graph
    assert d_dijk["A"] == 0,  "dist A→A should be 0"
    assert d_dijk["B"] == 2,  "dist A→B should be 2"
    assert d_dijk["C"] == 5,  "dist A→C should be 5"
    print("All assertions passed.")
