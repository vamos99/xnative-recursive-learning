from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CapturedMedia:
    media_type: str = "unknown"
    source_url: str = ""
    alt_text: str = ""
    local_path: str = ""
    media_scope: str = "post"


@dataclass
class CapturedPost:
    platform_post_id: str
    url: str
    author_handle: str
    display_name: str = ""
    text: str = ""
    timestamp: str = ""
    quoted_text: str = ""
    quoted_author: str = ""
    quoted_url: str = ""
    visible_metrics: dict[str, Any] = field(default_factory=dict)
    media: list[CapturedMedia] = field(default_factory=list)
    parse_quality: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
