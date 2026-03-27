import sys, os, time
# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import load_data, build_graph
from dijkstra import dijkstra, reconstruct_path, bellman_ford
from utils import walking_time

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
RENT_BUDGET = 1700
MAX_WALK_TO_STATION = 15

def filter_apartments(apartments, stations, budget, max_walk):
    """Filter apartments by rent and transit access constraints."""
    feasible, rejected = [], []
    for apt in apartments:
        if apt["rent"] > budget:
            rejected.append((apt, f"Rent ${apt['rent']} exceeds budget ${budget}"))
            continue
        min_walk = min(walking_time(apt["lat"], apt["lng"], s["lat"], s["lng"]) for s in stations)
        if min_walk > max_walk:
            rejected.append((apt, f"Nearest station {min_walk:.1f} min (limit: {max_walk})"))
            continue
        feasible.append(apt)
    return feasible, rejected

def compute_scores(graph, apartments, destinations):
      """
    For each feasible apartment, compute total weekly commute time.

    Score = sum of shortest_time(apartment, destination) * weekly_visits
            for all destinations.

    Args:
        graph: adjacency list graph
        feasible_apartments: list of feasible apartment dicts
        destinations: list of destination dicts
        """
  
    results = []
    for apt in apartments:
        dist, prev = dijkstra(graph, apt["id"])
        details = []
        total = 0
        for d in destinations:
            t = dist.get(d["id"], float("inf"))
            cost = t * d["weekly_visits"]
            total += cost
            details.append({
                "destination": d["name"], "time": round(t, 1),
                "visits": d["weekly_visits"], "cost": round(cost, 1),
                "path": reconstruct_path(prev, apt["id"], d["id"])
            })
        results.append({"id": apt["id"], "name": apt["name"], "rent": apt["rent"],
                        "total": round(total, 1), "details": details})
    results.sort(key=lambda x: x["total"])
    return results

def format_results(results, rejected, perf):
    """Format results as readable text."""
    lines = ["=" * 60, "  SF APARTMENT OPTIMIZER — RESULTS", "=" * 60, ""]
    if rejected:
        lines.append("FILTERED OUT:")
        for apt, reason in rejected:
            lines.append(f"  x {apt['id']} {apt['name']}: {reason}")
        lines.append("")
    lines.append("RANKED FEASIBLE APARTMENTS:")
    lines.append("-" * 60)
    for rank, r in enumerate(results, 1):
        lines += [f"", f"  #{rank}  {r['id']} — {r['name']}",
                  f"       Rent: ${r['rent']}/month",
                  f"       Total weekly commute: {r['total']} minutes", ""]
        for d in r["details"]:
            lines += [f"       -> {d['destination']}",
                      f"          {d['time']} min x {d['visits']} visits = {d['cost']} min",
                      f"          Path: {' -> '.join(d['path'])}"]
        lines.append("")
    if perf:
        lines += ["-" * 60, "PERFORMANCE:",
                  f"  Graph: {perf['nodes']} nodes, {perf['edges']} edges",
                  f"  Dijkstra:     {perf['dijkstra']:.6f}s",
                  f"  Bellman-Ford:  {perf['bellman']:.6f}s",
                  f"  Speedup: {perf['bellman']/perf['dijkstra']:.1f}x" if perf['dijkstra'] > 0 else "", ""]
    lines.append("=" * 60)
    return "\n".join(lines)

def main():
    apartments, destinations, stations = load_data(
        os.path.join(DATA_DIR, "apartments.json"),
        os.path.join(DATA_DIR, "destinations.json"),
        os.path.join(DATA_DIR, "stations.json"))

    graph, _ = build_graph(apartments, destinations, stations)
    feasible, rejected = filter_apartments(apartments, stations, RENT_BUDGET, MAX_WALK_TO_STATION)
    results = compute_scores(graph, feasible, destinations)

    # Performance comparison
    t1 = time.perf_counter()
    for a in feasible: dijkstra(graph, a["id"])
    d_time = time.perf_counter() - t1
    t2 = time.perf_counter()
    for a in feasible: bellman_ford(graph, a["id"])
    b_time = time.perf_counter() - t2
    perf = {"dijkstra": d_time, "bellman": b_time,
            "nodes": len(graph), "edges": sum(len(v) for v in graph.values()) // 2}

    output = format_results(results, rejected, perf)
    print(output)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "ranking_output.txt"), "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()
