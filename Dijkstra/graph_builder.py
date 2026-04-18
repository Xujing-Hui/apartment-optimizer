"""Build undirected weighted graph from v2 JSON transit data."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

Edge = Tuple[str, float, str]


def load_json_records(
    apartments_path: Union[str, Path],
    stations_path: Union[str, Path],
    destinations_path: Union[str, Path],
) -> Tuple[List[dict], List[dict], Dict[str, Any]]:
    """Load the three v2 JSON files.

    Returns:
        apartments, stations, destinations_doc (includes 'destinations' and 'categories')
    """
    apartments_path = Path(apartments_path)
    stations_path = Path(stations_path)
    destinations_path = Path(destinations_path)

    with open(apartments_path, encoding="utf-8") as f:
        apt_doc = json.load(f)
    with open(stations_path, encoding="utf-8") as f:
        stn_doc = json.load(f)
    with open(destinations_path, encoding="utf-8") as f:
        dest_doc = json.load(f)

    apartments = apt_doc["apartments"]
    stations = stn_doc["stations"]
    return apartments, stations, dest_doc


def build_graph(
    apartments: List[dict],
    stations: List[dict],
    destinations: List[dict],
) -> Dict[str, List[Edge]]:
    """Undirected graph: station neighbors (with mode), apt/station and dest/station walks."""
    graph: Dict[str, List[Edge]] = {}

    def ensure_node(nid: str) -> None:
        if nid not in graph:
            graph[nid] = []

    station_ids = {s["id"] for s in stations}
    for s in stations:
        ensure_node(s["id"])
    for a in apartments:
        ensure_node(a["id"])
    for d in destinations:
        ensure_node(d["id"])

    # Station–station edges (dedupe undirected pairs)
    seen_pairs: set = set()
    for s in stations:
        sid = s["id"]
        for nb in s.get("neighbors", []):
            oid = nb["id"]
            w = float(nb["travel_min"])
            mode = str(nb.get("mode", "unknown")).strip() or "unknown"
            key = tuple(sorted((sid, oid)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            if oid not in station_ids:
                raise ValueError(f"Neighbor {oid!r} of station {sid!r} is not a known station")
            ensure_node(oid)
            graph[sid].append((oid, w, mode))
            graph[oid].append((sid, w, mode))

    walk_mode = "walk"
    for apt in apartments:
        sid = apt["nearest_station_id"]
        if sid not in station_ids:
            raise ValueError(f"Apartment {apt['id']!r}: unknown nearest_station_id {sid!r}")
        w = float(apt["walk_min_to_station"])
        aid = apt["id"]
        graph[aid].append((sid, w, walk_mode))
        graph[sid].append((aid, w, walk_mode))

    for dest in destinations:
        sid = dest["nearest_station_id"]
        if sid not in station_ids:
            raise ValueError(f"Destination {dest['id']!r}: unknown nearest_station_id {sid!r}")
        w = float(dest["walk_min_from_station"])
        did = dest["id"]
        graph[did].append((sid, w, walk_mode))
        graph[sid].append((did, w, walk_mode))

    return graph
