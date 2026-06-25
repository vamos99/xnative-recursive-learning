from __future__ import annotations

import json
from pathlib import Path

from .dom_parser import parse_extension_payload
from .x_post_schema import CapturedPost


def load_fixture(path: str | Path) -> list[CapturedPost]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("posts", [data])
    return [parse_extension_payload(item) for item in data]
