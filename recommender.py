"""recommender.py
-----------------

This module implements basic heuristics for selecting candidate
accounts and topics to follow on X (formerly Twitter). While
``trending`` provides a stream of posts, the recommender analyses
content, quoted tweets and associated media to infer whether an
account is relevant to the user's interests.

The current implementation relies on simple keyword and metadata
matching but is structured such that more advanced techniques (e.g.
multi‑modal embedding models, CLIP) can be plugged in later without
significant refactoring.

Functions
---------
score_post
    Evaluate a single ``Post`` and return a float score reflecting
    relevance to a sports/news focus. Higher scores indicate a higher
    likelihood of the post being about football or general sports.

identify_candidate_accounts
    Aggregate scores across posts to rank users. Returns a list of
    usernames sorted by descending relevance score.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from .trending import Post

# A small set of Turkish and English keywords related to football. The
# recommender checks each post's text, quoted text and media alt text
# for occurrences of these words. This list can be extended or
# customised via configuration in the future.
FOOTBALL_KEYWORDS = {
    "futbol", "futbolu", "futbolun", "maç", "gol", "goll", "derbi",
    "lig", "şampiyon", "faul", "ofsayt", "hakem", "penaltı",
    # English equivalents
    "football", "goal", "match", "derby", "league", "score",
    "cup", "champions", "penalty",
}


def _count_keyword_hits(text: str) -> int:
    """Count how many football keywords appear in the given text.

    Parameters
    ----------
    text : str
        The text to scan. The search is case‑insensitive and
        normalises accented characters.

    Returns
    -------
    int
        Number of keyword occurrences found in the text.
    """
    if not text:
        return 0
    lowered = text.lower()
    # Normalise Turkish dotted/undotted i and accents by mapping to
    # ASCII approximations. This is a minimal approach and may be
    # improved with the ``unidecode`` library if available.
    for src, tgt in [("ç", "c"), ("ğ", "g"), ("ı", "i"), ("İ", "i"), ("ö", "o"), ("ş", "s"), ("ü", "u")]:
        lowered = lowered.replace(src, tgt)
    hits = 0
    for kw in FOOTBALL_KEYWORDS:
        if kw in lowered:
            hits += 1
    return hits


def score_post(post: Post) -> float:
    """Compute a relevance score for a single post.

    A post's score is derived from keyword matches in its text,
    quoted tweet (if present) and any alt text attached to media.
    We weight keyword hits found in media alt text slightly higher
    because images often convey context that might not be explicit in
    the main text. The scoring scheme is simple but provides a
    foundation for more sophisticated approaches.

    Parameters
    ----------
    post : Post
        The post to score.

    Returns
    -------
    float
        A non‑negative relevance score. Posts without any signals
        receive a score of 0.0.
    """
    score = 0.0
    # Base score from content
    score += _count_keyword_hits(post.content)
    # Boost for quoted tweet content
    if post.quoted is not None:
        quoted_content = post.quoted.get("content", "")
        score += 0.5 * _count_keyword_hits(quoted_content)
    # Boost for media alt text
    if post.media:
        for m in post.media:
            alt = m.get("alt_text", "")
            # Each alt text hit counts double
            score += 2.0 * _count_keyword_hits(alt)
    return score


def identify_candidate_accounts(posts: Iterable[Post], top_n: int = 10) -> List[Tuple[str, float]]:
    """Identify potential accounts to follow based on recent posts.

    This function aggregates scores across all posts grouped by user.
    Users whose posts consistently score high are considered strong
    candidates for following. The ``top_n`` parameter controls how
    many candidates to return.

    Parameters
    ----------
    posts : Iterable[Post]
        An iterable of posts to analyse. Posts should include media
        metadata and quoted tweet information for best results.
    top_n : int, optional
        Number of accounts to return. Defaults to 10.

    Returns
    -------
    List[Tuple[str, float]]
        A list of ``(username, score)`` tuples sorted by descending
        score. If no posts are provided an empty list is returned.
    """
    user_scores: Dict[str, float] = defaultdict(float)
    user_counts: Dict[str, int] = defaultdict(int)
    for post in posts:
        s = score_post(post)
        user_scores[post.user] += s
        user_counts[post.user] += 1
    # Normalise by number of posts so prolific posters don't dominate
    averaged: List[Tuple[str, float]] = []
    for user, total_score in user_scores.items():
        count = user_counts.get(user, 1)
        averaged.append((user, total_score / count))
    # Sort descending by score
    averaged.sort(key=lambda x: x[1], reverse=True)
    return averaged[:top_n]