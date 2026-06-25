from __future__ import annotations

import logging

from .config import settings


def configure_logging() -> None:
    settings.ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(settings.logs_dir / "xnative.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
