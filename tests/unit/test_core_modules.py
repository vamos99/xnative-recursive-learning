from xnative.capture.dom_parser import parse_extension_payload
from xnative.generation.draft_generator import generate_drafts
from xnative.ingestion.dedup import post_dedup_hash
from xnative.learning.online_weights import update_weight
from xnative.media.media_risk import media_risk
from xnative.nlp.ai_phrase_filter import find_ai_phrases
from xnative.nlp.quality_filter import assess_quality
from xnative.nlp.text_cleaner import clean_text, combined_context
from xnative.scoring.account_candidate_score import CandidateSignals, calculate_candidate_score
from xnative.scoring.event_score import EventScoreBreakdown, calculate_event_score
from xnative.scoring.novelty_fatigue import fatigue_score
from xnative.scoring.risk_score import calculate_risk_score


def test_text_cleaner_preserves_turkish_and_replaces_url():
    assert clean_text("Gol! https://x.com/a  maç") == "Gol! <url> maç"


def test_combined_context_uses_quote_and_alt():
    ctx = combined_context("Bunu konuşurlar", "Hakem kararı", ["penaltı pozisyonu"])
    assert "penaltı" in ctx


def test_ai_phrase_filter_blocks_news_tone():
    assert find_ai_phrases("Bu bağlamda önemli bir gelişme yaşandı")


def test_quality_filter_flags_news_tone():
    q = assess_quality("Futbol dünyasında gündem yaratan bu gelişme çok kritik.")
    assert not q.passed


def test_dedup_hash_stable():
    p = parse_extension_payload({"id": "1", "url": "u", "author_handle": "a", "text": "t"})
    assert post_dedup_hash(p) == post_dedup_hash(p)


def test_media_risk_unknown_review():
    score, label = media_risk("unknown")
    assert score >= 50 and "unknown" in label


def test_risk_score_claim():
    score, issues = calculate_risk_score("Transfer iddiası doğrulanmadı")
    assert score > 0 and "misinformation" in issues


def test_event_score_range():
    score, explain = calculate_event_score(EventScoreBreakdown(relevance_score=90, risk_score=10))
    assert 0 <= score <= 100 and explain["formula"]


def test_candidate_score_action():
    score, explain = calculate_candidate_score(
        CandidateSignals(football_relevance=90, language_style_fit=80)
    )
    assert 0 <= score <= 100 and explain["action"]


def test_fatigue_detects_near_duplicate():
    score, issues = fatigue_score(
        "Bu pozisyon daha çok konuşulur", ["Bu pozisyon daha çok konuşulur."]
    )
    assert score >= 70 and issues


def test_learning_weight_update():
    assert update_weight(1.0, 1.0, 1.0) > 1.0


def test_template_generation_without_llm():
    drafts = generate_drafts({"event_type": "match_moment", "topic": "Galatasaray"}, 0)
    assert len(drafts) >= 3
    assert all(d.quality_score >= 60 for d in drafts)
