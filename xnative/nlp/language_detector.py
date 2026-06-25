def detect_language(text: str) -> str:
    # Minimal local fallback. Avoids mandatory paid or heavy language APIs.
    t = (text or "").lower()
    tr_chars = set("çğıöşü")
    if any(c in t for c in tr_chars) or any(
        w in t.split() for w in ["maç", "gol", "takım", "taraftar"]
    ):
        return "tr"
    return "unknown"
