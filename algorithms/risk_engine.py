def _time_risk_bonus(time_of_day):
    return 0.35 if time_of_day == "night" else 0


def calculate_bayesian_style_score(start_area, destination_area, area_risk_scores, time_of_day):
    """
    Beginner-friendly probability-style score.
    It mimics the idea of using prior area risk and time context.
    """
    start_score = area_risk_scores.get(start_area, 1)
    destination_score = area_risk_scores.get(destination_area, 1)
    average_score = (start_score + destination_score) / 2
    return average_score + _time_risk_bonus(time_of_day)


def calculate_knn_style_score(start_area, destination_area, area_connections, area_risk_scores):
    """
    Beginner-friendly KNN-style score.
    It looks at connected neighboring areas and averages their risk.
    """
    related_areas = set(area_connections.get(start_area, []))
    related_areas.update(area_connections.get(destination_area, []))
    related_areas.update({start_area, destination_area})

    if not related_areas:
        return 1

    total_score = sum(area_risk_scores.get(area, 1) for area in related_areas)
    return total_score / len(related_areas)


def calculate_combined_risk_score(
    start_area,
    destination_area,
    time_of_day,
    area_connections,
    area_risk_scores,
    decision_tree_score=None,
):
    """
    Combine two simple AI-inspired scores.
    This keeps the project structured for future real ML work.
    """
    bayesian_score = calculate_bayesian_style_score(
        start_area=start_area,
        destination_area=destination_area,
        area_risk_scores=area_risk_scores,
        time_of_day=time_of_day,
    )
    knn_score = calculate_knn_style_score(
        start_area=start_area,
        destination_area=destination_area,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
    )

    model_scores = [bayesian_score, knn_score]

    if decision_tree_score is not None:
        model_scores.append(decision_tree_score)

    return round(sum(model_scores) / len(model_scores), 2)


def get_algorithm_breakdown(
    start_area,
    destination_area,
    time_of_day,
    area_connections,
    area_risk_scores,
    decision_tree_prediction=None,
):
    """Return individual AI-inspired scores for UI insight panels."""
    bayesian_score = calculate_bayesian_style_score(
        start_area=start_area,
        destination_area=destination_area,
        area_risk_scores=area_risk_scores,
        time_of_day=time_of_day,
    )
    knn_score = calculate_knn_style_score(
        start_area=start_area,
        destination_area=destination_area,
        area_connections=area_connections,
        area_risk_scores=area_risk_scores,
    )

    decision_tree_score = None
    if decision_tree_prediction:
        decision_tree_score = decision_tree_prediction.get("decision_tree_score")

    model_scores = [bayesian_score, knn_score]
    if decision_tree_score is not None:
        model_scores.append(decision_tree_score)

    return {
        "bayesian_score": round(bayesian_score, 2),
        "knn_score": round(knn_score, 2),
        "decision_tree_score": round(decision_tree_score, 2) if decision_tree_score is not None else None,
        "decision_tree_level": decision_tree_prediction.get("decision_tree_level") if decision_tree_prediction else None,
        "decision_tree_confidence": decision_tree_prediction.get("decision_tree_confidence") if decision_tree_prediction else None,
        "decision_tree_model_available": decision_tree_prediction.get("model_available") if decision_tree_prediction else False,
        "decision_tree_training_records": decision_tree_prediction.get("training_records") if decision_tree_prediction else 0,
        "decision_tree_training_accuracy": decision_tree_prediction.get("training_accuracy") if decision_tree_prediction else None,
        "combined_score": round(sum(model_scores) / len(model_scores), 2),
    }


def classify_risk_level(combined_score):
    """Convert score into a simple risk label."""
    if combined_score >= 3.6:
        return "High"
    if combined_score >= 2.2:
        return "Medium"
    return "Low"
