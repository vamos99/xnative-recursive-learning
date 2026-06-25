from __future__ import annotations

import hashlib
from pathlib import Path


def phash_file(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def hamming_distance_hex(a: str, b: str) -> int:
    ia, ib = int(a or "0", 16), int(b or "0", 16)
    return (ia ^ ib).bit_count()
