from __future__ import annotations

import hashlib


def stable_id(*parts: object, length: int = 16) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]
