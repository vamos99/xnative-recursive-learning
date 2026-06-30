from __future__ import annotations

import json
from pathlib import Path

from xnative.db.repositories import CapturePersistResult, UnitOfWork
from xnative.domain import CaptureSource

from .dom_parser import parse_extension_payload
from .x_post_schema import CapturedPost


def load_fixture(path: str | Path) -> list[CapturedPost]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("posts", [data])
    return [parse_extension_payload(item) for item in data]


def archive_fixture(
    path: str | Path,
    db_path: str | Path | None = None,
) -> list[CapturePersistResult]:
    from xnative.api.routes.capture import domain_post_from_payload

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("posts", [data])
    with UnitOfWork(db_path) as uow:
        return [
            uow.captures.persist_capture(
                domain_post_from_payload(item, capture_source=CaptureSource.MANUAL_JSON),
                raw_payload=item,
                correlation_id="manual-archive",
            )
            for item in data
        ]
