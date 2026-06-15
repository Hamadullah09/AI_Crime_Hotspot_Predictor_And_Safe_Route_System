from .decision_tree import predict_decision_tree_risk
from .pathfinding import build_direct_route, build_safe_route
from .risk_engine import (
    calculate_combined_risk_score,
    classify_risk_level,
    get_algorithm_breakdown,
)


def analyze_trip(start_area, destination_area, time_of_day, area_connections, area_risk_scores):
    """
    Run the project's algorithm layer.
    Real ML models can replace these internals later without changing the API layer.
    """
    decision_tree_prediction = predict_decision_tree_risk(
        start_area=start_area,
        destination_area=destination_area,
        time_of_day=time_of_day,
    )
    combined_score = calculate_combined_risk_score(
        start_area=start_area,
        destination_area=destination_area,
        time_of_day=time_of_day,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
        decision_tree_score=decision_tree_prediction["decision_tree_score"],
    )
    risk_level = classify_risk_level(combined_score)
    safe_route = build_safe_route(
        start_area=start_area,
        destination_area=destination_area,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
        time_of_day=time_of_day,
    )
    direct_route = build_direct_route(
        start_area=start_area,
        destination_area=destination_area,
        area_connections=area_connections,
    )
    breakdown = get_algorithm_breakdown(
        start_area=start_area,
        destination_area=destination_area,
        time_of_day=time_of_day,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
        decision_tree_prediction=decision_tree_prediction,
    )

    safe_route_risk = round(_route_risk_total(safe_route, area_risk_scores), 2)
    direct_route_risk = round(_route_risk_total(direct_route, area_risk_scores), 2)

    return {
        "risk_score": combined_score,
        "risk_level": risk_level,
        "decision_tree_prediction": decision_tree_prediction,
        "safe_route": safe_route,
        "direct_route": direct_route,
        "algorithm_breakdown": breakdown,
        "route_comparison": {
            "safe_route_steps": len(safe_route),
            "direct_route_steps": len(direct_route),
            "safe_route_risk": safe_route_risk,
            "direct_route_risk": direct_route_risk,
            "risk_reduction": round(max(direct_route_risk - safe_route_risk, 0), 2),
        },
    }


def _route_risk_total(route, area_risk_scores):
    return sum(area_risk_scores.get(area, 1) for area in route)
