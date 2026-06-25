"""
summarizer.py
----------------

This module wraps a Transformer-based sequence summarisation model to
provide concise summaries of lengthy text. During development we rely on
models from the Hugging Face ``transformers`` library; specifically the
``sshleifer/distilbart-cnn-12-6`` model which is a distilled variant of
Facebook's BART tuned on the CNN/DailyMail dataset. Distillation yields a
model that is faster to run while still producing high quality
summaries.

Example usage::

    from summarizer import summarize
    summary = summarize(long_text, max_length=120)
    print(summary)

This module caches the model and tokenizer after the first call to avoid
reloading them on subsequent invocations. Should the ``transformers``
package not be available in your environment a fallback implementation
provides a naive summarisation by truncating the input. This ensures
graceful degradation in environments with restricted dependencies.

Note: summarisation is resource intensive. Running a large model on the
CPU can take several seconds for long articles. Adjust ``max_length``
and ``min_length`` to suit your use-case.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, List

try:
    from transformers import pipeline  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pipeline = None  # type: ignore


@lru_cache(maxsize=1)
def _get_summarizer_pipeline():
    """Lazily load the summarisation pipeline.

    Uses DistilBART if available. Returns None when transformers
    is not installed.
    """
    if pipeline is None:
        return None
    try:
        summariser = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            framework="pt",
        )
        return summariser
    except Exception as exc:  # pragma: no cover - loading can fail
        print(f"[summarizer] warning: could not load model: {exc}")
        return None


def summarize(
    text: str,
    max_length: int = 150,
    min_length: int = 40,
    *,
    style_samples: Optional[list[str]] = None,
    top_style_words: int = 5,
) -> str:
    """Generate a summary from the given text.

    Parameters
    ----------
    text : str
        The full text to summarise. If the text is shorter than
        ``min_length`` characters the function simply returns the
        original text.
    max_length : int, optional
        The maximum number of tokens in the summary. Defaults to 150.
    min_length : int, optional
        The minimum number of tokens in the summary. Defaults to 40.
    style_samples : list[str], optional
        A collection of example texts (e.g. recent posts from a target
        account) whose vocabulary should be reflected in the summary.
        When provided the function will compute the most frequent
        non‑stopword tokens across these samples and append a handful
        of them to the end of the summary. This simple stylistic
        adaptation helps make summaries feel more in‑line with the
        language of the source domain without requiring full model
        fine‑tuning.
    top_style_words : int, optional
        The number of top keywords extracted from ``style_samples``
        to append to the summary. Defaults to 5. Set to 0 to disable
        keyword injection.

    Returns
    -------
    str
        A summary string. When the summariser pipeline is unavailable
        a simple substring of the input is returned. If ``style_samples``
        is provided the summary will include a suffix of frequent
        keywords.
    """
    if not text or len(text.split()) < min_length:
        return text

    summariser = _get_summarizer_pipeline()
    if summariser is None:
        # Fallback: return the first max_length words of the text
        words = text.split()
        summary_text = " ".join(words[:max_length]) + ("..." if len(words) > max_length else "")
    else:
        try:
            summary_list = summariser(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
            )
            if summary_list and isinstance(summary_list, list):
                summary_text = summary_list[0].get("summary_text", text).strip()
            else:
                summary_text = text
        except Exception as exc:
            print(f"[summarizer] warning: summarisation failed: {exc}")
            # Fallback on failure: return truncated input
            words = text.split()
            summary_text = " ".join(words[:max_length]) + ("..." if len(words) > max_length else "")

    # Inject stylistic keywords when samples are provided
    if style_samples and top_style_words > 0:
        try:
            # Very lightweight extraction: count token frequencies
            from collections import Counter
            import re
            # Simple tokeniser: split on non‑word characters
            token_counter = Counter()
            stopwords = {
                "the", "a", "an", "of", "and", "or", "to", "in", "is", "are", "for",
                "on", "with", "at", "by", "from", "that", "this", "it", "be", "as", "has",
                "have", "had", "was", "were", "will", "would", "can", "could", "should", "i",
                "you", "he", "she", "they", "we", "me", "them", "us"
            }
            for sample in style_samples:
                tokens = re.split(r"\W+", sample.lower())
                for token in tokens:
                    if token and token not in stopwords and len(token) > 2:
                        token_counter[token] += 1
            keywords = [tok for tok, _ in token_counter.most_common(top_style_words)]
            if keywords:
                # Append keywords separated by spaces and prefaced by a separator
                summary_text = f"{summary_text} | {' '.join(keywords)}"
        except Exception as exc:
            # Log silently; if extraction fails we simply omit the stylistic suffix
            print(f"[summarizer] warning: style keyword extraction failed: {exc}")
    return summary_text
