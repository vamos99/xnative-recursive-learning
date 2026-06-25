from __future__ import annotations

from typing import Any

from xnative.core.ids import stable_id

from .x_post_schema import CapturedMedia, CapturedPost


def parse_extension_payload(payload: dict[str, Any]) -> CapturedPost:
    """Parse a local browser-extension capture payload.

    This parser deliberately does not use X API credentials. It accepts only
    data already visible to the user in the browser DOM/content script.
    """
    text = str(payload.get("text") or payload.get("content") or "").strip()
    url = str(payload.get("url") or payload.get("post_url") or "").strip()
    author = (
        str(payload.get("author_handle") or payload.get("handle") or "unknown").lstrip("@").strip()
    )
    platform_id = str(
        payload.get("platform_post_id") or payload.get("id") or stable_id(url, author, text)
    )
    media_items = []
    for m in payload.get("media", []) or []:
        if isinstance(m, dict):
            media_items.append(
                CapturedMedia(
                    media_type=str(m.get("media_type") or m.get("type") or "unknown"),
                    source_url=str(m.get("source_url") or m.get("url") or ""),
                    alt_text=str(m.get("alt_text") or m.get("alt") or ""),
                    local_path=str(m.get("local_path") or ""),
                )
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
        quoted_url=str(payload.get("quoted_url") or ""),
        visible_metrics=dict(payload.get("visible_metrics") or payload.get("metrics") or {}),
        media=media_items,
        raw=payload,
    )
