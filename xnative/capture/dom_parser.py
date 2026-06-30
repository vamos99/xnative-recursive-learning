from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from xnative.core.ids import stable_id

from .x_post_schema import CapturedMedia, CapturedPost

SENSITIVE_KEY_PARTS = (
    "authorization",
    "bearer",
    "cookie",
    "csrf",
    "password",
    "secret",
    "token",
)

UI_MEDIA_MARKERS = (
    "profile_images",
    "default_profile_images",
    "emoji",
    "avatar",
    "badge",
    "icon",
)


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _redact_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value.strip())
    if not parts.scheme or not parts.netloc:
        return value.strip()
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _sanitize_raw(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): "[redacted]" if _is_sensitive_key(key) else _sanitize_raw(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_raw(item) for item in value]
    return value


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize_raw(payload)
    if not isinstance(sanitized, dict):
        return {}
    return sanitized


def _media_scope(item: dict[str, Any]) -> str:
    return _safe_text(
        item.get("media_scope")
        or item.get("scope")
        or item.get("context")
        or item.get("role")
        or "post"
    ).lower()


def _is_post_media(item: dict[str, Any], url: str, alt_text: str) -> bool:
    scope = _media_scope(item)
    if scope in {"avatar", "profile", "ui", "badge", "icon"}:
        return False
    haystack = f"{url} {alt_text} {scope}".lower()
    return not any(marker in haystack for marker in UI_MEDIA_MARKERS)


def parse_extension_payload(payload: dict[str, Any]) -> CapturedPost:
    """Parse a local browser-extension capture payload.

    This parser deliberately does not use X API credentials. It accepts only
    data already visible to the user in the browser DOM/content script.
    """
    text = _safe_text(payload.get("text") or payload.get("content"))
    url = _redact_url(_safe_text(payload.get("url") or payload.get("post_url")))
    author = _safe_text(payload.get("author_handle") or payload.get("handle") or "unknown").lstrip(
        "@"
    )
    platform_id = str(
        payload.get("platform_post_id") or payload.get("id") or stable_id(url, author, text)
    )
    media_items = []
    for m in payload.get("media", []) or []:
        if isinstance(m, dict):
            source_url = _redact_url(_safe_text(m.get("source_url") or m.get("url")))
            alt_text = _safe_text(m.get("alt_text") or m.get("alt"))
            if not source_url or not _is_post_media(m, source_url, alt_text):
                continue
            media_items.append(
                CapturedMedia(
                    media_type=_safe_text(m.get("media_type") or m.get("type") or "unknown"),
                    source_url=source_url,
                    alt_text=alt_text,
                    local_path=_safe_text(m.get("local_path")),
                    media_scope=_media_scope(m),
                )
            )
    parse_quality = dict(payload.get("parse_quality") or {})
    parse_quality.update(
        {
            "has_url": bool(url),
            "has_author": bool(author and author != "unknown"),
            "has_text": bool(text),
            "has_quote": bool(payload.get("quoted_text")),
            "media_count": len(media_items),
            "selector_version": _safe_text(
                payload.get("raw_capture_version") or parse_quality.get("selector_version")
            ),
        }
    )
    return CapturedPost(
        platform_post_id=platform_id,
        url=url,
        author_handle=author,
        display_name=str(payload.get("display_name") or payload.get("name") or ""),
        text=text,
        timestamp=str(payload.get("timestamp") or payload.get("post_time") or ""),
        quoted_text=str(payload.get("quoted_text") or ""),
        quoted_author=str(payload.get("quoted_author") or ""),
        quoted_url=_redact_url(_safe_text(payload.get("quoted_url"))),
        visible_metrics=dict(payload.get("visible_metrics") or payload.get("metrics") or {}),
        media=media_items,
        parse_quality=parse_quality,
        raw=_sanitize_payload(payload),
    )
