import os
from datetime import datetime, timezone

import requests
from concurrent.futures import ThreadPoolExecutor


APIMITRA_FUEL_URL = "https://api.apimitra.in/fuel"
APIMITRA_VEHICLE_URL = "https://api.apimitra.in/vehicle"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
REQUEST_TIMEOUT = 6


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_float(value):
    try:
        result = float(value)
        if result != result:
            return None
        return result
    except (TypeError, ValueError):
        return None


def _api_headers():
    headers = {
        "Accept": "application/json",
        "User-Agent": "HarvestShield/1.0",
    }
    api_key = os.getenv("APIMITRA_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def reverse_geocode_city(latitude, longitude):
    if latitude is None or longitude is None:
        return {
            "city": None,
            "state": None,
            "country": None,
            "status": "unavailable",
            "reason": "Destination coordinates are missing.",
        }

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "zoom": 10,
    }

    try:
        response = requests.get(
            NOMINATIM_REVERSE_URL,
            params=params,
            headers={"User-Agent": "HarvestShield/1.0"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        address = payload.get("address") or {}

        city = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("village")
        )

        return {
            "city": city,
            "state": address.get("state"),
            "country": address.get("country"),
            "status": "live",
            "display_name": payload.get("display_name"),
        }
    except (requests.RequestException, ValueError) as exc:
        return {
            "city": None,
            "state": None,
            "country": None,
            "status": "error",
            "reason": str(exc),
        }


def _normalize_city(city):
    value = str(city or "").strip()
    lowered = value.lower()

    aliases = {
        "warangal": "Warangal",
        "hanamkonda": "Warangal",
        "hyderabad": "Hyderabad",
        "secunderabad": "Hyderabad",
    }

    for key, canonical in aliases.items():
        if key in lowered:
            return canonical

    return value.title() if value else None


def _get_live_fuel_price_for_city(city, fuel_type, location):
    fuel_name = str(fuel_type or "").strip().lower()

    if fuel_name not in {"petrol", "diesel"}:
        return {
            "status": "unavailable",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": None,
            "retrieved_at": _now_iso(),
            "reason": (
                "Fuel type was not returned by a live vehicle source; "
                "no petrol/diesel assumption is used."
            ),
        }

    params = {"city": city, "fuel": fuel_name}

    try:
        response = requests.get(
            APIMITRA_FUEL_URL,
            params=params,
            headers=_api_headers(),
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "provider": "API Mitra",
                "price_per_litre": None,
                "fuel_type": fuel_name,
                "http_status": response.status_code,
                "retrieved_at": _now_iso(),
                "reason": response.text[:500],
                "city": city,
            }

        payload = response.json()
        price_object = payload.get("price") or {}
        fuel_object = price_object.get(fuel_name) or {}
        price = safe_float(fuel_object.get("price"))
        if price is None:
            for row in payload.get("data") or []:
                if str(row.get("location", "")).strip().lower() == city.lower():
                    price = safe_float((row.get(fuel_name) or {}).get("price"))
                    if price is not None:
                        break

        if price is None:
            return {
                "status": "unavailable",
                "provider": "API Mitra",
                "price_per_litre": None,
                "fuel_type": fuel_name,
                "retrieved_at": _now_iso(),
                "reason": "API Mitra returned no numeric fuel price for the destination city.",
                "city": city,
                "raw_status": payload.get("status"),
            }

        return {
            "status": "live",
            "provider": "API Mitra",
            "price_per_litre": round(price, 2),
            "fuel_type": fuel_name,
            "unit": fuel_object.get("unit", "per_litre"),
            "city": city,
            "state": location.get("state"),
            "source_updated_at": payload.get("fetched_at") or payload.get("updated_at"),
            "retrieved_at": _now_iso(),
        }
    except (requests.RequestException, ValueError) as exc:
        return {
            "status": "error",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": fuel_name,
            "city": city,
            "retrieved_at": _now_iso(),
            "reason": str(exc),
        }


def get_live_fuel_price(latitude, longitude, fuel_type=None):
    # Fuel type is itself a vehicle attribute. Under Harvest Shield's
    # live-only policy we must not silently assume petrol or diesel.
    fuel_name = str(fuel_type or "").strip().lower()

    if fuel_name not in {"petrol", "diesel"}:
        return {
            "status": "unavailable",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": None,
            "retrieved_at": _now_iso(),
            "reason": (
                "Fuel type was not returned by a live vehicle source; "
                "no petrol/diesel assumption is used."
            ),
        }

    location = reverse_geocode_city(latitude, longitude)
    city = _normalize_city(location.get("city"))

    if not city:
        return {
            "status": "unavailable",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": fuel_name,
            "retrieved_at": _now_iso(),
            "reason": "Destination city could not be resolved for live fuel lookup.",
            "location": location,
        }

    params = {
        "city": city,
        "fuel": fuel_name,
    }

    try:
        response = requests.get(
            APIMITRA_FUEL_URL,
            params=params,
            headers=_api_headers(),
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "provider": "API Mitra",
                "price_per_litre": None,
                "fuel_type": fuel_name,
                "http_status": response.status_code,
                "retrieved_at": _now_iso(),
                "reason": response.text[:500],
                "city": city,
            }

        payload = response.json()
        price_object = payload.get("price") or {}
        fuel_object = price_object.get(fuel_name) or {}

        # API Mitra can return a single city object under price or a data row.
        price = safe_float(fuel_object.get("price"))
        if price is None:
            for row in payload.get("data") or []:
                if str(row.get("location", "")).strip().lower() == city.lower():
                    price = safe_float((row.get(fuel_name) or {}).get("price"))
                    if price is not None:
                        break

        if price is None:
            return {
                "status": "unavailable",
                "provider": "API Mitra",
                "price_per_litre": None,
                "fuel_type": fuel_name,
                "retrieved_at": _now_iso(),
                "reason": "API Mitra returned no numeric fuel price for the destination city.",
                "city": city,
                "raw_status": payload.get("status"),
            }

        return {
            "status": "live",
            "provider": "API Mitra",
            "price_per_litre": round(price, 2),
            "fuel_type": fuel_name,
            "unit": fuel_object.get("unit", "per_litre"),
            "city": city,
            "state": location.get("state"),
            "source_updated_at": payload.get("fetched_at") or payload.get("updated_at"),
            "retrieved_at": _now_iso(),
        }

    except (requests.RequestException, ValueError) as exc:
        return {
            "status": "error",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": fuel_name,
            "city": city,
            "retrieved_at": _now_iso(),
            "reason": str(exc),
        }


def get_vehicle_configuration():
    return {
        "registration": os.getenv("HARVEST_SHIELD_VEHICLE_REGISTRATION", "").strip(),
        "maker": os.getenv("HARVEST_SHIELD_VEHICLE_MAKER", "").strip(),
        "model": os.getenv("HARVEST_SHIELD_VEHICLE_MODEL", "").strip(),
        "fuel_type": os.getenv("HARVEST_SHIELD_FUEL_TYPE", "diesel").strip().lower(),
    }


def get_live_vehicle_data():
    configuration = get_vehicle_configuration()
    registration = configuration.get("registration")

    if not registration:
        return {
            "status": "unavailable",
            "provider": "API Mitra Vehicle API",
            "km_per_litre": None,
            "retrieved_at": _now_iso(),
            "vehicle": configuration,
            "reason": (
                "No vehicle registration is configured. A model/benchmark mileage "
                "is intentionally not substituted."
            ),
        }

    try:
        response = requests.get(
            APIMITRA_VEHICLE_URL,
            params={"number": registration},
            headers=_api_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return {
                "status": "error",
                "provider": "API Mitra Vehicle API",
                "km_per_litre": None,
                "registration": registration,
                "http_status": response.status_code,
                "retrieved_at": _now_iso(),
                "reason": response.text[:500],
            }

        payload = response.json()
        vehicle = payload.get("vehicle")
        if isinstance(vehicle, dict):
            vehicle_data = vehicle
        else:
            vehicle_data = payload

        mileage = None
        for key in (
            "km_per_litre",
            "mileage_kmpl",
            "mileage",
            "fuel_efficiency_kmpl",
            "fuel_efficiency",
        ):
            mileage = safe_float(vehicle_data.get(key))
            if mileage is not None and mileage > 0:
                break

        return {
            "status": "live_api" if mileage is not None else "live_vehicle_no_mileage",
            "provider": "API Mitra Vehicle API",
            "km_per_litre": mileage,
            "registration": registration,
            "retrieved_at": _now_iso(),
            "vehicle": vehicle_data,
            "reason": (
                None
                if mileage is not None
                else "Live vehicle lookup returned vehicle information but no mileage field."
            ),
        }

    except (requests.RequestException, ValueError) as exc:
        return {
            "status": "error",
            "provider": "API Mitra Vehicle API",
            "km_per_litre": None,
            "registration": registration,
            "retrieved_at": _now_iso(),
            "reason": str(exc),
        }


def get_live_time_cost():
    return {
        "status": "unavailable",
        "cost_per_hour": None,
        "provider": None,
        "retrieved_at": _now_iso(),
        "reason": "No connected business-specific operating-cost source is configured.",
    }


def get_live_financial_inputs(destination_coordinates, route=None):
    latitude = None
    longitude = None

    if isinstance(destination_coordinates, (list, tuple)) and len(destination_coordinates) >= 2:
        latitude = safe_float(destination_coordinates[0])
        longitude = safe_float(destination_coordinates[1])

    # Vehicle lookup and destination reverse-geocoding are independent.
    # Run them together so one slow live provider does not serialize the other.
    with ThreadPoolExecutor(max_workers=2) as executor:
        vehicle_future = executor.submit(get_live_vehicle_data)
        location_future = executor.submit(reverse_geocode_city, latitude, longitude)
        vehicle = vehicle_future.result()
        location = location_future.result()

    vehicle_data = vehicle.get("vehicle") or {}
    fuel_type = (
        vehicle_data.get("fuel_type")
        or vehicle_data.get("fuelType")
        or vehicle_data.get("fuel")
        or vehicle.get("fuel_type")
    )

    # Reuse the already completed reverse-geocode response instead of making
    # a second Nominatim request inside get_live_fuel_price.
    city = _normalize_city(location.get("city"))

    if not city:
        fuel = {
            "status": "unavailable",
            "provider": "API Mitra",
            "price_per_litre": None,
            "fuel_type": fuel_type,
            "retrieved_at": _now_iso(),
            "reason": "Destination city could not be resolved for live fuel lookup.",
            "location": location,
        }
    else:
        fuel = _get_live_fuel_price_for_city(
            city=city,
            fuel_type=fuel_type,
            location=location,
        )
    time_cost = get_live_time_cost()

    return {
        "status": "live_partial" if fuel.get("status") == "live" else "unavailable",
        "retrieved_at": _now_iso(),
        "fuel": fuel,
        "vehicle_efficiency": vehicle,
        "time_cost": time_cost,
        "synthetic_values": False,
        "notes": [
            "Fuel price is retrieved from API Mitra only when a live vehicle source supplies the fuel type.",
            "No model, benchmark, configured fuel type, or default mileage is used as live data.",
            "Effective fuel cost remains unavailable unless both live fuel price and live vehicle efficiency are returned.",
            "No fabricated financial value is inserted when a live provider does not return the required field.",
        ],
    }
