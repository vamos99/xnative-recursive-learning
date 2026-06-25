"""analysis.py
-----------------

This module provides functions for analysing posts retrieved from
social media feeds. The goal of the analysis stage in the XNative
Recursive Learning project is to determine the most relevant
information contained in a post, classify posts into broad topical
categories, and generate concise summaries.  The implementation here
focuses on robustness and efficiency rather than deep learning.  By
avoiding large external models we ensure the analysis component can
operate in constrained environments where internet access may be
limited and additional dependencies cannot be downloaded on demand.

Key features provided by this module:

* Safe text cleaning routines that normalise whitespace, remove
  excessive punctuation and convert unicode characters into a
  consistent form.
* A configurable set of keyword based classifiers that map a post
  into one or more categories.  Categories can be declared by users
  through the :data:`CATEGORY_KEYWORDS` dictionary.
* A simple sentiment estimator that counts the number of positive and
  negative words present in the text.  This offers a coarse
  indication of the tone of the post without requiring a heavyweight
  NLP model.
* A unified :func:`analyse_post` function that accepts a post
  dictionary (as returned by :mod:`trending`) and returns a
  structured :class:`AnalysisResult` instance containing the
  classification, sentiment and cleaned text.  When images are
  present the analyser will attempt to detect their file type and
  return a list of media descriptions.

The analysis API is designed to be extended.  For example a future
implementation could import a pre-trained transformer or computer
vision model when available.  Additional analysis tasks (such as
entity recognition, topic modelling or custom scoring functions) can
be added as methods on the :class:`PostAnalyser` class without
breaking the external API.

Example usage::

    from trending import get_posts
    from analysis import analyse_post

    posts = get_posts("football")
    for post in posts:
        result = analyse_post(post)
        print(result.category, result.sentiment)

"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


def clean_text(text: str) -> str:
    """Normalise and clean text.

    This helper applies a series of inexpensive transformations to the
    input string.  The transformations include:

    * Converting all whitespace runs into single spaces.
    * Stripping leading and trailing whitespace.
    * Collapsing repeated punctuation characters (e.g. "!!!" becomes
      "!").
    * Converting common unicode quote marks to ASCII equivalents.

    Parameters
    ----------
    text : str
        The raw input text to clean.

    Returns
    -------
    str
        A cleaned and normalised string.
    """
    if not text:
        return ""
    # Replace fancy quotes with straight quotes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Collapse repeated punctuation (e.g. many exclamation marks)
    text = re.sub(r"([!?\.])\1+", r"\1", text)
    # Strip leading/trailing whitespace
    return text.strip()


# Define keyword categories.  These can be extended by users to cover
# additional topics.  The keys represent category names and the
# associated values are lists of keywords or key phrases that, when
# present in the text, suggest the post belongs to that category.  The
# matching is case-insensitive.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "football": [
        # Core terms for association football/soccer.  Including both
        # English and common non-English variants ensures posts from
        # multiple locales can be classified correctly.
        "football", "soccer", "futbol", "futebol",
        # Match-related words
        "goal", "match", "game", "maç", "oyun",
        # Scoring and results
        "victory", "defeat", "win", "loss", "gol", "penalty",
        # Competitions and leagues
        "world cup", "worldcup", "champions league", "premier league",
        "la liga", "serie a", "bundesliga", "europa league",
        # Roles and participants
        "coach", "manager", "takım", "player", "futbolcu",
        # Transfer news terms
        "transfer", "contract", "signing"
    ],
    "basketball": [
        "basketball", "nba", "dunk", "three-pointer", "slam dunk",
        "basket", "koç", "basketbol"
    ],
    "technology": [
        "ai", "artificial intelligence", "technology", "tech",
        "software", "hardware", "launch", "update", "release"
    ],
    "news": [
        "breaking", "according to", "reports", "news", "report",
        "headline", "son dakika", "haber"
    ],
}


POSITIVE_WORDS: set = {
    "good", "great", "amazing", "awesome", "fantastic", "love",
    "excellent", "happy", "win", "victory", "positive", "başarılı",
    "mutlu"
}
NEGATIVE_WORDS: set = {
    "bad", "terrible", "awful", "hate", "poor", "sad", "loss",
    "defeat", "negative", "kötü", "üzgün"
}


def classify_text(text: str, categories: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Classify text into categories based on keyword occurrence.

    The classification uses a simple bag-of-words approach.  The input
    text is converted to lowercase and searched for occurrences of
    keywords defined in :data:`CATEGORY_KEYWORDS` (or the provided
    ``categories`` mapping).  A category is assigned to the text if
    any of its keywords appear as a substring in the cleaned text.

    Parameters
    ----------
    text : str
        The input text to classify.  It is expected to be pre-cleaned
        by :func:`clean_text`.
    categories : dict, optional
        A mapping of category names to lists of keywords.  If
        ``None`` uses the default :data:`CATEGORY_KEYWORDS`.

    Returns
    -------
    list of str
        A list of category names that matched the text.  If no
        categories match the list will be empty.
    """
    if not text:
        return []
    if categories is None:
        categories = CATEGORY_KEYWORDS
    text_lower = text.lower()
    matched: List[str] = []
    for category, keywords in categories.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                matched.append(category)
                break  # stop checking other keywords for this category
    return matched


def estimate_sentiment(text: str) -> float:
    """Estimate sentiment polarity for a piece of text.

    A positive score indicates that the text contains more positive
    words than negative ones, a negative score indicates the
    opposite.  The magnitude of the score is normalised by the
    total number of words to ensure comparability across posts of
    different lengths.  If no sentiment words are found the score
    returned is 0.0.

    Parameters
    ----------
    text : str
        Cleaned input text.

    Returns
    -------
    float
        A sentiment polarity score in the range [-1.0, 1.0].
    """
    if not text:
        return 0.0
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return 0.0
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    score = (pos_count - neg_count) / len(words)
    # Clip the score to [-1, 1] just in case
    return max(min(score, 1.0), -1.0)


@dataclass
class MediaDescription:
    """Represent a description of a piece of media.

    The :class:`~trending.get_posts` function returns media items in
    posts as dictionaries with ``type`` and ``url`` keys.  This
    dataclass stores derived metadata about those media items.  For now
    it simply copies the type and URL but could be extended to record
    additional properties such as detected objects in images, dominant
    colours or media dimensions.

    Attributes
    ----------
    type : str
        The media type, e.g. "photo", "video" or "animated_gif".
    url : str
        The absolute URL of the media resource.
    description : str, optional
        A free form description of the media.  When the analysis
        cannot provide additional information this will be an empty
        string.
    """

    type: str
    url: str
    description: str = ""


@dataclass
class AnalysisResult:
    """Bundle the results of analysing a post.

    Instances of this dataclass are returned by :func:`analyse_post`.
    They capture the cleaned text, matched categories, estimated
    sentiment and descriptions of any attached media.  The API is
    intentionally simple and stable: additional fields may be added in
    future versions as optional attributes but existing fields will
    remain unchanged.
    """

    original_post_id: str
    cleaned_text: str
    categories: List[str] = field(default_factory=list)
    sentiment: float = 0.0
    media: List[MediaDescription] = field(default_factory=list)


def analyse_post(post: Dict) -> AnalysisResult:
    """Perform a comprehensive analysis of a single post.

    The input ``post`` should be a dictionary obtained from
    :func:`trending.get_posts` containing keys such as ``id``, ``text``
    and ``media``.  This function cleans the text, applies
    classification and sentiment estimation, and returns a structured
    :class:`AnalysisResult` describing the post.  When errors occur
    during analysis they are caught and logged; the resulting fields
    will default to sensible values rather than raising exceptions.

    Parameters
    ----------
    post : dict
        A post dictionary from the trending module.

    Returns
    -------
    AnalysisResult
        The analysis outcome with cleaned text, category matches,
        sentiment score and media descriptions.
    """
    # Ensure mandatory keys are present
    post_id = post.get("id", "")
    # Combine the main post text with any image alt text to enrich the
    # analysis.  Including alt text in the analysis helps the model
    # better capture the meaning of posts that rely heavily on images
    # or other media to convey context (e.g., sports highlights or
    # memes).  Some trending API responses place alt text on the
    # top-level key "image_alt", while media entries may contain
    # "alt_text" per item.  We concatenate any available alt text
    # into a single string alongside the raw text for analysis.
    raw_text = post.get("text", "") or ""
    alt_texts: List[str] = []
    # Top-level alt text (for convenience in trending.get_posts)
    top_alt = post.get("image_alt")
    if top_alt:
        alt_texts.append(str(top_alt))
    # Alt text from each media item (if present)
    media_items = post.get("media", []) or []
    if isinstance(media_items, Iterable):
        for m in media_items:
            alt = m.get("alt_text") if isinstance(m, dict) else None
            if alt:
                alt_texts.append(str(alt))
    # Build the combined textual representation
    combined_text = " ".join([raw_text] + alt_texts).strip()
    cleaned = clean_text(combined_text)
    try:
        categories = classify_text(cleaned)
    except Exception as exc:
        print(f"[analysis] classification error for post {post_id}: {exc}")
        categories = []
    try:
        sentiment = estimate_sentiment(cleaned)
    except Exception as exc:
        print(f"[analysis] sentiment error for post {post_id}: {exc}")
        sentiment = 0.0
    media_descriptions: List[MediaDescription] = []
    media = post.get("media", []) or []
    # Ensure media is iterable
    if not isinstance(media, Iterable):
        media = []
    for item in media:
        m_type = item.get("type", "unknown")
        url = item.get("url", "")
        desc = ""
        media_descriptions.append(MediaDescription(type=m_type, url=url, description=desc))
    return AnalysisResult(
        original_post_id=str(post_id),
        cleaned_text=cleaned,
        categories=categories,
        sentiment=sentiment,
        media=media_descriptions,
    )