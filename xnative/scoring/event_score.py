from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EventScoreBreakdown:
    source_reliability: float = 50.0
    source_count_score: float = 0.0
    velocity_score: float = 0.0
    relevance_score: float = 50.0
    novelty_score: float = 50.0
    media_context_score: float = 0.0
    risk_score: float = 0.0
    fatigue_score: float = 0.0


def normalize(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


def calculate_event_score(b: EventScoreBreakdown) -> tuple[float, dict[str, Any]]:
    raw = (
        0.25 * b.source_reliability
        + 0.20 * b.source_count_score
        + 0.15 * b.velocity_score
        + 0.15 * b.relevance_score
        + 0.10 * b.novelty_score
        + 0.10 * b.media_context_score
        - 0.20 * b.risk_score
        - 0.10 * b.fatigue_score
    )
    score = normalize(raw)
    return score, {"score": score, "inputs": asdict(b), "formula": "weighted_event_score_v1"}
