import math

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT = 8
CORRIDOR_RADIUS_METERS = 5000
MAX_ROUTE_SAMPLES = 32
MAX_STOPS = 12


def _safe_float(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _route_coordinates(route):
    geometry = (route or {}).get("geometry") or {}
    coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else geometry
    if not isinstance(coordinates, list):
        return []

    clean = []
    for point in coordinates:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            lon = _safe_float(point[0])
            lat = _safe_float(point[1])
            if lon is not None and lat is not None:
                clean.append((lon, lat))
    return clean


def _route_sample_points(coordinates, max_samples=MAX_ROUTE_SAMPLES):
    if not coordinates:
        return []
    if len(coordinates) <= max_samples:
        return coordinates

    indexes = [round(i * (len(coordinates) - 1) / (max_samples - 1)) for i in range(max_samples)]
    return [coordinates[i] for i in indexes]


def _distance_km(a_lon, a_lat, b_lon, b_lat):
    radius = 6371.0
    p1 = math.radians(a_lat)
    p2 = math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lon - a_lon)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(x), math.sqrt(max(0.0, 1 - x)))


def _point_to_segment_distance_km(point_lon, point_lat, a_lon, a_lat, b_lon, b_lat):
    """Approximate point-to-segment distance using a local equirectangular plane."""
    lat0 = math.radians((a_lat + b_lat + point_lat) / 3.0)
    scale_x = 6371.0 * math.cos(lat0)
    scale_y = 6371.0

    px = math.radians(point_lon) * scale_x
    py = math.radians(point_lat) * scale_y
    ax = math.radians(a_lon) * scale_x
    ay = math.radians(a_lat) * scale_y
    bx = math.radians(b_lon) * scale_x
    by = math.radians(b_lat) * scale_y

    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy

    if length_sq <= 1e-12:
        return _distance_km(point_lon, point_lat, a_lon, a_lat)

    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x = ax + t * dx
    closest_y = ay + t * dy

    return math.hypot(px - closest_x, py - closest_y)


def _distance_to_route_km(point_lon, point_lat, route_coordinates):
    if not route_coordinates:
        return None
    if len(route_coordinates) == 1:
        return _distance_km(point_lon, point_lat, route_coordinates[0][0], route_coordinates[0][1])

    return min(
        _point_to_segment_distance_km(
            point_lon,
            point_lat,
            route_coordinates[i][0],
            route_coordinates[i][1],
            route_coordinates[i + 1][0],
            route_coordinates[i + 1][1],
        )
        for i in range(len(route_coordinates) - 1)
    )


def _category(tags):
    if tags.get("warehouse") == "cold_storage" or "cold" in str(tags.get("name", "")).lower():
        return "Cold-storage candidate"
    if tags.get("amenity") == "marketplace":
        return "Mandi / marketplace candidate"
    if tags.get("highway") == "rest_area":
        return "Rest-area candidate"
    if tags.get("amenity") == "fuel":
        return "Fuel / stop candidate"
    if tags.get("amenity") in {"restaurant", "fast_food"}:
        return "Food / rest candidate"
    return "Logistics candidate"


def _build_overpass_query(sample_points):
    blocks = []
    for lon, lat in sample_points:
        blocks.append(
            f'nwr(area.in)(around:{CORRIDOR_RADIUS_METERS},{lat:.6f},{lon:.6f})["amenity"="marketplace"];'
            f'nwr(area.in)(around:{CORRIDOR_RADIUS_METERS},{lat:.6f},{lon:.6f})["highway"="rest_area"];'
            f'nwr(area.in)(around:{CORRIDOR_RADIUS_METERS},{lat:.6f},{lon:.6f})["amenity"="fuel"];'
            f'nwr(area.in)(around:{CORRIDOR_RADIUS_METERS},{lat:.6f},{lon:.6f})["warehouse"="cold_storage"];'
            f'nwr(area.in)(around:{CORRIDOR_RADIUS_METERS},{lat:.6f},{lon:.6f})["amenity"="restaurant"];'
        )

    return (
        '[out:json][timeout:7];'
        'area["ISO3166-1"="IN"][admin_level=2]->.in;'
        '(' + ''.join(blocks) + ');'
        'out center tags;'
    )


def find_route_stops(route):
    route_coordinates = _route_coordinates(route)
    if not route_coordinates:
        return {
            "success": True,
            "stops": [],
            "status": "unavailable",
            "source": "OpenStreetMap Overpass",
        }

    # Query several points along the real OSRM geometry, then perform a
    # second exact proximity check against the complete route geometry.
    sample_points = _route_sample_points(route_coordinates)
    query = _build_overpass_query(sample_points)

    try:
        response = requests.post(
            OVERPASS_URL,
            data=query,
            headers={"User-Agent": "HarvestShield/1.0"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        elements = response.json().get("elements") or []
    except (requests.RequestException, ValueError) as exc:
        return {
            "success": False,
            "stops": [],
            "status": "error",
            "source": "OpenStreetMap Overpass",
            "error": str(exc),
        }

    stops = {}
    for element in elements:
        tags = element.get("tags") or {}
        center = element.get("center") or {}
        lat = _safe_float(element.get("lat", center.get("lat")))
        lon = _safe_float(element.get("lon", center.get("lon")))
        if lat is None or lon is None:
            continue

        # Keep only facilities that are genuinely close to the real route
        # geometry, not merely close to one of the sampled query points.
        distance_km = _distance_to_route_km(lon, lat, route_coordinates)
        if distance_km is None or distance_km > (CORRIDOR_RADIUS_METERS / 1000.0):
            continue

        name = tags.get("name") or tags.get("brand") or "Unnamed mapped facility"
        key = f"{name}|{round(lat, 5)}|{round(lon, 5)}"
        stops[key] = {
            "name": name,
            "category": _category(tags),
            "latitude": lat,
            "longitude": lon,
            "distance_from_route_km": round(distance_km, 2),
            "osm_type": element.get("type"),
            "osm_id": element.get("id"),
        }

    ordered = sorted(stops.values(), key=lambda item: item["distance_from_route_km"])
    return {
        "success": True,
        "status": "live_mapped",
        "source": "OpenStreetMap Overpass",
        "stops": ordered[:MAX_STOPS],
        "notes": [
            "Stops are mapped OpenStreetMap candidates inside India's mapped boundary and within 5 km of the selected real route corridor.",
            "The route-distance check uses the actual OSRM geometry, not only origin/midpoint/destination samples.",
            "Verify suitability before dispatch or stopping the vehicle.",
        ],
    }
