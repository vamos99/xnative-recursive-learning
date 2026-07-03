from xnative.runtime.hardware import (
    HardwareProfile,
    HeavyModelRequest,
    assess_hardware_preflight,
    decide_heavy_model_admission,
)

GIB = 1024**3


def test_preflight_requires_cpu_fallback_when_gpu_is_unknown() -> None:
    report = assess_hardware_preflight(
        HardwareProfile(
            system_ram_bytes=8 * GIB,
            cpu_label="9th gen i5",
            gpu_name="GTX 1050",
            gpu_vram_bytes=None,
            cuda_available=False,
            current_rss_bytes=2 * GIB,
        )
    )

    assert report.heavy_jobs_allowed
    assert report.cpu_fallback_required
    assert report.max_concurrent_heavy_models == 1
    assert "gpu_unavailable_or_below_vram_floor" in report.warnings


def test_preflight_blocks_heavy_work_when_rss_soft_limit_is_exceeded() -> None:
    report = assess_hardware_preflight(
        HardwareProfile(
            system_ram_bytes=8 * GIB,
            current_rss_bytes=6 * GIB,
        )
    )
    decision = decide_heavy_model_admission(
        HeavyModelRequest(name="clip-small", estimated_ram_bytes=512 * 1024**2),
        profile=report.profile,
    )

    assert not report.heavy_jobs_allowed
    assert report.heavy_jobs_reason == "rss_soft_limit_exceeded"
    assert not decision.accepted
    assert decision.should_unload_models
    assert decision.reason == "rss_soft_limit_exceeded"


def test_heavy_model_admission_accepts_gpu_when_vram_and_cuda_fit() -> None:
    decision = decide_heavy_model_admission(
        HeavyModelRequest(
            name="openclip-small",
            estimated_ram_bytes=1 * GIB,
            estimated_vram_bytes=2 * GIB,
        ),
        profile=HardwareProfile(
            system_ram_bytes=8 * GIB,
            gpu_name="GTX 1050",
            gpu_vram_bytes=4 * GIB,
            cuda_available=True,
            current_rss_bytes=2 * GIB,
        ),
    )

    assert decision.accepted
    assert decision.execution_device == "gpu"
    assert decision.reason == "accepted_gpu"
    assert decision.max_concurrent_heavy_models == 1


def test_heavy_model_admission_uses_cpu_fallback_without_gpu() -> None:
    decision = decide_heavy_model_admission(
        HeavyModelRequest(name="ocr-or-embedding", estimated_ram_bytes=1 * GIB),
        profile=HardwareProfile(
            system_ram_bytes=8 * GIB,
            gpu_name="GTX 1050",
            gpu_vram_bytes=1 * GIB,
            cuda_available=False,
            current_rss_bytes=2 * GIB,
        ),
    )

    assert decision.accepted
    assert decision.execution_device == "cpu"
    assert decision.reason == "accepted_cpu_fallback"
    assert "gpu_unavailable_or_below_vram_floor" in decision.warnings


def test_heavy_model_admission_rejects_when_cpu_fallback_is_disabled() -> None:
    decision = decide_heavy_model_admission(
        HeavyModelRequest(
            name="gpu-only-vlm",
            estimated_ram_bytes=1 * GIB,
            estimated_vram_bytes=2 * GIB,
            allow_cpu_fallback=False,
            requires_gpu=True,
        ),
        profile=HardwareProfile(
            system_ram_bytes=8 * GIB,
            gpu_name="GTX 1050",
            gpu_vram_bytes=1 * GIB,
            cuda_available=True,
            current_rss_bytes=2 * GIB,
        ),
    )

    assert not decision.accepted
    assert decision.execution_device == "none"
    assert decision.reason == "gpu_required_but_unavailable"


def test_heavy_model_admission_rejects_estimated_ram_over_soft_limit() -> None:
    decision = decide_heavy_model_admission(
        HeavyModelRequest(name="too-large-local-vlm", estimated_ram_bytes=4 * GIB),
        profile=HardwareProfile(
            system_ram_bytes=8 * GIB,
            current_rss_bytes=2 * GIB,
        ),
    )

    assert not decision.accepted
    assert decision.reason == "estimated_ram_exceeds_soft_limit"
    assert decision.should_unload_models
