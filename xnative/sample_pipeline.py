from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from xnative.capture.manual_import import load_fixture
from xnative.generation.draft_generator import generate_drafts
from xnative.ingestion.event_builder import build_event
from xnative.media.media_features import media_context_score
from xnative.media.media_risk import media_risk
from xnative.nlp.quote_context import quote_context_risk
from xnative.scoring.account_candidate_score import CandidateSignals, calculate_candidate_score
from xnative.scoring.event_score import EventScoreBreakdown, calculate_event_score
from xnative.scoring.final_decision_score import decision_label
from xnative.scoring.risk_score import calculate_risk_score


def run_sample(fixture_path: str | Path = "tests/fixtures/posts.json") -> dict[str, Any]:
    posts = load_fixture(fixture_path)
    results = []
    candidates = {}
    for post in posts:
        event = build_event(post)
        mctx = media_context_score([m.__dict__ for m in post.media])
        mrisk = max([media_risk(alt_text=m.alt_text)[0] for m in post.media] or [0])
        qrisk = quote_context_risk(post.quoted_text)
        risk, issues = calculate_risk_score(
            event["summary"], media_risk_score=mrisk, quote_risk_score=qrisk
        )
        score, breakdown = calculate_event_score(
            EventScoreBreakdown(
                source_reliability=65,
                source_count_score=30,
                velocity_score=45,
                relevance_score=80 if event["event_type"] != "other" else 30,
                novelty_score=60,
                media_context_score=mctx,
                risk_score=risk,
                fatigue_score=0,
            )
        )
        drafts = [d.__dict__ for d in generate_drafts(event, risk)]
        results.append(
            {
                "post": post.to_dict(),
                "event": event,
                "risk": risk,
                "risk_issues": issues,
                "score": score,
                "decision": decision_label(score, risk),
                "drafts": drafts,
                "breakdown": breakdown,
            }
        )
        signals = CandidateSignals(
            football_relevance=80 if event["event_type"] != "other" else 20,
            early_signal_quality=40,
            media_context_quality=mctx,
            quote_context_quality=60 if post.quoted_text else 0,
            language_style_fit=70,
            engagement_quality=50,
            misinformation_risk=30 if "iddia" in event["summary"].lower() else 0,
            toxicity_risk=0,
        )
        cs, cb = calculate_candidate_score(signals)
        candidates[post.author_handle] = {
            "candidate_score": cs,
            "explain": cb,
            "example_post": post.text,
        }
    return {"post_count": len(posts), "events": results, "source_candidates": candidates}


if __name__ == "__main__":
    print(json.dumps(run_sample(), ensure_ascii=False, indent=2))
