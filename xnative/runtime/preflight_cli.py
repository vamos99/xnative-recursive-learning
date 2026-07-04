from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from xnative.runtime.hardware import (
    HardwareProfile,
    HeavyModelRequest,
    assess_hardware_preflight,
    collect_local_hardware_profile,
    decide_heavy_model_admission,
)

MIB = 1024**2


def _mib(value: int | None) -> int | None:
    return None if value is None else value * MIB


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run XNative local hardware preflight without loading heavy models."
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--output", type=Path, help="Optional report output path.")
    parser.add_argument("--system-ram-mib", type=int, help="Override detected system RAM.")
    parser.add_argument("--current-rss-mib", type=int, help="Override detected process RSS.")
    parser.add_argument("--gpu-name", help="Override detected GPU name.")
    parser.add_argument("--gpu-vram-mib", type=int, help="Override detected GPU VRAM.")
    parser.add_argument(
        "--cuda-available",
        action="store_true",
        help="Treat CUDA as available for this preflight run.",
    )
    parser.add_argument("--request-name", help="Optional heavy model request to evaluate.")
    parser.add_argument("--estimated-ram-mib", type=int, default=0)
    parser.add_argument("--estimated-vram-mib", type=int, default=0)
    parser.add_argument("--requires-gpu", action="store_true")
    parser.add_argument("--no-cpu-fallback", action="store_true")
    return parser


def _profile_from_args(args: argparse.Namespace) -> HardwareProfile:
    detected = collect_local_hardware_profile()
    return replace(
        detected,
        system_ram_bytes=_mib(args.system_ram_mib) or detected.system_ram_bytes,
        current_rss_bytes=_mib(args.current_rss_mib) or detected.current_rss_bytes,
        gpu_name=args.gpu_name or detected.gpu_name,
        gpu_vram_bytes=_mib(args.gpu_vram_mib) or detected.gpu_vram_bytes,
        cuda_available=bool(args.cuda_available or detected.cuda_available),
    )


def _request_from_args(args: argparse.Namespace) -> HeavyModelRequest | None:
    if not args.request_name:
        return None
    return HeavyModelRequest(
        name=args.request_name,
        estimated_ram_bytes=_mib(args.estimated_ram_mib) or 0,
        estimated_vram_bytes=_mib(args.estimated_vram_mib) or 0,
        allow_cpu_fallback=not args.no_cpu_fallback,
        requires_gpu=args.requires_gpu,
    )


def _render_text(payload: dict[str, Any]) -> str:
    report = payload["preflight"]
    profile = report["profile"]
    lines = [
        "XNative hardware preflight",
        f"heavy_jobs_allowed={report['heavy_jobs_allowed']}",
        f"heavy_jobs_reason={report['heavy_jobs_reason']}",
        f"cpu_fallback_required={report['cpu_fallback_required']}",
        f"max_concurrent_heavy_models={report['max_concurrent_heavy_models']}",
        f"system_ram_bytes={profile['system_ram_bytes']}",
        f"current_rss_bytes={profile['current_rss_bytes']}",
        f"gpu_name={profile['gpu_name']}",
        f"gpu_vram_bytes={profile['gpu_vram_bytes']}",
        f"cuda_available={profile['cuda_available']}",
        f"warnings={','.join(report['warnings']) or 'none'}",
    ]
    admission = payload.get("admission")
    if admission:
        lines.extend(
            [
                f"admission_accepted={admission['accepted']}",
                f"admission_device={admission['execution_device']}",
                f"admission_reason={admission['reason']}",
                f"admission_should_unload={admission['should_unload_models']}",
            ]
        )
    return "\n".join(lines) + "\n"


def _write_output(output: Path | None, content: str) -> None:
    if output is None:
        print(content, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    profile = _profile_from_args(args)
    report = assess_hardware_preflight(profile)
    request = _request_from_args(args)
    admission = (
        decide_heavy_model_admission(request, profile=profile).as_dict() if request else None
    )
    payload: dict[str, Any] = {
        "preflight": report.as_dict(),
        "admission": admission,
    }
    content = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else _render_text(payload)
    )
    _write_output(args.output, content)
    if not report.heavy_jobs_allowed:
        return 2
    if admission is not None and not bool(admission["accepted"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
