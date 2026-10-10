# ============================================================
# HARVEST SHIELD
# CARGO-CENTRIC LIVE RISK ENGINE
# ============================================================

CROP_PROFILES = {
    "tomato": {
        "damage_factor": 1.00,
        "spoilage_factor": 1.00,
        "label": "Tomato",
        "ideal_temp_min": 10.0,
        "ideal_temp_max": 25.0,
        "humidity_sensitivity": 1.0,
    },
    "potato": {
        "damage_factor": 0.82,
        "spoilage_factor": 0.80,
        "label": "Potato",
        "ideal_temp_min": 4.0,
        "ideal_temp_max": 18.0,
        "humidity_sensitivity": 0.85,
    },
    "mango": {
        "damage_factor": 1.10,
        "spoilage_factor": 1.08,
        "label": "Mango",
        "ideal_temp_min": 10.0,
        "ideal_temp_max": 24.0,
        "humidity_sensitivity": 1.0,
    },
    "banana": {
        "damage_factor": 1.07,
        "spoilage_factor": 1.05,
        "label": "Banana",
        "ideal_temp_min": 12.0,
        "ideal_temp_max": 22.0,
        "humidity_sensitivity": 1.0,
    },
    "leafy vegetables": {
        "damage_factor": 1.15,
        "spoilage_factor": 1.18,
        "label": "Leafy Vegetables",
        "ideal_temp_min": 2.0,
        "ideal_temp_max": 10.0,
        "humidity_sensitivity": 1.10,
    },
    "other": {
        "damage_factor": 1.00,
        "spoilage_factor": 1.00,
        "label": "Other",
        "ideal_temp_min": 8.0,
        "ideal_temp_max": 25.0,
        "humidity_sensitivity": 1.0,
    },
}


def get_crop_profile(crop):
    crop_name = str(crop).strip().lower()
    return CROP_PROFILES.get(crop_name, CROP_PROFILES["other"])


def safe_number(value, default=0.0):
    try:
        result = float(value)
        if result != result:
            return float(default)
        return result
    except (TypeError, ValueError):
        return float(default)


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, safe_number(value)))


def _weighted_average(components):
    available = [(value, weight) for value, weight in components if value is not None]
    if not available:
        return None
    total_weight = sum(weight for _, weight in available)
    if total_weight <= 0:
        return None
    return sum(value * weight for value, weight in available) / total_weight


def calculate_cargo_risk(
    crop,
    quantity_kg,
    cargo_value,
    fragility,
    distance_km,
    duration_minutes,
    traffic_risk,
    incident_risk,
    temperature_risk,
    weather_risk,
    road_quality=None,
    rough_road_percentage=None,
    road_damage_exposure=None,
):
    crop_profile = get_crop_profile(crop)
    damage_factor = crop_profile["damage_factor"]
    spoilage_factor = crop_profile["spoilage_factor"]

    fragility_scores = {
        "low": 25,
        "medium": 50,
        "high": 75,
        "very_high": 95,
    }
    fragility_score = fragility_scores.get(
        str(fragility).strip().lower(),
        50,
    )

    traffic_risk = clamp(traffic_risk) if traffic_risk is not None else None
    incident_risk = clamp(incident_risk) if incident_risk is not None else None
    temperature_risk = clamp(temperature_risk) if temperature_risk is not None else None
    weather_risk = clamp(weather_risk) if weather_risk is not None else None

    mapped_road_quality = safe_number(road_quality, None) if road_quality is not None else None
    mapped_rough_percentage = clamp(rough_road_percentage) if rough_road_percentage is not None else None

    if road_damage_exposure is not None:
        mapped_road_damage_exposure = clamp(road_damage_exposure)
    elif mapped_road_quality is not None:
        mapped_road_damage_exposure = clamp(100 - mapped_road_quality)
    elif mapped_rough_percentage is not None:
        mapped_road_damage_exposure = mapped_rough_percentage
    else:
        mapped_road_damage_exposure = None

    road_risk = None
    if mapped_road_damage_exposure is not None or mapped_rough_percentage is not None:
        road_values = [
            value
            for value in (
                mapped_road_damage_exposure,
                mapped_rough_percentage,
            )
            if value is not None
        ]
        road_risk = clamp(max(road_values)) if road_values else None

    duration = safe_number(duration_minutes, None)
    time_risk = min(100, (duration / 300) * 100) if duration is not None else None

    damage_components = [(fragility_score, 0.40)]
    if traffic_risk is not None:
        damage_components.append((traffic_risk, 0.25))
    if incident_risk is not None:
        damage_components.append((incident_risk, 0.15))
    if road_risk is not None:
        damage_components.append((road_risk, 0.20))

    damage_base = _weighted_average(damage_components)
    damage_risk = round(min(100, damage_base * damage_factor), 2) if damage_base is not None else None

    spoilage_components = []
    if time_risk is not None:
        spoilage_components.append((time_risk, 0.30))
    if temperature_risk is not None:
        spoilage_components.append((temperature_risk, 0.20))
    if weather_risk is not None:
        spoilage_components.append((weather_risk, 0.15))
    # Keep a small cargo-fragility contribution so the model remains cargo-centric.
    spoilage_components.append((fragility_score, 0.35))

    spoilage_base = _weighted_average(spoilage_components)
    spoilage_risk = round(min(100, spoilage_base * spoilage_factor), 2) if spoilage_base is not None else None

    overall_components = []
    if damage_risk is not None:
        overall_components.append((damage_risk, 0.55))
    if spoilage_risk is not None:
        overall_components.append((spoilage_risk, 0.45))

    overall_risk_value = _weighted_average(overall_components)
    overall_risk = round(min(100, overall_risk_value), 2) if overall_risk_value is not None else None

    risk_contributions = {
        "cargo_fragility": round(fragility_score * 0.40 * 0.55 * damage_factor, 2),
        "live_traffic": round(traffic_risk * 0.25 * 0.55 * damage_factor, 2) if traffic_risk is not None else None,
        "live_incidents": round(incident_risk * 0.15 * 0.55 * damage_factor, 2) if incident_risk is not None else None,
        "mapped_road_quality": round(road_risk * 0.20 * 0.55 * damage_factor, 2) if road_risk is not None else None,
        "travel_time": round(time_risk * 0.30 * 0.45 * spoilage_factor, 2) if time_risk is not None else None,
        "temperature": round(temperature_risk * 0.20 * 0.45 * spoilage_factor, 2) if temperature_risk is not None else None,
        "weather": round(weather_risk * 0.15 * 0.45 * spoilage_factor, 2) if weather_risk is not None else None,
    }

    comparable_contributions = {k: v for k, v in risk_contributions.items() if v is not None}
    primary_risk_driver = max(comparable_contributions, key=comparable_contributions.get) if comparable_contributions else "cargo_fragility"
    primary_risk_labels = {
        "cargo_fragility": "Cargo fragility",
        "live_traffic": "Live traffic",
        "live_incidents": "Live incidents",
        "mapped_road_quality": "Mapped road quality",
        "travel_time": "Travel time",
        "temperature": "Cargo-specific temperature",
        "weather": "Weather",
    }

    if overall_risk is None:
        risk_level = None
        safety_score = None
    elif overall_risk < 30:
        risk_level = "Low"
        safety_score = round(100 - overall_risk, 2)
    elif overall_risk < 60:
        risk_level = "Moderate"
        safety_score = round(100 - overall_risk, 2)
    elif overall_risk < 80:
        risk_level = "High"
        safety_score = round(100 - overall_risk, 2)
    else:
        risk_level = "Critical"
        safety_score = round(100 - overall_risk, 2)

    cargo_value_number = max(0, safe_number(cargo_value))
    expected_loss = round(cargo_value_number * overall_risk / 100, 2) if overall_risk is not None else None
    if expected_loss is not None:
        expected_loss = min(expected_loss, cargo_value_number)
    value_preserved = round(max(0, cargo_value_number - expected_loss), 2) if expected_loss is not None else None

    risk_factors = []
    if fragility_score >= 75:
        risk_factors.append("Cargo has high physical fragility")
    if traffic_risk is not None and traffic_risk >= 40:
        risk_factors.append("Live traffic congestion is increasing cargo exposure")
    if incident_risk is not None and incident_risk >= 20:
        risk_factors.append("Route-proximate live traffic incidents were detected")
    if road_risk is not None and road_risk >= 40:
        risk_factors.append("Mapped road-surface metadata indicates elevated physical road exposure")
    if time_risk is not None and time_risk >= 50:
        risk_factors.append("Long travel duration increases perishability exposure")
    if temperature_risk is not None and temperature_risk >= 50:
        risk_factors.append(f"Current temperature is outside the modeled {crop_profile['label']} handling range")
    if weather_risk is not None and weather_risk >= 50:
        risk_factors.append("Current precipitation/humidity conditions increase weather exposure")
    if incident_risk is None:
        risk_factors.append("TomTom incident feed is unavailable; no incident value was assumed")
    if mapped_road_quality is None:
        risk_factors.append("No mapped OSM surface/smoothness value was available for this route")
    if not risk_factors:
        risk_factors.append("No major live environmental risk driver detected")

    return {
        "status": "LIVE_MODEL" if overall_risk is not None else "UNAVAILABLE",
        "calculation_status": "LIVE_MODEL" if overall_risk is not None else "UNAVAILABLE",
        "crop": crop,
        "crop_profile": crop_profile["label"],
        "crop_factors": {
            "damage_factor": damage_factor,
            "spoilage_factor": spoilage_factor,
            "ideal_temp_min_c": crop_profile["ideal_temp_min"],
            "ideal_temp_max_c": crop_profile["ideal_temp_max"],
            "humidity_sensitivity": crop_profile["humidity_sensitivity"],
        },
        "quantity_kg": quantity_kg,
        "cargo_value": cargo_value,
        "risk_analysis": {
            "fragility_score": fragility_score,
            "traffic_risk": round(traffic_risk, 2) if traffic_risk is not None else None,
            "incident_risk": round(incident_risk, 2) if incident_risk is not None else None,
            "time_risk": round(time_risk, 2) if time_risk is not None else None,
            "temperature_risk": round(temperature_risk, 2) if temperature_risk is not None else None,
            "weather_risk": round(weather_risk, 2) if weather_risk is not None else None,
            "damage_risk": damage_risk,
            "spoilage_risk": spoilage_risk,
            "overall_risk": overall_risk,
            "risk_level": risk_level,
            "safety_score": safety_score,
            "road_quality": round(mapped_road_quality, 1) if mapped_road_quality is not None else None,
            "rough_road_percentage": round(mapped_rough_percentage, 1) if mapped_rough_percentage is not None else None,
            "road_damage_exposure": round(mapped_road_damage_exposure, 1) if mapped_road_damage_exposure is not None else None,
            "road_risk": round(road_risk, 2) if road_risk is not None else None,
            "risk_contributions": risk_contributions,
            "primary_risk_driver": primary_risk_driver,
            "primary_risk_driver_label": primary_risk_labels.get(primary_risk_driver, "Cargo risk"),
        },
        "financial_analysis": {
            "expected_loss": expected_loss,
            "value_preserved": value_preserved,
        },
        "risk_factors": risk_factors,
    }


def extract_live_risk_signals(conditions):
    conditions = conditions or {}
    risk_signals = conditions.get("risk_signals") or {}
    traffic = conditions.get("traffic") or {}
    incidents = conditions.get("incidents") or {}
    weather = conditions.get("weather") or {}

    traffic_live = traffic.get("status") == "live"
    weather_live = weather.get("status") == "live"
    incidents_live = incidents.get("status") == "live"

    traffic_congestion = safe_number(traffic.get("congestion_percent"), None) if traffic_live else None
    traffic_delay_seconds = safe_number(traffic.get("delay_seconds"), None) if traffic_live else None

    traffic_risk = None
    if traffic_live:
        congestion_risk = clamp(traffic_congestion * 2.0) if traffic_congestion is not None else None
        delay_risk = clamp(traffic_delay_seconds / 6.0) if traffic_delay_seconds is not None else None
        configured_traffic_risk = risk_signals.get("traffic_risk")
        configured_traffic_risk = safe_number(configured_traffic_risk) if configured_traffic_risk is not None else None
        values = [v for v in [congestion_risk, delay_risk, configured_traffic_risk] if v is not None]
        traffic_risk = max(values) if values else None

    incident_count = safe_number(incidents.get("incident_count"), None) if incidents_live else None
    incident_risk = None
    road_closure = None
    roadworks = None
    if incidents_live:
        road_closure = bool(incidents.get("road_closure_detected", False))
        roadworks = bool(incidents.get("roadworks_detected", False))
        configured_incident_risk = risk_signals.get("incident_risk")
        configured_incident_risk = safe_number(configured_incident_risk) if configured_incident_risk is not None else None
        incident_values = [v for v in [min(100, incident_count * 1.5) if incident_count is not None else None, configured_incident_risk] if v is not None]
        incident_risk = max(incident_values) if incident_values else 0.0
        if roadworks:
            incident_risk = max(incident_risk, 30.0)
        if road_closure:
            incident_risk = max(incident_risk, 80.0)

    temperature_c = safe_number(weather.get("temperature_c"), None) if weather_live else None
    humidity_percent = safe_number(weather.get("humidity_percent"), None) if weather_live else None
    precipitation_mm = safe_number(weather.get("precipitation_mm"), None) if weather_live else None
    rain_1h_mm = safe_number(weather.get("rain_1h_mm"), None) if weather_live else None

    return {
        "traffic_risk": round(traffic_risk, 2) if traffic_risk is not None else None,
        "incident_risk": round(incident_risk, 2) if incident_risk is not None else None,
        "temperature_c": round(temperature_c, 2) if temperature_c is not None else None,
        "humidity_percent": round(humidity_percent, 2) if humidity_percent is not None else None,
        "precipitation_mm": round(precipitation_mm, 2) if precipitation_mm is not None else None,
        "rain_1h_mm": round(rain_1h_mm, 2) if rain_1h_mm is not None else None,
        "traffic_congestion_percent": round(traffic_congestion, 2) if traffic_congestion is not None else None,
        "traffic_delay_seconds": round(traffic_delay_seconds, 2) if traffic_delay_seconds is not None else None,
        "incident_count": int(incident_count) if incident_count is not None else None,
        "road_closure_detected": road_closure,
        "roadworks_detected": roadworks,
        "road_quality": safe_number(conditions.get("road_quality")) if conditions.get("road_quality") is not None else None,
        "rough_road_percentage": safe_number(conditions.get("rough_road_percentage")) if conditions.get("rough_road_percentage") is not None else None,
        "road_damage_exposure": safe_number(conditions.get("road_damage_exposure")) if conditions.get("road_damage_exposure") is not None else None,
        "traffic_live": traffic_live,
        "incidents_live": incidents_live,
        "weather_live": weather_live,
    }


def _cargo_temperature_risk(crop, temperature_c):
    if temperature_c is None:
        return None
    profile = get_crop_profile(crop)
    low = profile["ideal_temp_min"]
    high = profile["ideal_temp_max"]
    if low <= temperature_c <= high:
        return 5.0
    distance = low - temperature_c if temperature_c < low else temperature_c - high
    return clamp(distance * 12.0)


def analyze_route_risk(
    route,
    conditions,
    crop,
    quantity_kg,
    cargo_value,
    fragility,
):
    live_signals = extract_live_risk_signals(conditions)

    temperature_risk = _cargo_temperature_risk(
        crop,
        live_signals["temperature_c"],
    )

    weather_components = []
    if live_signals["humidity_percent"] is not None:
        weather_components.append(max(0.0, min(100.0, (live_signals["humidity_percent"] - 50) * 1.5)))
    if live_signals["precipitation_mm"] is not None:
        weather_components.append(max(0.0, min(100.0, live_signals["precipitation_mm"] * 8)))
    if live_signals["rain_1h_mm"] is not None:
        weather_components.append(max(0.0, min(100.0, live_signals["rain_1h_mm"] * 10)))
    weather_risk = max(weather_components) if weather_components else None

    return calculate_cargo_risk(
        crop=crop,
        quantity_kg=quantity_kg,
        cargo_value=cargo_value,
        fragility=fragility,
        distance_km=route.get("distance_km", 0),
        duration_minutes=route.get("duration_minutes", 0),
        traffic_risk=live_signals["traffic_risk"],
        incident_risk=live_signals["incident_risk"],
        temperature_risk=temperature_risk,
        weather_risk=weather_risk,
        road_quality=live_signals["road_quality"],
        rough_road_percentage=live_signals["rough_road_percentage"],
        road_damage_exposure=live_signals["road_damage_exposure"],
    )

