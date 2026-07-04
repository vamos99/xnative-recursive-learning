import json
from pathlib import Path

from xnative.capture.x_post_schema import CapturedMedia, CapturedPost
from xnative.domain import CapturedPost as DomainCapturedPost
from xnative.domain import CaptureSource, MediaAsset, MediaKind
from xnative.media.multimodal_evidence import (
    build_multimodal_evidence,
    build_multimodal_evidence_from_post,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_visual_evidence_supplies_context_when_text_is_ambiguous() -> None:
    evidence = build_multimodal_evidence(
        text="Bunu kimse beklemiyordu",
        media_items=[
            {
                "media_type": "image",
                "alt_text": "Skor tabelası ve tribünler",
            }
        ],
    )

    assert evidence.language == "tr"
    assert "skor" in evidence.topic_candidates
    assert evidence.relationship_evidence.signals["relationship"] == "visual_supplies_context"
    assert evidence.uncertainty["media_missing_is_not_negative"] is False


def test_missing_media_is_tracked_without_negative_relevance() -> None:
    evidence = build_multimodal_evidence(text="Maç sonu bu karar çok konuşulur")

    assert "maç" in evidence.topic_candidates
    assert evidence.visual_evidence.missing_reason == "missing_media"
    assert "visual" in evidence.uncertainty["missing_modalities"]
    assert evidence.uncertainty["media_missing_is_not_negative"] is True
    assert evidence.relationship_evidence.signals["relationship"] == "text_only_context"


def test_ocr_and_audio_video_signals_are_explainable() -> None:
    evidence = build_multimodal_evidence(
        text="Bu kare yeter",
        media_items=[
            {
                "id": "video-1",
                "media_type": "video",
                "alt_text": "",
            }
        ],
        ocr_text_by_media_id={"video-1": "Saha içinde penaltı anı"},
    )

    assert "penaltı" in evidence.topic_candidates
    assert evidence.visual_evidence.signals["ocr_text_count"] == 1
    assert evidence.audio_video_evidence.present
    assert evidence.relationship_evidence.signals["relationship"] == "visual_supplies_context"


def test_build_multimodal_evidence_from_legacy_capture_post() -> None:
    post = CapturedPost(
        platform_post_id="1",
        url="https://x.com/example/status/1",
        author_handle="example",
        text="Bunu konuşurlar",
        media=[CapturedMedia(media_type="image", alt_text="Futbol sahası")],
    )

    evidence = build_multimodal_evidence_from_post(post)

    assert "futbol" in evidence.topic_candidates
    assert evidence.visual_evidence.present


def test_build_multimodal_evidence_from_domain_post() -> None:
    post = DomainCapturedPost(
        platform_post_id="2",
        canonical_url="https://x.com/example/status/2",
        author_handle="example",
        visible_text="Bu baskı maçın hikayesi",
        capture_source=CaptureSource.MANUAL_JSON,
        media=[MediaAsset(kind=MediaKind.IMAGE, alt_text="tribün baskısı")],
    )

    evidence = build_multimodal_evidence_from_post(post)

    assert evidence.language == "tr"
    assert "maç" in evidence.topic_candidates
    assert evidence.relationship_evidence.signals["relationship"] == "supports"


def test_weak_supervision_golden_set_covers_non_literal_football_context() -> None:
    cases = json.loads((FIXTURES_DIR / "multimodal_weak_supervision.json").read_text())

    assert cases
    for case in cases:
        evidence = build_multimodal_evidence(
            text=case["text"],
            quoted_text=case.get("quoted_text", ""),
            media_items=case.get("media_items", []),
            ocr_text_by_media_id=case.get("ocr_text_by_media_id", {}),
        )

        assert evidence.text_evidence.signals["matched_terms"] == [], case["id"]
        for topic in case["expected_topics"]:
            assert topic in evidence.topic_candidates, case["id"]
        assert (
            evidence.relationship_evidence.signals["relationship"] == case["expected_relationship"]
        ), case["id"]
        assert evidence.relationship_evidence.present, case["id"]
