from __future__ import annotations

import hashlib

from xnative.capture.x_post_schema import CapturedPost


def post_dedup_hash(post: CapturedPost) -> str:
    raw = "|".join(
        [post.url or "", post.author_handle or "", post.text or "", post.quoted_text or ""]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
