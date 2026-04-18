"""Straight-line walk beats transit when apartment and destination coincide."""

import unittest

import tests_v2._path  # noqa: F401
from Dijkstra.scoring import compute_apartment_scores


def E(nb: str, w: float, m: str = "walk"):
    return (nb, w, m)


class TestWalkShortcut(unittest.TestCase):
    def test_same_coords_zero_walk_beats_transit(self):
        graph = {
            "APT": [E("HUB", 100, "bus")],
            "HUB": [E("APT", 100, "bus"), E("C1", 100, "bus")],
            "C1": [E("HUB", 100, "bus")],
            "NEU_SV": [E("HUB", 1)],
            "S1": [E("HUB", 1)],
            "S2": [E("HUB", 1)],
            "T1": [E("HUB", 1)],
            "G1": [E("HUB", 1)],
        }
        same = {"lat": 37.0, "lng": -122.0}
        apartments = [{"id": "APT", "name": "A", **same}]
        destinations = [
            {"id": "NEU_SV", "name": "NEU", **same},
            {"id": "S1", "name": "S1", **same},
            {"id": "S2", "name": "S2", **same},
            {"id": "C1", "name": "C", **same},
            {"id": "T1", "name": "T", **same},
            {"id": "G1", "name": "G", **same},
        ]
        categories = {
            "starbucks_neu_chain": {
                "weekly_visits": 3,
                "candidates": ["S1", "S2"],
                "chain_endpoint": "NEU_SV",
            },
            "costco": {"weekly_visits": 1, "candidates": ["C1"]},
            "trader_joes": {"weekly_visits": 2, "candidates": ["T1"]},
            "gym_24hf": {"weekly_visits": 4, "candidates": ["G1"]},
        }
        raw = compute_apartment_scores(graph, apartments, destinations, categories)
        r = raw[0]
        costco = r["categories"]["costco"]
        self.assertEqual(costco["best_candidate_id"], "C1")
        self.assertAlmostEqual(costco["one_way_minutes"], 0.0, places=5)
        self.assertTrue(costco["used_straight_line_walk"])
        self.assertEqual(len(costco["path_apartment_to_best_legs"]), 1)
        self.assertEqual(costco["path_apartment_to_best_legs"][0]["mode"], "straight_line_walk")
        ch = r["categories"]["starbucks_neu_chain"]
        self.assertAlmostEqual(ch["one_trip_minutes"], 0.0, places=5)
        self.assertEqual(ch["optimal_leg1_mode"], "straight_line_walk")
        self.assertEqual(ch["optimal_leg2_mode"], "straight_line_walk")


if __name__ == "__main__":
    unittest.main()
