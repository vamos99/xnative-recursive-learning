from xnative.media.frame_sampler import (
    VideoAudioLifecyclePolicy,
    plan_video_audio_lifecycle,
    planned_video_frame_offsets,
    sample_video_frames,
)


def test_video_lifecycle_plans_bounded_frame_offsets_and_audio() -> None:
    policy = VideoAudioLifecyclePolicy(
        max_video_duration_ms=30_000,
        max_audio_duration_ms=20_000,
        max_frames=3,
        min_frame_gap_ms=1_000,
        audio_sample_rate_hz=16_000,
    )

    plan = plan_video_audio_lifecycle(
        kind="video",
        duration_ms=12_000,
        has_audio=True,
        policy=policy,
    )

    assert plan.accepted
    assert plan.reason == "accepted_video"
    assert plan.frame_offsets_ms == (3000, 6000, 9000)
    assert plan.audio_action == "extract_limited_audio"
    assert plan.audio_sample_rate_hz == 16_000
    assert plan.as_dict()["frame_offsets_ms"] == [3000, 6000, 9000]


def test_video_lifecycle_rejects_long_or_missing_duration() -> None:
    policy = VideoAudioLifecyclePolicy(max_video_duration_ms=5_000)

    too_long = plan_video_audio_lifecycle(
        kind="video",
        duration_ms=5_001,
        policy=policy,
    )
    missing = plan_video_audio_lifecycle(
        kind="video",
        duration_ms=None,
        policy=policy,
    )

    assert not too_long.accepted
    assert too_long.reason == "video_duration_limit_exceeded"
    assert too_long.frame_offsets_ms == ()
    assert too_long.audio_action == "skip_duration_limit"
    assert not missing.accepted
    assert missing.reason == "missing_duration"


def test_gif_lifecycle_samples_frames_without_audio() -> None:
    plan = plan_video_audio_lifecycle(
        kind="gif",
        duration_ms=4_000,
        has_audio=True,
        policy=VideoAudioLifecyclePolicy(max_frames=2),
    )

    assert plan.accepted
    assert plan.reason == "accepted_gif"
    assert plan.frame_offsets_ms == (1333, 2667)
    assert plan.audio_action == "skip_no_audio"
    assert plan.audio_sample_rate_hz is None


def test_audio_lifecycle_uses_audio_duration_gate() -> None:
    policy = VideoAudioLifecyclePolicy(max_audio_duration_ms=10_000)

    accepted = plan_video_audio_lifecycle(kind="audio", duration_ms=9_000, policy=policy)
    rejected = plan_video_audio_lifecycle(kind="audio", duration_ms=10_001, policy=policy)

    assert accepted.accepted
    assert accepted.audio_action == "extract_limited_audio"
    assert accepted.frame_offsets_ms == ()
    assert not rejected.accepted
    assert rejected.reason == "audio_duration_limit_exceeded"
    assert rejected.audio_action == "skip_duration_limit"


def test_frame_offset_planner_and_sampler_are_deterministic(tmp_path) -> None:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"fake-video-bytes")

    assert planned_video_frame_offsets(
        500,
        policy=VideoAudioLifecyclePolicy(max_frames=3, min_frame_gap_ms=1_000),
    ) == (250,)
    assert sample_video_frames(str(source), max_frames=3, duration_ms=9_000) == [
        "clip.mp4:frame@2250ms",
        "clip.mp4:frame@4500ms",
        "clip.mp4:frame@6750ms",
    ]
    assert sample_video_frames(str(tmp_path / "missing.mp4"), duration_ms=9_000) == []
