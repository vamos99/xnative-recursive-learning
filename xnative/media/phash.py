from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

DHASH_SIZE = 8
DHASH_BITS = DHASH_SIZE * DHASH_SIZE
DEFAULT_NEAR_DUPLICATE_THRESHOLD = 8


@dataclass(frozen=True)
class MediaHashes:
    exact_sha256: str
    perceptual_hash: str
    perceptual_algorithm: str = "dhash64-v1"


def exact_sha256_file(path: str | Path) -> str:
    """Return a full SHA-256 digest for exact byte-level deduplication."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def difference_hash_file(path: str | Path, hash_size: int = DHASH_SIZE) -> str:
    """Return a 64-bit dHash for cheap near-duplicate image detection.

    This is a perceptual hash, not a cryptographic digest. It is intentionally
    small and CPU-friendly for the target 8 GB RAM / GTX 1050 class machine.
    """

    source_image = Image.open(path)
    image: Image.Image = (
        ImageOps.exif_transpose(source_image)
        .convert("L")
        .resize(
            (hash_size + 1, hash_size),
            Image.Resampling.LANCZOS,
        )
    )
    pixels = list(getattr(image, "get_flattened_data", image.getdata)())
    bits: list[str] = []
    row_width = hash_size + 1
    for row in range(hash_size):
        offset = row * row_width
        for col in range(hash_size):
            left = pixels[offset + col]
            right = pixels[offset + col + 1]
            bits.append("1" if left > right else "0")
    return f"dhash{hash_size * hash_size}-v1:{int(''.join(bits), 2):0{hash_size * hash_size // 4}x}"


def media_hashes_file(path: str | Path) -> MediaHashes:
    exact = exact_sha256_file(path)
    perceptual = difference_hash_file(path)
    return MediaHashes(exact_sha256=exact, perceptual_hash=perceptual)


def _hash_payload(value: str) -> tuple[str, int]:
    if ":" in value:
        algorithm, payload = value.split(":", 1)
    else:
        algorithm, payload = "hex", value
    return algorithm, int(payload or "0", 16)


def hamming_distance_hex(a: str, b: str) -> int:
    algorithm_a, payload_a = _hash_payload(a)
    algorithm_b, payload_b = _hash_payload(b)
    if algorithm_a != algorithm_b:
        raise ValueError(
            f"Cannot compare different perceptual hash algorithms: {algorithm_a!r}, {algorithm_b!r}"
        )
    return (payload_a ^ payload_b).bit_count()


def is_near_duplicate(
    a: str,
    b: str,
    *,
    threshold: int = DEFAULT_NEAR_DUPLICATE_THRESHOLD,
) -> bool:
    return hamming_distance_hex(a, b) <= threshold


def cluster_similar_hashes(
    hashes: list[str],
    *,
    threshold: int = DEFAULT_NEAR_DUPLICATE_THRESHOLD,
) -> list[list[int]]:
    """Cluster small batches of perceptual hashes with union-find.

    The intended use is thumbnail batches, not large vector search. Later P6
    vector-index work owns larger-scale retrieval.
    """

    parent = list(range(len(hashes)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(len(hashes)):
        for right in range(left + 1, len(hashes)):
            if is_near_duplicate(hashes[left], hashes[right], threshold=threshold):
                union(left, right)

    groups: dict[int, list[int]] = {}
    for index in range(len(hashes)):
        groups.setdefault(find(index), []).append(index)
    return list(groups.values())


def phash_file(path: str | Path) -> str:
    """Backward-compatible alias.

    Historical code used this name for a SHA-256 prefix. It now returns a real
    perceptual dHash string and should be replaced by `difference_hash_file` in
    new code.
    """

    return difference_hash_file(path)
