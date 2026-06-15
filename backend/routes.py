from flask import Blueprint, jsonify, render_template, request

from algorithms import analyze_trip
from .utils import (
    get_mock_alert,
    get_mock_recommendations,
    get_network_data_for_time,
    get_network_overview,
    get_route_urban_summary,
    get_route_rationale,
    get_supported_areas,
    validate_input,
)


api_bp = Blueprint("api", __name__)


@api_bp.get("/")
def home():
    return render_template("index.html")


@api_bp.get("/api/health")
def health_check():
    return jsonify({"message": "Backend is running"}), 200


@api_bp.get("/api/supported-areas")
def supported_areas():
    return jsonify({"supported_areas": get_supported_areas()}), 200


@api_bp.get("/api/network-overview")
def network_overview():
    selected_time = request.args.get("time", "day").strip().lower()
    return jsonify(get_network_overview(selected_time)), 200


@api_bp.post("/api/predict-route")
def predict_route():
    data = request.get_json(silent=True)
    is_valid, cleaned_data, error_message = validate_input(data)

    if not is_valid:
        return jsonify({"error": error_message}), 400

    start = cleaned_data["start"]
    destination = cleaned_data["destination"]
    time_of_day = cleaned_data["time"]

    area_connections, area_risk_scores, area_display_names = get_network_data_for_time(time_of_day)
    analysis = analyze_trip(
        start_area=cleaned_data["start_key"],
        destination_area=cleaned_data["destination_key"],
        time_of_day=time_of_day,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
    )

    risk_level = analysis["risk_level"]
    safe_route = [area_display_names.get(area, area.title()) for area in analysis["safe_route"]]
    direct_route = [area_display_names.get(area, area.title()) for area in analysis["direct_route"]]
    route_sequence = [
        {
            "key": area_key,
            "name": area_display_names.get(area_key, area_key.title()),
            "role": (
                "start"
                if index == 0
                else "destination"
                if index == len(analysis["safe_route"]) - 1
                else "step"
            ),
        }
        for index, area_key in enumerate(analysis["safe_route"])
    ]
    alert = get_mock_alert(risk_level)
    recommendations = get_mock_recommendations(risk_level, time_of_day)
    route_rationale = get_route_rationale(risk_level, analysis["route_comparison"], time_of_day)
    route_urban_summary = get_route_urban_summary(analysis["safe_route"])

    response = {
        "start": start,
        "destination": destination,
        "time": time_of_day,
        "risk_score": analysis["risk_score"],
        "risk_level": risk_level,
        "safe_route": safe_route,
        "route_sequence": route_sequence,
        "direct_route": direct_route,
        "alert": alert,
        "recommendations": recommendations,
        "algorithm_breakdown": analysis["algorithm_breakdown"],
        "decision_tree_prediction": analysis["decision_tree_prediction"],
        "route_comparison": analysis["route_comparison"],
        "route_rationale": route_rationale,
        "route_urban_summary": route_urban_summary,
        "network_overview": get_network_overview(time_of_day),
    }
    return jsonify(response), 200
