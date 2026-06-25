from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .event_score import normalize


@dataclass
class CandidateSignals:
    football_relevance: float = 0.0
    early_signal_quality: float = 0.0
    media_context_quality: float = 0.0
    quote_context_quality: float = 0.0
    language_style_fit: float = 0.0
    engagement_quality: float = 0.0
    misinformation_risk: float = 0.0
    toxicity_risk: float = 0.0


def calculate_candidate_score(s: CandidateSignals) -> tuple[float, dict[str, Any]]:
    raw = (
        0.25 * s.football_relevance
        + 0.20 * s.early_signal_quality
        + 0.15 * s.media_context_quality
        + 0.15 * s.quote_context_quality
        + 0.10 * s.language_style_fit
        + 0.10 * s.engagement_quality
        - 0.20 * s.misinformation_risk
        - 0.10 * s.toxicity_risk
    )
    score = normalize(raw)
    if score >= 70:
        action = "approve_candidate"
    elif score >= 45:
        action = "watch_one_week"
    else:
        action = "reject_or_ignore"
    return score, {"score": score, "action": action, "inputs": asdict(s)}
