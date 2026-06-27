from __future__ import annotations

import shutil
from pathlib import Path

from xnative.core.config import settings

from .phash import media_hashes_file


def store_local_media(path: str | Path) -> dict[str, str]:
    settings.ensure_dirs()
    p = Path(path)
    target = settings.media_dir / p.name
    if p.exists() and p.resolve() != target.resolve():
        shutil.copy2(p, target)
    hashes = media_hashes_file(target) if target.exists() else None
    return {
        "local_path": str(target),
        "exact_sha256": hashes.exact_sha256 if hashes else "",
        "perceptual_hash": hashes.perceptual_hash if hashes else "",
        "phash": hashes.perceptual_hash if hashes else "",
    }
