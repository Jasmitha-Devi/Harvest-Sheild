# ============================================================
# HARVEST SHIELD
# LIVE CONDITION ENGINE
# ============================================================

def safe_number(value, default=0.0):
    try:
        if value is None:
            return float(default)

        result = float(value)

        if result != result:
            return float(default)

        return result

    except (TypeError, ValueError):
        return float(default)


def get_route_conditions(
    route_id,
    distance_km,
    duration_minutes,
):
    """
    Route-condition compatibility layer.

    IMPORTANT:
    This function intentionally does NOT invent road-quality,
    rough-road, temperature, or weather values.

    Real live traffic, incidents, weather and forecast data
    are obtained by live_data_engine.py.

    Road-quality data remains unavailable until a real
    road-quality provider is connected.
    """

    distance = safe_number(distance_km)
    duration = safe_number(duration_minutes)

    return {
        "road_quality": None,

        "rough_road_percentage": None,

        "rough_road_km": None,

        "road_damage_exposure": None,

        "temperature_risk": None,

        "weather_risk": None,

        "time_exposure": round(
            min(
                100,
                duration / 300 * 100,
            ),
            2,
        ),

        "data_source": (
            "No synthetic route-condition data; "
            "live conditions supplied by live_data_engine.py"
        ),
    }