from __future__ import annotations

import json
import random
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path

from xnative.core.config import settings
from xnative.domain import (
    CapturedPost,
    FeatureRecord,
    ResourceClass,
    new_uuid,
    utc_us,
)
from xnative.domain.models import canonical_json

from .database import init_db


@dataclass(frozen=True)
class CapturePersistResult:
    capture_id: str
    job_id: str | None
    duplicate: bool


@dataclass(frozen=True)
class JobEnqueueResult:
    job_id: str
    duplicate: bool


@dataclass(frozen=True)
class ClaimedJob:
    id: str
    job_type: str
    payload_ref: str
    status: str
    resource_class: str
    attempt_count: int
    lease_owner: str
    lease_expires_at: int


class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    def __init__(self, path: str | Path | None = None):
        self.path = path
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> UnitOfWork:
        self.conn = init_db(self.path)
        self.conn.execute("BEGIN")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.conn is None:
            return
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
        self.conn = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("UnitOfWork is not active")
        return self.conn

    @property
    def captures(self) -> CaptureRepository:
        return CaptureRepository(self.connection)

    @property
    def jobs(self) -> JobRepository:
        return JobRepository(self.connection)

    @property
    def features(self) -> FeatureRepository:
        return FeatureRepository(self.connection)

    @property
    def cursors(self) -> CursorRepository:
        return CursorRepository(self.connection)

    @property
    def cache(self) -> CacheRepository:
        return CacheRepository(self.connection)


class CaptureRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def persist_capture(
        self,
        post: CapturedPost,
        raw_payload: Mapping[str, object] | None = None,
        correlation_id: str | None = None,
    ) -> CapturePersistResult:
        existing = self._find_existing(post)
        if existing is not None:
            job = self.conn.execute(
                """
                SELECT id FROM jobs
                WHERE payload_ref=? AND status IN ('pending','running','retry')
                """,
                (existing,),
            ).fetchone()
            return CapturePersistResult(
                capture_id=existing,
                job_id=str(job["id"]) if job else None,
                duplicate=True,
            )

        now = utc_us()
        quote_json = post.quote_post.model_dump_json(exclude_none=True) if post.quote_post else None
        metrics_json = post.visible_metrics.model_dump_json(exclude_none=True)
        self.conn.execute(
            """
            INSERT INTO captured_posts(
              id, schema_version, platform, platform_post_id, canonical_url,
              author_handle, visible_text, quote_post_json, visible_metrics_json,
              platform_created_at, captured_at, capture_source, selector_version,
              idempotency_key, raw_payload_hash, data_class, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post.id,
                post.schema_version,
                str(post.platform),
                post.platform_post_id,
                post.canonical_url,
                post.author_handle,
                post.visible_text,
                quote_json,
                metrics_json,
                utc_us(post.platform_created_at) if post.platform_created_at else None,
                utc_us(post.captured_at),
                str(post.capture_source),
                post.selector_version,
                post.idempotency_key,
                post.raw_payload_hash,
                str(post.data_class),
                now,
                now,
            ),
        )
        self.conn.execute(
            """
            INSERT INTO captured_posts_fts(post_id, visible_text, author_handle)
            VALUES (?, ?, ?)
            """,
            (post.id, post.visible_text, post.author_handle),
        )
        for asset in post.media:
            self.conn.execute(
                """
                INSERT INTO media_assets(
                  id, post_id, kind, media_type, source_url, alt_text, mime_type,
                  byte_size, width, height, duration_ms, exact_sha256,
                  perceptual_hash, phash, storage_policy, local_path, availability,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.id,
                    post.id,
                    str(asset.kind),
                    str(asset.kind),
                    asset.source_url,
                    asset.alt_text,
                    asset.mime_type,
                    asset.byte_size,
                    asset.width,
                    asset.height,
                    asset.duration_ms,
                    asset.exact_sha256,
                    asset.perceptual_hash,
                    asset.perceptual_hash,
                    str(asset.storage_policy),
                    asset.local_path,
                    str(asset.availability),
                    now,
                ),
            )
        inbox_id = new_uuid()
        self.conn.execute(
            """
            INSERT INTO capture_inbox(
              id, post_id, raw_payload_hash, status, received_at, correlation_id
            )
            VALUES (?, ?, ?, 'accepted', ?, ?)
            """,
            (inbox_id, post.id, post.raw_payload_hash, now, correlation_id or new_uuid()),
        )
        job_id = self._enqueue_capture_job(post.id, now)
        self._audit(
            action="capture.accepted",
            entity_type="captured_post",
            entity_id=post.id,
            details={
                "capture_source": str(post.capture_source),
                "raw_payload_hash": post.raw_payload_hash,
                "raw_payload_present": raw_payload is not None,
                "job_id": job_id,
            },
            now=now,
        )
        return CapturePersistResult(capture_id=post.id, job_id=job_id, duplicate=False)

    def _find_existing(self, post: CapturedPost) -> str | None:
        row = self.conn.execute(
            "SELECT id FROM captured_posts WHERE idempotency_key=?", (post.idempotency_key,)
        ).fetchone()
        if row:
            return str(row["id"])
        if post.platform_post_id:
            row = self.conn.execute(
                """
                SELECT id FROM captured_posts
                WHERE platform=? AND platform_post_id=?
                """,
                (str(post.platform), post.platform_post_id),
            ).fetchone()
            if row:
                return str(row["id"])
        return None

    def _enqueue_capture_job(self, post_id: str, now: int) -> str:
        result = JobRepository(self.conn).enqueue_job(
            job_type="normalize_capture",
            payload_ref=post_id,
            priority=100,
            resource_class=ResourceClass.LIGHT,
            dedupe_key=f"normalize_capture:{post_id}:v1",
            available_at=now,
        )
        return result.job_id

    def _audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Mapping[str, object],
        now: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO audit_log(id, action, entity_type, entity_id, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_uuid(), action, entity_type, entity_id, canonical_json(details), now),
        )


class JobRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def enqueue_job(
        self,
        *,
        job_type: str,
        payload_ref: str,
        priority: int = 100,
        resource_class: ResourceClass = ResourceClass.LIGHT,
        dedupe_key: str | None = None,
        max_attempts: int | None = None,
        available_at: int | None = None,
        max_pending: int | None = None,
    ) -> JobEnqueueResult:
        now = utc_us()
        active_dedupe_key = dedupe_key or f"{job_type}:{payload_ref}:v1"
        existing = self.conn.execute(
            """
            SELECT id FROM jobs
            WHERE dedupe_key=? AND status IN ('pending', 'running', 'retry')
            """,
            (active_dedupe_key,),
        ).fetchone()
        if existing is not None:
            return JobEnqueueResult(job_id=str(existing["id"]), duplicate=True)

        pending_limit = max_pending or settings.max_pending_jobs_per_resource
        pending_count = self._queued_count(resource_class)
        if pending_count >= pending_limit:
            raise RuntimeError(f"QUEUE_BACKPRESSURE:{resource_class}:{pending_count}")

        job_id = new_uuid()
        self.conn.execute(
            """
            INSERT INTO jobs(
              id, job_type, payload_ref, status, priority, resource_class, dedupe_key,
              attempt_count, max_attempts, available_at, created_at, updated_at
            )
            VALUES (?, ?, ?, 'pending', ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                job_id,
                job_type,
                payload_ref,
                priority,
                str(resource_class),
                active_dedupe_key,
                max_attempts or settings.retry_max_attempts,
                available_at or now,
                now,
                now,
            ),
        )
        return JobEnqueueResult(job_id=job_id, duplicate=False)

    def claim_next(
        self,
        owner: str,
        resource_class: ResourceClass = ResourceClass.LIGHT,
        lease_seconds: int = 60,
        max_running: int | None = None,
    ) -> ClaimedJob | None:
        now = utc_us()
        lease_expires_at = now + lease_seconds * 1_000_000
        if self._running_count(resource_class) >= self._resource_limit(resource_class, max_running):
            return None
        aging_interval_us = max(1, settings.queue_aging_interval_seconds) * 1_000_000
        aging_max_boost = max(0, settings.queue_aging_max_boost)
        row = self.conn.execute(
            """
            SELECT * FROM jobs
            WHERE status IN ('pending', 'retry')
              AND resource_class=?
              AND available_at<=?
            ORDER BY
              CASE
                WHEN priority >= 100 THEN 3
                WHEN priority >= 50 THEN 2
                ELSE 1
              END DESC,
              (
                priority +
                MIN(?, MAX(0, CAST((? - created_at) / ? AS INTEGER)))
              ) DESC,
              priority DESC,
              created_at ASC
            LIMIT 1
            """,
            (str(resource_class), now, aging_max_boost, now, aging_interval_us),
        ).fetchone()
        if row is None:
            return None
        updated = self.conn.execute(
            """
            UPDATE jobs
            SET status='running',
                lease_owner=?,
                lease_expires_at=?,
                attempt_count=attempt_count+1,
                updated_at=?
            WHERE id=? AND status IN ('pending', 'retry')
            """,
            (owner, lease_expires_at, now, row["id"]),
        ).rowcount
        if updated != 1:
            return None
        claimed = self.conn.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
        self.conn.execute(
            """
            INSERT INTO job_attempts(
              id, job_id, attempt_number, owner, started_at, status
            )
            VALUES (?, ?, ?, ?, ?, 'running')
            """,
            (new_uuid(), row["id"], int(claimed["attempt_count"]), owner, now),
        )
        return ClaimedJob(
            id=str(claimed["id"]),
            job_type=str(claimed["job_type"]),
            payload_ref=str(claimed["payload_ref"]),
            status=str(claimed["status"]),
            resource_class=str(claimed["resource_class"]),
            attempt_count=int(claimed["attempt_count"]),
            lease_owner=str(claimed["lease_owner"]),
            lease_expires_at=int(claimed["lease_expires_at"]),
        )

    def _queued_count(self, resource_class: ResourceClass) -> int:
        row = self.conn.execute(
            """
            SELECT COUNT(*) c FROM jobs
            WHERE resource_class=? AND status IN ('pending', 'retry')
            """,
            (str(resource_class),),
        ).fetchone()
        return int(row["c"])

    def _running_count(self, resource_class: ResourceClass) -> int:
        row = self.conn.execute(
            """
            SELECT COUNT(*) c FROM jobs
            WHERE resource_class=? AND status='running'
            """,
            (str(resource_class),),
        ).fetchone()
        return int(row["c"])

    def _resource_limit(self, resource_class: ResourceClass, max_running: int | None) -> int:
        if max_running is not None:
            return max(0, max_running)
        if resource_class == ResourceClass.HEAVY:
            return max(0, settings.heavy_workers)
        if resource_class == ResourceClass.IO:
            return max(0, settings.io_workers)
        return max(0, settings.light_workers)

    def recover_expired_leases(self) -> int:
        now = utc_us()
        return self.conn.execute(
            """
            UPDATE jobs
            SET status='pending',
                lease_owner=NULL,
                lease_expires_at=NULL,
                updated_at=?
            WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at<?
            """,
            (now, now),
        ).rowcount

    def complete_job(self, job_id: str) -> None:
        now = utc_us()
        self.conn.execute(
            """
            UPDATE jobs
            SET status='completed',
                lease_owner=NULL,
                lease_expires_at=NULL,
                updated_at=?
            WHERE id=? AND status='running'
            """,
            (now, job_id),
        )
        self.conn.execute(
            """
            UPDATE job_attempts
            SET status='completed', completed_at=?
            WHERE job_id=? AND status='running'
            """,
            (now, job_id),
        )

    def fail_job(
        self,
        job_id: str,
        error_code: str,
        error_message: str,
        *,
        retryable: bool,
        retry_delay_seconds: float | None = None,
    ) -> str:
        now = utc_us()
        row = self.conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError(f"Job not found: {job_id}")
        self.conn.execute(
            """
            UPDATE job_attempts
            SET status='failed', completed_at=?, error_code=?, error_message=?
            WHERE job_id=? AND status='running'
            """,
            (now, error_code, error_message, job_id),
        )
        attempt_count = int(row["attempt_count"])
        max_attempts = int(row["max_attempts"])
        if retryable and attempt_count < max_attempts:
            delay = retry_delay_seconds
            if delay is None:
                cap = min(300.0, 2.0 * (4 ** max(0, attempt_count - 1)))
                delay = random.uniform(0.0, cap)
            available_at = now + int(delay * 1_000_000)
            self.conn.execute(
                """
                UPDATE jobs
                SET status='retry',
                    priority=70,
                    available_at=?,
                    lease_owner=NULL,
                    lease_expires_at=NULL,
                    last_error_code=?,
                    last_error_message=?,
                    updated_at=?
                WHERE id=?
                """,
                (available_at, error_code, error_message, now, job_id),
            )
            return "retry"
        self.conn.execute(
            """
            UPDATE jobs
            SET status='dead',
                lease_owner=NULL,
                lease_expires_at=NULL,
                last_error_code=?,
                last_error_message=?,
                updated_at=?
            WHERE id=?
            """,
            (error_code, error_message, now, job_id),
        )
        self.conn.execute(
            """
            INSERT INTO dead_letters(
              id, job_id, reason_code, reason_message, payload_snapshot_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                new_uuid(),
                job_id,
                error_code,
                error_message,
                json.dumps({"job_id": job_id}, sort_keys=True),
                now,
            ),
        )
        return "dead"


class FeatureRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record_feature(self, feature: FeatureRecord) -> str:
        self.conn.execute(
            """
            INSERT INTO features(
              id, owner_type, owner_id, feature_name, feature_version, value_json,
              model_version, config_hash, source_ids_json, data_class, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(owner_type, owner_id, feature_name, feature_version)
            DO UPDATE SET
              value_json=excluded.value_json,
              model_version=excluded.model_version,
              config_hash=excluded.config_hash,
              source_ids_json=excluded.source_ids_json,
              data_class=excluded.data_class
            """,
            (
                feature.id,
                feature.owner_type,
                feature.owner_id,
                feature.feature_name,
                feature.feature_version,
                json.dumps(feature.value, ensure_ascii=False, sort_keys=True),
                feature.model_version,
                feature.config_hash,
                json.dumps(feature.source_ids, ensure_ascii=False, sort_keys=True),
                str(feature.data_class),
                utc_us(feature.created_at),
            ),
        )
        row = self.conn.execute(
            """
            SELECT id FROM features
            WHERE owner_type=? AND owner_id=? AND feature_name=? AND feature_version=?
            """,
            (
                feature.owner_type,
                feature.owner_id,
                feature.feature_name,
                feature.feature_version,
            ),
        ).fetchone()
        return str(row["id"])


class CursorRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, name: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM pipeline_cursors WHERE name=?",
            (name,),
        ).fetchone()

    def advance(
        self,
        name: str,
        cursor_value: str,
        *,
        high_water_mark: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        now = utc_us()
        self.conn.execute(
            """
            INSERT INTO pipeline_cursors(
              name, cursor_value, high_water_mark, metadata_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              cursor_value=excluded.cursor_value,
              high_water_mark=excluded.high_water_mark,
              metadata_json=excluded.metadata_json,
              updated_at=excluded.updated_at
            """,
            (
                name,
                cursor_value,
                high_water_mark,
                canonical_json(metadata or {}),
                now,
            ),
        )


class CacheRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, namespace: str, cache_key: str, version: str) -> object | None:
        now = utc_us()
        row = self.conn.execute(
            """
            SELECT value_json FROM cache_entries
            WHERE namespace=?
              AND cache_key=?
              AND version=?
              AND invalidated_at IS NULL
              AND (expires_at IS NULL OR expires_at>?)
            """,
            (namespace, cache_key, version, now),
        ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["value_json"]))

    def put(
        self,
        namespace: str,
        cache_key: str,
        version: str,
        value: object,
        *,
        source_ids: list[str] | None = None,
        ttl_seconds: float | None = None,
    ) -> str:
        now = utc_us()
        expires_at = None if ttl_seconds is None else now + int(ttl_seconds * 1_000_000)
        cache_id = new_uuid()
        self.conn.execute(
            """
            INSERT INTO cache_entries(
              id, namespace, cache_key, version, value_json, source_ids_json,
              expires_at, invalidated_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
            ON CONFLICT(namespace, cache_key, version) DO UPDATE SET
              value_json=excluded.value_json,
              source_ids_json=excluded.source_ids_json,
              expires_at=excluded.expires_at,
              invalidated_at=NULL,
              updated_at=excluded.updated_at
            """,
            (
                cache_id,
                namespace,
                cache_key,
                version,
                json.dumps(value, ensure_ascii=False, sort_keys=True),
                json.dumps(source_ids or [], ensure_ascii=False, sort_keys=True),
                expires_at,
                now,
                now,
            ),
        )
        row = self.conn.execute(
            """
            SELECT id FROM cache_entries
            WHERE namespace=? AND cache_key=? AND version=?
            """,
            (namespace, cache_key, version),
        ).fetchone()
        return str(row["id"])

    def invalidate(self, namespace: str, *, version: str | None = None) -> int:
        now = utc_us()
        if version is None:
            return self.conn.execute(
                """
                UPDATE cache_entries
                SET invalidated_at=?, updated_at=?
                WHERE namespace=? AND invalidated_at IS NULL
                """,
                (now, now, namespace),
            ).rowcount
        return self.conn.execute(
            """
            UPDATE cache_entries
            SET invalidated_at=?, updated_at=?
            WHERE namespace=? AND version=? AND invalidated_at IS NULL
            """,
            (now, now, namespace, version),
        ).rowcount


def rows(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[object, ...] = (),
) -> Iterator[sqlite3.Row]:
    yield from conn.execute(sql, params).fetchall()
