import os
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "").strip()

TOMTOM_FLOW_URL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT = 8
MAX_TRAFFIC_SAMPLES = 4
MAX_INCIDENT_ROUTE_SAMPLES = 40
INCIDENT_ROUTE_DISTANCE_KM = 2.0
TOMTOM_INCIDENTS_URL = "https://api.tomtom.com/maps/orbis/traffic/incidents/details"


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_float(value, default=None):
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except (TypeError, ValueError):
        pass
    return default


def clamp(value, minimum, maximum):
    number = safe_float(value, minimum)
    return max(minimum, min(maximum, number))


def sample_route_coordinates(route, max_samples=MAX_TRAFFIC_SAMPLES):
    geometry = route.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []

    cleaned = []

    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            continue

        longitude = safe_float(coordinate[0])
        latitude = safe_float(coordinate[1])

        if longitude is None or latitude is None:
            continue

        if -180 <= longitude <= 180 and -90 <= latitude <= 90:
            cleaned.append((longitude, latitude))

    if not cleaned:
        return []

    if len(cleaned) <= max_samples:
        return cleaned

    indexes = []
    for index in range(max_samples):
        position = index / (max_samples - 1)
        indexes.append(round(position * (len(cleaned) - 1)))

    return [cleaned[index] for index in indexes]


def average(values):
    valid = [safe_float(value) for value in values]
    valid = [value for value in valid if value is not None]

    if not valid:
        return None

    return sum(valid) / len(valid)


def get_tomtom_flow(latitude, longitude):
    if not TOMTOM_API_KEY:
        return {
            "provider": "TomTom",
            "status": "unavailable",
            "error": "TOMTOM_API_KEY is missing from the project .env file.",
            "latitude": latitude,
            "longitude": longitude,
        }

    params = {
        "key": TOMTOM_API_KEY,
        "point": f"{latitude:.6f},{longitude:.6f}",
        "unit": "KMPH",
    }

    try:
        response = requests.get(
            TOMTOM_FLOW_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return {
                "provider": "TomTom",
                "status": "error",
                "http_status": response.status_code,
                "error": response.text[:500],
                "latitude": latitude,
                "longitude": longitude,
            }

        payload = response.json()
        flow = payload.get("flowSegmentData") or {}

        current_speed = safe_float(flow.get("currentSpeed"))
        free_flow_speed = safe_float(flow.get("freeFlowSpeed"))
        current_travel_time = safe_float(flow.get("currentTravelTime"))
        free_flow_travel_time = safe_float(flow.get("freeFlowTravelTime"))
        confidence = safe_float(flow.get("confidence"))
        road_closure = bool(flow.get("roadClosure", False))

        speed_ratio = None
        congestion_percent = None

        if current_speed is not None and free_flow_speed and free_flow_speed > 0:
            speed_ratio = current_speed / free_flow_speed
            congestion_percent = clamp((1 - speed_ratio) * 100, 0, 100)

        delay_seconds = None
        if current_travel_time is not None and free_flow_travel_time is not None:
            delay_seconds = max(0, current_travel_time - free_flow_travel_time)

        return {
            "provider": "TomTom",
            "status": "live",
            "observed_at": utc_now_iso(),
            "query_point": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "frc": flow.get("frc"),
            "current_speed_kmph": current_speed,
            "free_flow_speed_kmph": free_flow_speed,
            "current_travel_time_seconds": current_travel_time,
            "free_flow_travel_time_seconds": free_flow_travel_time,
            "delay_seconds": delay_seconds,
            "speed_ratio": round(speed_ratio, 4) if speed_ratio is not None else None,
            "congestion_percent": (
                round(congestion_percent, 2)
                if congestion_percent is not None
                else None
            ),
            "confidence": confidence,
            "road_closure": road_closure,
            "coordinates": (
                flow.get("coordinates", {}).get("coordinate", [])
                if isinstance(flow.get("coordinates"), dict)
                else []
            ),
        }

    except requests.RequestException as exc:
        return {
            "provider": "TomTom",
            "status": "error",
            "error": str(exc),
            "latitude": latitude,
            "longitude": longitude,
        }
    except ValueError as exc:
        return {
            "provider": "TomTom",
            "status": "error",
            "error": f"Invalid JSON response: {exc}",
            "latitude": latitude,
            "longitude": longitude,
        }


def get_route_traffic(route):
    coordinates = sample_route_coordinates(route)
    # The samples are independent external requests. Run them concurrently
    # so one slow TomTom point does not block all the other route samples.
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(coordinates)))) as executor:
        futures = [
            executor.submit(get_tomtom_flow, latitude, longitude)
            for longitude, latitude in coordinates
        ]
        samples = [future.result() for future in futures]

    live_samples = [
        sample for sample in samples if sample.get("status") == "live"
    ]

    if not live_samples:
        return {
            "provider": "TomTom",
            "status": "unavailable",
            "sample_count": len(samples),
            "live_sample_count": 0,
            "samples": samples,
            "current_speed_kmph": None,
            "free_flow_speed_kmph": None,
            "congestion_percent": None,
            "delay_seconds": None,
            "confidence": None,
            "road_closure": False,
            "road_closure_detected": False,
            "retrieved_at": utc_now_iso(),
        }

    closure_detected = any(
        sample.get("road_closure") is True for sample in live_samples
    )

    return {
        "provider": "TomTom",
        "status": "live",
        "retrieved_at": utc_now_iso(),
        "sample_count": len(samples),
        "live_sample_count": len(live_samples),
        "current_speed_kmph": (
            round(average(s.get("current_speed_kmph") for s in live_samples), 2)
            if average(s.get("current_speed_kmph") for s in live_samples) is not None
            else None
        ),
        "free_flow_speed_kmph": (
            round(average(s.get("free_flow_speed_kmph") for s in live_samples), 2)
            if average(s.get("free_flow_speed_kmph") for s in live_samples) is not None
            else None
        ),
        "congestion_percent": (
            round(average(s.get("congestion_percent") for s in live_samples), 2)
            if average(s.get("congestion_percent") for s in live_samples) is not None
            else None
        ),
        "delay_seconds": (
            round(average(s.get("delay_seconds") for s in live_samples), 2)
            if average(s.get("delay_seconds") for s in live_samples) is not None
            else None
        ),
        "confidence": (
            round(average(s.get("confidence") for s in live_samples), 4)
            if average(s.get("confidence") for s in live_samples) is not None
            else None
        ),
        "road_closure": closure_detected,
        "road_closure_detected": closure_detected,
        "samples": samples,
    }



def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def route_bbox(route):
    coordinates = sample_route_coordinates(
        route, max_samples=max(MAX_INCIDENT_ROUTE_SAMPLES, 2)
    )

    if not coordinates:
        return None

    longitudes = [coordinate[0] for coordinate in coordinates]
    latitudes = [coordinate[1] for coordinate in coordinates]

    return (
        min(longitudes),
        min(latitudes),
        max(longitudes),
        max(latitudes),
    )


def incident_coordinates(incident):
    geometry = incident.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []

    if geometry.get("type") == "Point":
        if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
            longitude = safe_float(coordinates[0])
            latitude = safe_float(coordinates[1])
            if longitude is not None and latitude is not None:
                return [(longitude, latitude)]
        return []

    points = []

    def collect(value):
        if not isinstance(value, (list, tuple)):
            return

        if len(value) >= 2 and all(
            isinstance(item, (int, float)) for item in value[:2]
        ):
            longitude = safe_float(value[0])
            latitude = safe_float(value[1])
            if longitude is not None and latitude is not None:
                points.append((longitude, latitude))
            return

        for item in value:
            collect(item)

    collect(coordinates)
    return points


def minimum_distance_to_route_km(incident, route_coordinates):
    points = incident_coordinates(incident)

    if not points or not route_coordinates:
        return None

    minimum = None

    for incident_lon, incident_lat in points:
        for route_lon, route_lat in route_coordinates:
            distance = haversine_km(
                incident_lat,
                incident_lon,
                route_lat,
                route_lon,
            )
            if minimum is None or distance < minimum:
                minimum = distance

    return minimum


def get_tomtom_incidents(route):
    if not TOMTOM_API_KEY:
        return {
            "provider": "TomTom",
            "status": "unavailable",
            "error": "TOMTOM_API_KEY is missing from the project .env file.",
            "incident_count": 0,
            "incidents": [],
        }

    bbox = route_bbox(route)
    route_coordinates = sample_route_coordinates(
        route, max_samples=MAX_INCIDENT_ROUTE_SAMPLES
    )

    if bbox is None or not route_coordinates:
        return {
            "provider": "TomTom",
            "status": "unavailable",
            "error": "Route geometry is unavailable for incident lookup.",
            "incident_count": 0,
            "incidents": [],
        }

    min_lon, min_lat, max_lon, max_lat = bbox

    # Small geographic padding keeps incidents just beside the route visible
    # without requesting an unnecessarily large city/region bounding box.
    padding = 0.02
    bbox_value = (
        f"{min_lon - padding:.6f},{min_lat - padding:.6f},"
        f"{max_lon + padding:.6f},{max_lat + padding:.6f}"
    )

    params = {
        "apiVersion": "2",
        "bbox": bbox_value,
        "timeValidity": "present",
    }

    headers = {
        "TomTom-Api-Key": TOMTOM_API_KEY,
        "TomTom-Api-Version": "2",
        "Accept": "application/json",
        "Attributes": (
            "incidents("
            "type,geometry(type,coordinates),"
            "properties("
            "id,iconCategory,magnitudeOfDelay,events,startTime,endTime,"
            "from,to,lengthInMeters,delayInSeconds,roadNumbers,timeValidity,"
            "probabilityOfOccurrence,numberOfReports,lastReportTime"
            ")"
            ")"
        ),
    }

    try:
        response = requests.get(
            TOMTOM_INCIDENTS_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return {
                "provider": "TomTom",
                "status": "error",
                "http_status": response.status_code,
                "error": response.text[:1000],
                "bbox": bbox_value,
                "incident_count": 0,
                "incidents": [],
            }

        payload = response.json()
        raw_incidents = payload.get("incidents") or []
        route_incidents = []

        for incident in raw_incidents:
            distance_km = minimum_distance_to_route_km(
                incident, route_coordinates
            )

            if distance_km is None or distance_km > INCIDENT_ROUTE_DISTANCE_KM:
                continue

            properties = incident.get("properties") or {}
            events = properties.get("events") or []

            route_incidents.append(
                {
                    "id": properties.get("id"),
                    "type": incident.get("type"),
                    "icon_category": properties.get("iconCategory"),
                    "magnitude_of_delay": properties.get("magnitudeOfDelay"),
                    "start_time": properties.get("startTime"),
                    "end_time": properties.get("endTime"),
                    "from": properties.get("from"),
                    "to": properties.get("to"),
                    "length_meters": safe_float(
                        properties.get("lengthInMeters")
                    ),
                    "delay_seconds": safe_float(
                        properties.get("delayInSeconds")
                    ),
                    "road_numbers": properties.get("roadNumbers") or [],
                    "time_validity": properties.get("timeValidity"),
                    "probability_of_occurrence": properties.get(
                        "probabilityOfOccurrence"
                    ),
                    "number_of_reports": properties.get("numberOfReports"),
                    "last_report_time": properties.get("lastReportTime"),
                    "events": [
                        {
                            "code": event.get("code"),
                            "description": event.get("description"),
                            "icon_category": event.get("iconCategory"),
                        }
                        for event in events
                        if isinstance(event, dict)
                    ],
                    "distance_from_route_km": round(distance_km, 3),
                    "geometry": incident.get("geometry") or {},
                }
            )

        return {
            "provider": "TomTom",
            "status": "live",
            "retrieved_at": utc_now_iso(),
            "bbox": bbox_value,
            "source_incident_count": len(raw_incidents),
            "incident_count": len(route_incidents),
            "road_closure_detected": any(
                incident.get("icon_category") == "roadClosed"
                or any(
                    event.get("icon_category") == "roadClosed"
                    or str(event.get("description", "")).lower() == "closed"
                    for event in incident.get("events", [])
                )
                for incident in route_incidents
            ),
            "roadworks_detected": any(
                incident.get("icon_category") == "roadWorks"
                or any(
                    event.get("icon_category") == "roadWorks"
                    for event in incident.get("events", [])
                )
                for incident in route_incidents
            ),
            "incidents": route_incidents,
        }

    except requests.RequestException as exc:
        return {
            "provider": "TomTom",
            "status": "error",
            "error": str(exc),
            "incident_count": 0,
            "incidents": [],
        }
    except ValueError as exc:
        return {
            "provider": "TomTom",
            "status": "error",
            "error": f"Invalid JSON response: {exc}",
            "incident_count": 0,
            "incidents": [],
        }

def get_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "snowfall,"
            "weather_code,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "wind_gusts_10m"
        ),
        "wind_speed_unit": "ms",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timezone": "auto",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        payload = response.json()
        current = payload.get("current") or {}

        return {
            "provider": "Open-Meteo",
            "status": "live",
            "observed_at": current.get("time"),
            "retrieved_at": utc_now_iso(),
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "timezone": payload.get("timezone"),
            "temperature_c": safe_float(current.get("temperature_2m")),
            "feels_like_c": safe_float(current.get("apparent_temperature")),
            "humidity_percent": safe_float(current.get("relative_humidity_2m")),
            "precipitation_mm": safe_float(current.get("precipitation")),
            "rain_1h_mm": safe_float(current.get("rain")),
            "snowfall_mm": safe_float(current.get("snowfall")),
            "wind_speed_mps": safe_float(current.get("wind_speed_10m")),
            "wind_direction_deg": safe_float(current.get("wind_direction_10m")),
            "wind_gust_mps": safe_float(current.get("wind_gusts_10m")),
            "cloud_percent": safe_float(current.get("cloud_cover")),
            "weather_code": current.get("weather_code"),
        }

    except requests.RequestException as exc:
        return {
            "provider": "Open-Meteo",
            "status": "error",
            "error": str(exc),
            "latitude": latitude,
            "longitude": longitude,
        }
    except ValueError as exc:
        return {
            "provider": "Open-Meteo",
            "status": "error",
            "error": f"Invalid JSON response: {exc}",
            "latitude": latitude,
            "longitude": longitude,
        }


def get_route_weather(route):
    coordinates = sample_route_coordinates(route, max_samples=3)

    with ThreadPoolExecutor(max_workers=min(3, max(1, len(coordinates)))) as executor:
        futures = [
            executor.submit(get_weather, latitude, longitude)
            for longitude, latitude in coordinates
        ]
        samples = [future.result() for future in futures]

    live_samples = [
        sample for sample in samples if sample.get("status") == "live"
    ]

    if not live_samples:
        return {
            "provider": "Open-Meteo",
            "status": "unavailable",
            "sample_count": len(samples),
            "live_sample_count": 0,
            "samples": samples,
            "temperature_c": None,
            "humidity_percent": None,
            "precipitation_mm": None,
            "rain_1h_mm": None,
            "wind_speed_mps": None,
            "wind_gust_mps": None,
            "weather_code": None,
            "retrieved_at": utc_now_iso(),
        }

    rain_values = [
        safe_float(sample.get("rain_1h_mm"))
        for sample in live_samples
    ]
    rain_values = [value for value in rain_values if value is not None]

    return {
        "provider": "Open-Meteo",
        "status": "live",
        "retrieved_at": utc_now_iso(),
        "sample_count": len(samples),
        "live_sample_count": len(live_samples),
        "temperature_c": (
            round(average(s.get("temperature_c") for s in live_samples), 2)
            if average(s.get("temperature_c") for s in live_samples) is not None
            else None
        ),
        "humidity_percent": (
            round(average(s.get("humidity_percent") for s in live_samples), 2)
            if average(s.get("humidity_percent") for s in live_samples) is not None
            else None
        ),
        "wind_speed_mps": (
            round(average(s.get("wind_speed_mps") for s in live_samples), 2)
            if average(s.get("wind_speed_mps") for s in live_samples) is not None
            else None
        ),
        "wind_gust_mps": (
            round(average(s.get("wind_gust_mps") for s in live_samples), 2)
            if average(s.get("wind_gust_mps") for s in live_samples) is not None
            else None
        ),
        "precipitation_mm": (
            round(average(s.get("precipitation_mm") for s in live_samples), 2)
            if average(s.get("precipitation_mm") for s in live_samples) is not None
            else None
        ),
        "rain_1h_mm": round(max(rain_values, default=0), 2),
        "weather_code": next(
            (
                sample.get("weather_code")
                for sample in live_samples
                if sample.get("weather_code") is not None
            ),
            None,
        ),
        "samples": samples,
    }



def get_weather_forecast(latitude, longitude, forecast_hours=24):
    """Return live Open-Meteo hourly forecast data for the next N hours."""
    forecast_hours = max(1, min(int(forecast_hours), 168))

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation_probability,"
            "precipitation,"
            "rain,"
            "showers,"
            "snowfall,"
            "weather_code,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "wind_gusts_10m"
        ),
        "forecast_hours": forecast_hours,
        "wind_speed_unit": "ms",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timezone": "auto",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []

        def value(name, index):
            values = hourly.get(name) or []
            return values[index] if index < len(values) else None

        rows = []
        for index, timestamp in enumerate(times):
            rows.append({
                "time": timestamp,
                "temperature_c": safe_float(value("temperature_2m", index)),
                "feels_like_c": safe_float(value("apparent_temperature", index)),
                "humidity_percent": safe_float(value("relative_humidity_2m", index)),
                "precipitation_probability_percent": safe_float(value("precipitation_probability", index)),
                "precipitation_mm": safe_float(value("precipitation", index)),
                "rain_mm": safe_float(value("rain", index)),
                "showers_mm": safe_float(value("showers", index)),
                "snowfall_cm": safe_float(value("snowfall", index)),
                "weather_code": value("weather_code", index),
                "cloud_percent": safe_float(value("cloud_cover", index)),
                "wind_speed_mps": safe_float(value("wind_speed_10m", index)),
                "wind_direction_deg": safe_float(value("wind_direction_10m", index)),
                "wind_gust_mps": safe_float(value("wind_gusts_10m", index)),
            })

        precipitation = [r["precipitation_mm"] for r in rows if r["precipitation_mm"] is not None]
        rain = [r["rain_mm"] for r in rows if r["rain_mm"] is not None]
        probability = [r["precipitation_probability_percent"] for r in rows if r["precipitation_probability_percent"] is not None]
        wind = [r["wind_speed_mps"] for r in rows if r["wind_speed_mps"] is not None]
        gusts = [r["wind_gust_mps"] for r in rows if r["wind_gust_mps"] is not None]

        return {
            "provider": "Open-Meteo",
            "status": "live",
            "retrieved_at": utc_now_iso(),
            "location": {
                "latitude": safe_float(payload.get("latitude"), latitude),
                "longitude": safe_float(payload.get("longitude"), longitude),
            },
            "timezone": payload.get("timezone"),
            "forecast_hours": len(rows),
            "hourly": rows,
            "summary": {
                "maximum_precipitation_mm": max(precipitation) if precipitation else 0.0,
                "total_precipitation_mm": round(sum(precipitation), 2) if precipitation else 0.0,
                "maximum_rain_mm": max(rain) if rain else 0.0,
                "maximum_precipitation_probability_percent": max(probability) if probability else 0.0,
                "maximum_wind_speed_mps": max(wind) if wind else 0.0,
                "maximum_wind_gust_mps": max(gusts) if gusts else 0.0,
            },
        }
    except requests.RequestException as exc:
        return {
            "provider": "Open-Meteo",
            "status": "error",
            "error": str(exc),
            "latitude": latitude,
            "longitude": longitude,
            "forecast_hours": 0,
            "hourly": [],
            "summary": {},
        }
    except ValueError as exc:
        return {
            "provider": "Open-Meteo",
            "status": "error",
            "error": f"Invalid JSON response: {exc}",
            "latitude": latitude,
            "longitude": longitude,
            "forecast_hours": 0,
            "hourly": [],
            "summary": {},
        }


def get_route_weather_forecast(route, forecast_hours=24):
    """Forecast weather at start, midpoint and end of the actual route."""
    coordinates = sample_route_coordinates(route, max_samples=3)
    with ThreadPoolExecutor(max_workers=min(3, max(1, len(coordinates)))) as executor:
        futures = [
            executor.submit(
                get_weather_forecast,
                latitude,
                longitude,
                forecast_hours=forecast_hours,
            )
            for longitude, latitude in coordinates
        ]
        samples = [future.result() for future in futures]

    live_samples = [sample for sample in samples if sample.get("status") == "live"]

    if not live_samples:
        return {
            "provider": "Open-Meteo",
            "status": "unavailable",
            "sample_count": len(samples),
            "live_sample_count": 0,
            "samples": samples,
            "summary": {},
        }

    summaries = [sample.get("summary", {}) for sample in live_samples]

    def maximum(name):
        values = [safe_float(summary.get(name)) for summary in summaries]
        values = [value for value in values if value is not None]
        return max(values) if values else 0.0

    return {
        "provider": "Open-Meteo",
        "status": "live",
        "retrieved_at": utc_now_iso(),
        "forecast_hours": max(sample.get("forecast_hours", 0) for sample in live_samples),
        "sample_count": len(samples),
        "live_sample_count": len(live_samples),
        "summary": {
            "maximum_precipitation_mm": round(maximum("maximum_precipitation_mm"), 2),
            "maximum_rain_mm": round(maximum("maximum_rain_mm"), 2),
            "maximum_precipitation_probability_percent": round(maximum("maximum_precipitation_probability_percent"), 2),
            "maximum_wind_speed_mps": round(maximum("maximum_wind_speed_mps"), 2),
            "maximum_wind_gust_mps": round(maximum("maximum_wind_gust_mps"), 2),
            "total_precipitation_mm": round(
                sum(safe_float(summary.get("total_precipitation_mm"), 0.0) for summary in summaries),
                2,
            ),
        },
        "samples": samples,
    }

def build_live_conditions(route):
    # These four providers are independent. Fetch them concurrently so a slow
    # provider does not block the other live feeds. Values and providers remain
    # exactly the same; only request scheduling changes.
    with ThreadPoolExecutor(max_workers=4) as executor:
        traffic_future = executor.submit(get_route_traffic, route)
        incidents_future = executor.submit(get_tomtom_incidents, route)
        weather_future = executor.submit(get_route_weather, route)
        traffic = traffic_future.result()
        incidents = incidents_future.result()
        weather = weather_future.result()

        # Forecast data is not required by the current cargo-risk model or
        # dashboard. Do not make three extra Open-Meteo requests per route
        # during the critical /routes response.
        weather_forecast = {
            "provider": "Open-Meteo",
            "status": "not_requested",
            "reason": "Forecast is loaded only when a forecast-specific feature requests it.",
            "forecast_hours": 0,
            "samples": [],
            "summary": {},
        }

    return {
        "data_source": "TomTom Traffic Flow + TomTom Traffic Incidents + Open-Meteo",
        "status": (
            "live"
            if traffic.get("status") == "live"
            or weather.get("status") == "live"
            else "unavailable"
        ),
        "retrieved_at": utc_now_iso(),

        "traffic": traffic,
        "incidents": incidents,
        "weather": weather,
        "weather_forecast": weather_forecast,

        # These are intentionally unavailable.
        # Do NOT replace them with fabricated road-quality values.
        "road_quality": None,
        "rough_road_percentage": None,
        "rough_road_km": None,
        "road_damage_exposure": None,

        "traffic_congestion_percent": traffic.get("congestion_percent"),
        "traffic_delay_seconds": traffic.get("delay_seconds"),
        "road_closure_detected": bool(
            traffic.get("road_closure_detected", False)
            or incidents.get("road_closure_detected", False)
        ),
        "incident_count": incidents.get("incident_count", 0),
        "roadworks_detected": bool(
            incidents.get("roadworks_detected", False)
        ),

        "temperature_c": weather.get("temperature_c"),
        "humidity_percent": weather.get("humidity_percent"),
        "precipitation_mm": weather.get("precipitation_mm"),
        "rain_1h_mm": weather.get("rain_1h_mm"),
        "wind_speed_mps": weather.get("wind_speed_mps"),
        "weather_code": weather.get("weather_code"),
    }


def get_live_conditions(route):
    return build_live_conditions(route)

