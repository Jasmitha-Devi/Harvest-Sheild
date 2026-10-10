def generate_route_scenarios(
    route_data
):
    """
    Preserve only the real routes returned
    by the routing engine.

    This function intentionally does NOT
    create synthetic Route B / Route C data.
    """

    routes = (
        route_data.get(
            "routes",
            []
        )
        if route_data
        else []
    )

    return {
        "start":
            (
                route_data.get(
                    "start"
                )
                if route_data
                else None
            ),

        "destination":
            (
                route_data.get(
                    "destination"
                )
                if route_data
                else None
            ),

        "route_count":
            len(routes),

        "routes": [
            dict(route)
            for route
            in routes
        ],
    }