from __future__ import annotations

from typing import Any

from xnative.nlp.quality_filter import assess_quality

TEMPLATES = {
    "reaction": [
        "Bu pozisyon daha çok konuşulur.",
        "Bu görüntü tek başına gündem olur.",
        "Bunu maçtan sonra tekrar açarlar.",
    ],
    "dry_humor": [
        "Dakika {minute}, senaryo yine aynı.",
        "Klasik maç günü hikayesi.",
        "Bir futbol akşamı daha sakin geçmedi.",
    ],
    "neutral_short": [
        "{topic} cephesinde gündem bu pozisyona döndü.",
        "Bu olay kısa sürede konuşulur.",
        "Şimdilik not düşelim, devamı gelir.",
    ],
    "quote_context": [
        "Burada mesele karar değil, standardın değişmesi.",
        "Bu alıntı tek başına bağlamı anlatıyor.",
        "Bunu kenara yazmak lazım.",
    ],
}


def render_template(event: dict[str, Any], variant: str) -> str:
    topic = event.get("team") or event.get("topic") or "Futbol"
    minute = event.get("minute") or "70"
    for tpl in TEMPLATES.get(variant, TEMPLATES["neutral_short"]):
        text = tpl.format(topic=topic, minute=minute)
        if assess_quality(text).passed:
            return text
    return TEMPLATES["neutral_short"][1]
