from __future__ import annotations

import re

URL_RE = re.compile(r"https?://\S+")
WS_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = text or ""
    text = URL_RE.sub("<url>", text)
    text = text.replace("\u200b", "")
    text = re.sub(r"([!?\.])\1{2,}", r"\1\1", text)
    return WS_RE.sub(" ", text).strip()


def combined_context(
    text: str = "",
    quoted_text: str = "",
    alt_texts: list[str] | None = None,
    ocr_texts: list[str] | None = None,
) -> str:
    parts = [text or "", quoted_text or ""] + (alt_texts or []) + (ocr_texts or [])
    return clean_text(" ".join(p for p in parts if p))
