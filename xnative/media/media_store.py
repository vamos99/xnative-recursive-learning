from __future__ import annotations

import shutil
from pathlib import Path

from xnative.core.config import settings

from .phash import phash_file


def store_local_media(path: str | Path) -> dict[str, str]:
    settings.ensure_dirs()
    p = Path(path)
    target = settings.media_dir / p.name
    if p.exists() and p.resolve() != target.resolve():
        shutil.copy2(p, target)
    h = phash_file(target) if target.exists() else ""
    return {"local_path": str(target), "phash": h}
