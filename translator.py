"""
translator.py
----------------

Provides a simple interface for translating text between languages. The
default implementation uses the ``googletrans`` package which in turn
scrapes Google's translation service. This requires outbound network
access. If network connectivity is unavailable or the package cannot be
imported the module falls back to returning the input text unchanged.

The ``translate`` function accepts a source text, the target language
code (e.g. "en" for English, "tr" for Turkish), and an optional source
language code. When the source language is not provided the
translator will attempt to detect the language automatically.

Example usage::

    from translator import translate
    english = translate("Merhaba dünya", target_lang="en")
    print(english)  # "Hello world"

At project initialisation you can check if translation is available by
calling ``is_translation_available``.
"""

from __future__ import annotations

from typing import Optional

try:
    # googletrans 4.0.0rc1 is more stable than earlier releases
    from googletrans import Translator  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Translator = None  # type: ignore


def is_translation_available() -> bool:
    """Return True if the translation backend is installed and operational.

    When this returns ``False`` calls to :func:`translate` will return
    the input unchanged. This allows the rest of the system to function
    without raising exceptions when translation cannot be performed.
    """
    return Translator is not None


def translate(text: str, target_lang: str = "en", source_lang: Optional[str] = None) -> str:
    """Translate text from one language to another.

    Parameters
    ----------
    text : str
        The text to translate. If empty, returns an empty string.
    target_lang : str, optional
        ISO 639‑1 code of the language to translate into. Defaults to
        English (``"en"``).
    source_lang : str, optional
        ISO 639‑1 code of the language of ``text``. If omitted the
        translator attempts to auto-detect the source language.

    Returns
    -------
    str
        The translated text if translation services are available,
        otherwise the original text. If translation fails an error
        message is printed and the original text is returned.
    """
    if not text:
        return ""
    if Translator is None:
        # translation package is not installed
        print(
            "[translator] warning: googletrans is not installed. "
            "Install it via `pip install googletrans==4.0.0rc1` to enable translation."
        )
        return text
    try:
        translator = Translator()
        result = translator.translate(text, src=source_lang, dest=target_lang)
        return result.text
    except Exception as exc:
        print(f"[translator] translation failed: {exc}")
        return text
