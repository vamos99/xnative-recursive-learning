from __future__ import annotations

from pathlib import Path


def extract_ocr_text(path: str | Path | None) -> tuple[str, str]:
    """OCR optional fallback. Returns (text, status)."""
    if not path:
        return "", "ocr_unavailable_no_path"
    try:
        import pytesseract
        from PIL import Image

        return pytesseract.image_to_string(Image.open(path)), "ocr_ok"
    except Exception:
        return "", "ocr_unavailable_used_alt_text_fallback"
