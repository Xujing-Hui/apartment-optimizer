"""Haversine straight-line walk minutes (80 m/min)."""

import unittest

import tests_v2._path  # noqa: F401
from Dijkstra.walk_estimate import (
    MAX_STRAIGHT_LINE_WALK_MINUTES,
    WALK_SPEED_M_PER_MIN,
    build_coord_map,
    haversine_km,
    straight_line_walk_minutes,
    walk_minutes_between_ids,
)


class TestWalkEstimate(unittest.TestCase):
    def test_zero_distance_zero_minutes(self):
        self.assertAlmostEqual(straight_line_walk_minutes(1.0, 2.0, 1.0, 2.0), 0.0, places=6)

    def test_one_km_is_1000_over_speed_minutes(self):
        # North: 1 degree latitude ~ 111 km; use tiny delta for ~1 km
        dlat = 1.0 / 111.0
        km = haversine_km(0.0, 0.0, dlat, 0.0)
        self.assertAlmostEqual(km, 1.0, delta=0.02)
        mins = straight_line_walk_minutes(0.0, 0.0, dlat, 0.0)
        self.assertAlmostEqual(mins, (km * 1000.0) / WALK_SPEED_M_PER_MIN, places=3)

    def test_build_coord_map_and_between_ids(self):
        apartments = [{"id": "A", "lat": 0.0, "lng": 0.0}]
        destinations = [{"id": "D", "lat": 0.0, "lng": 0.0}]
        m = build_coord_map(apartments, destinations)
        self.assertEqual(m["A"], (0.0, 0.0))
        self.assertAlmostEqual(walk_minutes_between_ids("A", "D", m), 0.0)
        self.assertEqual(walk_minutes_between_ids("A", "MISSING", m), float("inf"))

    def test_long_straight_line_capped_to_inf_by_default(self):
        apartments = [{"id": "A", "lat": 0.0, "lng": 0.0}]
        destinations = [{"id": "B", "lat": 5.0, "lng": 0.0}]
        m = build_coord_map(apartments, destinations)
        raw = straight_line_walk_minutes(0.0, 0.0, 5.0, 0.0)
        self.assertGreater(raw, MAX_STRAIGHT_LINE_WALK_MINUTES)
        self.assertEqual(walk_minutes_between_ids("A", "B", m), float("inf"))

    def test_cap_disabled_with_inf_max_minutes(self):
        apartments = [{"id": "A", "lat": 0.0, "lng": 0.0}]
        destinations = [{"id": "B", "lat": 5.0, "lng": 0.0}]
        m = build_coord_map(apartments, destinations)
        t = walk_minutes_between_ids("A", "B", m, max_minutes=float("inf"))
        self.assertLess(t, float("inf"))
        self.assertGreater(t, MAX_STRAIGHT_LINE_WALK_MINUTES)


if __name__ == "__main__":
    unittest.main()
