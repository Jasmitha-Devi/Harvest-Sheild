import math
from datetime import datetime, timezone

import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 12
RAIL_CANDIDATE_RADIUS_METERS = 5000


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_float(value, default=None):
    try:
        result = float(value)
        if math.isfinite(result):
            return result
    except (TypeError, ValueError):
        pass
    return default


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def point_from_route(route):
    geometry = route.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if not coordinates:
        return None

    first = coordinates[0]
    last = coordinates[-1]

    if (
        isinstance(first, (list, tuple))
        and len(first) >= 2
        and isinstance(last, (list, tuple))
        and len(last) >= 2
    ):
        first_lon = safe_float(first[0])
        first_lat = safe_float(first[1])
        last_lon = safe_float(last[0])
        last_lat = safe_float(last[1])
        if None not in (first_lon, first_lat, last_lon, last_lat):
            return {
                "origin": (first_lat, first_lon),
                "destination": (last_lat, last_lon),
            }

    return None


def _query_rail_candidates(latitude, longitude):
    query = f"""
    [out:json][timeout:{REQUEST_TIMEOUT}];
    (
      node[railway=station](around:{RAIL_CANDIDATE_RADIUS_METERS},{latitude},{longitude});
      node[railway=halt](around:{RAIL_CANDIDATE_RADIUS_METERS},{latitude},{longitude});
    );
    out center tags;
    """

    response = requests.post(
        OVERPASS_URL,
        data=query,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "HarvestShield/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    elements = payload.get("elements") or []

    candidates = []
    seen = set()

    for element in elements:
        tags = element.get("tags") or {}
        name = str(tags.get("name") or "Unnamed rail station/halt").strip()
        latitude_value = safe_float(element.get("lat"))
        longitude_value = safe_float(element.get("lon"))

        if latitude_value is None or longitude_value is None:
            continue

        key = (
            element.get("type"),
            element.get("id"),
            round(latitude_value, 6),
            round(longitude_value, 6),
        )
        if key in seen:
            continue
        seen.add(key)

        distance_km = haversine_km(
            latitude,
            longitude,
            latitude_value,
            longitude_value,
        )

        candidates.append(
            {
                "name": name,
                "railway_type": tags.get("railway"),
                "distance_from_endpoint_km": round(distance_km, 2),
                "latitude": latitude_value,
                "longitude": longitude_value,
            }
        )

    candidates.sort(key=lambda item: item["distance_from_endpoint_km"])
    return candidates[:5]


def _endpoint_candidate(endpoint_name, point):
    latitude, longitude = point

    try:
        candidates = _query_rail_candidates(latitude, longitude)
    except requests.RequestException as exc:
        return {
            "status": "unavailable",
            "endpoint": endpoint_name,
            "candidate": None,
            "candidates": [],
            "error": str(exc),
        }
    except ValueError as exc:
        return {
            "status": "unavailable",
            "endpoint": endpoint_name,
            "candidate": None,
            "candidates": [],
            "error": f"Invalid Overpass response: {exc}",
        }

    candidate = candidates[0] if candidates else None

    return {
        "status": "live" if candidate else "no_candidate",
        "endpoint": endpoint_name,
        "candidate": candidate,
        "candidates": candidates,
    }


def analyze_multimodal_plan(route, transport_mode="road"):
    mode = str(transport_mode or "road").strip().lower()

    if mode == "road":
        return {
            "requested_mode": "road",
            "display_mode": "Road only",
            "status": "road_only",
            "available": True,
            "planning_level": "live_road_routing",
            "rail_data_status": "not_requested",
            "transfer_candidates": None,
            "notes": [
                "Live road routing is used for route geometry, distance and duration.",
                "No rail leg is requested or fabricated.",
            ],
            "retrieved_at": utc_now_iso(),
        }

    if mode != "multimodal":
        mode = "road"

    route_points = point_from_route(route)
    if not route_points:
        return {
            "requested_mode": "multimodal",
            "display_mode": "Multimodal planning",
            "status": "unavailable",
            "available": False,
            "planning_level": "planning_candidate_only",
            "rail_data_status": "unavailable",
            "transfer_candidates": None,
            "notes": [
                "The live road route has no usable endpoint geometry for rail-candidate lookup.",
                "No rail route, schedule, freight service or rail ETA is fabricated.",
            ],
            "retrieved_at": utc_now_iso(),
        }

    origin = _endpoint_candidate("Origin", route_points["origin"])
    destination = _endpoint_candidate("Destination", route_points["destination"])

    origin_candidate = origin.get("candidate")
    destination_candidate = destination.get("candidate")

    if origin_candidate and destination_candidate:
        status = "candidate_available"
        available = True
    elif origin_candidate or destination_candidate:
        status = "partial_candidate"
        available = False
    else:
        status = "no_candidate"
        available = False

    return {
        "requested_mode": "multimodal",
        "display_mode": "Multimodal planning (Road + Rail candidate)",
        "status": status,
        "available": available,
        "planning_level": "planning_candidate_only",
        "rail_data_status": (
            "live_osm_infrastructure"
            if origin.get("status") != "unavailable"
            or destination.get("status") != "unavailable"
            else "unavailable"
        ),
        "transfer_candidates": {
            "origin": origin,
            "destination": destination,
        },
        "notes": [
            "Rail candidates are based on live OpenStreetMap railway station/halt infrastructure near the road-route endpoints.",
            "The displayed road route remains the real OSRM route geometry.",
            "No rail timetable, freight availability, rail duration, or confirmed intermodal booking is claimed.",
            "A candidate station is an infrastructure planning point, not proof of a freight service.",
        ],
        "retrieved_at": utc_now_iso(),
    }



def analyze_multimodal_routes(routes, transport_mode="road"):
    """Check railway infrastructure independently for every real road route."""
    mode = str(transport_mode or "road").strip().lower()

    if mode == "road":
        return {
            "requested_mode": "road",
            "display_mode": "Road only",
            "status": "road_only",
            "available": True,
            "planning_level": "live_road_routing",
            "rail_data_status": "not_requested",
            "route_count_checked": 0,
            "route_analyses": [],
            "notes": [
                "No railway infrastructure lookup is performed in Road-only mode.",
                "Live road routing is used for route geometry, distance and duration.",
            ],
            "retrieved_at": utc_now_iso(),
        }

    route_analyses = []
    for route in routes or []:
        analysis = analyze_multimodal_plan(route, transport_mode="multimodal")
        analysis["route_id"] = route.get("route_id")
        analysis["route_name"] = route.get("route_name")
        route_analyses.append(analysis)

    checked_count = len(route_analyses)
    complete_count = sum(
        1
        for analysis in route_analyses
        if analysis.get("status") == "candidate_available"
    )
    partial_count = sum(
        1
        for analysis in route_analyses
        if analysis.get("status") == "partial_candidate"
    )
    no_candidate_count = sum(
        1
        for analysis in route_analyses
        if analysis.get("status") == "no_candidate"
    )
    unavailable_count = sum(
        1
        for analysis in route_analyses
        if analysis.get("status") == "unavailable"
    )

    if unavailable_count == checked_count and checked_count > 0:
        overall_status = "lookup_unavailable"
    elif complete_count == checked_count and checked_count > 0:
        overall_status = "all_routes_have_candidates"
    elif complete_count or partial_count:
        overall_status = "mixed_candidate_coverage"
    elif no_candidate_count == checked_count and checked_count > 0:
        overall_status = "no_route_candidates"
    else:
        overall_status = "checked"

    return {
        "requested_mode": "multimodal",
        "display_mode": "Multimodal planning (Road + Rail infrastructure check)",
        "status": overall_status,
        "available": checked_count > 0,
        "planning_level": "planning_candidate_only",
        "rail_data_status": "checked_per_route",
        "route_count_checked": checked_count,
        "routes_with_two_transfer_candidates": complete_count,
        "routes_with_partial_candidates": partial_count,
        "routes_with_no_candidates": no_candidate_count,
        "routes_with_lookup_unavailable": unavailable_count,
        "route_analyses": route_analyses,
        "notes": [
            "Railway infrastructure is checked independently for every real OSRM route returned for the journey.",
            "Candidates are based on OpenStreetMap-mapped railway station/halt infrastructure near each route's road endpoints.",
            "The displayed road routes remain the real OSRM route geometry.",
            "No rail timetable, freight availability, rail duration, or confirmed intermodal booking is claimed.",
            "A mapped rail candidate is an infrastructure planning point, not proof of a freight service.",
        ],
        "retrieved_at": utc_now_iso(),
    }
