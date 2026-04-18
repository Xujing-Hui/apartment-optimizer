"""Straight-line (Haversine) walking time between nodes with lat/lng."""

import math
from typing import Dict, List, Optional, Tuple

WALK_SPEED_M_PER_MIN = 80.0
EARTH_RADIUS_KM = 6371.0

# Straight-line walk is only used as a shortcut when it is at most this many minutes.
# Above this, treat as unavailable so transit=inf does not fall back to a fake "reachable"
# multi-hour hike (data gaps stay unreachable).
MAX_STRAIGHT_LINE_WALK_MINUTES = 45.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometers."""
    r1 = math.radians(lat1)
    r2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def straight_line_walk_minutes(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    speed_m_per_min: float = WALK_SPEED_M_PER_MIN,
) -> float:
    """Minutes if walking straight-line distance at ``speed_m_per_min`` (default 80 m/min)."""
    km = haversine_km(lat1, lng1, lat2, lng2)
    meters = km * 1000.0
    return meters / speed_m_per_min


def build_coord_map(apartments: List[dict], destinations: List[dict]) -> Dict[str, Tuple[float, float]]:
    """Map node id -> (lat, lng) for apartments and all destinations."""
    m: Dict[str, Tuple[float, float]] = {}
    for a in apartments:
        m[a["id"]] = (float(a["lat"]), float(a["lng"]))
    for d in destinations:
        m[d["id"]] = (float(d["lat"]), float(d["lng"]))
    return m


def walk_minutes_between_ids(
    id_a: str,
    id_b: str,
    coord_map: Dict[str, Tuple[float, float]],
    speed_m_per_min: float = WALK_SPEED_M_PER_MIN,
    max_minutes: Optional[float] = None,
) -> float:
    """Haversine walk time between two nodes; ``inf`` if either id lacks coordinates.

    If ``max_minutes`` is ``None``, uses ``MAX_STRAIGHT_LINE_WALK_MINUTES``. When the
    raw straight-line time exceeds the cap, returns ``inf`` (do not use as fallback).
    Pass ``float('inf')`` for ``max_minutes`` to disable capping.
    """
    ca = coord_map.get(id_a)
    cb = coord_map.get(id_b)
    if ca is None or cb is None:
        return float("inf")
    raw = straight_line_walk_minutes(
        ca[0], ca[1], cb[0], cb[1], speed_m_per_min=speed_m_per_min
    )
    cap = MAX_STRAIGHT_LINE_WALK_MINUTES if max_minutes is None else max_minutes
    if cap != float("inf") and raw > cap:
        return float("inf")
    return raw
