from __future__ import annotations

import json

import pytest

from xnative.db.database import init_db
from xnative.db.repositories import UnitOfWork
from xnative.domain import CapturedPost, CaptureSource, ResourceClass, utc_us
from xnative.worker.scheduler import run_due_job_once, run_worker_loop


def make_post(post_id: str = "1840000000000000200") -> CapturedPost:
    return CapturedPost(
        platform_post_id=post_id,
        canonical_url=f"https://x.com/example/status/{post_id}",
        author_handle="example",
        visible_text="Bu pres kırılma anı olabilir.",
        capture_source=CaptureSource.EXTENSION,
        selector_version="visible_dom_v1",
    )


def test_worker_completes_normalize_capture_job(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        result = uow.captures.persist_capture(make_post())
        job_id = result.job_id

    assert run_due_job_once(str(db_path))

    conn = init_db(db_path)
    job = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    feature_count = conn.execute(
        "SELECT COUNT(*) c FROM features WHERE feature_name='normalized_capture'"
    ).fetchone()["c"]
    attempt = conn.execute("SELECT status FROM job_attempts WHERE job_id=?", (job_id,)).fetchone()
    assert job["status"] == "completed"
    assert feature_count == 1
    assert attempt["status"] == "completed"


def test_expired_running_job_is_recovered_and_claimed(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        result = uow.captures.persist_capture(make_post("1840000000000000201"))
        job = uow.jobs.claim_next("worker-a", ResourceClass.LIGHT, lease_seconds=60)
        assert job is not None
        uow.connection.execute(
            "UPDATE jobs SET lease_expires_at=1 WHERE id=?",
            (job.id,),
        )

    with UnitOfWork(db_path) as uow:
        recovered = uow.jobs.recover_expired_leases()
        reclaimed = uow.jobs.claim_next("worker-b", ResourceClass.LIGHT)

    assert recovered == 1
    assert reclaimed is not None
    assert reclaimed.id == result.job_id
    assert reclaimed.lease_owner == "worker-b"
    assert reclaimed.attempt_count == 2


def test_retryable_failure_then_dead_letter(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        result = uow.captures.persist_capture(make_post("1840000000000000202"))
        job = uow.jobs.claim_next("worker-a", ResourceClass.LIGHT)
        assert job is not None
        retry_state = uow.jobs.fail_job(
            job.id,
            "TRANSIENT",
            "temporary failure",
            retryable=True,
            retry_delay_seconds=0,
        )

    with UnitOfWork(db_path) as uow:
        retry_job = uow.jobs.claim_next("worker-b", ResourceClass.LIGHT)
        assert retry_job is not None
        uow.connection.execute(
            "UPDATE jobs SET attempt_count=max_attempts WHERE id=?",
            (retry_job.id,),
        )
        dead_state = uow.jobs.fail_job(
            retry_job.id,
            "TRANSIENT",
            "max attempts reached",
            retryable=True,
            retry_delay_seconds=0,
        )

    conn = init_db(db_path)
    job_row = conn.execute("SELECT status FROM jobs WHERE id=?", (result.job_id,)).fetchone()
    dead_count = conn.execute("SELECT COUNT(*) c FROM dead_letters").fetchone()["c"]
    assert retry_state == "retry"
    assert dead_state == "dead"
    assert job_row["status"] == "dead"
    assert dead_count == 1


def test_unknown_job_type_goes_dead_without_retry(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    now = 1
    conn = init_db(db_path)
    conn.execute(
        """
        INSERT INTO jobs(
          id, job_type, payload_ref, status, priority, resource_class, dedupe_key,
          attempt_count, max_attempts, available_at, created_at, updated_at
        )
        VALUES ('unknown-job', 'missing_handler', 'payload', 'pending', 100, 'light',
                'missing:payload', 0, 5, ?, ?, ?)
        """,
        (now, now, now),
    )
    conn.commit()

    assert run_due_job_once(str(db_path))

    conn = init_db(db_path)
    row = conn.execute("SELECT status, last_error_code FROM jobs WHERE id='unknown-job'").fetchone()
    assert row["status"] == "dead"
    assert row["last_error_code"] == "UNKNOWN_JOB_TYPE"


def test_resource_semaphore_blocks_when_class_limit_is_reached(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        first = uow.jobs.enqueue_job(
            job_type="hydrate_media",
            payload_ref="media-1",
            resource_class=ResourceClass.HEAVY,
            dedupe_key="hydrate_media:media-1:v1",
        )
        second = uow.jobs.enqueue_job(
            job_type="hydrate_media",
            payload_ref="media-2",
            resource_class=ResourceClass.HEAVY,
            dedupe_key="hydrate_media:media-2:v1",
        )
        claimed_first = uow.jobs.claim_next(
            "worker-heavy-a",
            ResourceClass.HEAVY,
            max_running=1,
        )
        blocked_claim = uow.jobs.claim_next(
            "worker-heavy-b",
            ResourceClass.HEAVY,
            max_running=1,
        )

    assert not first.duplicate
    assert not second.duplicate
    assert claimed_first is not None
    assert blocked_claim is None

    with UnitOfWork(db_path) as uow:
        uow.jobs.complete_job(claimed_first.id)
        claimed_second = uow.jobs.claim_next(
            "worker-heavy-b",
            ResourceClass.HEAVY,
            max_running=1,
        )

    assert claimed_second is not None
    assert claimed_second.payload_ref == "media-2"


def test_priority_aging_prevents_old_jobs_from_starving_without_burying_live_work(
    tmp_path,
) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    very_old = 1
    fresh_now = utc_us()
    conn = init_db(db_path)
    conn.execute(
        """
        INSERT INTO jobs(
          id, job_type, payload_ref, status, priority, resource_class, dedupe_key,
          attempt_count, max_attempts, available_at, created_at, updated_at
        )
        VALUES ('old-job', 'backfill', 'old', 'pending', 60, 'light',
                'backfill:old:v1', 0, 5, 1, ?, ?)
        """,
        (very_old, very_old),
    )
    conn.execute(
        """
        INSERT INTO jobs(
          id, job_type, payload_ref, status, priority, resource_class, dedupe_key,
          attempt_count, max_attempts, available_at, created_at, updated_at
        )
        VALUES ('fresh-job', 'backfill', 'fresh', 'pending', 70, 'light',
                'backfill:fresh:v1', 0, 5, 1, ?, ?)
        """,
        (fresh_now, fresh_now),
    )
    conn.execute(
        """
        INSERT INTO jobs(
          id, job_type, payload_ref, status, priority, resource_class, dedupe_key,
          attempt_count, max_attempts, available_at, created_at, updated_at
        )
        VALUES ('live-job', 'normalize_capture', 'live', 'pending', 100, 'light',
                'normalize_capture:live:v1', 0, 5, 1, ?, ?)
        """,
        (fresh_now, fresh_now),
    )
    conn.commit()

    with UnitOfWork(db_path) as uow:
        live = uow.jobs.claim_next("worker-a", ResourceClass.LIGHT, max_running=10)
        assert live is not None
        uow.jobs.complete_job(live.id)
        aged = uow.jobs.claim_next("worker-a", ResourceClass.LIGHT, max_running=10)

    assert live.id == "live-job"
    assert aged is not None
    assert aged.id == "old-job"


def test_enqueue_dedupes_and_applies_bounded_backpressure(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        first = uow.jobs.enqueue_job(
            job_type="backfill",
            payload_ref="page-1",
            dedupe_key="backfill:page-1:v1",
            max_pending=2,
        )
        duplicate = uow.jobs.enqueue_job(
            job_type="backfill",
            payload_ref="page-1",
            dedupe_key="backfill:page-1:v1",
            max_pending=2,
        )
        uow.jobs.enqueue_job(
            job_type="backfill",
            payload_ref="page-2",
            dedupe_key="backfill:page-2:v1",
            max_pending=2,
        )
        with pytest.raises(RuntimeError, match="QUEUE_BACKPRESSURE"):
            uow.jobs.enqueue_job(
                job_type="backfill",
                payload_ref="page-3",
                dedupe_key="backfill:page-3:v1",
                max_pending=2,
            )

    assert not first.duplicate
    assert duplicate.duplicate
    assert duplicate.job_id == first.job_id


def test_cursor_and_cache_repositories_support_incremental_runtime_state(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        uow.cursors.advance(
            "x_search_recent",
            "cursor-2",
            high_water_mark="cursor-9",
            metadata={"source": "manual_fixture"},
        )
        cache_id = uow.cache.put(
            "post_features",
            "post-1",
            "feature-v1",
            {"score": 0.75},
            source_ids=["post-1"],
        )
        cached_value = uow.cache.get("post_features", "post-1", "feature-v1")
        invalidated = uow.cache.invalidate("post_features", version="feature-v1")
        after_invalidate = uow.cache.get("post_features", "post-1", "feature-v1")
        cursor = uow.cursors.get("x_search_recent")

    assert len(cache_id) == 36
    assert cached_value == {"score": 0.75}
    assert invalidated == 1
    assert after_invalidate is None
    assert cursor is not None
    assert cursor["cursor_value"] == "cursor-2"
    assert json.loads(cursor["metadata_json"]) == {"source": "manual_fixture"}


def test_worker_loop_processes_multiple_jobs_and_stops_when_idle(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        uow.captures.persist_capture(make_post("1840000000000000203"))
        uow.captures.persist_capture(make_post("1840000000000000204"))

    processed = run_worker_loop(
        str(db_path),
        owner="worker-loop",
        max_jobs=2,
        stop_after_idle=1,
        idle_sleep_seconds=0,
    )

    conn = init_db(db_path)
    completed = conn.execute("SELECT COUNT(*) c FROM jobs WHERE status='completed'").fetchone()["c"]
    assert processed == 2
    assert completed == 2


def test_failed_handler_rolls_back_partial_side_effects_before_retry(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    with UnitOfWork(db_path) as uow:
        uow.jobs.enqueue_job(
            job_type="partial_failure",
            payload_ref="payload-1",
            dedupe_key="partial_failure:payload-1:v1",
        )

    def failing_handler(job, uow: UnitOfWork) -> None:
        uow.cache.put(
            "handler_side_effect",
            job.payload_ref,
            "v1",
            {"should_not_commit": True},
        )
        raise ValueError("boom")

    assert run_due_job_once(
        str(db_path),
        handlers={"partial_failure": failing_handler},
    )

    conn = init_db(db_path)
    cached = conn.execute("SELECT COUNT(*) c FROM cache_entries").fetchone()["c"]
    job = conn.execute(
        "SELECT status, last_error_code FROM jobs WHERE job_type='partial_failure'"
    ).fetchone()
    assert cached == 0
    assert job["status"] == "retry"
    assert job["last_error_code"] == "ValueError"
