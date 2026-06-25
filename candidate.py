"""
candidate.py
----------------

This module implements heuristics for discovering promising X accounts to
follow based on a search keyword. The goal is to automatically identify
accounts that are not only relevant to a particular topic but also exhibit
qualities conducive to high‑quality content generation and learning. The
module uses the extended post scraping utilities from
``xnative_recursive_learning.trending`` to gather posts enriched with
metadata such as follower counts, media URLs and quoted tweet details.

Overview
========

Given a search keyword, the candidate selector fetches a sample of recent
tweets and aggregates statistics per author. Each author is then scored
according to a weighted set of heuristics:

* **Follower count** – accounts with more followers are given a higher base
  score since they likely produce influential content. A logarithmic
  scaling is used to prevent domination by mega‑influencers.
* **Media richness** – tweets containing images, videos or gifs receive
  additional points because visual media tends to drive engagement and
  provides rich training material for multimodal models.
* **Use of quotes** – accounts that quote other tweets are rewarded,
  indicating engagement with the broader community and an ability to
  contextualise content.
* **Keyword relevance** – if a tweet contains the search keyword
  (case‑insensitive) or any of the extracted trending keywords (hashtags or
  tokens appearing in multiple tweets), a bonus is applied.

The aggregated score per author is normalised by the number of tweets
analysed for that author. The top scoring accounts are returned as
candidates.

Usage
-----

``python
from xnative_recursive_learning.candidate import select_candidates

# Find top 10 accounts discussing "Galatasaray" in Turkish
candidates = select_candidates("Galatasaray", limit=10, lang="tr")
for username, score in candidates:
    print(username, score)
```

"""

from __future__ import annotations

import math
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Iterable, Optional

from .trending import get_posts_extended, ExtendedPost


def _extract_keywords_from_posts(posts: Iterable[ExtendedPost], top_n: int = 10) -> List[str]:
    """Extract frequently occurring tokens from the list of posts.

    This simple keyword extractor tokenises content by whitespace and
    lowercases all tokens. It then returns the ``top_n`` most common tokens
    longer than two characters. Hashtags and mentions are included as
    tokens. For a more advanced keyword extraction, consider plugging in
    libraries like spaCy or nltk at the call site.

    Parameters
    ----------
    posts : Iterable[ExtendedPost]
        An iterable of extended posts from which to extract tokens.
    top_n : int, optional
        Number of keywords to return. Defaults to 10.

    Returns
    -------
    List[str]
        A list of common tokens (case‑insensitive) across all posts.
    """
    counter: Counter[str] = Counter()
    for post in posts:
        tokens = post.content.lower().split()
        for token in tokens:
            if len(token) > 2:
                counter[token] += 1
    return [token for token, _ in counter.most_common(top_n)]


def _score_post(post: ExtendedPost, keywords: List[str]) -> float:
    """Compute a heuristic score for a single post.

    The scoring function rewards media usage, quoted content and the
    presence of any of the provided keywords in the post. Follower count
    influences the base score using a logarithmic transformation to avoid
    favouring extremely popular accounts excessively.

    Parameters
    ----------
    post : ExtendedPost
        The post to score.
    keywords : List[str]
        A list of keywords used to check the relevance of the post content.

    Returns
    -------
    float
        The computed score for the post.
    """
    score = 0.0

    # Base score from follower count (logarithmic to moderate effect)
    score += math.log(post.followers_count + 1, 10)

    # Media bonus
    if post.media_urls:
        score += 1.0

    # Quoted tweet bonus
    if post.quoted_url:
        score += 0.5

    # Keyword relevance bonus (case‑insensitive match)
    content_lower = post.content.lower()
    keyword_hits = sum(1 for kw in keywords if kw.lower() in content_lower)
    if keyword_hits:
        score += 0.3 * keyword_hits

    return score


def select_candidates(
    keyword: str,
    *,
    sample_size: int = 50,
    top_n: int = 10,
    lang: str = "tr",
) -> List[Tuple[str, float]]:
    """Select promising accounts based on a keyword.

    This function scrapes a sample of recent posts containing the keyword,
    extracts frequently occurring tokens to use as additional signals,
    computes per‑post scores via :func:`_score_post` and aggregates the
    results per author. The final candidate list comprises the top ``top_n``
    authors sorted by their normalised score in descending order.

    Parameters
    ----------
    keyword : str
        The search term to look for in tweets.
    sample_size : int, optional
        Maximum number of tweets to analyse. Defaults to 50. Increase to
        sample more accounts at the expense of scraping time.
    top_n : int, optional
        Number of candidate accounts to return. Defaults to 10.
    lang : str, optional
        ISO 639‑1 language code used to filter tweets. Set to an empty
        string or ``None`` to disable language filtering. Defaults to
        Turkish (``"tr"``).

    Returns
    -------
    List[Tuple[str, float]]
        A list of tuples containing the username and aggregated score of
        candidate accounts, sorted from highest to lowest score. If no
        candidates are found, an empty list is returned.
    """
    # Fetch extended posts for the keyword
    posts = get_posts_extended(keyword, limit=sample_size, lang=lang)
    if not posts:
        return []

    # Extract recurring keywords from the sample to enrich relevance checks
    common_tokens = _extract_keywords_from_posts(posts, top_n=15)
    # Include the original keyword as a strong signal
    keywords = list({keyword.lower(), *common_tokens})

    # Aggregate scores per user
    user_scores: Dict[str, List[float]] = defaultdict(list)
    for post in posts:
        score = _score_post(post, keywords)
        user_scores[post.user].append(score)

    # Compute average score per user
    aggregated: List[Tuple[str, float]] = []
    for user, scores in user_scores.items():
        avg_score = sum(scores) / len(scores)
        aggregated.append((user, avg_score))

    # Sort by score descending and return top_n
    aggregated.sort(key=lambda x: x[1], reverse=True)
    return aggregated[:top_n]