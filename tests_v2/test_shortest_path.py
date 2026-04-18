"""Dijkstra correctness on hand-verified graphs."""

import unittest

import tests_v2._path  # noqa: F401 — repo root on sys.path
from Dijkstra.shortest_path import dijkstra, lookup_edge, path_leg_breakdown, reconstruct_path


def _e(nb: str, w: float, m: str = "edge") -> tuple:
    """Neighbor id, weight, mode."""
    return (nb, w, m)


class TestDijkstra(unittest.TestCase):
    def test_triangle(self):
        # A --5-- B --3-- C
        # |               |
        # 2               1
        # |               |
        # D ------4------ E
        graph = {
            "A": [_e("B", 5), _e("D", 2)],
            "B": [_e("A", 5), _e("C", 3)],
            "C": [_e("B", 3), _e("E", 1)],
            "D": [_e("A", 2), _e("E", 4)],
            "E": [_e("D", 4), _e("C", 1)],
        }
        dist, prev = dijkstra(graph, "A")
        self.assertEqual(dist["A"], 0)
        self.assertEqual(dist["B"], 5)
        self.assertEqual(dist["D"], 2)
        self.assertEqual(dist["E"], 6)
        self.assertEqual(dist["C"], 7)
        self.assertEqual(reconstruct_path(prev, "A", "C"), ["A", "D", "E", "C"])

    def test_single_node(self):
        graph = {"X": []}
        dist, prev = dijkstra(graph, "X")
        self.assertEqual(dist["X"], 0)
        self.assertIsNone(prev["X"])

    def test_zero_weight_edge(self):
        graph = {
            "A": [_e("B", 0)],
            "B": [_e("A", 0), _e("C", 5)],
            "C": [_e("B", 5)],
        }
        dist, _ = dijkstra(graph, "A")
        self.assertEqual(dist["C"], 5)

    def test_lookup_edge_and_path_legs(self):
        graph = {
            "A": [("B", 4.0, "bus")],
            "B": [("A", 4.0, "bus"), ("C", 3.0, "caltrain")],
            "C": [("B", 3.0, "caltrain")],
        }
        self.assertEqual(lookup_edge(graph, "A", "B"), (4.0, "bus"))
        self.assertIsNone(lookup_edge(graph, "A", "C"))
        legs = path_leg_breakdown(graph, ["A", "B", "C"])
        self.assertEqual(len(legs), 2)
        self.assertEqual(legs[0]["mode"], "bus")
        self.assertEqual(legs[1]["mode"], "caltrain")
        self.assertEqual(legs[0]["minutes"], 4.0)
        self.assertEqual(legs[1]["minutes"], 3.0)


if __name__ == "__main__":
    unittest.main()
