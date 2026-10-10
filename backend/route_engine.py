import re
import requests


# ============================================================
# EXTERNAL SERVICES
# ============================================================

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

NOMINATIM_HEADERS = {
    "User-Agent": "HarvestShield/1.0 (route-planning-dashboard)",
    "Accept": "application/json",
}

# Restrict normal place searches to India. This avoids Nominatim selecting
# a same-named place in another country or a distant low-importance locality.
INDIA_VIEWBOX = "68.1,37.5,97.5,6.5"


# ============================================================
# GEOCODING HELPERS
# ============================================================


def _clean_text(value):
    return " ".join(str(value).strip().split())


def _normalise_location_label(location):
    text = _clean_text(location)
    text = re.sub(r"\s*[-—–]\s*(district\s*/\s*city|district|city|state.*)$", "", text, flags=re.I)
    return _clean_text(text)


def _state_hint(location):
    """
    Extract a likely state hint from inputs such as:
        Hyderabad, Telangana
        Warangal, Telangana
        Bengaluru, Karnataka

    This is only used to rank real Nominatim results. Coordinates always
    come from Nominatim itself.
    """
    cleaned = _normalise_location_label(location)
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]

    if len(parts) >= 2:
        return parts[-1].lower()

    return ""


def _location_hint(location):
    cleaned = _normalise_location_label(location)
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    return parts[0].lower() if parts else ""


def _candidate_score(candidate, location):
    """
    Rank real Nominatim candidates so broad names such as "Hyderabad"
    are matched to the requested Indian state when the user supplied one.

    No coordinates are invented or modified here.
    """
    address = candidate.get("address") or {}
    display_name = str(candidate.get("display_name") or "").lower()

    score = 0.0

    # Country match is expected because of countrycodes=in, but retaining
    # this score makes the selection explicit.
    if str(address.get("country_code") or "").lower() == "in":
        score += 1000

    state_hint = _state_hint(location)
    if state_hint:
        state_name = str(address.get("state") or "").lower()
        region_name = str(address.get("state_district") or "").lower()
        if state_hint in state_name:
            score += 500
        elif state_hint in region_name:
            score += 100
        elif state_hint in display_name:
            score += 50

    place_hint = _location_hint(location)
    candidate_name = str(candidate.get("name") or "").strip().lower()
    if place_hint and candidate_name == place_hint:
        score += 900
    elif place_hint and place_hint in display_name:
        score += 250

    # Prefer the actual named city/town/municipality over a mandal,
    # administrative boundary, suburb, or tiny locality when an exact place
    # result is available.
    place_type = str(candidate.get("type") or "").lower()
    if place_type == "city":
        score += 350
    elif place_type in {"town", "municipality"}:
        score += 300
    elif place_type in {"administrative", "county", "state", "district"}:
        score += 0
    elif place_type in {"village", "suburb", "hamlet"}:
        score += 5

    try:
        score += float(candidate.get("importance") or 0) * 10
    except (TypeError, ValueError):
        pass

    return score


# ============================================================
# GEOCODING
# ============================================================


def geocode_location(location):
    """
    Convert a place name into real coordinates using OpenStreetMap Nominatim.

    The function requests several India candidates and ranks them using the
    user's supplied state/location text. The chosen latitude/longitude always
    come directly from Nominatim.
    """

    location = _clean_text(location)

    print(f"[GEOCODE] Input: {location}")
    print(f"[GEOCODE] Normalised: {_normalise_location_label(location)}")

    if not location:
        raise RuntimeError("Location cannot be empty.")

    normalised = _normalise_location_label(location)
    query = normalised
    if "india" not in normalised.lower():
        query = f"{normalised}, India"

    print(f"[GEOCODE] Query: {query}")
    print(f"[GEOCODE] State hint: {_state_hint(location) or 'none'}")

    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "in",
        "viewbox": INDIA_VIEWBOX,
        "bounded": 1,
        "accept-language": "en",
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=NOMINATIM_HEADERS,
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Nominatim geocoding request failed for '{location}': {exc}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            f"Nominatim returned invalid JSON for '{location}'."
        ) from exc

    if not isinstance(data, list) or not data:
        raise RuntimeError(
            f"Could not geocode location in India: {location}"
        )

    candidates = [
        item
        for item in data
        if isinstance(item, dict)
    ]

    if not candidates:
        raise RuntimeError(
            f"Nominatim returned no usable candidates for: {location}"
        )

    candidates.sort(
        key=lambda item: _candidate_score(item, location),
        reverse=True,
    )

    result = candidates[0]

    print("[GEOCODE] Selected:")
    print(f"           {result.get('display_name', location)}")
    print(f"           latitude={result.get('lat')} longitude={result.get('lon')}")
    print(f"           state={(result.get('address') or {}).get('state')} district={(result.get('address') or {}).get('state_district')} type={result.get('type')}")

    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Geocoding returned invalid coordinates for: {location}"
        ) from exc

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise RuntimeError(
            f"Geocoding returned out-of-range coordinates for: {location}"
        )

    return {
        "display_name": result.get("display_name", location),
        "latitude": latitude,
        "longitude": longitude,
        "type": result.get("type"),
        "importance": result.get("importance"),
    }


# ============================================================
# OSRM ROUTING
# ============================================================


def request_osrm_route(
    start_lon,
    start_lat,
    end_lon,
    end_lat,
):
    """
    Request real road-routing data from OSRM.

    OSRM coordinate order:
        longitude,latitude

    Geometry is kept in OSRM's GeoJSON structure so the rest of Harvest
    Shield can use route["geometry"]["coordinates"] consistently.
    """

    url = (
        f"{OSRM_URL}/"
        f"{start_lon:.6f},{start_lat:.6f};"
        f"{end_lon:.6f},{end_lat:.6f}"
    )

    params = {
        "alternatives": "true",
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    print("[OSRM] Request:", url)
    print(f"[OSRM] Start: {start_lat}, {start_lon}")
    print(f"[OSRM] End:   {end_lat}, {end_lon}")

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"OSRM routing request failed: {exc}"
        ) from exc

    if response.status_code != 200:
        detail = response.text.strip()
        raise RuntimeError(
            "OSRM rejected the route request "
            f"(HTTP {response.status_code}). "
            f"OSRM response: {detail[:500]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "OSRM returned an invalid JSON response."
        ) from exc

    if data.get("code") != "Ok":
        message = data.get("message") or "Unknown OSRM error"
        raise RuntimeError(
            f"OSRM could not calculate the route: {message}"
        )

    routes = data.get("routes") or []
    print(f"[OSRM] Real routes returned: {len(routes)}")

    if not routes:
        raise RuntimeError(
            "OSRM returned no real route alternatives."
        )

    return routes


# ============================================================
# ROUTE CONVERSION
# ============================================================


def build_route(
    osrm_route,
    route_id,
):
    """
    Convert one real OSRM route into the structure expected by Harvest Shield.

    No distance, duration or geometry values are fabricated.
    """

    distance_meters = osrm_route.get("distance")
    duration_seconds = osrm_route.get("duration")
    geometry = osrm_route.get("geometry")

    if (
        distance_meters is None
        or duration_seconds is None
        or not isinstance(geometry, dict)
        or geometry.get("type") != "LineString"
        or not isinstance(geometry.get("coordinates"), list)
        or len(geometry.get("coordinates")) < 2
    ):
        raise RuntimeError(
            f"OSRM returned incomplete geometry/data for route {route_id}."
        )

    if route_id <= 26:
        route_name = f"Route {chr(64 + route_id)}"
    else:
        route_name = f"Route {route_id}"

    return {
        "route_id": route_id,
        "route_name": route_name,
        "route_type": (
            "Direct OSRM route"
            if route_id == 1
            else "OSRM corridor alternative"
        ),
        "distance_km": round(
            float(distance_meters) / 1000,
            2,
        ),
        "duration_minutes": round(
            float(duration_seconds) / 60,
            2,
        ),
        "geometry": geometry,
    }


# ============================================================
# MAIN ROUTING FUNCTION
# ============================================================


def get_routes(start, end):
    """
    Geocode the supplied origin/destination and request only the real route
    alternatives returned by OSRM.

    No synthetic Route B or Route C is created.
    """

    print("[ROUTING] ==================================================")
    print(f"[ROUTING] Input start: {start!r}")
    print(f"[ROUTING] Input end:   {end!r}")

    start_location = geocode_location(start)
    end_location = geocode_location(end)

    start_lat = start_location["latitude"]
    start_lon = start_location["longitude"]
    end_lat = end_location["latitude"]
    end_lon = end_location["longitude"]

    print(f"[ROUTING] Final start coordinates: {start_lat}, {start_lon}")
    print(f"[ROUTING] Final end coordinates:   {end_lat}, {end_lon}")

    osrm_routes = request_osrm_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
    )

    routes = []

    for index, osrm_route in enumerate(osrm_routes, start=1):
        routes.append(
            build_route(
                osrm_route,
                index,
            )
        )

    return {
        "start": start,
        "destination": end,
        "start_coordinates": [
            start_lat,
            start_lon,
        ],
        "destination_coordinates": [
            end_lat,
            end_lon,
        ],
        "start_geocoded_name": start_location["display_name"],
        "destination_geocoded_name": end_location["display_name"],
        "route_count": len(routes),
        "routes": routes,
    }
