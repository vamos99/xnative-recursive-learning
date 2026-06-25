from __future__ import annotations

RISK_WORDS = {
    "misinformation": ["iddia", "doğrulanmadı", "kulis"],
    "toxicity": ["salak", "aptal", "nefret", "hain"],
    "crisis": ["ölüm", "afet", "saldırı", "yaralı"],
    "political_tension": ["siyaset", "bakan", "parti"],
    "copyright": ["telif"],
}


def calculate_risk_score(
    text: str = "", media_risk_score: float = 0.0, quote_risk_score: float = 0.0
) -> tuple[float, list[str]]:
    low = (text or "").lower()
    issues: list[str] = []
    score = 0.0
    for cat, words in RISK_WORDS.items():
        if any(w in low for w in words):
            issues.append(cat)
            score += 18.0
    score += 0.35 * media_risk_score + 0.25 * quote_risk_score
    return min(score, 100.0), issues
