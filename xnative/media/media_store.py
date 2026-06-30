from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import UnidentifiedImageError

from xnative.core.config import settings

from .phash import exact_sha256_file, media_hashes_file

MANIFEST_NAME = ".xnative_media_manifest.json"
DEFAULT_RETENTION_REASON = "metadata-first-local-cache"


@dataclass(frozen=True)
class MediaRetentionPolicy:
    storage_policy: str = "metadata"
    ttl_seconds: int | None = None
    reason: str = DEFAULT_RETENTION_REASON

    def expires_at(self, now: int) -> int | None:
        if self.ttl_seconds is None:
            return None
        return now + max(self.ttl_seconds, 0)


@dataclass(frozen=True)
class MediaStoreResult:
    local_path: str
    relative_path: str
    exact_sha256: str
    perceptual_hash: str
    phash: str
    byte_size: int
    reference_count: int
    duplicate: bool

    def as_dict(self) -> dict[str, str]:
        return {
            "local_path": self.local_path,
            "relative_path": self.relative_path,
            "exact_sha256": self.exact_sha256,
            "perceptual_hash": self.perceptual_hash,
            "phash": self.phash,
            "byte_size": str(self.byte_size),
            "reference_count": str(self.reference_count),
            "duplicate": str(self.duplicate).lower(),
        }


def _manifest_path(media_dir: Path) -> Path:
    return media_dir / MANIFEST_NAME


def _empty_manifest() -> dict[str, Any]:
    return {"schema_version": 1, "files": {}, "remote_snapshots": {}}


def _load_manifest(media_dir: Path) -> dict[str, Any]:
    path = _manifest_path(media_dir)
    if not path.exists():
        return _empty_manifest()
    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)
    if not isinstance(manifest.get("files"), dict):
        manifest["files"] = {}
    if not isinstance(manifest.get("remote_snapshots"), dict):
        manifest["remote_snapshots"] = {}
    return manifest


def _write_manifest(media_dir: Path, manifest: dict[str, Any]) -> None:
    path = _manifest_path(media_dir)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, sort_keys=True)
        file.write("\n")
    tmp_path.replace(path)


def _content_path(media_dir: Path, exact_sha256: str, source: Path) -> Path:
    suffix = source.suffix.lower()
    filename = f"{exact_sha256}{suffix}" if suffix else exact_sha256
    return media_dir / exact_sha256[:2] / exact_sha256[2:4] / filename


def _relative_to_media_dir(media_dir: Path, path: Path) -> str:
    return str(path.relative_to(media_dir))


def _safe_perceptual_hash(path: Path) -> str:
    try:
        return media_hashes_file(path).perceptual_hash
    except (OSError, ValueError, UnidentifiedImageError):
        return ""


def _remote_snapshot_key(source_url: str) -> str:
    return hashlib.sha256(source_url.strip().encode("utf-8")).hexdigest()


def store_local_media(
    path: str | Path,
    *,
    reference_id: str | None = None,
    source_url: str | None = None,
    retention_policy: MediaRetentionPolicy | None = None,
    now: int | None = None,
) -> dict[str, str]:
    """Store one local media blob once and track logical references.

    The file path is content-addressed by full SHA-256. `reference_id` should be
    stable per logical attachment, for example `post_id:media_id`; repeated
    writes with the same reference do not inflate the reference count.
    """

    settings.ensure_dirs()
    media_dir = settings.media_dir
    retention = retention_policy or MediaRetentionPolicy()
    current_time = int(time.time()) if now is None else now
    source = Path(path)
    if not source.exists():
        return MediaStoreResult(
            local_path=str(_content_path(media_dir, "", source)),
            relative_path="",
            exact_sha256="",
            perceptual_hash="",
            phash="",
            byte_size=0,
            reference_count=0,
            duplicate=False,
        ).as_dict()

    exact_sha256 = exact_sha256_file(source)
    target = _content_path(media_dir, exact_sha256, source)
    duplicate = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve() and not duplicate:
        shutil.copy2(source, target)

    manifest = _load_manifest(media_dir)
    files = manifest.setdefault("files", {})
    entry = files.setdefault(
        exact_sha256,
        {
            "relative_path": _relative_to_media_dir(media_dir, target),
            "byte_size": target.stat().st_size,
            "perceptual_hash": _safe_perceptual_hash(target),
            "references": [],
            "created_at": current_time,
            "last_accessed_at": current_time,
        },
    )
    entry["relative_path"] = _relative_to_media_dir(media_dir, target)
    entry["byte_size"] = target.stat().st_size
    entry.setdefault("perceptual_hash", _safe_perceptual_hash(target))
    entry["last_accessed_at"] = current_time
    entry["storage_policy"] = retention.storage_policy
    entry["retention_reason"] = retention.reason
    entry["retention_expires_at"] = retention.expires_at(current_time)
    if source_url:
        entry["source_url"] = source_url

    references = entry.setdefault("references", [])
    if reference_id is None:
        references.append(f"anonymous:{current_time}:{len(references)}")
    elif reference_id not in references:
        references.append(reference_id)
    references.sort()
    _write_manifest(media_dir, manifest)

    perceptual_hash = str(entry.get("perceptual_hash") or "")
    return MediaStoreResult(
        local_path=str(target),
        relative_path=str(entry["relative_path"]),
        exact_sha256=exact_sha256,
        perceptual_hash=perceptual_hash,
        phash=perceptual_hash,
        byte_size=int(entry["byte_size"]),
        reference_count=len(references),
        duplicate=duplicate,
    ).as_dict()


def release_local_media(exact_sha256: str, *, reference_id: str | None = None) -> int:
    """Release one logical media reference and return the remaining count."""

    settings.ensure_dirs()
    media_dir = settings.media_dir
    manifest = _load_manifest(media_dir)
    entry = manifest.get("files", {}).get(exact_sha256)
    if not entry:
        return 0
    references = entry.setdefault("references", [])
    if reference_id is None:
        if references:
            references.pop()
    elif reference_id in references:
        references.remove(reference_id)
    entry["last_accessed_at"] = int(time.time())
    _write_manifest(media_dir, manifest)
    return len(references)


def _is_expired(entry: dict[str, Any], now: int) -> bool:
    expires_at = entry.get("retention_expires_at")
    return isinstance(expires_at, int) and expires_at <= now


def garbage_collect_media(
    *,
    max_bytes: int,
    dry_run: bool = True,
    now: int | None = None,
) -> dict[str, int]:
    """Delete expired local media or unreferenced media until under quota."""

    settings.ensure_dirs()
    media_dir = settings.media_dir
    manifest = _load_manifest(media_dir)
    files = manifest.setdefault("files", {})
    current_time = int(time.time()) if now is None else now
    entries = [
        (exact_sha256, entry)
        for exact_sha256, entry in files.items()
        if int(entry.get("byte_size") or 0) > 0
    ]
    total_bytes = sum(int(entry.get("byte_size") or 0) for _, entry in entries)
    expired_hashes = {
        exact_sha256 for exact_sha256, entry in entries if _is_expired(entry, current_time)
    }
    candidates = sorted(
        (
            (exact_sha256, entry)
            for exact_sha256, entry in entries
            if exact_sha256 in expired_hashes or len(entry.get("references", [])) == 0
        ),
        key=lambda item: (
            0 if item[0] in expired_hashes else 1,
            int(item[1].get("last_accessed_at") or 0),
        ),
    )

    deleted_files = 0
    expired_files = 0
    freed_bytes = 0
    for exact_sha256, entry in candidates:
        expired = exact_sha256 in expired_hashes
        if not expired and total_bytes - freed_bytes <= max_bytes:
            break
        byte_size = int(entry.get("byte_size") or 0)
        relative_path = str(entry.get("relative_path") or "")
        target = media_dir / relative_path if relative_path else None
        if not dry_run and target is not None and target.exists():
            target.unlink()
        if not dry_run:
            entry["local_deleted_at"] = current_time
            entry["availability"] = "metadata_only"
            entry["local_deleted_reason"] = "retention_expired" if expired else "quota_unreferenced"
            entry["relative_path"] = ""
            entry["byte_size"] = 0
        deleted_files += 1
        if expired:
            expired_files += 1
        freed_bytes += byte_size
        if not dry_run and len(entry.get("references", [])) == 0:
            files.pop(exact_sha256, None)

    if not dry_run:
        _write_manifest(media_dir, manifest)

    return {
        "total_bytes_before": total_bytes,
        "total_bytes_after": total_bytes - freed_bytes,
        "freed_bytes": freed_bytes,
        "deleted_files": deleted_files,
        "expired_files": expired_files,
        "remaining_files": len(files) if not dry_run else len(entries),
    }


def record_remote_media_snapshot(
    *,
    source_url: str,
    reason: str,
    visible_text: str = "",
    alt_text: str = "",
    observed_at: int | None = None,
) -> dict[str, str]:
    """Persist minimum metadata evidence when a remote media URL is gone."""

    settings.ensure_dirs()
    media_dir = settings.media_dir
    manifest = _load_manifest(media_dir)
    current_time = int(time.time()) if observed_at is None else observed_at
    key = _remote_snapshot_key(source_url)
    snapshot = {
        "source_url": source_url,
        "reason": reason,
        "visible_text": visible_text,
        "alt_text": alt_text,
        "observed_at": current_time,
        "availability": "remote_unavailable",
    }
    manifest.setdefault("remote_snapshots", {})[key] = snapshot
    _write_manifest(media_dir, manifest)
    return {
        "snapshot_id": key,
        "source_url": source_url,
        "reason": reason,
        "availability": "remote_unavailable",
        "observed_at": str(current_time),
    }
