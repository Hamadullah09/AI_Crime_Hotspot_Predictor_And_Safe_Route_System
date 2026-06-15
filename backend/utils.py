import csv
from collections import Counter, defaultdict
from pathlib import Path

from algorithms.pathfinding import AREA_COORDINATES
from algorithms.risk_engine import classify_risk_level


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "processed" / "karachi_crime_processed.csv"
RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "karachi_crime_reference_dataset.csv"


AREA_RISK_SCORES = {}
AREA_DISPLAY_NAMES = {}
AREA_MAP_POSITIONS = {}
AREA_RISK_PROFILES = {}
AREA_URBAN_PROFILES = {}

MANUAL_MAP_POSITIONS = {
    "clifton": {"x": 1.25, "y": 1.25},
    "dha": {"x": 2.05, "y": 1.25},
    "defence-view": {"x": 2.0, "y": 3.45},
    "saddar": {"x": 2.05, "y": 2.55},
    "garden": {"x": 1.75, "y": 2.35},
    "kharadar": {"x": 1.55, "y": 2.95},
    "lyari": {"x": 1.05, "y": 2.65},
    "keamari": {"x": 0.95, "y": 3.45},
    "pechs": {"x": 2.95, "y": 2.35},
    "jamshed-town": {"x": 2.7, "y": 2.15},
    "mehmoodabad": {"x": 2.75, "y": 2.85},
    "gulberg": {"x": 2.35, "y": 1.95},
    "nazimabad": {"x": 2.35, "y": 2.05},
    "north-nazimabad": {"x": 2.55, "y": 1.75},
    "fb-area": {"x": 2.85, "y": 1.45},
    "sakhi-hasan": {"x": 3.05, "y": 1.6},
    "new-karachi": {"x": 3.0, "y": 1.05},
    "surjani-town": {"x": 3.55, "y": 0.9},
    "sohrab-goth": {"x": 4.1, "y": 0.95},
    "banaras": {"x": 1.95, "y": 1.5},
    "orangi-town": {"x": 1.35, "y": 1.8},
    "baldia-town": {"x": 0.95, "y": 2.0},
    "site-area": {"x": 1.75, "y": 2.05},
    "gulshan": {"x": 3.25, "y": 2.0},
    "gulistan-e-johar": {"x": 4.15, "y": 2.0},
    "scheme-33": {"x": 4.55, "y": 1.55},
    "shah-faisal": {"x": 4.55, "y": 2.75},
    "malir": {"x": 5.05, "y": 2.45},
    "korangi": {"x": 4.35, "y": 3.25},
    "landhi": {"x": 4.95, "y": 3.15},
}


def _load_area_data():
    """Load balanced mock crime profiles from CSV."""
    area_profiles = {}
    area_names = {}
    area_positions = {}
    latitudes = []
    longitudes = []

    with DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    for row in rows:
        latitudes.append(float(row["latitude"]))
        longitudes.append(float(row["longitude"]))

    min_lat = min(latitudes)
    max_lat = max(latitudes)
    min_lng = min(longitudes)
    max_lng = max(longitudes)

    for row in rows:
            key = row["area_key"].strip().lower()
            area_names[key] = row["display_name"].strip()
            area_profiles[key] = {
                "base_score": float(row["base_score"]),
                "day_score": float(row["day_risk_score"]),
                "night_score": float(row["night_risk_score"]),
                "day_category": row["day_risk_category"].strip(),
                "night_category": row["night_risk_category"].strip(),
            }

            # Convert lat/lng into a stable map grid for the frontend board.
            lat_ratio = (float(row["latitude"]) - min_lat) / max(max_lat - min_lat, 0.0001)
            lng_ratio = (float(row["longitude"]) - min_lng) / max(max_lng - min_lng, 0.0001)
            area_positions[key] = {
                "x": round(1 + (lng_ratio * 4), 2),
                "y": round(1 + ((1 - lat_ratio) * 3), 2),
            }

    return area_names, area_profiles, area_positions


def _load_urban_profiles():
    """Build richer area summaries from the raw academic incident dataset."""
    area_buckets = defaultdict(
        lambda: {
            "display_name": "",
            "records": 0,
            "incident_total": 0,
            "day_incidents": 0,
            "night_incidents": 0,
            "crime_counter": Counter(),
            "population_band": Counter(),
            "poverty_total": 0.0,
            "unemployment_total": 0.0,
        }
    )

    with RAW_DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            area_key = row["area_key"].strip().lower()
            incident_count = int(row["incident_count"])
            bucket = area_buckets[area_key]
            bucket["display_name"] = row["display_name"].strip()
            bucket["records"] += 1
            bucket["incident_total"] += incident_count
            bucket["crime_counter"][row["crime_type"].strip()] += incident_count
            bucket["population_band"][row["population_band"].strip()] += 1
            bucket["poverty_total"] += float(row["poverty_index"])
            bucket["unemployment_total"] += float(row["unemployment_index"])

            if row["time_of_day"].strip().lower() == "night":
                bucket["night_incidents"] += incident_count
            else:
                bucket["day_incidents"] += incident_count

    urban_profiles = {}
    for area_key, bucket in area_buckets.items():
        records = max(bucket["records"], 1)
        top_crimes = bucket["crime_counter"].most_common(3)
        urban_profiles[area_key] = {
            "display_name": bucket["display_name"],
            "record_count": bucket["records"],
            "incident_total": bucket["incident_total"],
            "day_incidents": bucket["day_incidents"],
            "night_incidents": bucket["night_incidents"],
            "top_crime_type": top_crimes[0][0] if top_crimes else "Unknown",
            "top_crime_types": [
                {"name": crime_name, "count": count}
                for crime_name, count in top_crimes
            ],
            "population_band": bucket["population_band"].most_common(1)[0][0] if bucket["population_band"] else "Unknown",
            "poverty_index": round(bucket["poverty_total"] / records, 2),
            "unemployment_index": round(bucket["unemployment_total"] / records, 2),
        }

    return urban_profiles


AREA_DISPLAY_NAMES, AREA_RISK_PROFILES, AREA_MAP_POSITIONS = _load_area_data()
AREA_URBAN_PROFILES = _load_urban_profiles()


_AREA_CONNECTION_BLUEPRINT = {
    "clifton": ["dha", "saddar"],
    "dha": ["clifton", "pechs", "gulshan", "defence-view"],
    "defence-view": ["dha", "korangi", "saddar"],
    "saddar": ["clifton", "garden", "jamshed-town", "gulshan", "defence-view", "lyari"],
    "garden": ["saddar", "site-area", "nazimabad", "kharadar"],
    "kharadar": ["garden", "lyari", "keamari"],
    "lyari": ["saddar", "kharadar", "keamari", "garden"],
    "keamari": ["lyari", "kharadar", "baldia-town"],
    "baldia-town": ["keamari", "orangi-town", "site-area"],
    "orangi-town": ["baldia-town", "banaras", "site-area", "nazimabad"],
    "banaras": ["orangi-town", "site-area", "sakhi-hasan"],
    "site-area": ["banaras", "garden", "nazimabad", "gulberg", "baldia-town"],
    "nazimabad": ["garden", "site-area", "north-nazimabad", "gulberg", "gulshan", "orangi-town"],
    "north-nazimabad": ["nazimabad", "fb-area", "sakhi-hasan", "new-karachi", "gulberg"],
    "sakhi-hasan": ["north-nazimabad", "banaras", "fb-area", "sohrab-goth"],
    "fb-area": ["north-nazimabad", "gulberg", "gulshan", "new-karachi", "sakhi-hasan"],
    "new-karachi": ["north-nazimabad", "surjani-town", "sohrab-goth", "fb-area"],
    "surjani-town": ["new-karachi", "sohrab-goth"],
    "sohrab-goth": ["surjani-town", "scheme-33", "sakhi-hasan", "new-karachi"],
    "gulberg": ["nazimabad", "fb-area", "gulshan", "jamshed-town", "north-nazimabad"],
    "gulshan": ["dha", "fb-area", "gulberg", "pechs", "jamshed-town", "gulistan-e-johar", "nazimabad", "saddar"],
    "jamshed-town": ["saddar", "gulberg", "pechs", "mehmoodabad", "gulshan"],
    "pechs": ["dha", "gulshan", "jamshed-town", "mehmoodabad", "shah-faisal"],
    "mehmoodabad": ["jamshed-town", "pechs", "shah-faisal", "defence-view"],
    "gulistan-e-johar": ["gulshan", "scheme-33", "malir"],
    "scheme-33": ["gulistan-e-johar", "sohrab-goth", "malir"],
    "shah-faisal": ["pechs", "mehmoodabad", "malir", "korangi", "landhi"],
    "malir": ["gulistan-e-johar", "scheme-33", "shah-faisal", "landhi", "korangi"],
    "korangi": ["defence-view", "shah-faisal", "malir", "landhi"],
    "landhi": ["korangi", "malir", "shah-faisal"],
}


def _build_bidirectional_connections(connection_blueprint):
    connections = {area: set(targets) for area, targets in connection_blueprint.items()}

    for area, targets in connection_blueprint.items():
        connections.setdefault(area, set())
        for target in targets:
            connections.setdefault(target, set()).add(area)

    return {
        area: sorted(targets)
        for area, targets in connections.items()
    }


AREA_CONNECTIONS = _build_bidirectional_connections(_AREA_CONNECTION_BLUEPRINT)


VALID_TIMES = {"day", "night"}
LOCATION_ALIASES = {
    "johar": "gulistan-e-johar",
    "gulistan e johar": "gulistan-e-johar",
    "north nazimabad": "north-nazimabad",
}


def normalize_location(location_name):
    """Convert user input into a consistent internal key."""
    cleaned_name = location_name.strip().lower().replace("_", " ")
    cleaned_name = " ".join(cleaned_name.split())
    normalized = cleaned_name.replace(" - ", "-").replace(" ", "-")
    return LOCATION_ALIASES.get(cleaned_name, LOCATION_ALIASES.get(normalized, normalized))


def get_supported_areas():
    """Return the list of supported areas for frontend dropdowns or testing."""
    return sorted(AREA_DISPLAY_NAMES.values())


def get_network_data():
    """Return graph and risk data for the algorithm layer."""
    return get_network_data_for_time("day")


def get_network_data_for_time(time_of_day):
    """Return graph and selected-time risk scores for the algorithm layer."""
    selected_time = time_of_day if time_of_day in VALID_TIMES else "day"
    score_key = f"{selected_time}_score"
    area_scores = {
        area_key: profile[score_key]
        for area_key, profile in AREA_RISK_PROFILES.items()
    }
    return AREA_CONNECTIONS, area_scores, AREA_DISPLAY_NAMES


def get_network_overview(time_of_day="day"):
    """Return UI-friendly data for map and hotspot panels."""
    selected_time = time_of_day if time_of_day in VALID_TIMES else "day"
    score_key = f"{selected_time}_score"
    category_key = f"{selected_time}_category"
    areas = []
    for area_key, display_name in AREA_DISPLAY_NAMES.items():
        profile = AREA_RISK_PROFILES.get(area_key, {})
        score = profile.get(score_key, 1.5)
        fallback_x, fallback_y = AREA_COORDINATES.get(area_key, (2.5, 2.5))
        map_position = MANUAL_MAP_POSITIONS.get(
            area_key,
            AREA_MAP_POSITIONS.get(area_key, {"x": fallback_x, "y": fallback_y}),
        )
        areas.append(
            {
                "key": area_key,
                "name": display_name,
                "risk_score": score,
                "risk_level": profile.get(category_key, classify_risk_level(score)),
                "x": map_position["x"],
                "y": map_position["y"],
                "connections": AREA_CONNECTIONS.get(area_key, []),
                "urban_profile": AREA_URBAN_PROFILES.get(area_key, {}),
            }
        )

    hotspot_zones = sorted(
        (
            {
                "name": area["name"],
                "risk_score": area["risk_score"],
                "risk_level": area["risk_level"],
                "incident_total": area["urban_profile"].get("incident_total", 0),
                "top_crime_type": area["urban_profile"].get("top_crime_type", "Unknown"),
            }
            for area in areas
        ),
        key=lambda area: (-area["incident_total"], -area["risk_score"], area["name"]),
    )[:4]

    return {
        "areas": areas,
        "hotspot_zones": hotspot_zones,
        "heatmap_bands": _build_heatmap_bands(areas),
        "selected_time": selected_time,
        "network_summary": _build_network_summary(areas),
    }


def validate_input(data):
    """
    Validate request data and return:
    - is_valid: bool
    - cleaned_data: dict
    - error_message: str or None
    """
    if not isinstance(data, dict):
        return False, {}, "Request body must be valid JSON."

    start = data.get("start", "")
    destination = data.get("destination", "")
    time_of_day = data.get("time", "")

    if not isinstance(start, str) or not start.strip():
        return False, {}, "Start location is required."

    if not isinstance(destination, str) or not destination.strip():
        return False, {}, "Destination is required."

    if not isinstance(time_of_day, str) or not time_of_day.strip():
        return False, {}, "Time must be 'day' or 'night'."

    normalized_start = normalize_location(start)
    normalized_destination = normalize_location(destination)
    normalized_time = time_of_day.strip().lower()

    if normalized_time not in VALID_TIMES:
        return False, {}, "Time must be either 'day' or 'night'."

    if normalized_start not in AREA_DISPLAY_NAMES:
        return False, {}, _unsupported_area_message("start")

    if normalized_destination not in AREA_DISPLAY_NAMES:
        return False, {}, _unsupported_area_message("destination")

    cleaned_data = {
        "start_key": normalized_start,
        "start": AREA_DISPLAY_NAMES[normalized_start],
        "destination_key": normalized_destination,
        "destination": AREA_DISPLAY_NAMES[normalized_destination],
        "time": normalized_time,
    }
    return True, cleaned_data, None


def get_mock_alert(risk_level):
    """Return a short safety message based on the risk level."""
    if risk_level == "High":
        return "High-risk travel detected. Avoid isolated areas and use the suggested route."
    if risk_level == "Medium":
        return "Moderate risk detected. Stay alert and prefer the safer route."
    return "Low-risk travel detected. Continue with normal precautions."


def get_mock_recommendations(risk_level, time_of_day):
    """Return short beginner-friendly travel recommendations."""
    recommendations = ["Use the suggested route for safer travel."]

    if time_of_day == "night":
        recommendations.append("Avoid quiet streets and prefer well-lit roads at night.")

    if risk_level == "High":
        recommendations.append("Share your route with someone before leaving.")
        recommendations.append("Avoid stopping in high-risk zones unless necessary.")
    elif risk_level == "Medium":
        recommendations.append("Stay alert and avoid unnecessary delays on the way.")
    else:
        recommendations.append("Normal travel is possible, but stay aware of your surroundings.")

    return recommendations


def get_route_rationale(risk_level, route_comparison, time_of_day):
    """Return short reasons explaining why the chosen route is safer."""
    reasons = []

    if route_comparison["risk_reduction"] > 0:
        reasons.append(
            f"The safer route lowers total exposure by {route_comparison['risk_reduction']:.2f} risk points."
        )
    else:
        reasons.append("The current safest route matches the direct route because no lower-risk detour was available.")

    if route_comparison["safe_route_steps"] > route_comparison["direct_route_steps"]:
        reasons.append("An extra stop was added to avoid higher-risk connected zones.")
    else:
        reasons.append("The selected route keeps travel efficient without adding unnecessary stops.")

    if time_of_day == "night":
        reasons.append("Night travel increases route sensitivity, so better-lit and lower-risk links were prioritized.")

    if risk_level == "High":
        reasons.append("High-risk endpoints increase the need for caution even on the recommended path.")
    elif risk_level == "Medium":
        reasons.append("Moderate-risk zones remain nearby, so the route focuses on lowering hotspot exposure.")
    else:
        reasons.append("Low-risk travel conditions allow a more direct but still monitored route.")

    return reasons


def get_route_urban_summary(route_keys):
    """Return richer route intelligence using the raw dataset summaries."""
    covered_areas = []
    route_crime_mix = Counter()
    total_incidents = 0
    day_incidents = 0
    night_incidents = 0

    for area_key in route_keys:
        profile = AREA_URBAN_PROFILES.get(area_key, {})
        if not profile:
            continue

        total_incidents += profile.get("incident_total", 0)
        day_incidents += profile.get("day_incidents", 0)
        night_incidents += profile.get("night_incidents", 0)

        for crime in profile.get("top_crime_types", []):
            route_crime_mix[crime["name"]] += crime["count"]

        covered_areas.append(
            {
                "key": area_key,
                "name": profile.get("display_name", AREA_DISPLAY_NAMES.get(area_key, area_key.title())),
                "incident_total": profile.get("incident_total", 0),
                "top_crime_type": profile.get("top_crime_type", "Unknown"),
                "population_band": profile.get("population_band", "Unknown"),
                "poverty_index": profile.get("poverty_index", 0),
                "unemployment_index": profile.get("unemployment_index", 0),
            }
        )

    return {
        "covered_areas": covered_areas,
        "total_incidents": total_incidents,
        "day_incidents": day_incidents,
        "night_incidents": night_incidents,
        "top_route_crimes": [
            {"name": name, "count": count}
            for name, count in route_crime_mix.most_common(4)
        ],
    }


def _unsupported_area_message(field_name):
    supported_area_names = ", ".join(get_supported_areas())
    return f"Unsupported {field_name} location. Supported areas: {supported_area_names}."


def _build_heatmap_bands(areas):
    return sorted(
        (
            {
                "name": area["name"],
                "risk_score": area["risk_score"],
                "risk_level": area["risk_level"],
                "intensity": round(min(area["urban_profile"].get("incident_total", 0) / 80, 1), 2),
                "incident_total": area["urban_profile"].get("incident_total", 0),
                "top_crime_type": area["urban_profile"].get("top_crime_type", "Unknown"),
            }
            for area in areas
        ),
        key=lambda item: (-item["incident_total"], -item["risk_score"], item["name"]),
    )


def _build_network_summary(areas):
    total_incidents = sum(area["urban_profile"].get("incident_total", 0) for area in areas)
    total_day = sum(area["urban_profile"].get("day_incidents", 0) for area in areas)
    total_night = sum(area["urban_profile"].get("night_incidents", 0) for area in areas)
    all_crime_types = Counter()

    for area in areas:
        for crime in area["urban_profile"].get("top_crime_types", []):
            all_crime_types[crime["name"]] += crime["count"]

    return {
        "area_count": len(areas),
        "total_incidents": total_incidents,
        "day_incidents": total_day,
        "night_incidents": total_night,
        "top_crime_types": [
            {"name": name, "count": count}
            for name, count in all_crime_types.most_common(5)
        ],
    }
