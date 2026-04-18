"""Chain objective: closest Starbucks to apt need not minimize apt→S + S→NEU."""

import unittest

import tests_v2._path  # noqa: F401 — sys.path
from Dijkstra.scoring import compute_apartment_scores, rank_apartments


def E(nb: str, w: float, m: str = "walk"):
    return (nb, w, m)


class TestChainScoring(unittest.TestCase):
    def test_chain_prefers_s2_not_closest_s1(self):
        # S1 is closer to APT but S1→NEU is long; S2 wins chain.
        # APT--1--H--1--S1 ; H--20--S2--1--NEU_SV ; H--100--NEU_SV
        graph = {
            "APT": [E("H", 1)],
            "H": [
                E("APT", 1),
                E("S1", 1),
                E("S2", 20),
                E("NEU_SV", 100),
                E("C1", 0),
                E("T1", 0),
                E("G1", 0),
            ],
            "S1": [E("H", 1)],
            "S2": [E("H", 20), E("NEU_SV", 1, "bus")],
            "NEU_SV": [E("H", 100), E("S2", 1, "bus")],
            "C1": [E("H", 0)],
            "T1": [E("H", 0)],
            "G1": [E("H", 0)],
        }

        # Distinct coords so Haversine legs are huge vs graph; min = transit (not zero NEU-to-S walk).
        apartments = [{"id": "APT", "name": "Test", "lat": 10.0, "lng": -120.0}]
        destinations = [
            {"id": "NEU_SV", "name": "NEU", "lat": 11.0, "lng": -119.0},
            {"id": "S1", "name": "SB1", "lat": 12.0, "lng": -118.0},
            {"id": "S2", "name": "SB2", "lat": 13.0, "lng": -117.0},
            {"id": "C1", "name": "C", "lat": 50.0, "lng": -60.0},
            {"id": "T1", "name": "T", "lat": 50.0, "lng": -60.0},
            {"id": "G1", "name": "G", "lat": 50.0, "lng": -60.0},
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
        self.assertEqual(len(raw), 1)
        r = raw[0]
        ch = r["categories"]["starbucks_neu_chain"]
        # dist APT→S1 = 2, NEU→S1 = 101 → chain 103
        # dist APT→S2 = 21, NEU→S2 = 1 → chain 22
        self.assertEqual(ch["optimal_starbucks_id"], "S2")
        self.assertAlmostEqual(ch["one_trip_minutes"], 22.0)
        self.assertAlmostEqual(ch["weekly_weighted_minutes"], 66.0)
        self.assertTrue(ch["path_apartment_to_optimal_starbucks_legs"])
        self.assertTrue(ch["path_optimal_starbucks_to_neu_legs"])
        ranked = rank_apartments(raw)
        self.assertEqual(ranked[0]["apartment_id"], "APT")


if __name__ == "__main__":
    unittest.main()
