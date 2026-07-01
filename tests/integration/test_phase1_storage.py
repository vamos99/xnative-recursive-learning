from __future__ import annotations

import json
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
    assert "0004" in second


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


def test_media_lifecycle_repository_tracks_references_and_snapshots(tmp_path) -> None:
    db_path = tmp_path / "phase4.sqlite3"
    exact_sha = "a" * 64

    with UnitOfWork(db_path) as uow:
        first = uow.media_lifecycle.upsert_local_object(
            exact_sha256=exact_sha,
            relative_path="aa/aa/blob.png",
            byte_size=123,
            perceptual_hash="dhash64-v1:abcd",
            storage_policy="thumbnail",
            availability="local",
            source_url="https://pbs.twimg.com/media/blob.jpg",
            retention_reason="test",
            retention_expires_at=200,
            reference_id="post-1:media-1",
            owner_type="post",
            owner_id="post-1",
            now=100,
        )
        duplicate = uow.media_lifecycle.upsert_local_object(
            exact_sha256=exact_sha,
            relative_path="aa/aa/blob.png",
            byte_size=123,
            perceptual_hash="dhash64-v1:abcd",
            storage_policy="thumbnail",
            availability="local",
            source_url="https://pbs.twimg.com/media/blob.jpg",
            retention_reason="test",
            retention_expires_at=200,
            reference_id="post-1:media-1",
            owner_type="post",
            owner_id="post-1",
            now=101,
        )
        second_ref = uow.media_lifecycle.upsert_local_object(
            exact_sha256=exact_sha,
            reference_id="post-2:media-1",
            owner_type="post",
            owner_id="post-2",
            now=102,
        )
        remaining = uow.media_lifecycle.release_reference(exact_sha, "post-1:media-1", now=103)
        snapshot = uow.media_lifecycle.record_remote_snapshot(
            source_url="https://pbs.twimg.com/media/deleted.jpg",
            reason="http_404",
            visible_text="Maçtan sonra tepki",
            alt_text="tribün",
            observed_at=300,
            now=301,
        )
        snapshot_duplicate = uow.media_lifecycle.record_remote_snapshot(
            source_url="https://pbs.twimg.com/media/deleted.jpg",
            reason="http_404",
            visible_text="Maçtan sonra tepki",
            alt_text="tribün",
            observed_at=300,
            now=302,
        )

    conn = init_db(db_path)
    object_row = conn.execute(
        "SELECT * FROM local_media_objects WHERE exact_sha256=?",
        (exact_sha,),
    ).fetchone()
    refs = conn.execute(
        "SELECT reference_id FROM local_media_references WHERE exact_sha256=?",
        (exact_sha,),
    ).fetchall()
    snapshot_rows = conn.execute("SELECT * FROM remote_media_snapshots").fetchall()
    audit_rows = conn.execute(
        """
        SELECT action, entity_type, entity_id, details_json FROM audit_log
        WHERE entity_id IN (?, ?, ?)
        ORDER BY created_at, action
        """,
        (exact_sha, snapshot.snapshot_id, snapshot_duplicate.snapshot_id),
    ).fetchall()
    audit_actions = [row["action"] for row in audit_rows]
    duplicate_ref_audit = next(
        row for row in audit_rows if row["action"] == "media.reference.duplicate"
    )
    release_audit = next(row for row in audit_rows if row["action"] == "media.reference.released")
    snapshot_audit = next(
        row for row in audit_rows if row["action"] == "media.remote_snapshot.recorded"
    )

    assert first.reference_count == 1
    assert not first.duplicate_reference
    assert duplicate.reference_count == 1
    assert duplicate.duplicate_reference
    assert second_ref.reference_count == 2
    assert remaining == 1
    assert object_row["reference_count"] == 1
    assert object_row["storage_policy"] == "thumbnail"
    assert object_row["source_url"] == "https://pbs.twimg.com/media/blob.jpg"
    assert [row["reference_id"] for row in refs] == ["post-2:media-1"]
    assert len(snapshot_rows) == 1
    assert snapshot_rows[0]["id"] == snapshot.snapshot_id
    assert snapshot_rows[0]["availability"] == "remote_unavailable"
    assert not snapshot.duplicate
    assert snapshot_duplicate.duplicate
    assert audit_actions.count("media.object.upserted") == 3
    assert audit_actions.count("media.reference.added") == 2
    assert audit_actions.count("media.reference.duplicate") == 1
    assert audit_actions.count("media.reference.released") == 1
    assert audit_actions.count("media.remote_snapshot.recorded") == 1
    assert audit_actions.count("media.remote_snapshot.duplicate") == 1
    assert json.loads(duplicate_ref_audit["details_json"])["reference_count"] == 1
    assert json.loads(release_audit["details_json"])["reference_count"] == 1
    assert json.loads(snapshot_audit["details_json"])["visible_text_present"]
