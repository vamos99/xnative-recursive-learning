from __future__ import annotations

import sqlite3

import pytest
from pydantic import ValidationError

from xnative.db.database import init_db
from xnative.db.migration_runner import applied_migrations
from xnative.db.repositories import UnitOfWork
from xnative.domain import (
    CapturedPost,
    CaptureSource,
    FeatureRecord,
    MediaAsset,
    MediaKind,
    ResourceClass,
)


def make_post(platform_post_id: str = "1840000000000000000") -> CapturedPost:
    return CapturedPost(
        platform_post_id=platform_post_id,
        canonical_url=f"https://x.com/example/status/{platform_post_id}",
        author_handle="@Example",
        visible_text="Maç sonu baskı çok konuşulur.",
        capture_source=CaptureSource.EXTENSION,
        selector_version="extension-dom-v1",
        media=[
            MediaAsset(
                kind=MediaKind.IMAGE,
                source_url="https://pbs.twimg.com/media/example.jpg",
                alt_text="Futbol sahasında skor tabelası",
            )
        ],
    )


def test_domain_contract_normalizes_and_rejects_empty_capture() -> None:
    post = make_post()
    assert post.author_handle == "example"
    assert post.idempotency_key
    assert post.media[0].post_id == post.id

    with pytest.raises(ValidationError):
        CapturedPost(
            platform_post_id="empty",
            canonical_url="https://x.com/example/status/empty",
            author_handle="example",
            visible_text="",
            capture_source=CaptureSource.MANUAL_JSON,
        )


def test_migration_is_idempotent_and_checksum_verified(tmp_path) -> None:
    db_path = tmp_path / "phase1.sqlite3"
    conn = init_db(db_path)
    first = applied_migrations(conn)
    conn.close()

    conn = init_db(db_path)
    second = applied_migrations(conn)
    conn.close()

    assert first == second
    assert "0001" in second


def test_capture_persistence_is_idempotent_and_enqueues_one_job(tmp_path) -> None:
    db_path = tmp_path / "phase1.sqlite3"
    post = make_post()

    with UnitOfWork(db_path) as uow:
        first = uow.captures.persist_capture(post, raw_payload={"source": "test"})
        second = uow.captures.persist_capture(post, raw_payload={"source": "test"})

    conn = init_db(db_path)
    post_count = conn.execute("SELECT COUNT(*) c FROM captured_posts").fetchone()["c"]
    job_count = conn.execute("SELECT COUNT(*) c FROM jobs").fetchone()["c"]
    audit_count = conn.execute("SELECT COUNT(*) c FROM audit_log").fetchone()["c"]
    media_count = conn.execute("SELECT COUNT(*) c FROM media_assets").fetchone()["c"]

    assert first.capture_id == second.capture_id
    assert first.job_id == second.job_id
    assert not first.duplicate
    assert second.duplicate
    assert post_count == 1
    assert job_count == 1
    assert audit_count == 1
    assert media_count == 1


def test_foreign_key_failure_rolls_back_transaction(tmp_path) -> None:
    db_path = tmp_path / "phase1.sqlite3"

    with pytest.raises(sqlite3.IntegrityError), UnitOfWork(db_path) as uow:
        uow.connection.execute(
            """
            INSERT INTO media_assets(id, post_id, kind, created_at)
            VALUES ('bad-media-id', 'missing-post-id', 'image', 1)
            """
        )

    conn = init_db(db_path)
    count = conn.execute("SELECT COUNT(*) c FROM media_assets").fetchone()["c"]
    assert count == 0


def test_job_claim_is_single_consumer(tmp_path) -> None:
    db_path = tmp_path / "phase1.sqlite3"
    post = make_post("1840000000000000001")
    with UnitOfWork(db_path) as uow:
        uow.captures.persist_capture(post)

    with UnitOfWork(db_path) as uow:
        first = uow.jobs.claim_next("worker-a", ResourceClass.LIGHT)
        second = uow.jobs.claim_next("worker-b", ResourceClass.LIGHT)

    assert first is not None
    assert first.status == "running"
    assert first.lease_owner == "worker-a"
    assert first.attempt_count == 1
    assert second is None


def test_feature_record_requires_provenance(tmp_path) -> None:
    db_path = tmp_path / "phase1.sqlite3"
    post = make_post("1840000000000000002")
    with UnitOfWork(db_path) as uow:
        result = uow.captures.persist_capture(post)
        feature_id = uow.features.record_feature(
            FeatureRecord(
                owner_type="post",
                owner_id=result.capture_id,
                feature_name="cheap_text",
                feature_version="cheap-text-v1",
                value={"has_media": True, "language": "tr"},
                model_version="rules-v1",
                config_hash="config-sha256-test",
                source_ids=[result.capture_id],
            )
        )

    conn = init_db(db_path)
    row = conn.execute("SELECT * FROM features WHERE id=?", (feature_id,)).fetchone()
    assert row["model_version"] == "rules-v1"
    assert row["feature_version"] == "cheap-text-v1"
    assert row["config_hash"] == "config-sha256-test"
    assert result.capture_id in row["source_ids_json"]
