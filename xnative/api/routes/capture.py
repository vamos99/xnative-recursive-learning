from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ValidationError

from xnative.capture.dom_parser import parse_extension_payload
from xnative.core.config import settings
from xnative.db.repositories import UnitOfWork
from xnative.domain import (
    CapturedPost,
    CaptureSource,
    MediaAsset,
    MediaKind,
    QuotePost,
    VisibleMetrics,
)

router = APIRouter()


class CaptureAccepted(BaseModel):
    capture_id: str
    job_id: str | None
    status: str = "accepted"
    duplicate: bool = False


def _payload_size(payload: dict[str, Any]) -> int:
    import json

    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _safe_validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    safe = []
    for error in exc.errors():
        item = dict(error)
        ctx = item.get("ctx")
        if isinstance(ctx, dict):
            item["ctx"] = {key: str(value) for key, value in ctx.items()}
        safe.append(item)
    return safe


def capture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return parse_extension_payload(payload).to_dict()


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _metric_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return max(value, 0)
    text = str(value).replace(".", "").replace(",", "").strip()
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def _metrics(raw: dict[str, Any]) -> dict[str, int | None]:
    normalized: dict[str, int | None] = {
        "likes": None,
        "reposts": None,
        "replies": None,
        "views": None,
    }
    for key, value in raw.items():
        label = str(key).lower()
        if "like" in label or "beğeni" in label:
            normalized["likes"] = _metric_int(value)
        elif "repost" in label or "retweet" in label:
            normalized["reposts"] = _metric_int(value)
        elif "reply" in label or "yanıt" in label:
            normalized["replies"] = _metric_int(value)
        elif "view" in label or "görüntülenme" in label:
            normalized["views"] = _metric_int(value)
    return normalized


def domain_post_from_payload(
    payload: dict[str, Any],
    *,
    capture_source: CaptureSource = CaptureSource.EXTENSION,
) -> CapturedPost:
    parsed = parse_extension_payload(payload)
    quote = None
    if parsed.quoted_text:
        quote = QuotePost(
            canonical_url=parsed.quoted_url or None,
            author_handle=parsed.quoted_author or None,
            visible_text=parsed.quoted_text,
        )
    media = [
        MediaAsset(
            kind=MediaKind(
                item.media_type if item.media_type in {k.value for k in MediaKind} else "unknown"
            ),
            source_url=item.source_url or None,
            alt_text=item.alt_text or None,
            local_path=item.local_path or None,
        )
        for item in parsed.media[:4]
    ]
    return CapturedPost(
        platform_post_id=parsed.platform_post_id,
        canonical_url=parsed.url,
        author_handle=parsed.author_handle,
        visible_text=parsed.text,
        quote_post=quote,
        media=media,
        visible_metrics=VisibleMetrics(**_metrics(parsed.visible_metrics)),
        platform_created_at=_parse_datetime(parsed.timestamp),
        capture_source=capture_source,
        selector_version=str(
            parsed.parse_quality.get("selector_version")
            or payload.get("raw_capture_version")
            or "unknown"
        ),
    )


def _db_path(request: Request) -> str | None:
    value = getattr(request.app.state, "db_path", None)
    return str(value) if value is not None else None


def _persist_capture(request: Request, payload: dict[str, Any]) -> CaptureAccepted:
    if _payload_size(payload) > settings.max_capture_bytes:
        raise HTTPException(status_code=413, detail="Capture payload is too large")
    try:
        post = domain_post_from_payload(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_safe_validation_errors(exc)) from exc
    with UnitOfWork(_db_path(request)) as uow:
        result = uow.captures.persist_capture(post, raw_payload=payload)
    return CaptureAccepted(
        capture_id=result.capture_id,
        job_id=result.job_id,
        duplicate=result.duplicate,
    )


@router.post(
    "/api/v1/captures",
    response_model=CaptureAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def capture_v1(payload: dict[str, Any], request: Request) -> CaptureAccepted:
    return _persist_capture(request, payload)


@router.post("/capture", response_model=CaptureAccepted, status_code=status.HTTP_202_ACCEPTED)
def capture_compat(
    payload: dict[str, Any],
    request: Request,
    response: Response,
) -> CaptureAccepted:
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v1/captures>; rel="successor-version"'
    return _persist_capture(request, payload)
