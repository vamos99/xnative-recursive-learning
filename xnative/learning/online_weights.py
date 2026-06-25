from __future__ import annotations


def clamp(v: float, min_value: float = 0.2, max_value: float = 2.0) -> float:
    return max(min_value, min(max_value, v))


def update_weight(
    old: float, reward: float, feature_value: float = 1.0, learning_rate: float = 0.05
) -> float:
    return clamp(old + learning_rate * reward * feature_value)
