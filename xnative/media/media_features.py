from typing import Any


def media_context_score(media_items: list[dict[str, Any]]) -> float:
    if not media_items:
        return 0.0
    score = 30.0
    for m in media_items:
        if m.get("alt_text"):
            score += 20.0
        if m.get("ocr_text"):
            score += 15.0
    return min(score, 100.0)
