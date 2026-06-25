from __future__ import annotations

from enum import StrEnum


class Platform(StrEnum):
    X = "x"


class CaptureSource(StrEnum):
    EXTENSION = "extension"
    MANUAL_JSON = "manual_json"
    MANUAL_CSV = "manual_csv"
    FIXTURE = "fixture"


class MediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    AUDIO = "audio"
    UNKNOWN = "unknown"


class StoragePolicy(StrEnum):
    METADATA = "metadata"
    THUMBNAIL = "thumbnail"
    ORIGINAL = "original"


class MediaAvailability(StrEnum):
    REMOTE = "remote"
    STORED = "stored"
    MISSING = "missing"
    DELETED = "deleted"
    BLOCKED = "blocked"
    ERROR = "error"


class EventStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    COOLING = "cooling"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    IGNORED = "ignored"
    EXPIRED = "expired"


class FeedbackAction(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    IGNORE = "ignore"
    MANUAL_POST = "manual_post"
    UNDO = "undo"


class DataClass(StrEnum):
    METADATA = "metadata"
    VISIBLE_CONTENT = "visible_content"
    LOCAL_MEDIA = "local_media"
    DERIVED_FEATURE = "derived_feature"
    USER_FEEDBACK = "user_feedback"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    RETRY = "retry"
    COMPLETED = "completed"
    DEAD = "dead"
    CANCELLED = "cancelled"


class ResourceClass(StrEnum):
    LIGHT = "light"
    HEAVY = "heavy"
    IO = "io"
