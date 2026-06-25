from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import (
    CaptureSource,
    DataClass,
    EventStatus,
    FeedbackAction,
    MediaAvailability,
    MediaKind,
    Platform,
    ReviewState,
    StoragePolicy,
)


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_us(value: datetime | None = None) -> int:
    dt = value or utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.astimezone(UTC).timestamp() * 1_000_000)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class DomainModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)


class QuotePost(DomainModel):
    platform_post_id: str | None = None
    canonical_url: str | None = None
    author_handle: str | None = None
    visible_text: str = Field(default="", max_length=20_000)

    @field_validator("author_handle")
    @classmethod
    def normalize_author(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lstrip("@").lower()
        return cleaned or None


class VisibleMetrics(DomainModel):
    likes: int | None = Field(default=None, ge=0)
    reposts: int | None = Field(default=None, ge=0)
    replies: int | None = Field(default=None, ge=0)
    views: int | None = Field(default=None, ge=0)


class MediaAsset(DomainModel):
    id: str = Field(default_factory=new_uuid)
    post_id: str | None = None
    kind: MediaKind = MediaKind.UNKNOWN
    source_url: str | None = None
    alt_text: str | None = Field(default=None, max_length=10_000)
    mime_type: str | None = None
    byte_size: int | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    duration_ms: int | None = Field(default=None, ge=0)
    exact_sha256: str | None = None
    perceptual_hash: str | None = None
    storage_policy: StoragePolicy = StoragePolicy.METADATA
    local_path: str | None = None
    availability: MediaAvailability = MediaAvailability.REMOTE

    @field_validator("source_url")
    @classmethod
    def clean_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CapturedPost(DomainModel):
    id: str = Field(default_factory=new_uuid)
    schema_version: int = 1
    platform: Platform = Platform.X
    platform_post_id: str | None = None
    canonical_url: str
    author_handle: str
    visible_text: str = Field(default="", max_length=20_000)
    quote_post: QuotePost | None = None
    media: list[MediaAsset] = Field(default_factory=list, max_length=4)
    visible_metrics: VisibleMetrics = Field(default_factory=VisibleMetrics)
    platform_created_at: datetime | None = None
    captured_at: datetime = Field(default_factory=utc_now)
    capture_source: CaptureSource = CaptureSource.MANUAL_JSON
    selector_version: str | None = None
    idempotency_key: str | None = None
    raw_payload_hash: str | None = None
    data_class: DataClass = DataClass.VISIBLE_CONTENT

    @field_validator("author_handle")
    @classmethod
    def normalize_author(cls, value: str) -> str:
        cleaned = value.strip().lstrip("@").lower()
        if not cleaned:
            raise ValueError("author_handle is required")
        return cleaned

    @field_validator("canonical_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.startswith(("https://x.com/", "https://twitter.com/")):
            raise ValueError("canonical_url must be an x.com or twitter.com URL")
        return cleaned

    @field_validator("captured_at", "platform_created_at")
    @classmethod
    def ensure_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_capture(self) -> CapturedPost:
        has_quote = bool(self.quote_post and self.quote_post.visible_text.strip())
        has_media = bool(self.media)
        if not self.visible_text.strip() and not has_quote and not has_media:
            raise ValueError("capture requires visible text, quote text or media")
        if self.capture_source == CaptureSource.EXTENSION and not self.selector_version:
            raise ValueError("selector_version is required for extension captures")
        payload = {
            "platform": self.platform,
            "platform_post_id": self.platform_post_id,
            "canonical_url": self.canonical_url,
            "author_handle": self.author_handle,
            "visible_text": self.visible_text,
            "quote_post": self.quote_post.model_dump(mode="json") if self.quote_post else None,
            "media": [m.model_dump(mode="json", exclude={"post_id"}) for m in self.media],
            "visible_metrics": self.visible_metrics.model_dump(mode="json"),
        }
        if self.idempotency_key is None:
            self.idempotency_key = sha256_text(canonical_json(payload))
        if self.raw_payload_hash is None:
            self.raw_payload_hash = self.idempotency_key
        for asset in self.media:
            asset.post_id = self.id
        return self


class Event(DomainModel):
    id: str = Field(default_factory=new_uuid)
    event_type: str = "other"
    title: str
    status: EventStatus = EventStatus.CANDIDATE
    started_at: datetime | None = None
    last_seen_at: datetime = Field(default_factory=utc_now)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    post_count: int = Field(default=0, ge=0)
    source_count: int = Field(default=0, ge=0)
    entity_ids: list[str] = Field(default_factory=list)
    cluster_version: str = "rule-v1"
    merged_into_event_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Candidate(DomainModel):
    id: str = Field(default_factory=new_uuid)
    post_id: str | None = None
    event_id: str | None = None
    feature_version: str
    model_version: str
    config_hash: str
    utility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    selector_reason: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class Suggestion(DomainModel):
    id: str = Field(default_factory=new_uuid)
    candidate_id: str
    variant_family: str
    draft_text: str
    evidence_ids: list[str] = Field(default_factory=list)
    policy_result: str = "pending"
    review_state: ReviewState = ReviewState.PENDING
    model_version: str
    feature_version: str
    config_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class FeedbackEvent(DomainModel):
    id: str = Field(default_factory=new_uuid)
    suggestion_id: str
    action: FeedbackAction
    reason_codes: list[str] = Field(default_factory=list)
    original_text: str | None = None
    edited_text: str | None = None
    edit_distance: int | None = Field(default=None, ge=0)
    actor: str = "local_user"
    occurred_at: datetime = Field(default_factory=utc_now)
    model_version: str
    feature_version: str


class PerformanceSnapshot(DomainModel):
    id: str = Field(default_factory=new_uuid)
    post_id: str
    observed_at: datetime = Field(default_factory=utc_now)
    metrics: dict[str, int | float | None] = Field(default_factory=dict)
    ingestion_method: str = "manual"
    created_at: datetime = Field(default_factory=utc_now)


class FeatureRecord(DomainModel):
    id: str = Field(default_factory=new_uuid)
    owner_type: str
    owner_id: str
    feature_name: str
    feature_version: str
    value: dict[str, Any]
    model_version: str = "none"
    config_hash: str
    source_ids: list[str] = Field(default_factory=list)
    data_class: DataClass = DataClass.DERIVED_FEATURE
    created_at: datetime = Field(default_factory=utc_now)
