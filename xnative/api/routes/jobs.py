from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from xnative.db.repositories import UnitOfWork

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class JobsView(BaseModel):
    queue_summary: list[dict[str, Any]]
    dead_letters: list[dict[str, Any]]


class JobReplayAccepted(BaseModel):
    job_id: str
    source_job_id: str
    duplicate: bool
    status: str = "accepted"


def _db_path(request: Request) -> str | None:
    value = getattr(request.app.state, "db_path", None)
    return str(value) if value is not None else None


@router.get("", response_model=JobsView)
def get_jobs(request: Request, limit: int = 50) -> JobsView:
    with UnitOfWork(_db_path(request)) as uow:
        return JobsView(
            queue_summary=uow.jobs.queue_summary(),
            dead_letters=uow.jobs.list_dead_letters(limit=limit),
        )


@router.post(
    "/{job_id}/retry", response_model=JobReplayAccepted, status_code=status.HTTP_202_ACCEPTED
)
def retry_job(job_id: str, request: Request) -> JobReplayAccepted:
    try:
        with UnitOfWork(_db_path(request)) as uow:
            result = uow.jobs.replay_dead_letter(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JobReplayAccepted(
        job_id=result.job_id,
        source_job_id=result.source_job_id,
        duplicate=result.duplicate,
    )
