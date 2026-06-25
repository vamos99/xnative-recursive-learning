from __future__ import annotations

from xnative.capture.x_post_schema import CapturedPost
from xnative.nlp.text_cleaner import combined_context


def normalize_post_text(post: CapturedPost) -> str:
    alt = [m.alt_text for m in post.media if m.alt_text]
    return combined_context(post.text, post.quoted_text, alt)
