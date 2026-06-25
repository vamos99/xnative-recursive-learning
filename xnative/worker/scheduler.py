from __future__ import annotations

import time
from collections.abc import Callable

from xnative.core.config import settings
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
) -> bool:
    active_handlers = handlers or DEFAULT_HANDLERS
    with UnitOfWork(db_path) as uow:
        uow.jobs.recover_expired_leases()
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
            uow.jobs.fail_job(
                job.id,
                exc.__class__.__name__,
                str(exc),
                retryable=True,
            )
        else:
            uow.connection.execute("RELEASE job_handler")
            uow.jobs.complete_job(job.id)
        return True


def run_worker_loop(
    db_path: str | None = None,
    *,
    owner: str = "worker-light",
    resource_class: ResourceClass = ResourceClass.LIGHT,
    handlers: dict[str, JobHandler] | None = None,
    max_jobs: int | None = None,
    stop_after_idle: int | None = None,
    idle_sleep_seconds: float | None = None,
) -> int:
    processed = 0
    idle_count = 0
    sleep_seconds = (
        settings.worker_idle_sleep_seconds
        if idle_sleep_seconds is None
        else max(0.0, idle_sleep_seconds)
    )
    while True:
        did_work = run_due_job_once(
            db_path,
            owner=owner,
            resource_class=resource_class,
            handlers=handlers,
        )
        if did_work:
            processed += 1
            idle_count = 0
            if max_jobs is not None and processed >= max_jobs:
                return processed
            continue

        idle_count += 1
        if stop_after_idle is not None and idle_count >= stop_after_idle:
            return processed
        time.sleep(sleep_seconds)
