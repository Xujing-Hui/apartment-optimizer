"""
tests for graph.py

Tests cover:
  - Correct node count after loading real data
  - Bidirectionality of all edges
  - Presence of walk-fallback edges for known nearby pairs
  - Absence of fallback edges for distant pairs
  - Apartment and destination nodes each connect to at least one station
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from graph import load_data, build_graph, graph_stats
from utils import WALK_FALLBACK_CAP_MIN


def test_node_count():
    """Graph must contain exactly 66 nodes (5 apts + 25 dests + 36 transit)."""
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)
    stats = graph_stats(G)
    assert stats["nodes"] == 66, (
        f"Expected 66 nodes, got {stats['nodes']}"
    )
    print(f"PASS  test_node_count  ({stats['nodes']} nodes)")


def test_edge_bidirectionality():
    """
    Every edge (u, v) must also appear as (v, u) with the same weight.
    Verifies the undirected invariant.
    """
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    violations = []
    for u, neighbours in G.items():
        for v, w in neighbours:
            reverse = [w2 for nb, w2 in G.get(v, []) if nb == u]
            if not reverse:
                violations.append(f"Missing reverse edge {v} → {u}")
            elif abs(reverse[0] - w) > 1e-6:
                violations.append(
                    f"Weight mismatch {u}↔{v}: forward={w}, reverse={reverse[0]}"
                )
    assert not violations, "\n".join(violations)
    print("PASS  test_edge_bidirectionality")


def test_walk_fallback_edges_present():
    """
    Known nearby pairs that SHOULD have a walk-fallback edge:
      - villas_on_the_blvd ↔ S2   (~4.6 min)
      - villas_on_the_blvd ↔ G2   (~4.6 min)
      - murphy_station     ↔ S1   (~6.1 min)
      - murphy_station     ↔ T1   (~6.7 min)
      - the_verdant        ↔ S4   (~1.7 min)
    """
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    expected = [
        ("villas_on_the_blvd", "S2"),
        ("villas_on_the_blvd", "G2"),
        ("murphy_station",     "S1"),
        ("murphy_station",     "T1"),
        ("the_verdant",        "S4"),
    ]
    for apt_id, dest_id in expected:
        neighbours = [nb for nb, _ in G.get(apt_id, [])]
        assert dest_id in neighbours, (
            f"Expected walk-fallback edge {apt_id} ↔ {dest_id} not found"
        )
    print(f"PASS  test_walk_fallback_edges_present  ({len(expected)} pairs)")


def test_walk_fallback_cap_respected():
    """
    No walk-fallback edge should have a weight exceeding WALK_FALLBACK_CAP_MIN.
    """
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    apt_ids  = {a["id"] for a in apartments}
    dest_ids = {d["id"] for d in destinations}

    violations = []
    for u, neighbours in G.items():
        if u not in apt_ids:
            continue
        for v, w in neighbours:
            if v in dest_ids and w > WALK_FALLBACK_CAP_MIN + 1e-6:
                violations.append(
                    f"Fallback edge {u}↔{v} weight={w} > cap={WALK_FALLBACK_CAP_MIN}"
                )
    assert not violations, "\n".join(violations)
    print(f"PASS  test_walk_fallback_cap_respected  (cap={WALK_FALLBACK_CAP_MIN} min)")


def test_apartments_connected_to_stations():
    """Each apartment must be directly connected to at least one transit station."""
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    station_ids = {s["id"] for s in stations}
    for apt in apartments:
        neighbours = [nb for nb, _ in G.get(apt["id"], [])]
        transit_nbs = [nb for nb in neighbours if nb in station_ids]
        assert transit_nbs, (
            f"Apartment {apt['id']} has no direct connection to any station"
        )
    print(f"PASS  test_apartments_connected_to_stations")


def test_destinations_connected_to_stations():
    """Each destination must be directly connected to at least one transit station."""
    apartments, destinations, stations, constraints, _ = load_data()
    G = build_graph(apartments, destinations, stations)

    station_ids = {s["id"] for s in stations}
    for dest in destinations:
        neighbours = [nb for nb, _ in G.get(dest["id"], [])]
        transit_nbs = [nb for nb in neighbours if nb in station_ids]
        assert transit_nbs, (
            f"Destination {dest['id']} has no direct connection to any station"
        )
    print(f"PASS  test_destinations_connected_to_stations")


# ── Run all tests ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_node_count,
        test_edge_bidirectionality,
        test_walk_fallback_edges_present,
        test_walk_fallback_cap_respected,
        test_apartments_connected_to_stations,
        test_destinations_connected_to_stations,
    ]
    print(f"Running {len(tests)} graph tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
