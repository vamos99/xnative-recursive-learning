from __future__ import annotations

from fastapi import FastAPI

from xnative.api.routes.capture import router as capture_router
from xnative.api.routes.health import router as health_router
from xnative.db.seed import seed


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="XNative Recursive Learning", version="1.0.0")
    app.state.db_path = db_path
    seed(db_path)
    app.include_router(health_router)
    app.include_router(capture_router)
    return app


app = create_app()
