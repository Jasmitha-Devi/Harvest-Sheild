from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Body,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from concurrent.futures import ThreadPoolExecutor

from route_engine import (
    get_routes as route_engine_get_routes,
)

from scenario_engine import (
    generate_route_scenarios,
)

from live_data_engine import (
    build_live_conditions,
)

from risk_engine import (
    analyze_route_risk,
)

from economic_engine import (
    calculate_economic_analysis,
)

from live_financial_data import (
    get_live_financial_inputs,
)

from multimodal_engine import (
    analyze_multimodal_routes,
)

from stop_planning import find_route_stops


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Harvest Shield API",

    description=(
        "Cargo-centric route intelligence "
        "using external live data."
    ),

    version="6.3.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5799",
        "http://127.0.0.1:5799",
    ],

    # Also allow local Vite dev/preview ports without opening CORS to arbitrary
    # remote origins. This prevents a port change from turning a healthy API
    # into a browser-level "Failed to fetch" error.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# HELPERS
# ============================================================

def number(
    value,
    default=None,
):
    try:

        result = float(value)

        if result != result:
            return default

        return result

    except (
        TypeError,
        ValueError,
    ):

        return default


def route_is_live_complete(
    route
):
    conditions = route.get("conditions") or {}
    traffic = conditions.get("traffic") or {}
    weather = conditions.get("weather") or {}

    # Traffic + current weather are the required live feeds for the
    # base cargo-risk model. Incidents are optional: if the TomTom
    # incident product is unavailable for the key, we never fabricate
    # an incident count of zero.
    return (
        traffic.get("status") == "live"
        and weather.get("status") == "live"
        and number(traffic.get("congestion_percent")) is not None
        and number(weather.get("temperature_c")) is not None
        and number(weather.get("humidity_percent")) is not None
    )


def route_effective_cost(
    route
):
    economic = (
        route.get(
            "economic_analysis"
        )
        or {}
    )

    return number(
        economic.get(
            "effective_total_cost"
        )
    )


def _risk_payload(route):
    value = route.get("risk_analysis") or {}
    nested = value.get("risk_analysis")
    return nested if isinstance(nested, dict) else value


def simplify_route_geometry(geometry, max_points=1200):
    """Reduce response geometry using only coordinates returned by OSRM.

    This changes only the amount of geometry sent to the browser. It does not
    create, move, or invent road coordinates; selected points are taken from
    the original OSRM geometry and the first/last points are always preserved.
    """
    if not isinstance(geometry, dict):
        return geometry

    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) <= max_points:
        return geometry

    step = (len(coordinates) - 1) / float(max_points - 1)
    simplified = []

    for index in range(max_points):
        source_index = int(round(index * step))
        if source_index >= len(coordinates):
            source_index = len(coordinates) - 1
        point = coordinates[source_index]
        if point not in simplified:
            simplified.append(point)

    return {
        **geometry,
        "coordinates": simplified,
    }


def compact_route_geometry(route, max_points=1200):
    compacted = dict(route)
    compacted["geometry"] = simplify_route_geometry(
        route.get("geometry"),
        max_points=max_points,
    )
    return compacted


def route_expected_loss(
    route
):
    economic = route.get("economic_analysis") or {}
    direct = number(economic.get("expected_cargo_loss"))
    if direct is not None:
        return direct

    financial = (route.get("risk_analysis") or {}).get("financial_analysis") or {}
    return number(financial.get("expected_loss"))


def route_risk(
    route
):
    risk = _risk_payload(route)
    return number(risk.get("overall_risk"))


def route_safety(
    route
):
    risk = _risk_payload(route)
    return number(risk.get("safety_score"))


# ============================================================
# RECOMMENDATION
# ============================================================

def build_recommendation(
    routes,
    cargo_value,
):
    live_routes = [
        route
        for route in routes
        if route_is_live_complete(route) and route_risk(route) is not None
    ]

    if not live_routes:

        return {
            "available":
                False,

            "route_id":
                None,

            "route_name":
                None,

            "reason":
                (
                    "No recommendation is available because "
                    "live traffic or current-weather data is incomplete."
                ),

            "effective_total_cost":
                None,

            "expected_cargo_loss":
                None,

            "value_preserved":
                None,

            "safety_score":
                None,

            "overall_risk":
                None,
        }

    def recommendation_key(route):
        effective = route_effective_cost(route)
        expected_loss = route_expected_loss(route)
        risk = route_risk(route)
        return (
            0 if effective is not None else 1,
            effective if effective is not None else float("inf"),
            expected_loss if expected_loss is not None else float("inf"),
            risk if risk is not None else float("inf"),
            number(route.get("distance_km"), float("inf")),
        )

    best = min(live_routes, key=recommendation_key)

    expected_loss = (
        route_expected_loss(
            best
        )
    )

    effective_cost = (
        route_effective_cost(
            best
        )
    )

    safety = (
        route_safety(
            best
        )
    )

    risk = (
        route_risk(
            best
        )
    )

    cargo_value_number = number(
        cargo_value
    )

    preserved = None

    if (
        expected_loss is not None

        and cargo_value_number
        is not None
    ):

        preserved = max(
            0.0,

            cargo_value_number
            - expected_loss,
        )

    return {
        "available":
            True,

        "route_id":
            best.get(
                "route_id"
            ),

        "route_name":
            best.get(
                "route_name"
            ),

        "basis": (
            "LIVE_ECONOMIC_COST"
            if route_effective_cost(best) is not None
            else "LIVE_CARGO_RISK"
        ),

        "reason": (
            (
                "Selected using the lowest modeled effective economic cost "
                "among routes with complete live traffic and current-weather "
                "inputs."
            )
            if effective_cost is not None
            else (
                "Effective operating cost is unavailable because the required "
                "live financial inputs were not returned. The route is selected "
                "using modeled cargo risk and expected cargo loss from the "
                "available live condition feeds; no fallback operating cost is used."
            )
        ),

        "effective_total_cost":
            (
                round(
                    effective_cost,
                    2,
                )
                if effective_cost
                is not None
                else None
            ),

        "expected_cargo_loss":
            (
                round(
                    expected_loss,
                    2,
                )
                if expected_loss
                is not None
                else None
            ),

        "expected_loss":
            (
                round(
                    expected_loss,
                    2,
                )
                if expected_loss
                is not None
                else None
            ),

        "value_preserved":
            (
                round(
                    preserved,
                    2,
                )
                if preserved
                is not None
                else None
            ),

        "safety_score":
            (
                round(
                    safety,
                    2,
                )
                if safety
                is not None
                else None
            ),

        "overall_risk":
            (
                round(
                    risk,
                    2,
                )
                if risk
                is not None
                else None
            ),
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service":
            "Harvest Shield API",

        "status":
            "online",

        "version":
            "6.2.0",

        "data_mode":
            "LIVE_EXTERNAL_DATA",

        "synthetic_live_values":
            False,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    loaded_code = getattr(route_engine_get_routes, "__code__", None)
    return {
        "status": "healthy",
        "backend_version": "6.3.0",
        "data_mode": "LIVE_EXTERNAL_DATA",
        "synthetic_live_values": False,
        "route_engine_file": (
            loaded_code.co_filename
            if loaded_code is not None
            else "unknown"
        ),
        "routing_contract": (
            "real OSRM routes with coordinate-order and distance sanity checks"
        ),
        "providers": {
            "routing": "OSRM",
            "traffic": "TomTom Traffic Flow API",
            "incidents": "TomTom Traffic Incidents API",
            "weather": "Open-Meteo Current Weather API",
            "forecast": "Open-Meteo Forecast API",
            "fuel_price": "API Mitra Fuel Prices",
            "vehicle_mileage": "Live vehicle mileage API only; no benchmark fallback",
        },
    }


# ============================================================
# ROUTE ANALYSIS HELPERS
# ============================================================

def _unavailable_financial_inputs(reason):
    return {
        "status": "unavailable",
        "synthetic_values": False,
        "fuel": {
            "status": "unavailable",
            "price_per_litre": None,
            "provider": "API Mitra",
            "reason": reason,
        },
        "vehicle_efficiency": {
            "status": "unavailable",
            "km_per_litre": None,
        },
        "time_cost": {
            "status": "unavailable",
            "cost_per_hour": None,
        },
        "missing_inputs": ["financial provider error"],
        "notes": [
            "Live financial provider failed; no synthetic value was inserted."
        ],
    }


def _get_financial_inputs_once(destination_coordinates):
    """Fetch destination financial inputs once for the whole request.

    Fuel price and vehicle information are not route-specific for the same
    destination, so fetching them once prevents duplicate external calls when
    OSRM returns multiple real alternatives.
    """
    try:
        live_financial_inputs = get_live_financial_inputs(
            destination_coordinates=destination_coordinates,
            route=None,
        )
    except Exception as financial_error:
        live_financial_inputs = _unavailable_financial_inputs(
            str(financial_error)
        )

    # Never let benchmark/model mileage become a live value.
    vehicle_efficiency = (
        live_financial_inputs.get("vehicle_efficiency") or {}
    )
    vehicle_status = str(
        vehicle_efficiency.get("status") or ""
    ).strip().lower()

    if vehicle_status not in {"live", "live_api", "api_live"}:
        live_financial_inputs["vehicle_efficiency"] = {
            **vehicle_efficiency,
            "status": "unavailable",
            "km_per_litre": None,
            "reason": (
                "Vehicle mileage was not returned by a live vehicle source. "
                "Model/benchmark mileage is intentionally excluded."
            ),
        }

    live_financial_inputs["synthetic_values"] = False
    return live_financial_inputs


def _analyze_route_conditions_and_risk(
    route,
    crop,
    quantity_kg,
    cargo_value,
    fragility,
):
    """Build live conditions and risk for one real route.

    This function does not perform financial analysis. Independent real route
    alternatives can therefore be processed concurrently, while shared
    destination financial inputs are fetched only once by the caller.
    """
    route_copy = dict(route)

    if not route_copy.get("geometry"):
        raise RuntimeError(
            f"Route {route_copy.get('route_name')} has no geometry."
        )

    live_conditions = build_live_conditions(route_copy)

    risk_analysis = analyze_route_risk(
        route=route_copy,
        conditions=live_conditions,
        crop=crop,
        quantity_kg=quantity_kg,
        cargo_value=cargo_value,
        fragility=fragility,
    )

    return route_copy, live_conditions, risk_analysis


# ============================================================
# ROUTE ANALYSIS
# ============================================================

@app.get("/routes")
def routes(

    start: str = Query(
        ...,
        min_length=1,
    ),

    end: str = Query(
        ...,
        min_length=1,
    ),

    crop: str = Query(
        ...,
        min_length=1,
    ),

    quantity_kg: float = Query(
        ...,
        gt=0,
    ),

    cargo_value: float = Query(
        ...,
        gt=0,
    ),

    fragility: str = Query(
        ...,
        min_length=1,
    ),

    transport_mode: str = Query(
        "road",
        min_length=1,
    ),
):

    try:

        from time import perf_counter
        request_started = perf_counter()

        requested_transport_mode = str(transport_mode).strip().lower()
        if requested_transport_mode not in {"road", "multimodal"}:
            raise HTTPException(
                status_code=400,
                detail=(
                    "transport_mode must be either 'road' or 'multimodal'."
                ),
            )

        # ====================================================
        # 1. REAL ROUTING
        # ====================================================

        route_data = route_engine_get_routes(
            start,
            end,
        )
        print(
            f"[TIMING] routing={perf_counter() - request_started:.2f}s"
        )

        # ====================================================
        # 2. REAL ROUTE SCENARIOS
        # ====================================================

        route_scenarios = (
            generate_route_scenarios(
                route_data
            )
        )

        analyzed_routes = []

        real_routes = route_scenarios.get("routes", [])
        if not real_routes:
            raise RuntimeError("Routing service returned no real route alternatives.")

        # Shared destination financial inputs are fetched exactly once. This
        # avoids repeating reverse-geocoding/API Mitra calls for every route.
        destination_coordinates = route_data.get("destination_coordinates")

        # Route live-data and risk calculations are independent across routes,
        # so run the real alternatives concurrently. This is the main response-
        # time fix when OSRM returns 2 or 3 alternatives.
        worker_count = min(3, max(1, len(real_routes)))
        with ThreadPoolExecutor(max_workers=worker_count + 1) as executor:
            financial_future = executor.submit(
                _get_financial_inputs_once,
                destination_coordinates,
            )

            route_futures = [
                executor.submit(
                    _analyze_route_conditions_and_risk,
                    route,
                    crop,
                    quantity_kg,
                    cargo_value,
                    fragility,
                )
                for route in real_routes
            ]

            live_financial_inputs = financial_future.result()

            analyzed_work = [
                future.result()
                for future in route_futures
            ]

        print(
            f"[TIMING] routing_plus_live={perf_counter() - request_started:.2f}s"
        )

        # ====================================================
        # ECONOMIC + RESPONSE ANALYSIS
        # ====================================================

        for route_copy, live_conditions, risk_analysis in analyzed_work:

            # =================================================
            # LIVE-ONLY FINANCIAL POLICY
            # =================================================
            # Financial inputs are shared across the real alternatives, but
            # each route still receives its own calculated fuel/expected-loss
            # result because fuel litres depend on route distance.
            route_live_financial_inputs = dict(live_financial_inputs)
            route_copy["live_financial_inputs"] = route_live_financial_inputs

            economic_risk_input = (
                risk_analysis.get("risk_analysis")
                if isinstance(risk_analysis, dict)
                and isinstance(risk_analysis.get("risk_analysis"), dict)
                else risk_analysis
            )

            economic_analysis = calculate_economic_analysis(
                route_copy,
                economic_risk_input,
                cargo_value,
                quantity_kg,
                live_financial_inputs=route_live_financial_inputs,
            )

            # =================================================
            # FINANCIAL SUMMARY
            # =================================================

            financial_analysis = {
                "status": economic_analysis.get("status"),
                "expected_loss": economic_analysis.get("expected_cargo_loss"),
                "expected_cargo_loss": economic_analysis.get("expected_cargo_loss"),
                "value_preserved": economic_analysis.get("value_preserved"),
                "effective_total_cost": economic_analysis.get("effective_total_cost"),
                "fuel_cost": economic_analysis.get("fuel_cost"),
                "fuel_price_per_litre": economic_analysis.get("fuel_price_per_litre"),
                "fuel_efficiency_km_per_litre": economic_analysis.get("fuel_efficiency_km_per_litre"),
                "fuel_litres": economic_analysis.get("fuel_litres"),
            }

            # =================================================
            # ATTACH RESULTS TO RISK OBJECT
            # =================================================

            risk_analysis["financial_analysis"] = financial_analysis

            # =================================================
            # ATTACH RESULTS TO ROUTE
            # =================================================

            route_copy["live_conditions"] = live_conditions
            route_copy["conditions"] = live_conditions
            route_copy["risk_analysis"] = risk_analysis
            route_copy["economic_analysis"] = economic_analysis
            route_copy["financial_analysis"] = financial_analysis

            # Keep full OSRM geometry inside the backend for all calculations,
            # then send only a compact subset of the real OSRM points to the
            # browser. No geometry is invented.
            analyzed_routes.append(
                compact_route_geometry(
                    route_copy,
                    max_points=1200,
                )
            )

        # ====================================================
        # 4. TRANSPORT-MODE ANALYSIS
        # ====================================================

        multimodal_analysis = {
            "requested_mode": requested_transport_mode,
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
        }

        if requested_transport_mode == "multimodal" and analyzed_routes:
            # Check railway infrastructure independently for every real OSRM
            # route. The lookup is planning support only; it never changes
            # OSRM road geometry or invents rail schedules.
            multimodal_analysis = analyze_multimodal_routes(
                analyzed_routes,
                transport_mode=requested_transport_mode,
            )

        # ====================================================
        # 5. RECOMMENDATION
        # ====================================================

        recommendation = (
            build_recommendation(
                analyzed_routes,
                cargo_value,
            )
        )

        if requested_transport_mode == "multimodal":
            route_analyses = multimodal_analysis.get("route_analyses") or []
            recommended_id = recommendation.get("route_id")
            selected_analysis = next(
                (item for item in route_analyses if item.get("route_id") == recommended_id),
                None,
            )
            multimodal_analysis["selected_route_id"] = recommended_id
            multimodal_analysis["selected_route_analysis"] = selected_analysis

        # ====================================================
        # 5. LIVE COVERAGE
        # ====================================================

        complete_routes = sum(
            1
            for route
            in analyzed_routes
            if route_is_live_complete(
                route
            )
        )

        # ====================================================
        # 6. RESPONSE
        # ====================================================

        print(
            f"[TIMING] total={perf_counter() - request_started:.2f}s routes={len(analyzed_routes)} mode={requested_transport_mode}"
        )

        return {

            "success":
                True,

            "data_mode":
                "LIVE_EXTERNAL_DATA",

            "synthetic_live_values":
                False,

            "transport_mode":
                requested_transport_mode,

            "transport_mode_label":
                multimodal_analysis.get(
                    "display_mode"
                ),

            "multimodal_analysis":
                multimodal_analysis,

            "cargo": {

                "crop":
                    crop,

                "quantity_kg":
                    quantity_kg,

                "cargo_value":
                    cargo_value,

                "fragility":
                    fragility,
            },

            "start":
                route_data.get(
                    "start"
                ),

            "destination":
                route_data.get(
                    "destination"
                ),

            "start_coordinates":
                route_data.get(
                    "start_coordinates"
                ),

            "destination_coordinates":
                route_data.get(
                    "destination_coordinates"
                ),

            "route_count":
                len(
                    analyzed_routes
                ),

            "routes":
                analyzed_routes,

            "recommendation":
                recommendation,

            "live_coverage": {

                "complete_routes":
                    complete_routes,

                "total_routes":
                    len(
                        analyzed_routes
                    ),

                "required_live_feeds": [
                    "TomTom Traffic Flow",
                    "Open-Meteo Current Weather",
                ],

                "optional_live_feeds": [
                    "TomTom Traffic Incidents",
                    "API Mitra Fuel Price",
                    "Live Vehicle Efficiency",
                ],
            },

            "notes": [

                (
                    "Traffic values come "
                    "from TomTom Traffic "
                    "Flow when the API "
                    "returns live data."
                ),

                (
                    "Incident values come "
                    "from TomTom Traffic "
                    "Incidents filtered "
                    "to the route corridor."
                ),

                (
                    "Weather values come "
                    "from Open-Meteo "
                    "current weather."
                ),

                (
                    "OSRM distance and "
                    "duration are routing "
                    "engine results."
                ),

                (
                    "Risk and expected "
                    "cargo loss are model "
                    "outputs based on "
                    "live inputs."
                ),

                (
                    "Fuel price comes "
                    "from API Mitra when "
                    "available."
                ),

                (
                    "Vehicle mileage is used only when returned by "
                    "a live vehicle source; model/benchmark mileage "
                    "is not used."
                ),

                (
                    "Missing external "
                    "values are not "
                    "replaced with fake "
                    "zeroes."
                ),

                (
                    "Multimodal mode uses mapped OpenStreetMap railway infrastructure "
                    "near the road-route endpoints as planning candidates only; "
                    "no rail timetable, freight service, rail ETA or confirmed "
                    "intermodal booking is fabricated."
                ),
            ],
        }

    except HTTPException:
        raise

    except Exception as exc:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,

            detail=str(
                exc
            ),
        ) from exc

# ============================================================
# REAL MAPPED STOP PLANNING
# ============================================================

@app.post("/stops")
def stops(payload: dict = Body(...)):
    route = payload.get("route") or {}
    if not route:
        raise HTTPException(status_code=400, detail="A real analyzed route is required.")
    return find_route_stops(route)


# ============================================================
# FAST WHAT-IF SCENARIO
# ============================================================

@app.post("/simulate")
def simulate(payload: dict = Body(...)):
    """Recalculate cargo risk using the already-fetched live route data.

    What-If does not need to call Nominatim, OSRM, TomTom or Open-Meteo again.
    The browser sends the last successful live route analysis and only the
    cargo profile changes. This keeps the scenario calculation fast while
    preserving the real live conditions captured by the main analysis.
    """
    try:
        routes = payload.get("routes") or []
        cargo = payload.get("cargo") or {}

        crop = str(cargo.get("crop") or "").strip()
        quantity_kg = float(cargo.get("quantity_kg") or 0)
        cargo_value = float(cargo.get("cargo_value") or 0)
        fragility = str(cargo.get("fragility") or "").strip()

        if not routes:
            raise HTTPException(status_code=400, detail="No previously analyzed routes were supplied.")
        if not crop or quantity_kg <= 0 or cargo_value <= 0 or not fragility:
            raise HTTPException(status_code=400, detail="Complete cargo scenario details are required.")

        analyzed_routes = []

        for original_route in routes:
            route_copy = dict(original_route)
            live_conditions = (
                route_copy.get("conditions")
                or route_copy.get("live_conditions")
                or {}
            )

            risk_analysis = analyze_route_risk(
                route=route_copy,
                conditions=live_conditions,
                crop=crop,
                quantity_kg=quantity_kg,
                cargo_value=cargo_value,
                fragility=fragility,
            )

            economic_risk_input = (
                risk_analysis.get("risk_analysis")
                if isinstance(risk_analysis, dict)
                and isinstance(risk_analysis.get("risk_analysis"), dict)
                else risk_analysis
            )

            live_financial_inputs = route_copy.get("live_financial_inputs") or {}
            economic_analysis = calculate_economic_analysis(
                route_copy,
                economic_risk_input,
                cargo_value,
                quantity_kg,
                live_financial_inputs=live_financial_inputs,
            )

            financial_analysis = {
                "status": economic_analysis.get("status"),
                "expected_loss": economic_analysis.get("expected_cargo_loss"),
                "expected_cargo_loss": economic_analysis.get("expected_cargo_loss"),
                "value_preserved": economic_analysis.get("value_preserved"),
                "effective_total_cost": economic_analysis.get("effective_total_cost"),
                "fuel_cost": economic_analysis.get("fuel_cost"),
                "fuel_price_per_litre": economic_analysis.get("fuel_price_per_litre"),
                "fuel_efficiency_km_per_litre": economic_analysis.get("fuel_efficiency_km_per_litre"),
                "fuel_litres": economic_analysis.get("fuel_litres"),
            }

            risk_analysis["financial_analysis"] = financial_analysis
            route_copy["risk_analysis"] = risk_analysis
            route_copy["economic_analysis"] = economic_analysis
            route_copy["financial_analysis"] = financial_analysis
            analyzed_routes.append(route_copy)

        recommendation = build_recommendation(analyzed_routes, cargo_value)

        transport_mode = str(payload.get("transport_mode") or "road").strip().lower()
        multimodal_analysis = payload.get("multimodal_analysis") or {
            "requested_mode": transport_mode,
            "display_mode": "Road only" if transport_mode == "road" else "Multimodal",
            "status": "reused_from_live_analysis",
            "available": True,
            "notes": ["Rail infrastructure results are reused from the last live route analysis."] if transport_mode == "multimodal" else [],
        }

        if transport_mode == "multimodal":
            route_analyses = multimodal_analysis.get("route_analyses") or []
            recommended_id = recommendation.get("route_id")
            multimodal_analysis = dict(multimodal_analysis)
            multimodal_analysis["selected_route_id"] = recommended_id
            multimodal_analysis["selected_route_analysis"] = next(
                (item for item in route_analyses if item.get("route_id") == recommended_id),
                None,
            )

        return {
            "success": True,
            "data_mode": "LIVE_EXTERNAL_DATA_REUSED",
            "synthetic_live_values": False,
            "transport_mode": transport_mode,
            "transport_mode_label": multimodal_analysis.get("display_mode"),
            "multimodal_analysis": multimodal_analysis,
            "cargo": {
                "crop": crop,
                "quantity_kg": quantity_kg,
                "cargo_value": cargo_value,
                "fragility": fragility,
            },
            "start": payload.get("start"),
            "destination": payload.get("destination"),
            "start_coordinates": payload.get("start_coordinates"),
            "destination_coordinates": payload.get("destination_coordinates"),
            "route_count": len(analyzed_routes),
            "routes": analyzed_routes,
            "recommendation": recommendation,
            "notes": [
                "What-If reuses the live traffic, incident and weather observations from the last completed route analysis.",
                "No new external provider request is made for the scenario calculation.",
            ],
        }

    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


