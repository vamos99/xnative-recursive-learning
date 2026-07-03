from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field

from xnative.core.config import settings


@dataclass(frozen=True)
class HardwareProfile:
    system_ram_bytes: int | None = None
    cpu_label: str = "unknown"
    gpu_name: str | None = None
    gpu_vram_bytes: int | None = None
    cuda_available: bool = False
    current_rss_bytes: int | None = None


@dataclass(frozen=True)
class HardwarePreflightReport:
    profile: HardwareProfile
    target_system_ram_bytes: int
    rss_soft_limit_bytes: int
    min_os_headroom_bytes: int
    min_gpu_vram_bytes: int
    max_concurrent_heavy_models: int
    cpu_fallback_required: bool
    heavy_jobs_allowed: bool
    heavy_jobs_reason: str
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": {
                "system_ram_bytes": self.profile.system_ram_bytes,
                "cpu_label": self.profile.cpu_label,
                "gpu_name": self.profile.gpu_name,
                "gpu_vram_bytes": self.profile.gpu_vram_bytes,
                "cuda_available": self.profile.cuda_available,
                "current_rss_bytes": self.profile.current_rss_bytes,
            },
            "target_system_ram_bytes": self.target_system_ram_bytes,
            "rss_soft_limit_bytes": self.rss_soft_limit_bytes,
            "min_os_headroom_bytes": self.min_os_headroom_bytes,
            "min_gpu_vram_bytes": self.min_gpu_vram_bytes,
            "max_concurrent_heavy_models": self.max_concurrent_heavy_models,
            "cpu_fallback_required": self.cpu_fallback_required,
            "heavy_jobs_allowed": self.heavy_jobs_allowed,
            "heavy_jobs_reason": self.heavy_jobs_reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class HeavyModelRequest:
    name: str
    estimated_ram_bytes: int = 0
    estimated_vram_bytes: int = 0
    allow_cpu_fallback: bool = True
    requires_gpu: bool = False


@dataclass(frozen=True)
class HeavyModelAdmission:
    accepted: bool
    execution_device: str
    reason: str
    max_concurrent_heavy_models: int
    should_unload_models: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "execution_device": self.execution_device,
            "reason": self.reason,
            "max_concurrent_heavy_models": self.max_concurrent_heavy_models,
            "should_unload_models": self.should_unload_models,
            "warnings": list(self.warnings),
        }


def _system_ram_bytes() -> int | None:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if isinstance(pages, int) and isinstance(page_size, int):
            return pages * page_size
    except (AttributeError, OSError, ValueError):
        return None
    return None


def _current_rss_bytes() -> int | None:
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except (ImportError, OSError, ValueError):
        return None
    if platform.system().lower() == "darwin":
        return int(rss)
    return int(rss) * 1024


def collect_local_hardware_profile() -> HardwareProfile:
    """Best-effort local profile without importing heavy GPU libraries."""

    gpu_name = os.getenv("XNATIVE_GPU_NAME") or None
    gpu_vram = os.getenv("XNATIVE_GPU_VRAM_BYTES")
    cuda = os.getenv("XNATIVE_CUDA_AVAILABLE", "0") == "1"
    return HardwareProfile(
        system_ram_bytes=_system_ram_bytes(),
        cpu_label=platform.processor() or platform.machine() or "unknown",
        gpu_name=gpu_name,
        gpu_vram_bytes=int(gpu_vram) if gpu_vram else None,
        cuda_available=cuda,
        current_rss_bytes=_current_rss_bytes(),
    )


def assess_hardware_preflight(
    profile: HardwareProfile | None = None,
) -> HardwarePreflightReport:
    active_profile = profile or collect_local_hardware_profile()
    warnings: list[str] = []
    system_ram = active_profile.system_ram_bytes
    if system_ram is None:
        warnings.append("system_ram_unknown")
    elif system_ram < settings.target_system_ram_bytes:
        warnings.append("system_ram_below_target")

    current_rss = active_profile.current_rss_bytes or 0
    if current_rss >= settings.rss_soft_limit_bytes:
        return HardwarePreflightReport(
            profile=active_profile,
            target_system_ram_bytes=settings.target_system_ram_bytes,
            rss_soft_limit_bytes=settings.rss_soft_limit_bytes,
            min_os_headroom_bytes=settings.min_os_headroom_bytes,
            min_gpu_vram_bytes=settings.min_gpu_vram_bytes,
            max_concurrent_heavy_models=settings.max_concurrent_heavy_models,
            cpu_fallback_required=True,
            heavy_jobs_allowed=False,
            heavy_jobs_reason="rss_soft_limit_exceeded",
            warnings=tuple(warnings + ["unload_models_before_heavy_work"]),
        )

    gpu_ready = (
        active_profile.cuda_available
        and active_profile.gpu_vram_bytes is not None
        and active_profile.gpu_vram_bytes >= settings.min_gpu_vram_bytes
    )
    if not gpu_ready:
        warnings.append("gpu_unavailable_or_below_vram_floor")

    return HardwarePreflightReport(
        profile=active_profile,
        target_system_ram_bytes=settings.target_system_ram_bytes,
        rss_soft_limit_bytes=settings.rss_soft_limit_bytes,
        min_os_headroom_bytes=settings.min_os_headroom_bytes,
        min_gpu_vram_bytes=settings.min_gpu_vram_bytes,
        max_concurrent_heavy_models=settings.max_concurrent_heavy_models,
        cpu_fallback_required=not gpu_ready,
        heavy_jobs_allowed=True,
        heavy_jobs_reason="accepted_with_cpu_fallback" if not gpu_ready else "accepted_gpu_ready",
        warnings=tuple(warnings),
    )


def decide_heavy_model_admission(
    request: HeavyModelRequest,
    *,
    profile: HardwareProfile | None = None,
) -> HeavyModelAdmission:
    report = assess_hardware_preflight(profile)
    warnings = list(report.warnings)
    if not report.heavy_jobs_allowed:
        return HeavyModelAdmission(
            accepted=False,
            execution_device="none",
            reason=report.heavy_jobs_reason,
            max_concurrent_heavy_models=report.max_concurrent_heavy_models,
            should_unload_models=True,
            warnings=tuple(warnings),
        )

    current_rss = report.profile.current_rss_bytes or 0
    if current_rss + max(0, request.estimated_ram_bytes) > report.rss_soft_limit_bytes:
        return HeavyModelAdmission(
            accepted=False,
            execution_device="none",
            reason="estimated_ram_exceeds_soft_limit",
            max_concurrent_heavy_models=report.max_concurrent_heavy_models,
            should_unload_models=True,
            warnings=tuple(warnings + ["defer_or_use_cheaper_model"]),
        )

    gpu_ready = (
        report.profile.cuda_available
        and report.profile.gpu_vram_bytes is not None
        and report.profile.gpu_vram_bytes
        >= max(settings.min_gpu_vram_bytes, request.estimated_vram_bytes)
    )
    if gpu_ready:
        return HeavyModelAdmission(
            accepted=True,
            execution_device="gpu",
            reason="accepted_gpu",
            max_concurrent_heavy_models=report.max_concurrent_heavy_models,
            warnings=tuple(warnings),
        )

    if request.requires_gpu or not request.allow_cpu_fallback:
        return HeavyModelAdmission(
            accepted=False,
            execution_device="none",
            reason="gpu_required_but_unavailable",
            max_concurrent_heavy_models=report.max_concurrent_heavy_models,
            warnings=tuple(warnings + ["cpu_fallback_disabled"]),
        )

    return HeavyModelAdmission(
        accepted=True,
        execution_device="cpu",
        reason="accepted_cpu_fallback",
        max_concurrent_heavy_models=report.max_concurrent_heavy_models,
        warnings=tuple(warnings),
    )
