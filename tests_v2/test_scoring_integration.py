"""Full pipeline on repository Data/*_v2.json."""

import json
import unittest
from pathlib import Path

import tests_v2._path  # noqa: F401
from Dijkstra.graph_builder import build_graph, load_json_records
from Dijkstra.report import build_scores_document, format_ranking_report
from Dijkstra.scoring import graph_edge_stats, rank_apartments, run_full_pipeline


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (DATA / "apartments_json_v2.json").exists():
            raise unittest.SkipTest("Data files missing")

    def test_five_apartments_finite_scores(self):
        apartments, stations, dest_doc = load_json_records(
            DATA / "apartments_json_v2.json",
            DATA / "stations_json_v2.json",
            DATA / "destinations_json_v2.json",
        )
        self.assertEqual(len(apartments), 5)
        graph, ranked = run_full_pipeline(apartments, stations, dest_doc)
        self.assertEqual(len(ranked), 5)
        nodes, edges = graph_edge_stats(graph)
        self.assertEqual(nodes, 5 + len(stations) + len(dest_doc["destinations"]))
        for r in ranked:
            self.assertNotEqual(r["total_minutes_per_week"], float("inf"), msg=r["apartment_id"])
            for cat in ("starbucks_neu_chain", "costco", "trader_joes", "gym_24hf"):
                self.assertTrue(
                    r["categories"][cat]["reachable"],
                    msg=f"{r['apartment_id']} {cat}",
                )

    def test_json_report_roundtrip(self):
        apartments, stations, dest_doc = load_json_records(
            DATA / "apartments_json_v2.json",
            DATA / "stations_json_v2.json",
            DATA / "destinations_json_v2.json",
        )
        graph, ranked = run_full_pipeline(apartments, stations, dest_doc)
        nodes, edges = graph_edge_stats(graph)
        doc = build_scores_document(
            ranked,
            nodes=nodes,
            undirected_edges=edges,
            data_paths={"apartments": "x", "stations": "y", "destinations": "z"},
        )
        s = json.dumps(doc)
        back = json.loads(s)
        self.assertIn("rankings", back)
        self.assertEqual(len(back["rankings"]), 5)
        self.assertIn("metadata", back)
        self.assertIn("total_minutes_per_week", back["rankings"][0])
        c0 = back["rankings"][0]["categories"]["costco"]
        self.assertIn("one_way_minutes_transit", c0)
        self.assertIn("walk_straight_line_minutes", c0["candidates_minutes"][0])
        self.assertIn("path_apartment_to_best_legs", c0)
        self.assertTrue(ranked[0]["categories"]["starbucks_neu_chain"]["path_apartment_to_optimal_starbucks_legs"])

    def test_stable_sort_tiebreak(self):
        # Same total → lexicographic apartment_id
        fake = [
            {"apartment_id": "b", "total_minutes_per_week": 100.0, "categories": {}},
            {"apartment_id": "a", "total_minutes_per_week": 100.0, "categories": {}},
        ]
        out = rank_apartments(fake)
        self.assertEqual([x["apartment_id"] for x in out], ["a", "b"])

    def test_report_text_non_empty(self):
        apartments, stations, dest_doc = load_json_records(
            DATA / "apartments_json_v2.json",
            DATA / "stations_json_v2.json",
            DATA / "destinations_json_v2.json",
        )
        _, ranked = run_full_pipeline(apartments, stations, dest_doc)
        graph = build_graph(apartments, stations, dest_doc["destinations"])
        nodes, edges = graph_edge_stats(graph)
        text = format_ranking_report(ranked, nodes=nodes, undirected_edges=edges)
        self.assertIn("TRANSIT-WEIGHTED", text)
        self.assertIn("Starbucks", text)
        self.assertIn("Executive summary", text)
        self.assertIn("Haversine", text)


if __name__ == "__main__":
    unittest.main()
