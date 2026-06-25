def quote_context_risk(quoted_text: str) -> float:
    t = (quoted_text or "").lower()
    risk_words = ["iddia", "skandal", "kavga", "siyaset", "ölüm", "sakatlık"]
    return min(100.0, 20.0 * sum(w in t for w in risk_words))
