def decision_label(event_score: float, risk_score: float) -> str:
    if risk_score >= 81:
        return "block"
    if risk_score >= 61:
        return "human_review"
    if event_score >= 75:
        return "high_priority_suggestion"
    if event_score >= 60:
        return "normal_suggestion"
    if event_score >= 40:
        return "watch"
    return "archive"
