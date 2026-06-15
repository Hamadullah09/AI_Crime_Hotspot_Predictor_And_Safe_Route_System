import csv
from collections import Counter
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "karachi_crime_reference_dataset.csv"
PROCESSED_DATA_FILE = BASE_DIR / "data" / "processed" / "karachi_crime_processed.csv"

RISK_LEVEL_TO_SCORE = {
    "Low": 1.5,
    "Medium": 2.8,
    "High": 4.2,
}


def predict_decision_tree_risk(start_area, destination_area, time_of_day):
    """
    Train a small Decision Tree classifier on the academic mock dataset and
    predict route risk from the start and destination area profiles.
    """
    model_bundle = _get_decision_tree_model()
    area_profiles = _load_area_profiles()
    start_features = _build_area_feature_row(start_area, time_of_day)
    destination_features = _build_area_feature_row(destination_area, time_of_day)

    if not model_bundle["model_available"]:
        return _fallback_prediction(
            start_area=start_area,
            destination_area=destination_area,
            time_of_day=time_of_day,
            area_profiles=area_profiles,
        )

    model = model_bundle["pipeline"]
    classes = list(model.named_steps["classifier"].classes_)
    endpoint_predictions = [
        _predict_endpoint(model, classes, start_area, start_features),
        _predict_endpoint(model, classes, destination_area, destination_features),
    ]
    decision_tree_score = round(
        sum(prediction["score"] for prediction in endpoint_predictions) / len(endpoint_predictions),
        2,
    )

    return {
        "model_available": True,
        "decision_tree_score": decision_tree_score,
        "decision_tree_level": _classify_score(decision_tree_score),
        "decision_tree_confidence": round(
            sum(prediction["confidence"] for prediction in endpoint_predictions) / len(endpoint_predictions),
            2,
        ),
        "endpoint_predictions": endpoint_predictions,
        "training_records": model_bundle["training_records"],
        "training_accuracy": model_bundle["training_accuracy"],
        "feature_count": model_bundle["feature_count"],
    }


@lru_cache(maxsize=1)  #one time train and save results
def _get_decision_tree_model():
    training_rows = _build_training_rows()

    try:
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.pipeline import Pipeline
        from sklearn.tree import DecisionTreeClassifier
    except ImportError:
        return {
            "model_available": False,
            "pipeline": None,
            "training_records": len(training_rows),
            "training_accuracy": None,
            "feature_count": 0,
        }

    features = [row["features"] for row in training_rows]
    labels = [row["target"] for row in training_rows]
    pipeline = Pipeline(
        steps=[
            ("vectorizer", DictVectorizer(sparse=False)),
            (
                "classifier",
                DecisionTreeClassifier(max_depth=6, min_samples_leaf=4, random_state=42),
            ),
        ]
    )
    pipeline.fit(features, labels)    #training

    predictions = pipeline.predict(features)
    training_accuracy = sum(
        1 for predicted, actual in zip(predictions, labels) if predicted == actual
    ) / max(len(labels), 1)

    return {
        "model_available": True,
        "pipeline": pipeline,
        "training_records": len(training_rows),
        "training_accuracy": round(training_accuracy, 2),
        "feature_count": len(pipeline.named_steps["vectorizer"].feature_names_),
    }


def _build_training_rows():                                                  # read raw csv data and convert it correct format
    area_profiles = _load_area_profiles()
    training_rows = []

    with RAW_DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            area_key = row["area_key"].strip().lower()
            time_of_day = row["time_of_day"].strip().lower()
            profile = area_profiles.get(area_key, {})
            target = profile.get(f"{time_of_day}_category")                           #result

            if not target:
                continue

            training_rows.append(
                {
                    "features": _row_to_features(row),                                # input (jo model dekhega)
                    "target": target                                                   # answer (jo model seekhega)
                }
            )

    return training_rows


@lru_cache(maxsize=1)
def _load_area_profiles():
    profiles = {}

    with PROCESSED_DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            area_key = row["area_key"].strip().lower()
            profiles[area_key] = {
                "day_score": float(row["day_risk_score"]),
                "night_score": float(row["night_risk_score"]),
                "day_category": row["day_risk_category"].strip(),
                "night_category": row["night_risk_category"].strip(),
            }

    return profiles


@lru_cache(maxsize=64)
def _load_area_time_rows(area_key, time_of_day):
    rows = []

    with RAW_DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if (
                row["area_key"].strip().lower() == area_key
                and row["time_of_day"].strip().lower() == time_of_day
            ):
                rows.append(row)

    if rows:
        return rows

    with RAW_DATA_FILE.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            row
            for row in reader
            if row["area_key"].strip().lower() == area_key
        ]


def _build_area_feature_row(area_key, time_of_day):                    #make summary of 1 areas all crime records then take aveg
    rows = _load_area_time_rows(area_key, time_of_day)

    if not rows:
        return {
            "area_key": area_key,
            "crime_type": "Unknown",
            "time_of_day": time_of_day,
            "day_of_week": "Unknown",
            "population_band": "Unknown",
            "incident_count": 0.0,
            "base_risk_score": 1.0,
            "poverty_index": 0.0,
            "unemployment_index": 0.0,
        }

    return {
        "area_key": area_key,
        "crime_type": _weighted_mode(rows, "crime_type"),                      # sabse common crime
        "time_of_day": time_of_day,
        "day_of_week": _weighted_mode(rows, "day_of_week"),
        "population_band": _weighted_mode(rows, "population_band", weight_field=None),
        "incident_count": _average(rows, "incident_count"),                     # average incidents
        "base_risk_score": _average(rows, "base_risk_score"),
        "poverty_index": _average(rows, "poverty_index"),                       # average poverty
        "unemployment_index": _average(rows, "unemployment_index"),
    }


def _row_to_features(row):
    return {
        "area_key": row["area_key"].strip().lower(),
        "crime_type": row["crime_type"].strip(),
        "time_of_day": row["time_of_day"].strip().lower(),
        "day_of_week": row["day_of_week"].strip(),
        "population_band": row["population_band"].strip(),
        "incident_count": float(row["incident_count"]),
        "base_risk_score": float(row["base_risk_score"]),
        "poverty_index": float(row["poverty_index"]),
        "unemployment_index": float(row["unemployment_index"]),
    }


def _predict_endpoint(model, classes, area_key, features):                # predict_proba :sirf "High/Low/Medium" nahi batata, probability batata hai
    probabilities = model.predict_proba([features])[0]
    probability_map = {
        str(risk_level): float(probability)
        for risk_level, probability in zip(classes, probabilities)
    }
    predicted_level = max(probability_map, key=probability_map.get)
    score = sum(
        RISK_LEVEL_TO_SCORE.get(risk_level, 1.5) * probability
        for risk_level, probability in probability_map.items()
    )

    return {
        "area_key": area_key,
        "risk_level": predicted_level,
        "confidence": round(probability_map[predicted_level], 2),
        "score": round(score, 2),                            #weighted score find
    }


def _fallback_prediction(start_area, destination_area, time_of_day, area_profiles):
    score_key = f"{time_of_day}_score"
    start_score = area_profiles.get(start_area, {}).get(score_key, 1.0)
    destination_score = area_profiles.get(destination_area, {}).get(score_key, 1.0)
    decision_tree_score = round((start_score + destination_score) / 2, 2)

    return {
        "model_available": False,
        "decision_tree_score": decision_tree_score,
        "decision_tree_level": _classify_score(decision_tree_score),
        "decision_tree_confidence": None,
        "endpoint_predictions": [],
        "training_records": 0,
        "training_accuracy": None,
        "feature_count": 0,
    }


def _weighted_mode(rows, field_name, weight_field="incident_count"):
    counter = Counter()

    for row in rows:
        value = row[field_name].strip()
        weight = float(row[weight_field]) if weight_field else 1
        counter[value] += weight

    return counter.most_common(1)[0][0]


def _average(rows, field_name):
    return round(
        sum(float(row[field_name]) for row in rows) / max(len(rows), 1),
        2,
    )


def _classify_score(score):
    if score >= 3.6:
        return "High"
    if score >= 2.2:
        return "Medium"
    return "Low"
