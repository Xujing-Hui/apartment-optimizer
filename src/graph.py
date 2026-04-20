"""
graph.py
--------
Loads the three project JSON data files and builds a weighted,
undirected adjacency-list graph suitable for Dijkstra's algorithm.

Graph node types
----------------
  - Apartment nodes   (5)  : source nodes for shortest-path queries
  - Destination nodes (25) : sink nodes (NEU, Starbucks, Costco, TJ, Gym)
  - Transit nodes     (36) : Caltrain stations, VTA bus hubs/stops, BART

Edge types
----------
  1. station ↔ station   : travel_min from stations_json_v2.json neighbors
  2. apartment ↔ station : walk_min_to_station from apartments_json.json
  3. destination ↔ station: walk_min_from_station from destinations_json.json
  4. walk-fallback        : direct walk edge added when haversine walk ≤ 30 min
                            (handles cases where two nearby nodes have no
                             short transit path between them)

All edges are bidirectional (undirected graph).

Usage
-----
    from graph import build_graph, load_data

    apartments, destinations, stations, constraints, categories = load_data()
    G = build_graph(apartments, destinations, stations)
"""

import json
import os
from utils import walk_time_min, WALK_FALLBACK_CAP_MIN

# ── Default data-file paths ───────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

APT_FILE   = os.path.join(_DATA_DIR, "apartments_json.json")
DEST_FILE  = os.path.join(_DATA_DIR, "destinations_json.json")
STAT_FILE  = os.path.join(_DATA_DIR, "stations_json_v2.json")


# ── Data loader ───────────────────────────────────────────────────────────────
def load_data(apt_path=APT_FILE, dest_path=DEST_FILE, stat_path=STAT_FILE):
    """
    Load and return the raw data from the three JSON files.

    Returns
    -------
    apartments   : list[dict]
    destinations : list[dict]
    stations     : list[dict]
    constraints  : dict   (max_monthly_rent, max_walk_min_to_station)
    categories   : dict   (category → {weekly_visits, candidates, …})
    """
    with open(apt_path,  encoding="utf-8") as f:
        apt_data  = json.load(f)
    with open(dest_path, encoding="utf-8") as f:
        dest_data = json.load(f)
    with open(stat_path, encoding="utf-8") as f:
        stat_data = json.load(f)

    return (
        apt_data["apartments"],
        dest_data["destinations"],
        stat_data["stations"],
        apt_data["constraints"],
        dest_data["categories"],
    )


# ── Graph builder ─────────────────────────────────────────────────────────────
def _add_edge(G: dict, u: str, v: str, weight: float) -> None:
    """
    Add an undirected edge (u, v) with the given weight to adjacency
    list G.  Duplicate edges (same pair, any order) are silently
    ignored — the first weight encountered is kept.
    """
    G.setdefault(u, [])
    G.setdefault(v, [])
    if not any(nb == v for nb, _ in G[u]):
        G[u].append((v, weight))
    if not any(nb == u for nb, _ in G[v]):
        G[v].append((u, weight))


def build_graph(apartments: list, destinations: list,
                stations: list) -> dict:
    """
    Construct and return the weighted adjacency-list graph G.

    Steps
    -----
    1. Station ↔ station edges from the JSON neighbor lists.
    2. Apartment → nearest-station walk edges.
    3. Destination → nearest-station walk edges.
    4. Walk-fallback edges for (apartment, destination) pairs whose
       estimated walking time does not exceed WALK_FALLBACK_CAP_MIN.

    Parameters
    ----------
    apartments   : list of apartment dicts (from apartments_json.json)
    destinations : list of destination dicts (from destinations_json.json)
    stations     : list of station dicts (from stations_json_v2.json)

    Returns
    -------
    G : dict[str, list[tuple[str, float]]]
        Adjacency list mapping node_id → [(neighbour_id, weight), …]
    """
    G: dict = {}

    # ── Step 1: station ↔ station edges ─────────────────────────────────────
    for station in stations:
        sid = station["id"]
        G.setdefault(sid, [])
        for nb in station.get("neighbors", []):
            _add_edge(G, sid, nb["id"], nb["travel_min"])

    # ── Step 2: apartment ↔ nearest station ─────────────────────────────────
    for apt in apartments:
        _add_edge(G, apt["id"], apt["nearest_station_id"],
                  apt["walk_min_to_station"])

    # ── Step 3: destination ↔ nearest station ────────────────────────────────
    for dest in destinations:
        _add_edge(G, dest["id"], dest["nearest_station_id"],
                  dest["walk_min_from_station"])

    # ── Step 4: walk-fallback edges (apartment ↔ destination) ────────────────
    for apt in apartments:
        for dest in destinations:
            wt = walk_time_min(
                apt["lat"],  apt["lng"],
                dest["lat"], dest["lng"],
            )
            if wt <= WALK_FALLBACK_CAP_MIN:
                _add_edge(G, apt["id"], dest["id"], wt)

    return G


def graph_stats(G: dict) -> dict:
    """
    Return basic statistics about graph G.

    Returns
    -------
    dict with keys: nodes (int), edges (int)
    """
    node_count = len(G)
    edge_count = sum(len(neighbours) for neighbours in G.values()) // 2
    return {"nodes": node_count, "edges": edge_count}


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    apartments, destinations, stations, constraints, categories = load_data()
    G = build_graph(apartments, destinations, stations)
    stats = graph_stats(G)
    print(f"Graph built successfully.")
    print(f"  Nodes : {stats['nodes']}")
    print(f"  Edges : {stats['edges']}")
    print(f"  Walk-fallback cap : {WALK_FALLBACK_CAP_MIN} min")

    # Spot-check: Villas should connect to S2 and G2 via walk-fallback
    villas_nb = [nb for nb, _ in G.get("villas_on_the_blvd", [])]
    print(f"\nVillas neighbours (first 8): {villas_nb[:8]}")
    assert "S2" in villas_nb, "Walk-fallback Villas ↔ S2 missing"
    assert "G2" in villas_nb, "Walk-fallback Villas ↔ G2 missing"
    print("Walk-fallback spot-checks passed.")
