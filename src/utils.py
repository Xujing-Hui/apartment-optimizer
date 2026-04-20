"""
utils.py
--------
Utility functions for the Apartment Commute Optimizer.

Provides:
  - haversine_m(lat1, lon1, lat2, lon2) -> float
      Computes the great-circle distance (in meters) between two
      geographic coordinates using the Haversine formula.

  - walk_time_min(lat1, lon1, lat2, lon2) -> float
      Converts a straight-line distance to an estimated walking time
      (in minutes) by applying a street-detour factor and a fixed
      pedestrian speed.

Constants
---------
WALK_SPEED_M_PER_MIN : float
    Assumed pedestrian speed in meters per minute (~4.8 km/h).

DETOUR_FACTOR : float
    Multiplier applied to straight-line distance to approximate the
    actual walked path length on a street grid (1.3 = +30 % detour).

WALK_FALLBACK_CAP_MIN : float
    Maximum walking time (minutes) for which a direct walk-fallback
    edge is added to the graph.  Pairs whose estimated walk exceeds
    this threshold are NOT connected by a fallback edge.
"""

import math

# ── Constants ─────────────────────────────────────────────────────────────────
WALK_SPEED_M_PER_MIN   = 80.0   # metres per minute  (~4.8 km/h)
DETOUR_FACTOR          = 1.3    # straight-line → street-path multiplier
WALK_FALLBACK_CAP_MIN  = 30.0   # only add direct walk edge if ≤ 30 min


# ── Haversine distance ────────────────────────────────────────────────────────
def haversine_m(lat1: float, lon1: float,
                lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in **metres** between two points
    given as (latitude, longitude) pairs in decimal degrees.

    Uses the Haversine formula:
        a = sin²(Δφ/2) + cos φ1 · cos φ2 · sin²(Δλ/2)
        c = 2 · arcsin(√a)
        d = R · c        where R = 6 371 000 m

    Parameters
    ----------
    lat1, lon1 : float
        Coordinates of the first point (decimal degrees).
    lat2, lon2 : float
        Coordinates of the second point (decimal degrees).

    Returns
    -------
    float
        Distance in metres.
    """
    R = 6_371_000.0                         # Earth's mean radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# ── Walk-time estimate ────────────────────────────────────────────────────────
def walk_time_min(lat1: float, lon1: float,
                  lat2: float, lon2: float) -> float:
    """
    Estimate the walking time in **minutes** between two coordinates.

    Formula:
        walk_time = haversine_m(p1, p2) × DETOUR_FACTOR / WALK_SPEED

    The DETOUR_FACTOR (1.3) accounts for the fact that pedestrians
    must follow streets rather than travelling in a straight line.

    Parameters
    ----------
    lat1, lon1 : float
        Coordinates of the starting point.
    lat2, lon2 : float
        Coordinates of the destination.

    Returns
    -------
    float
        Estimated walking time in minutes, rounded to one decimal place.
    """
    dist_m = haversine_m(lat1, lon1, lat2, lon2)
    return round((dist_m * DETOUR_FACTOR) / WALK_SPEED_M_PER_MIN, 1)


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Sunnyvale Caltrain  →  Lawrence Caltrain  (approx. 4.2 km, ~3.5 min walk)
    d = haversine_m(37.3785, -122.0306, 37.3705, -121.9971)
    w = walk_time_min(37.3785, -122.0306, 37.3705, -121.9971)
    print(f"Haversine distance : {d:.0f} m")
    print(f"Walk time estimate : {w} min")
