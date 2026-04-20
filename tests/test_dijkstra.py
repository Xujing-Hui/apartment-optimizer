"""
tests for dijkstra.py

Tests cover:
  - Source node has distance 0
  - Unreachable node returns infinity
  - Known hand-computed shortest paths on a small graph
  - Dijkstra and Bellman-Ford produce identical results on the real graph
  - Path reconstruction returns correct node sequence
  - Path from source to source is a single-node list
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dijkstra import dijkstra, bellman_ford, reconstruct_path
from graph    import load_data, build_graph


# ── Small hand-crafted graphs ─────────────────────────────────────────────────
SIMPLE_G = {
    "A": [("B", 2), ("C", 10)],
    "B": [("A", 2), ("C", 3),  ("D", 7)],
    "C": [("A", 10),("B", 3),  ("D", 1)],
    "D": [("B", 7), ("C", 1)],
}
# Correct answers (from source A):
#   A→A = 0,  A→B = 2,  A→C = 5,  A→D = 6

DISCONNECTED_G = {
    "X": [("Y", 4)],
    "Y": [("X", 4)],
    "Z": [],          # isolated node
}


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_source_distance_is_zero():
    """dist[source] must always equal 0."""
    for source in ["A", "B", "C", "D"]:
        dist, _ = dijkstra(SIMPLE_G, source)
        assert dist[source] == 0, f"dist[{source}] should be 0, got {dist[source]}"
    print("PASS  test_source_distance_is_zero")


def test_known_distances_simple_graph():
    """Verify Dijkstra against hand-computed distances on SIMPLE_G."""
    dist, _ = dijkstra(SIMPLE_G, "A")
    expected = {"A": 0, "B": 2, "C": 5, "D": 6}
    for node, exp_d in expected.items():
        assert dist[node] == exp_d, (
            f"A→{node}: expected {exp_d}, got {dist[node]}"
        )
    print("PASS  test_known_distances_simple_graph")


def test_unreachable_node_is_infinity():
    """An isolated node must have distance infinity."""
    dist, _ = dijkstra(DISCONNECTED_G, "X")
    assert dist.get("Z", float("inf")) == float("inf"), (
        "Isolated node Z should be unreachable (inf)"
    )
    print("PASS  test_unreachable_node_is_infinity")


def test_dijkstra_bellman_ford_agree():
    """
    On the real transit graph, Dijkstra and Bellman-Ford must produce
    identical distance values for every apartment as source.
    """
    apartments, destinations, stations, _, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    TOL = 1e-6
    for apt in apartments:
        d_dijk, _ = dijkstra(G, apt["id"])
        d_bf,   _ = bellman_ford(G, apt["id"])

        for node in d_dijk:
            dd = d_dijk.get(node, float("inf"))
            db = d_bf.get(node, float("inf"))
            assert abs(dd - db) < TOL, (
                f"Mismatch for source={apt['id']}, node={node}: "
                f"Dijkstra={dd}, BF={db}"
            )
    print("PASS  test_dijkstra_bellman_ford_agree  (5 apartments cross-validated)")


def test_path_reconstruction_correct():
    """Reconstructed path must start at source and end at target."""
    dist, prev = dijkstra(SIMPLE_G, "A")
    path = reconstruct_path(prev, "A", "D")
    assert path is not None,   "Path A→D should exist"
    assert path[0]  == "A",    "Path must start at A"
    assert path[-1] == "D",    "Path must end at D"
    # Verify path cost matches dist
    cost = sum(
        next(w for nb, w in SIMPLE_G[path[i]] if nb == path[i+1])
        for i in range(len(path)-1)
    )
    assert abs(cost - dist["D"]) < 1e-6, (
        f"Path cost {cost} should equal dist[D]={dist['D']}"
    )
    print(f"PASS  test_path_reconstruction_correct  (path={path}, cost={cost})")


def test_path_source_to_self():
    """Path from source to itself must be a single-element list."""
    dist, prev = dijkstra(SIMPLE_G, "A")
    path = reconstruct_path(prev, "A", "A")
    assert path == ["A"], f"Expected ['A'], got {path}"
    print("PASS  test_path_source_to_self")


def test_unreachable_path_is_none():
    """Reconstruct path to an unreachable node must return None."""
    dist, prev = dijkstra(DISCONNECTED_G, "X")
    path = reconstruct_path(prev, "X", "Z")
    assert path is None, f"Expected None for unreachable path, got {path}"
    print("PASS  test_unreachable_path_is_none")


def test_real_graph_neu_distances():
    """
    On the real graph, verify known NEU distances fall within
    plausible bounds (10–60 min from any apartment to NEU).
    """
    apartments, destinations, stations, _, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    for apt in apartments:
        dist, _ = dijkstra(G, apt["id"])
        neu_dist = dist.get("NEU_SV", float("inf"))
        assert 5 <= neu_dist <= 90, (
            f"{apt['name']} → NEU: {neu_dist} min out of expected range [5, 90]"
        )
    print("PASS  test_real_graph_neu_distances")


# ── Run all tests ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_source_distance_is_zero,
        test_known_distances_simple_graph,
        test_unreachable_node_is_infinity,
        test_dijkstra_bellman_ford_agree,
        test_path_reconstruction_correct,
        test_path_source_to_self,
        test_unreachable_path_is_none,
        test_real_graph_neu_distances,
    ]
    print(f"Running {len(tests)} Dijkstra tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
