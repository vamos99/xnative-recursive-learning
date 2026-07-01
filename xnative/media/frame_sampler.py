from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

MediaLifecycleKind = Literal["video", "gif", "audio", "unknown"]


@dataclass(frozen=True)
class VideoAudioLifecyclePolicy:
    """Cheap lifecycle guard before expensive CV/OCR/ASR stages."""

    max_video_duration_ms: int = 90_000
    max_audio_duration_ms: int = 60_000
    max_frames: int = 3
    min_frame_gap_ms: int = 1_000
    audio_sample_rate_hz: int = 16_000


@dataclass(frozen=True)
class VideoAudioLifecyclePlan:
    kind: MediaLifecycleKind
    accepted: bool
    reason: str
    duration_ms: int | None
    max_duration_ms: int
    frame_offsets_ms: tuple[int, ...]
    audio_action: str
    audio_sample_rate_hz: int | None
    lifecycle_version: str = "video-audio-lifecycle-v1"

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "accepted": self.accepted,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
            "max_duration_ms": self.max_duration_ms,
            "frame_offsets_ms": list(self.frame_offsets_ms),
            "audio_action": self.audio_action,
            "audio_sample_rate_hz": self.audio_sample_rate_hz,
            "lifecycle_version": self.lifecycle_version,
        }


def _bounded_duration(duration_ms: int | None) -> int | None:
    if duration_ms is None:
        return None
    return max(0, int(duration_ms))


def planned_video_frame_offsets(
    duration_ms: int | None,
    *,
    policy: VideoAudioLifecyclePolicy | None = None,
) -> tuple[int, ...]:
    """Return stable frame offsets without decoding the video.

    Offsets are placed inside the duration, not at exact boundaries. This keeps
    Phase 4 cheap and deterministic; Phase 5 can consume these offsets with an
    ffmpeg/OpenCV adapter when that dependency is deliberately enabled.
    """

    active_policy = policy or VideoAudioLifecyclePolicy()
    duration = _bounded_duration(duration_ms)
    if duration is None or duration <= 0:
        return ()
    if duration > active_policy.max_video_duration_ms:
        return ()

    usable_frames = max(0, active_policy.max_frames)
    if usable_frames == 0:
        return ()

    if duration < active_policy.min_frame_gap_ms:
        return (duration // 2,)

    max_by_gap = max(1, duration // active_policy.min_frame_gap_ms)
    frame_count = min(usable_frames, max_by_gap)
    step = duration / (frame_count + 1)
    offsets = tuple(int(round(step * index)) for index in range(1, frame_count + 1))
    return tuple(sorted(set(offsets)))


def plan_video_audio_lifecycle(
    *,
    kind: MediaLifecycleKind,
    duration_ms: int | None,
    has_audio: bool = True,
    policy: VideoAudioLifecyclePolicy | None = None,
) -> VideoAudioLifecyclePlan:
    active_policy = policy or VideoAudioLifecyclePolicy()
    duration = _bounded_duration(duration_ms)

    if kind == "audio":
        if duration is None:
            return VideoAudioLifecyclePlan(
                kind=kind,
                accepted=False,
                reason="missing_duration",
                duration_ms=None,
                max_duration_ms=active_policy.max_audio_duration_ms,
                frame_offsets_ms=(),
                audio_action="skip_missing_duration",
                audio_sample_rate_hz=None,
            )
        if duration > active_policy.max_audio_duration_ms:
            return VideoAudioLifecyclePlan(
                kind=kind,
                accepted=False,
                reason="audio_duration_limit_exceeded",
                duration_ms=duration,
                max_duration_ms=active_policy.max_audio_duration_ms,
                frame_offsets_ms=(),
                audio_action="skip_duration_limit",
                audio_sample_rate_hz=None,
            )
        return VideoAudioLifecyclePlan(
            kind=kind,
            accepted=True,
            reason="accepted_audio",
            duration_ms=duration,
            max_duration_ms=active_policy.max_audio_duration_ms,
            frame_offsets_ms=(),
            audio_action="extract_limited_audio",
            audio_sample_rate_hz=active_policy.audio_sample_rate_hz,
        )

    if kind not in {"video", "gif"}:
        return VideoAudioLifecyclePlan(
            kind="unknown",
            accepted=False,
            reason="unsupported_media_kind",
            duration_ms=duration,
            max_duration_ms=active_policy.max_video_duration_ms,
            frame_offsets_ms=(),
            audio_action="skip_unsupported_kind",
            audio_sample_rate_hz=None,
        )

    if duration is None:
        return VideoAudioLifecyclePlan(
            kind=kind,
            accepted=False,
            reason="missing_duration",
            duration_ms=None,
            max_duration_ms=active_policy.max_video_duration_ms,
            frame_offsets_ms=(),
            audio_action="skip_missing_duration",
            audio_sample_rate_hz=None,
        )
    if duration > active_policy.max_video_duration_ms:
        return VideoAudioLifecyclePlan(
            kind=kind,
            accepted=False,
            reason="video_duration_limit_exceeded",
            duration_ms=duration,
            max_duration_ms=active_policy.max_video_duration_ms,
            frame_offsets_ms=(),
            audio_action="skip_duration_limit",
            audio_sample_rate_hz=None,
        )

    frame_offsets = planned_video_frame_offsets(duration, policy=active_policy)
    audio_allowed = (
        kind == "video" and has_audio and duration <= active_policy.max_audio_duration_ms
    )
    return VideoAudioLifecyclePlan(
        kind=kind,
        accepted=True,
        reason="accepted_video" if kind == "video" else "accepted_gif",
        duration_ms=duration,
        max_duration_ms=active_policy.max_video_duration_ms,
        frame_offsets_ms=frame_offsets,
        audio_action="extract_limited_audio" if audio_allowed else "skip_no_audio",
        audio_sample_rate_hz=active_policy.audio_sample_rate_hz if audio_allowed else None,
    )


def sample_video_frames(
    path: str,
    max_frames: int = 3,
    *,
    duration_ms: int | None = None,
) -> list[str]:
    """Return deterministic frame markers for the bounded sampler lifecycle.

    The function intentionally does not decode video bytes. It gives downstream
    stages stable frame IDs to materialize only when a local decoder is present.
    """

    source = Path(path)
    if not source.exists():
        return []
    policy = VideoAudioLifecyclePolicy(max_frames=max_frames)
    offsets = planned_video_frame_offsets(duration_ms, policy=policy)
    return [f"{source.name}:frame@{offset_ms}ms" for offset_ms in offsets]
