def initial_source_reliability(source_type: str = "unknown") -> float:
    mapping = {
        "official_club": 90.0,
        "club": 90.0,
        "journalist": 75.0,
        "stats": 70.0,
        "fan": 45.0,
        "meme": 40.0,
        "candidate": 35.0,
        "unknown": 30.0,
    }
    return mapping.get((source_type or "unknown").lower(), 30.0)


def update_source_reliability(old_score: float, observed_score: float) -> float:
    return max(0.0, min(100.0, old_score * 0.85 + observed_score * 0.15))
