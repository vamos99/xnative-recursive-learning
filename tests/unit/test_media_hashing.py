from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from xnative.media.media_store import (
    MediaGarbageCollectionPolicy,
    MediaRetentionPolicy,
    garbage_collect_media,
    record_remote_media_snapshot,
    release_local_media,
    store_local_media,
)
from xnative.media.phash import (
    cluster_similar_hashes,
    difference_hash_file,
    exact_sha256_file,
    hamming_distance_hex,
    is_near_duplicate,
    media_hashes_file,
)


def _save_pattern(path: Path, *, variant: str = "base") -> None:
    image = Image.new("RGB", (96, 96), "white")
    draw = ImageDraw.Draw(image)
    if variant == "base":
        draw.rectangle((8, 8, 70, 48), fill="black")
        draw.line((0, 92, 95, 20), fill="gray", width=5)
    elif variant == "near":
        draw.rectangle((10, 8, 72, 48), fill="black")
        draw.line((0, 92, 95, 20), fill="gray", width=5)
    else:
        draw.ellipse((16, 16, 80, 80), fill="black")
        draw.line((0, 10, 95, 88), fill="gray", width=6)
    image.save(path)


def test_exact_sha_and_perceptual_hash_are_separate(tmp_path) -> None:
    original = tmp_path / "original.png"
    copy = tmp_path / "copy.png"
    near = tmp_path / "near.png"
    different = tmp_path / "different.png"

    _save_pattern(original)
    copy.write_bytes(original.read_bytes())
    _save_pattern(near, variant="near")
    _save_pattern(different, variant="different")

    original_hashes = media_hashes_file(original)
    copy_hashes = media_hashes_file(copy)
    near_hashes = media_hashes_file(near)
    different_hashes = media_hashes_file(different)

    assert original_hashes.exact_sha256 == copy_hashes.exact_sha256
    assert original_hashes.perceptual_hash == copy_hashes.perceptual_hash
    assert original_hashes.exact_sha256 != near_hashes.exact_sha256
    assert is_near_duplicate(original_hashes.perceptual_hash, near_hashes.perceptual_hash)
    assert not is_near_duplicate(
        original_hashes.perceptual_hash,
        different_hashes.perceptual_hash,
        threshold=8,
    )


def test_dhash_distance_and_small_batch_clustering(tmp_path) -> None:
    paths = [tmp_path / name for name in ("base.png", "near.png", "different.png")]
    _save_pattern(paths[0])
    _save_pattern(paths[1], variant="near")
    _save_pattern(paths[2], variant="different")
    hashes = [difference_hash_file(path) for path in paths]

    assert hamming_distance_hex(hashes[0], hashes[1]) <= 8
    assert hamming_distance_hex(hashes[0], hashes[2]) > 8
    assert cluster_similar_hashes(hashes, threshold=8) == [[0, 1], [2]]


def test_store_local_media_returns_exact_and_perceptual_hashes(tmp_path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    fake_settings = SimpleNamespace(
        media_dir=media_dir,
        ensure_dirs=lambda: media_dir.mkdir(parents=True, exist_ok=True),
    )
    monkeypatch.setattr("xnative.media.media_store.settings", fake_settings)

    source = tmp_path / "source.png"
    _save_pattern(source)
    result = store_local_media(source, reference_id="post-1:media-1")

    assert Path(result["local_path"]).exists()
    assert result["exact_sha256"] == exact_sha256_file(source)
    assert result["perceptual_hash"].startswith("dhash64-v1:")
    assert result["phash"] == result["perceptual_hash"]
    assert result["reference_count"] == "1"


def test_content_addressed_store_dedupes_references_and_garbage_collects(
    tmp_path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    fake_settings = SimpleNamespace(
        media_dir=media_dir,
        ensure_dirs=lambda: media_dir.mkdir(parents=True, exist_ok=True),
    )
    monkeypatch.setattr("xnative.media.media_store.settings", fake_settings)

    source = tmp_path / "source.png"
    same_bytes = tmp_path / "same-bytes.png"
    _save_pattern(source)
    same_bytes.write_bytes(source.read_bytes())

    first = store_local_media(source, reference_id="post-a:media")
    second = store_local_media(same_bytes, reference_id="post-b:media")
    repeated = store_local_media(source, reference_id="post-a:media")

    assert first["local_path"] == second["local_path"] == repeated["local_path"]
    assert second["duplicate"] == "true"
    assert repeated["reference_count"] == "2"
    assert len(list(media_dir.glob("**/*.png"))) == 1

    assert release_local_media(first["exact_sha256"], reference_id="post-a:media") == 1
    assert release_local_media(first["exact_sha256"], reference_id="post-b:media") == 0

    dry_run = garbage_collect_media(max_bytes=0, dry_run=True)
    assert dry_run["deleted_files"] == 1
    assert Path(first["local_path"]).exists()

    result = garbage_collect_media(max_bytes=0, dry_run=False)
    assert result["deleted_files"] == 1
    assert not Path(first["local_path"]).exists()


def test_retention_ttl_deletes_local_file_but_keeps_metadata_snapshot(
    tmp_path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    fake_settings = SimpleNamespace(
        media_dir=media_dir,
        ensure_dirs=lambda: media_dir.mkdir(parents=True, exist_ok=True),
    )
    monkeypatch.setattr("xnative.media.media_store.settings", fake_settings)

    source = tmp_path / "expiring.png"
    _save_pattern(source)
    stored = store_local_media(
        source,
        reference_id="post-c:media",
        source_url="https://pbs.twimg.com/media/expiring.jpg",
        retention_policy=MediaRetentionPolicy(
            storage_policy="thumbnail",
            ttl_seconds=10,
            reason="test-retention",
        ),
        now=100,
    )

    result = garbage_collect_media(max_bytes=10_000_000, dry_run=False, now=111)
    manifest = json.loads((media_dir / ".xnative_media_manifest.json").read_text())
    entry = manifest["files"][stored["exact_sha256"]]

    assert result["expired_files"] == 1
    assert result["deleted_files"] == 1
    assert not Path(stored["local_path"]).exists()
    assert entry["availability"] == "metadata_only"
    assert entry["local_deleted_reason"] == "retention_expired"
    assert entry["source_url"] == "https://pbs.twimg.com/media/expiring.jpg"
    assert entry["byte_size"] == 0
    assert entry["references"] == ["post-c:media"]


def test_remote_media_snapshot_records_deleted_url_evidence(tmp_path, monkeypatch) -> None:
    media_dir = tmp_path / "media"
    fake_settings = SimpleNamespace(
        media_dir=media_dir,
        ensure_dirs=lambda: media_dir.mkdir(parents=True, exist_ok=True),
    )
    monkeypatch.setattr("xnative.media.media_store.settings", fake_settings)

    snapshot = record_remote_media_snapshot(
        source_url="https://pbs.twimg.com/media/deleted.jpg",
        reason="http_404",
        visible_text="Maçtan sonra gelen tepki",
        alt_text="tribün fotoğrafı",
        observed_at=123,
    )
    manifest = json.loads((media_dir / ".xnative_media_manifest.json").read_text())
    stored = manifest["remote_snapshots"][snapshot["snapshot_id"]]

    assert snapshot["availability"] == "remote_unavailable"
    assert stored["reason"] == "http_404"
    assert stored["visible_text"] == "Maçtan sonra gelen tepki"
    assert stored["alt_text"] == "tribün fotoğrafı"
    assert stored["observed_at"] == 123


def test_garbage_collection_policy_uses_lru_and_protects_originals(
    tmp_path,
    monkeypatch,
) -> None:
    media_dir = tmp_path / "media"
    fake_settings = SimpleNamespace(
        media_dir=media_dir,
        ensure_dirs=lambda: media_dir.mkdir(parents=True, exist_ok=True),
    )
    monkeypatch.setattr("xnative.media.media_store.settings", fake_settings)

    oldest = tmp_path / "oldest.png"
    newest = tmp_path / "newest.png"
    protected = tmp_path / "protected.png"
    _save_pattern(oldest, variant="base")
    _save_pattern(newest, variant="near")
    _save_pattern(protected, variant="different")

    stored_oldest = store_local_media(
        oldest,
        reference_id="oldest",
        retention_policy=MediaRetentionPolicy(storage_policy="thumbnail"),
        now=100,
    )
    stored_newest = store_local_media(
        newest,
        reference_id="newest",
        retention_policy=MediaRetentionPolicy(storage_policy="thumbnail"),
        now=200,
    )
    stored_protected = store_local_media(
        protected,
        reference_id="protected",
        retention_policy=MediaRetentionPolicy(storage_policy="original"),
        now=50,
    )
    release_local_media(stored_oldest["exact_sha256"], reference_id="oldest")
    release_local_media(stored_newest["exact_sha256"], reference_id="newest")
    release_local_media(stored_protected["exact_sha256"], reference_id="protected")

    total_size = sum(
        Path(row["local_path"]).stat().st_size
        for row in (stored_oldest, stored_newest, stored_protected)
    )
    newest_size = Path(stored_newest["local_path"]).stat().st_size
    protected_size = Path(stored_protected["local_path"]).stat().st_size
    policy = MediaGarbageCollectionPolicy(
        max_bytes=total_size,
        min_free_bytes=newest_size + 1,
    )

    result = garbage_collect_media(max_bytes=total_size, dry_run=False, policy=policy)

    assert result["quota_files"] == 1
    assert result["protected_files"] == 1
    assert result["target_bytes"] == total_size - newest_size - 1
    assert not Path(stored_oldest["local_path"]).exists()
    assert Path(stored_newest["local_path"]).exists()
    assert Path(stored_protected["local_path"]).exists()
    assert result["total_bytes_after"] == newest_size + protected_size
