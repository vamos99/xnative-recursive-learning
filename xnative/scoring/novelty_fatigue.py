from __future__ import annotations

from difflib import SequenceMatcher


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def fatigue_score(
    new_text: str, recent_texts: list[str], duplicate_threshold: float = 0.85
) -> tuple[float, list[str]]:
    issues: list[str] = []
    if not recent_texts:
        return 0.0, issues
    max_sim = max(text_similarity(new_text, t) for t in recent_texts)
    if max_sim >= duplicate_threshold:
        issues.append("near_duplicate_text")
        return 80.0, issues
    return max(0.0, (max_sim - 0.5) * 100), issues
