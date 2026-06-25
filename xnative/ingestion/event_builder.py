from __future__ import annotations

from typing import Any

from xnative.capture.x_post_schema import CapturedPost
from xnative.ingestion.normalizer import normalize_post_text

FOOTBALL_TERMS = [
    "gol",
    "maç",
    "derbi",
    "futbol",
    "transfer",
    "hakem",
    "penaltı",
    "galatasaray",
    "fenerbahçe",
    "beşiktaş",
    "trabzonspor",
]


def infer_event_type(text: str) -> str:
    low = (text or "").lower()
    if "transfer" in low:
        return "transfer"
    if any(w in low for w in ["gol", "maç", "penaltı", "hakem"]):
        return "match_moment"
    if any(w in low for w in ["sakat", "kriz"]):
        return "injury"
    if any(w in low for w in ["meme", "mizah", "😂"]):
        return "meme"
    return "global_football" if any(w in low for w in FOOTBALL_TERMS) else "other"


def build_event(post: CapturedPost) -> dict[str, Any]:
    text = normalize_post_text(post)
    return {
        "event_type": infer_event_type(text),
        "title": text[:80],
        "summary": text[:240],
        "source_count": 1,
    }
