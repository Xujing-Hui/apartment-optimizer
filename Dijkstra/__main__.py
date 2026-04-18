
import argparse
from pathlib import Path

from Dijkstra.graph_builder import load_json_records
from Dijkstra.report import (
    build_scores_document,
    format_ranking_report,
    write_ranking_report,
    write_scores_json,
)
from Dijkstra.scoring import graph_edge_stats, run_full_pipeline


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> None:
    root = _default_repo_root()
    p = argparse.ArgumentParser(description="Transit-weighted apartment scoring (Dijkstra v2)")
    p.add_argument(
        "--apartments",
        type=Path,
        default=root / "Data" / "apartments_json_v2.json",
    )
    p.add_argument(
        "--stations",
        type=Path,
        default=root / "Data" / "stations_json_v2.json",
    )
    p.add_argument(
        "--destinations",
        type=Path,
        default=root / "Data" / "destinations_json_v2.json",
    )
    p.add_argument("--out-dir", type=Path, default=root / "results_v2")
    args = p.parse_args()

    apartments, stations, dest_doc = load_json_records(
        args.apartments,
        args.stations,
        args.destinations,
    )

    graph, ranked = run_full_pipeline(apartments, stations, dest_doc)
    nodes, edges = graph_edge_stats(graph)

    data_paths = {
        "apartments": str(args.apartments.resolve()),
        "stations": str(args.stations.resolve()),
        "destinations": str(args.destinations.resolve()),
    }
    doc = build_scores_document(
        ranked,
        nodes=nodes,
        undirected_edges=edges,
        data_paths=data_paths,
    )
    out_dir = args.out_dir
    write_scores_json(out_dir / "scores.json", doc)
    report_text = format_ranking_report(ranked, nodes=nodes, undirected_edges=edges)
    write_ranking_report(out_dir / "ranking_report.txt", report_text)
    print(report_text)


if __name__ == "__main__":
    main()
