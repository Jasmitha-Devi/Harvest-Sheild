from datetime import datetime, timezone


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


def _is_live_vehicle_status(status):
    return str(status or "").strip().lower() in {
        "live",
        "live_api",
        "api_live",
    }


def calculate_economic_cost(route, expected_cargo_loss, live_financial_inputs):
    """Calculate economic cost using only externally returned live inputs.

    No benchmark mileage, default fuel price, default fuel type, or business
    time-cost assumption is used here.
    """
    distance_km = safe_float((route or {}).get("distance_km"))
    expected_loss = safe_float(expected_cargo_loss)

    live_inputs = live_financial_inputs or {}
    fuel = live_inputs.get("fuel") or {}
    vehicle = live_inputs.get("vehicle_efficiency") or {}
    time_cost = live_inputs.get("time_cost") or {}

    fuel_price = safe_float(fuel.get("price_per_litre"))
    fuel_efficiency = safe_float(vehicle.get("km_per_litre"))

    fuel_status = str(fuel.get("status") or "").strip().lower()
    vehicle_status = str(vehicle.get("status") or "").strip().lower()
    time_status = str(time_cost.get("status") or "").strip().lower()

    fuel_litres = None
    fuel_cost = None
    effective_total_cost = None

    if (
        distance_km is not None
        and distance_km > 0
        and fuel_price is not None
        and fuel_price > 0
        and fuel_efficiency is not None
        and fuel_efficiency > 0
        and fuel_status == "live"
        and _is_live_vehicle_status(vehicle_status)
    ):
        fuel_litres = distance_km / fuel_efficiency
        fuel_cost = fuel_litres * fuel_price

    if fuel_cost is not None and expected_loss is not None:
        effective_total_cost = fuel_cost + expected_loss

    missing_inputs = []
    if fuel_price is None or fuel_status != "live":
        missing_inputs.append("live_fuel_price")
    if fuel_efficiency is None or not _is_live_vehicle_status(vehicle_status):
        missing_inputs.append("live_vehicle_efficiency")
    if time_status != "live":
        missing_inputs.append("live_business_time_cost")

    return {
        "fuel_litres": round(fuel_litres, 4) if fuel_litres is not None else None,
        "fuel_cost": round(fuel_cost, 2) if fuel_cost is not None else None,
        "expected_cargo_loss": round(expected_loss, 2) if expected_loss is not None else None,
        "effective_total_cost": (
            round(effective_total_cost, 2)
            if effective_total_cost is not None
            else None
        ),
        "fuel_price_per_litre": (
            round(fuel_price, 4)
            if fuel_price is not None and fuel_status == "live"
            else None
        ),
        "fuel_efficiency_km_per_litre": (
            round(fuel_efficiency, 4)
            if fuel_efficiency is not None and _is_live_vehicle_status(vehicle_status)
            else None
        ),
        "missing_inputs": missing_inputs,
        "pricing_status": "LIVE" if effective_total_cost is not None else "INCOMPLETE",
        "retrieved_at": _now_iso(),
    }


def calculate_economic_analysis(
    route,
    risk_analysis,
    cargo_value,
    quantity_kg,
    live_financial_inputs=None,
):
    cargo_value_number = safe_float(cargo_value)
    risk = safe_float((risk_analysis or {}).get("overall_risk"))

    expected_loss = None
    if cargo_value_number is not None and cargo_value_number > 0 and risk is not None:
        expected_loss = min(
            cargo_value_number,
            cargo_value_number * risk / 100.0,
        )

    economic_cost = calculate_economic_cost(
        route,
        expected_loss,
        live_financial_inputs or {},
    )

    value_preserved = None
    if cargo_value_number is not None and expected_loss is not None:
        value_preserved = max(0.0, cargo_value_number - expected_loss)

    return {
        "status": economic_cost["pricing_status"],
        "expected_cargo_loss": economic_cost["expected_cargo_loss"],
        "value_preserved": round(value_preserved, 2) if value_preserved is not None else None,
        "fuel_litres": economic_cost["fuel_litres"],
        "fuel_cost": economic_cost["fuel_cost"],
        "effective_total_cost": economic_cost["effective_total_cost"],
        "fuel_price_per_litre": economic_cost["fuel_price_per_litre"],
        "fuel_efficiency_km_per_litre": economic_cost["fuel_efficiency_km_per_litre"],
        "missing_inputs": economic_cost["missing_inputs"],
        "pricing_status": economic_cost["pricing_status"],
        "retrieved_at": economic_cost["retrieved_at"],
        "live_financial_inputs": live_financial_inputs or {},
        "notes": [
            "Fuel price is used only when returned live by API Mitra.",
            "Vehicle efficiency is used only when returned by a live vehicle source.",
            "No benchmark mileage, default fuel price, default fuel type, or assumed time cost is used.",
            "Effective cost = live fuel cost + modeled expected cargo loss when all required live inputs are present.",
        ],
    }
