from __future__ import annotations

import time
from collections.abc import Callable

from xnative.core.config import settings
from xnative.core.errors import FatalJobError, RetryableJobError, StageTimeoutError
from xnative.db.repositories import ClaimedJob, UnitOfWork
from xnative.domain import ResourceClass
from xnative.worker.jobs import normalize_capture_job

JobHandler = Callable[[ClaimedJob, UnitOfWork], object]

DEFAULT_HANDLERS: dict[str, JobHandler] = {
    "normalize_capture": normalize_capture_job,
}


def run_once(job):
    return job()


def run_due_job_once(
    db_path: str | None = None,
    *,
    owner: str = "worker-light",
    resource_class: ResourceClass = ResourceClass.LIGHT,
    handlers: dict[str, JobHandler] | None = None,
    token_bucket: str | None = None,
    token_cost: float = 1.0,
) -> bool:
    active_handlers = handlers or DEFAULT_HANDLERS
    with UnitOfWork(db_path) as uow:
        uow.jobs.recover_expired_leases()
        if token_bucket is not None and not uow.rate_limits.try_acquire(
            token_bucket,
            capacity=settings.worker_token_bucket_capacity,
            refill_per_second=settings.worker_token_bucket_refill_per_second,
            cost=token_cost,
        ):
            return False
        job = uow.jobs.claim_next(owner=owner, resource_class=resource_class)
        if job is None:
            return False
        handler = active_handlers.get(job.job_type)
        if handler is None:
            uow.jobs.fail_job(
                job.id,
                "UNKNOWN_JOB_TYPE",
                f"No handler registered for {job.job_type}",
                retryable=False,
            )
            return True
        try:
            uow.connection.execute("SAVEPOINT job_handler")
            handler(job, uow)
        except Exception as exc:
            uow.connection.execute("ROLLBACK TO job_handler")
            uow.connection.execute("RELEASE job_handler")
            error_code, retryable = _classify_job_exception(exc)
            uow.jobs.fail_job(
                job.id,
                error_code,
                str(exc),
                retryable=retryable,
            )
        else:
            uow.connection.execute("RELEASE job_handler")
            uow.jobs.complete_job(job.id)
        return True


def _classify_job_exception(exc: Exception) -> tuple[str, bool]:
    if isinstance(exc, FatalJobError):
        return exc.__class__.__name__, False
    if isinstance(exc, StageTimeoutError):
        return "STAGE_TIMEOUT", True
    if isinstance(exc, RetryableJobError):
        return exc.__class__.__name__, True
    return exc.__class__.__name__, True


def run_due_job_batch(
    db_path: str | None = None,
    *,
    owner: str = "worker-light",
    resource_class: ResourceClass = ResourceClass.LIGHT,
    handlers: dict[str, JobHandler] | None = None,
    batch_size: int | None = None,
    token_bucket: str | None = None,
) -> int:
    limit = batch_size or settings.worker_batch_size
    processed = 0
    for index in range(max(0, limit)):
        did_work = run_due_job_once(
            db_path,
            owner=f"{owner}-{index + 1}",
            resource_class=resource_class,
            handlers=handlers,
            token_bucket=token_bucket,
        )
        if not did_work:
            break
        processed += 1
    return processed


def run_worker_loop(
    db_path: str | None = None,
    *,
    owner: str = "worker-light",
    resource_class: ResourceClass = ResourceClass.LIGHT,
    handlers: dict[str, JobHandler] | None = None,
    max_jobs: int | None = None,
    stop_after_idle: int | None = None,
    idle_sleep_seconds: float | None = None,
    batch_size: int | None = None,
    token_bucket: str | None = None,
) -> int:
    processed = 0
    idle_count = 0
    sleep_seconds = (
        settings.worker_idle_sleep_seconds
        if idle_sleep_seconds is None
        else max(0.0, idle_sleep_seconds)
    )
    while True:
        batch_processed = run_due_job_batch(
            db_path,
            owner=owner,
            resource_class=resource_class,
            handlers=handlers,
            batch_size=batch_size,
            token_bucket=token_bucket,
        )
        if batch_processed:
            processed += batch_processed
            idle_count = 0
            if max_jobs is not None and processed >= max_jobs:
                return processed
            continue

        idle_count += 1
        if stop_after_idle is not None and idle_count >= stop_after_idle:
            return processed
        time.sleep(sleep_seconds)
