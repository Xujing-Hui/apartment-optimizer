"""
This file is about Utility functions for distance calculation and walking time estimation.
"""

import math


def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the straight-line distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lng1: Latitude and longitude of point 1 (in degrees)
        lat2, lng2: Latitude and longitude of point 2 (in degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def walking_time(lat1, lng1, lat2, lng2, speed_kmh=5.0):
    """
    Estimate walking time between two points.

    Assumes average walking speed of 5 km/h.
    Multiplies straight-line distance by 1.3 to approximate real walking paths
    (streets are not straight lines).

    Args:
        lat1, lng1: Coordinates of point 1
        lat2, lng2: Coordinates of point 2
        speed_kmh: Walking speed in km/h (default 5.0)

    Returns:
        Walking time in minutes
    """
    dist = haversine_distance(lat1, lng1, lat2, lng2)
    real_dist = dist * 1.3  # Adjust for non-straight walking paths
    time_hours = real_dist / speed_kmh
    return time_hours * 60  # Convert to minutes
