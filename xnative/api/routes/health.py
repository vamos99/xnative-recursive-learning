from __future__ import annotations

from fastapi import APIRouter, Request

from xnative.db.migration_runner import applied_migrations
from xnative.db.seed import seed

router = APIRouter()


def health_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "no_api_mode": True,
        "x_api": "disabled",
        "paid_services_required": False,
    }


@router.get("/health")
def health() -> dict[str, object]:
    return health_payload()


@router.get("/ready")
def ready(request: Request) -> dict[str, object]:
    db_path = getattr(request.app.state, "db_path", None)
    conn = seed(db_path)
    migrations = applied_migrations(conn)
    conn.execute("SELECT 1").fetchone()
    return {
        "status": "ready",
        "database": "ok",
        "migrations": sorted(migrations),
        "queue": "ok",
    }
