from pathlib import Path

from xnative.capture.manual_import import load_fixture
from xnative.db.seed import seed
from xnative.learning.feedback_store import record_feedback
from xnative.learning.weekly_report import generate_weekly_report
from xnative.sample_pipeline import run_sample

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "posts.json"


def test_fixture_ingest_count():
    posts = load_fixture(FIXTURE)
    assert len(posts) == 10
    assert any(p.quoted_text for p in posts)
    assert any(p.media and p.media[0].alt_text for p in posts)


def test_sample_pipeline_generates_suggestions_and_candidates():
    result = run_sample(FIXTURE)
    assert result["post_count"] == 10
    assert any(
        len(e["drafts"]) >= 3 or e["drafts"][0]["variant_label"] == "do_not_post"
        for e in result["events"]
    )
    assert result["source_candidates"]


def test_feedback_updates_learning_and_report(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    conn = seed(db_path)
    conn.execute(
        "INSERT INTO suggestions(event_id,text,variant_label,status) "
        "VALUES (1,'Bu pozisyon konuşulur','reaction','pending')"
    )
    suggestion_id = conn.execute("SELECT id FROM suggestions").fetchone()["id"]
    conn.commit()
    record_feedback(suggestion_id, "approved", db_path=db_path)
    report = generate_weekly_report(db_path)
    assert "approved" in report and "tone.reaction" in report
