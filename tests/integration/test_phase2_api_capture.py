from __future__ import annotations

from fastapi.testclient import TestClient

from xnative.api.main import create_app
from xnative.capture.dom_parser import parse_extension_payload
from xnative.capture.manual_import import archive_fixture
from xnative.db.database import init_db


def payload(post_id: str = "1840000000000000100") -> dict[str, object]:
    return {
        "id": post_id,
        "url": f"https://x.com/example/status/{post_id}",
        "author_handle": "@Example",
        "text": "Bu baskı maçın kırılma anı olabilir.",
        "timestamp": "2026-06-23T08:00:00Z",
        "visible_metrics": {"likes": "12", "reposts": "3", "views": "1,240"},
        "media": [
            {
                "type": "image",
                "url": "https://pbs.twimg.com/media/example.jpg",
                "alt_text": "Futbol maçından saha görüntüsü",
            }
        ],
        "raw_capture_version": "visible_dom_v1",
    }


def test_health_and_ready_use_real_db(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))

    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready").json()

    assert ready["status"] == "ready"
    assert ready["database"] == "ok"
    assert "0001" in ready["migrations"]


def test_capture_v1_persists_post_and_job(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))

    response = client.post("/api/v1/captures", json=payload())

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["duplicate"] is False
    assert body["capture_id"]
    assert body["job_id"]

    conn = init_db(db_path)
    assert conn.execute("SELECT COUNT(*) c FROM captured_posts").fetchone()["c"] == 1
    assert conn.execute("SELECT COUNT(*) c FROM jobs").fetchone()["c"] == 1
    assert conn.execute("SELECT COUNT(*) c FROM capture_inbox").fetchone()["c"] == 1


def test_capture_alias_is_deprecated_and_idempotent(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))
    body = payload("1840000000000000101")

    first = client.post("/capture", json=body)
    second = client.post("/capture", json=body)

    assert first.status_code == 202
    assert first.headers["Deprecation"] == "true"
    assert first.json()["duplicate"] is False
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    assert second.json()["capture_id"] == first.json()["capture_id"]
    assert second.json()["job_id"] == first.json()["job_id"]

    conn = init_db(db_path)
    assert conn.execute("SELECT COUNT(*) c FROM captured_posts").fetchone()["c"] == 1
    assert conn.execute("SELECT COUNT(*) c FROM jobs").fetchone()["c"] == 1


def test_capture_rejects_oversized_payload(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))
    body = payload("1840000000000000102")
    body["text"] = "x" * (600 * 1024)

    response = client.post("/api/v1/captures", json=body)

    assert response.status_code == 413
    conn = init_db(db_path)
    assert conn.execute("SELECT COUNT(*) c FROM captured_posts").fetchone()["c"] == 0


def test_capture_validation_error_is_422(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))
    body = payload("1840000000000000103")
    body["url"] = "https://example.com/not-x"

    response = client.post("/api/v1/captures", json=body)

    assert response.status_code == 422
    conn = init_db(db_path)
    assert conn.execute("SELECT COUNT(*) c FROM captured_posts").fetchone()["c"] == 0


def test_dom_parser_filters_ui_media_and_redacts_sensitive_raw_fields() -> None:
    body = payload("1840000000000000104")
    body["url"] = f"{body['url']}?s=20&secret=abc"
    body["authorization"] = "Bearer should-not-survive"
    body["cookie"] = "session=private"
    body["media"] = [
        {
            "type": "image",
            "url": "https://pbs.twimg.com/profile_images/avatar.jpg",
            "alt_text": "avatar",
            "media_scope": "avatar",
        },
        {
            "type": "image",
            "url": "https://pbs.twimg.com/media/post.jpg?format=jpg&name=small",
            "alt_text": "Maç içi kare",
            "media_scope": "post",
        },
    ]

    parsed = parse_extension_payload(body)

    assert parsed.url == "https://x.com/example/status/1840000000000000104"
    assert len(parsed.media) == 1
    assert parsed.media[0].source_url == "https://pbs.twimg.com/media/post.jpg"
    assert parsed.media[0].media_scope == "post"
    assert parsed.parse_quality["has_url"] is True
    assert parsed.parse_quality["media_count"] == 1
    assert parsed.raw["authorization"] == "[redacted]"
    assert parsed.raw["cookie"] == "[redacted]"


def test_capture_persists_selector_version_from_parse_quality(tmp_path) -> None:
    db_path = tmp_path / "api.sqlite3"
    client = TestClient(create_app(str(db_path)))
    body = payload("1840000000000000105")
    body["parse_quality"] = {"selector_version": "visible_dom_fixture_v2"}
    body.pop("raw_capture_version")

    response = client.post("/api/v1/captures", json=body)

    assert response.status_code == 202
    conn = init_db(db_path)
    row = conn.execute("SELECT selector_version FROM captured_posts").fetchone()
    assert row["selector_version"] == "visible_dom_fixture_v2"


def test_manual_archive_fixture_persists_without_external_api(tmp_path) -> None:
    db_path = tmp_path / "archive.sqlite3"
    fixture_path = tmp_path / "manual_posts.json"
    fixture_path.write_text(
        """
        {
          "posts": [
            {
              "id": "1840000000000000106",
              "url": "https://x.com/example/status/1840000000000000106",
              "author_handle": "@Example",
              "text": "Manuel arşiv kaydı",
              "raw_capture_version": "manual_fixture_v1"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    results = archive_fixture(fixture_path, db_path)

    assert len(results) == 1
    assert results[0].duplicate is False
    conn = init_db(db_path)
    post = conn.execute("SELECT capture_source FROM captured_posts").fetchone()
    inbox = conn.execute("SELECT correlation_id FROM capture_inbox").fetchone()
    assert post["capture_source"] == "manual_json"
    assert inbox["correlation_id"] == "manual-archive"
