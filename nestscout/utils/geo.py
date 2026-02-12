"""Geo utilities — haversine distance for SQLite dev mode."""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points (in metres).

    Uses the haversine formula. This is the fallback for SQLite dev mode
    where PostGIS spatial queries are unavailable.

    Args:
        lat1, lon1: Coordinates of point A (decimal degrees).
        lat2, lon2: Coordinates of point B (decimal degrees).

    Returns:
        Distance in metres.
    """
    R = 6_371_000  # Earth radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def estimate_walk_time(distance_m: float, speed_kmh: float = 5.0) -> float:
    """Estimate walking time in minutes given distance in metres.

    Args:
        distance_m: Distance in metres.
        speed_kmh: Walking speed (default 5 km/h).

    Returns:
        Walking time in minutes.
    """
    speed_mpm = (speed_kmh * 1000) / 60  # metres per minute
    return distance_m / speed_mpm
