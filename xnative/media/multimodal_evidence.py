from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from xnative.media.ocr import extract_ocr_text
from xnative.nlp.language_detector import detect_language
from xnative.nlp.text_cleaner import clean_text, combined_context

FOOTBALL_TERMS = frozenset(
    {
        "asist",
        "derbi",
        "forma",
        "futbol",
        "gol",
        "hakem",
        "kale",
        "kart",
        "lig",
        "maç",
        "mac",
        "oyuncu",
        "penaltı",
        "penalti",
        "saha",
        "skor",
        "stad",
        "stadyum",
        "takım",
        "takim",
        "taraftar",
        "tribün",
        "tribun",
    }
)


@dataclass(frozen=True)
class ModalityEvidence:
    name: str
    present: bool
    confidence: float
    signals: dict[str, object] = field(default_factory=dict)
    missing_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "present": self.present,
            "confidence": self.confidence,
            "signals": self.signals,
            "missing_reason": self.missing_reason,
        }


@dataclass(frozen=True)
class MultimodalEvidence:
    language: str
    combined_text: str
    topic_candidates: tuple[str, ...]
    text_evidence: ModalityEvidence
    quote_evidence: ModalityEvidence
    visual_evidence: ModalityEvidence
    audio_video_evidence: ModalityEvidence
    relationship_evidence: ModalityEvidence
    uncertainty: dict[str, object]
    feature_version: str = "multimodal-evidence-v1"

    def as_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "combined_text": self.combined_text,
            "topic_candidates": list(self.topic_candidates),
            "text_evidence": self.text_evidence.as_dict(),
            "quote_evidence": self.quote_evidence.as_dict(),
            "visual_evidence": self.visual_evidence.as_dict(),
            "audio_video_evidence": self.audio_video_evidence.as_dict(),
            "relationship_evidence": self.relationship_evidence.as_dict(),
            "uncertainty": self.uncertainty,
            "feature_version": self.feature_version,
        }


def _token_matches(text: str) -> tuple[str, ...]:
    lowered = clean_text(text).lower()
    matches = sorted(term for term in FOOTBALL_TERMS if term in lowered)
    return tuple(matches)


def _media_attr(media: object, key: str, default: object = "") -> object:
    if isinstance(media, Mapping):
        return media.get(key, default)
    return getattr(media, key, default)


def _media_kind(media: object) -> str:
    kind = _media_attr(media, "kind", None)
    if kind is None:
        kind = _media_attr(media, "media_type", "unknown")
    value = str(kind or "unknown")
    return value.split(".")[-1].lower()


def _media_id(media: object, index: int) -> str:
    media_id = _media_attr(media, "id", None)
    if media_id:
        return str(media_id)
    source_url = _media_attr(media, "source_url", None)
    if source_url:
        return str(source_url)
    return f"media-{index}"


def _collect_media_text(
    media_items: Sequence[object],
    *,
    ocr_text_by_media_id: Mapping[str, str] | None = None,
    run_ocr: bool = False,
) -> tuple[list[str], list[str], list[str], int]:
    alt_texts: list[str] = []
    ocr_texts: list[str] = []
    ocr_statuses: list[str] = []
    audio_video_count = 0
    supplied_ocr = ocr_text_by_media_id or {}

    for index, media in enumerate(media_items):
        media_id = _media_id(media, index)
        kind = _media_kind(media)
        if kind in {"video", "gif", "audio"}:
            audio_video_count += 1
        alt_text = str(_media_attr(media, "alt_text", "") or "").strip()
        if alt_text:
            alt_texts.append(alt_text)

        direct_ocr = str(_media_attr(media, "ocr_text", "") or "").strip()
        supplied = supplied_ocr.get(media_id, "").strip()
        if direct_ocr or supplied:
            ocr_texts.append(direct_ocr or supplied)
            ocr_statuses.append("ocr_supplied")
            continue

        local_path = str(_media_attr(media, "local_path", "") or "").strip()
        if run_ocr and local_path and kind in {"image", "video", "gif"}:
            ocr_text, status = extract_ocr_text(local_path)
            if ocr_text.strip():
                ocr_texts.append(ocr_text.strip())
            ocr_statuses.append(status)
        elif alt_text:
            ocr_statuses.append("alt_text_fallback")
        else:
            ocr_statuses.append("missing_visual_text")

    return alt_texts, ocr_texts, ocr_statuses, audio_video_count


def build_multimodal_evidence(
    *,
    text: str = "",
    quoted_text: str = "",
    media_items: Sequence[object] | None = None,
    ocr_text_by_media_id: Mapping[str, str] | None = None,
    run_ocr: bool = False,
) -> MultimodalEvidence:
    media = list(media_items or [])
    normalized_text = clean_text(text)
    normalized_quote = clean_text(quoted_text)
    alt_texts, ocr_texts, ocr_statuses, audio_video_count = _collect_media_text(
        media,
        ocr_text_by_media_id=ocr_text_by_media_id,
        run_ocr=run_ocr,
    )
    context = combined_context(normalized_text, normalized_quote, alt_texts, ocr_texts)
    text_terms = _token_matches(normalized_text)
    quote_terms = _token_matches(normalized_quote)
    visual_terms = _token_matches(" ".join(alt_texts + ocr_texts))
    topic_candidates = tuple(sorted(set(text_terms + quote_terms + visual_terms)))
    language = detect_language(context)

    text_evidence = ModalityEvidence(
        name="text",
        present=bool(normalized_text),
        confidence=0.85 if text_terms else (0.45 if normalized_text else 0.0),
        signals={"matched_terms": list(text_terms), "char_count": len(normalized_text)},
        missing_reason=None if normalized_text else "missing_text",
    )
    quote_evidence = ModalityEvidence(
        name="quote",
        present=bool(normalized_quote),
        confidence=0.75 if quote_terms else (0.35 if normalized_quote else 0.0),
        signals={"matched_terms": list(quote_terms), "char_count": len(normalized_quote)},
        missing_reason=None if normalized_quote else "missing_quote",
    )
    visual_present = bool(media)
    visual_text_present = bool(alt_texts or ocr_texts)
    visual_evidence = ModalityEvidence(
        name="visual",
        present=visual_present,
        confidence=0.80
        if visual_terms
        else (0.45 if visual_text_present else 0.20 if media else 0.0),
        signals={
            "media_count": len(media),
            "alt_text_count": len(alt_texts),
            "ocr_text_count": len(ocr_texts),
            "ocr_statuses": ocr_statuses,
            "matched_terms": list(visual_terms),
        },
        missing_reason=None if visual_present else "missing_media",
    )
    audio_video_evidence = ModalityEvidence(
        name="audio_video",
        present=audio_video_count > 0,
        confidence=0.40 if audio_video_count else 0.0,
        signals={"audio_video_count": audio_video_count},
        missing_reason=None if audio_video_count else "missing_audio_video",
    )

    text_has_topic = bool(text_terms or quote_terms)
    visual_has_topic = bool(visual_terms)
    if text_has_topic and visual_has_topic:
        relationship = "supports"
        relationship_confidence = 0.75
    elif not text_has_topic and visual_has_topic:
        relationship = "visual_supplies_context"
        relationship_confidence = 0.65
    elif text_has_topic and media and not visual_has_topic:
        relationship = "media_unclear_not_penalized"
        relationship_confidence = 0.45
    elif text_has_topic:
        relationship = "text_only_context"
        relationship_confidence = 0.55
    else:
        relationship = "insufficient_topic_evidence"
        relationship_confidence = 0.20

    relationship_evidence = ModalityEvidence(
        name="relationship",
        present=relationship != "insufficient_topic_evidence",
        confidence=relationship_confidence,
        signals={
            "relationship": relationship,
            "text_terms": list(text_terms),
            "quote_terms": list(quote_terms),
            "visual_terms": list(visual_terms),
        },
    )
    uncertainty = {
        "missing_modalities": [
            name
            for name, present in {
                "text": text_evidence.present,
                "quote": quote_evidence.present,
                "visual": visual_evidence.present,
                "audio_video": audio_video_evidence.present,
            }.items()
            if not present
        ],
        "media_missing_is_not_negative": not visual_evidence.present,
        "requires_heavy_model": False,
        "fallback_policy": "local_rules_no_paid_api",
    }

    return MultimodalEvidence(
        language=language,
        combined_text=context,
        topic_candidates=topic_candidates,
        text_evidence=text_evidence,
        quote_evidence=quote_evidence,
        visual_evidence=visual_evidence,
        audio_video_evidence=audio_video_evidence,
        relationship_evidence=relationship_evidence,
        uncertainty=uncertainty,
    )


def build_multimodal_evidence_from_post(
    post: object,
    *,
    ocr_text_by_media_id: Mapping[str, str] | None = None,
    run_ocr: bool = False,
) -> MultimodalEvidence:
    quote = getattr(post, "quote_post", None)
    quoted_text = getattr(post, "quoted_text", "")
    if quote is not None:
        quoted_text = str(getattr(quote, "visible_text", "") or "")
    text = str(getattr(post, "visible_text", getattr(post, "text", "")) or "")
    media = list(getattr(post, "media", []) or [])
    return build_multimodal_evidence(
        text=text,
        quoted_text=str(quoted_text or ""),
        media_items=media,
        ocr_text_by_media_id=ocr_text_by_media_id,
        run_ocr=run_ocr,
    )
