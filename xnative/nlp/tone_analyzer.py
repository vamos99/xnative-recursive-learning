def infer_tone(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ["yine", "senaryo", "klasik"]):
        return "dry_humor"
    if any(x in t for x in ["bu pozisyon", "bu görüntü", "konuşulur"]):
        return "reaction"
    if len(t.split()) < 12:
        return "neutral_short"
    return "fan_voice"
