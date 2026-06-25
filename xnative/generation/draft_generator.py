from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from xnative.nlp.quality_filter import assess_quality

from .post_variants import VARIANTS
from .template_fallback import render_template


@dataclass
class Draft:
    text: str
    variant_label: str
    quality_score: float
    issues: list[str]


def generate_drafts(
    event: dict[str, Any], risk_score: float = 0.0, max_variants: int = 3
) -> list[Draft]:
    if risk_score >= 61:
        return [
            Draft(
                "Risk yüksek. Paylaşma; önce doğrula.",
                "do_not_post",
                100.0,
                ["risk_review_required"],
            )
        ]
    drafts = []
    for v in VARIANTS:
        text = render_template(event, v)
        qr = assess_quality(text)
        drafts.append(Draft(text=text, variant_label=v, quality_score=qr.score, issues=qr.issues))
    # dedupe by text while preserving order
    out, seen = [], set()
    for d in drafts:
        if d.text not in seen:
            seen.add(d.text)
            out.append(d)
    return out[:max_variants]
