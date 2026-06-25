from typing import Any

from xnative.generation.draft_generator import generate_drafts


def suggest(event: dict[str, Any], risk_score: float = 0) -> list[dict[str, Any]]:
    return [d.__dict__ for d in generate_drafts(event, risk_score)]
