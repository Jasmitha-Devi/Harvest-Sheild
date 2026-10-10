import os
import math
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

REQUEST_TIMEOUT = 20
MAX_TRAFFIC_SAMPLES = 8


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
    samples = [
        get_tomtom_flow(latitude, longitude)
        for longitude, latitude in coordinates
    ]

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

    samples = [
        get_weather(latitude, longitude)
        for longitude, latitude in coordinates
    ]

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


def build_live_conditions(route):
    traffic = get_route_traffic(route)
    weather = get_route_weather(route)

    return {
        "data_source": "TomTom Traffic Flow + Open-Meteo",
        "status": (
            "live"
            if traffic.get("status") == "live"
            or weather.get("status") == "live"
            else "unavailable"
        ),
        "retrieved_at": utc_now_iso(),

        "traffic": traffic,
        "weather": weather,

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
