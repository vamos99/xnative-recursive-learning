from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from xnative.media.media_store import store_local_media
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
    result = store_local_media(source)

    assert Path(result["local_path"]).exists()
    assert result["exact_sha256"] == exact_sha256_file(source)
    assert result["perceptual_hash"].startswith("dhash64-v1:")
    assert result["phash"] == result["perceptual_hash"]
