"""Graph construction from minimal v2-shaped JSON."""

import json
import tempfile
import unittest
from pathlib import Path

import tests_v2._path  # noqa: F401 — repo root on sys.path
from Dijkstra.graph_builder import build_graph, load_json_records


class TestGraphBuilder(unittest.TestCase):
    def test_minimal_undirected_station_and_walks(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            apt_doc = {
                "apartments": [
                    {
                        "id": "A1",
                        "nearest_station_id": "S1",
                        "walk_min_to_station": 3,
                    }
                ]
            }
            stn_doc = {
                "stations": [
                    {
                        "id": "S1",
                        "neighbors": [{"id": "S2", "travel_min": 10, "mode": "bus"}],
                    },
                    {
                        "id": "S2",
                        "neighbors": [{"id": "S1", "travel_min": 10, "mode": "bus"}],
                    },
                ]
            }
            dest_doc = {
                "destinations": [
                    {
                        "id": "D1",
                        "nearest_station_id": "S2",
                        "walk_min_from_station": 2,
                    }
                ],
                "categories": {},
            }
            (td / "a.json").write_text(json.dumps(apt_doc), encoding="utf-8")
            (td / "s.json").write_text(json.dumps(stn_doc), encoding="utf-8")
            (td / "d.json").write_text(json.dumps(dest_doc), encoding="utf-8")

            apartments, stations, _ = load_json_records(td / "a.json", td / "s.json", td / "d.json")
            g = build_graph(apartments, stations, dest_doc["destinations"])

        # S1-S2 once (neighbor, weight, mode)
        def by_neighbor(edges):
            return {x[0]: (x[1], x[2]) for x in edges}

        s1n = by_neighbor(g["S1"])
        self.assertEqual(s1n["S2"], (10, "bus"))
        self.assertEqual(s1n["A1"], (3, "walk"))
        s2n = by_neighbor(g["S2"])
        self.assertEqual(s2n["S1"], (10, "bus"))
        self.assertEqual(s2n["D1"], (2, "walk"))
        d1n = by_neighbor(g["D1"])
        self.assertEqual(d1n["S2"], (2, "walk"))

    def test_unknown_station_raises(self):
        apartments = [{"id": "A1", "nearest_station_id": "MISSING", "walk_min_to_station": 1}]
        stations = [{"id": "S1", "neighbors": []}]
        destinations = []
        with self.assertRaises(ValueError) as ctx:
            build_graph(apartments, stations, destinations)
        self.assertIn("MISSING", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
