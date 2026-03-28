"""
Basic test cases 

"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dijkstra import dijkstra, reconstruct_path
from utils import haversine_distance, walking_time


def test_dijkstra_simple():
    """Test Dijkstra on a small hand-verified graph."""
    #
    #  A --5-- B --3-- C
    #  |               |
    #  2               1
    #  |               |
    #  D ------4------ E
    #
    graph = {
        "A": [("B", 5), ("D", 2)],
        "B": [("A", 5), ("C", 3)],
        "C": [("B", 3), ("E", 1)],
        "D": [("A", 2), ("E", 4)],
        "E": [("D", 4), ("C", 1)],
    }

    dist, prev = dijkstra(graph, "A")

    assert dist["A"] == 0, f"Distance to self should be 0, got {dist['A']}"
    assert dist["B"] == 5, f"A->B should be 5, got {dist['B']}"
    assert dist["D"] == 2, f"A->D should be 2, got {dist['D']}"
    assert dist["E"] == 6, f"A->D->E should be 6, got {dist['E']}"
    assert dist["C"] == 7, f"A->D->E->C should be 7, got {dist['C']}"

    print("  [PASS] test_dijkstra_simple")


def test_path_reconstruction():
    """Test that path reconstruction returns the correct route."""
    graph = {
        "A": [("B", 5), ("D", 2)],
        "B": [("A", 5), ("C", 3)],
        "C": [("B", 3), ("E", 1)],
        "D": [("A", 2), ("E", 4)],
        "E": [("D", 4), ("C", 1)],
    }

    dist, prev = dijkstra(graph, "A")
    path = reconstruct_path(prev, "A", "C")

    # Shortest path A->C is A->D->E->C (cost 7)
    assert path == ["A", "D", "E", "C"], f"Expected ['A','D','E','C'], got {path}"

    print("  [PASS] test_path_reconstruction")


def test_dijkstra_single_node():
    """Test Dijkstra with a single node graph."""
    graph = {"X": []}
    dist, prev = dijkstra(graph, "X")

    assert dist["X"] == 0
    assert prev["X"] is None

    print("  [PASS] test_dijkstra_single_node")


def test_haversine_distance():
    """Test distance calculation with known coordinates."""
    # San Jose to San Francisco is approximately 77 km
    dist = haversine_distance(37.3382, -121.8863, 37.7749, -122.4194)
    assert 60 < dist < 80, f"SJ to SF should be ~68km, got {dist:.1f}km"

    # Same point should be 0
    dist = haversine_distance(37.3382, -121.8863, 37.3382, -121.8863)
    assert dist == 0, f"Same point distance should be 0, got {dist}"

    print("  [PASS] test_haversine_distance")


def test_walking_time_calculation():
    """Test walking time is reasonable."""
    # Two points about 0.5 km apart -> should be about 7-8 min walking
    t = walking_time(37.3382, -121.8890, 37.3397, -121.8896)
    assert 1 < t < 15, f"Short walk should be 1-15 min, got {t:.1f}"

    print("  [PASS] test_walking_time_calculation")


if __name__ == "__main__":
    print("Running basic tests...\n")
    test_dijkstra_simple()
    test_path_reconstruction()
    test_dijkstra_single_node()
    test_haversine_distance()
    test_walking_time_calculation()
    print("\nAll basic tests passed!")
