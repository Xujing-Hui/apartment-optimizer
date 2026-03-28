import json
from collections import defaultdict
from utils import walking_time

MAX_WALK_MINUTES = 15       
LIGHT_RAIL_INTERVAL = 3     

def load_data(apartments_path, destinations_path, stations_path):
    with open(apartments_path) as f: apartments = json.load(f)
    with open(destinations_path) as f: destinations = json.load(f)
    with open(stations_path) as f: stations = json.load(f)
    return apartments, destinations, stations

def build_graph(apartments, destinations, stations):
    """Build weighted adjacency list from apartments, destinations, and stations."""
    graph = defaultdict(list)
    node_info = {}
    for item in apartments + destinations + stations:
        node_info[item["id"]] = item

    # Transit edges: adjacent stations
    for i in range(len(stations) - 1):
        a, b = stations[i]["id"], stations[i + 1]["id"]
        graph[a].append((b, LIGHT_RAIL_INTERVAL))
        graph[b].append((a, LIGHT_RAIL_INTERVAL))

    # Walking edges: apartments/destinations <-> nearby stations
    for node in apartments + destinations:
        for stn in stations:
            wt = walking_time(node["lat"], node["lng"], stn["lat"], stn["lng"])
            if wt <= MAX_WALK_MINUTES:
                graph[node["id"]].append((stn["id"], round(wt, 1)))
                graph[stn["id"]].append((node["id"], round(wt, 1)))

    # Direct walking edges: apartment <-> destination （if within 30 min)
    for apt in apartments:
        for dest in destinations:
            wt = walking_time(apt["lat"], apt["lng"], dest["lat"], dest["lng"])
            if wt <= 30:
                graph[apt["id"]].append((dest["id"], round(wt, 1)))
                graph[dest["id"]].append((apt["id"], round(wt, 1)))

    return dict(graph), node_info
