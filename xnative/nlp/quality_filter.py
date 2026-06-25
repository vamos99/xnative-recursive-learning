from __future__ import annotations

from dataclasses import dataclass

from .ai_phrase_filter import find_ai_phrases


@dataclass
class QualityResult:
    passed: bool
    score: float
    issues: list[str]


def assess_quality(text: str, max_len: int = 280) -> QualityResult:
    issues: list[str] = []
    if not text.strip():
        issues.append("empty_text")
    if len(text) > max_len:
        issues.append("too_long")
    phrases = find_ai_phrases(text)
    if phrases:
        issues.append("ai_or_news_phrases:" + ",".join(phrases))
    if text.count("#") > 2:
        issues.append("too_many_hashtags")
    if len(text.split()) > 38:
        issues.append("too_explanatory")
    score = max(0.0, 100.0 - 20.0 * len(issues))
    return QualityResult(passed=not issues, score=score, issues=issues)
