"""
trending.py
-----------------

This module provides helper functions for retrieving posts from X (formerly
Twitter) without relying on the official API. The project aims to collect
public content for analysis and therefore cannot depend on paid API tiers or
authenticated calls. To achieve this the module leverages the
``snscrape`` package which scrapes publicly accessible timelines and
search results.

The key function, ``get_posts``, accepts a search keyword and returns a list
of dictionaries containing metadata about each retrieved post. The number of
posts returned can be limited via the ``limit`` parameter. If ``snscrape``
is not available or network connectivity is restricted, the function
gracefully falls back to returning an empty list and logs a warning.

Example usage::

    from trending import get_posts
    posts = get_posts("yapay zeka", limit=10)
    for post in posts:
        print(post["content"])

``get_posts`` uses a simple search string of the form ``<keyword> lang:<lang>``
which instructs snscrape to fetch recent posts written in the requested
language. By default Turkish (``tr``) is used, but any ISO 639‑1 language code
can be passed.

If you need to fetch posts for multiple keywords concurrently, consider
wrapping ``get_posts`` in a ``ThreadPoolExecutor`` to execute calls in
parallel. See ``main.py`` for an example.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import snscrape.modules.twitter as sntwitter  # type: ignore
except ImportError:  # pragma: no cover - import guarded for optional dep
    sntwitter = None


@dataclass
class Post:
    """Represents a single post retrieved from X.

    This dataclass has been extended beyond a simple text-only
    representation to also capture information about any attached
    media as well as quoted tweets. Having access to rich media
    metadata allows downstream consumers to perform multi‑modal
    analysis and better understand the context of a post without
    needing to make additional network calls. If you do not need
    this metadata simply ignore the ``media`` and ``quoted`` fields.

    Attributes
    ----------
    id : int
        The unique identifier of the post.
    url : str
        URL pointing directly to the post on X.
    date : datetime
        The timestamp when the post was created (UTC).
    content : str
        The raw text content of the post.
    user : str
        The username of the post author (screen name).
    media : List[Dict[str, Any]]
        A list of media attachments present in the post. Each item is
        a dictionary containing keys such as ``type`` (e.g. ``"photo"``,
        ``"video"``), ``url`` (direct link to the media file), and
        ``alt_text`` (if available). Absent media will result in an
        empty list.
    quoted : Dict[str, Any] | None
        If the post quotes or retweets another tweet the quoted
        content will be captured here. The dictionary contains the
        ``user`` and ``content`` of the quoted tweet. For posts
        without a quoted tweet this field is ``None``.
    """

    id: int
    url: str
    date: datetime
    content: str
    user: str
    media: List[Dict[str, Any]]
    quoted: Dict[str, Any] | None


def get_posts(keyword: str, limit: int = 20, lang: str = "tr") -> List[Post]:
    """Retrieve a list of recent posts containing a specific keyword.

    This function uses the ``snscrape`` library to fetch public posts from X.
    Because no authentication is required it can be run in environments
    without API keys. If the library is unavailable or an exception occurs
    during scraping an empty list is returned.

    Parameters
    ----------
    keyword : str
        The search term used to filter posts. This can be a hashtag (e.g.
        ``"#deprem"``) or a free text query. Avoid including language
        filters here; use ``lang`` instead.
    limit : int, optional
        Maximum number of posts to return. Defaults to 20. Note that
        snscrape can yield thousands of posts; retrieving too many may be
        time consuming.
    lang : str, optional
        ISO 639‑1 language code to restrict results. Defaults to Turkish
        (``"tr"``). Set to ``None`` or ``""`` to disable language filtering.

    Returns
    -------
    List[Post]
        A list of ``Post`` dataclass instances. The order reflects the
        recency of the posts (newest first).

    Notes
    -----
    ``snscrape`` performs network calls to download data. If your execution
    environment does not allow outbound HTTP requests the function will
    return an empty list. Consider populating a local cache or using
    offline test data during development.
    """

    if sntwitter is None:
        # snscrape is not available; return empty list with warning
        print(
            "[trending.get_posts] warning: snscrape is not installed. "
            "Install it via `pip install snscrape` to enable scraping."
        )
        return []

    if not keyword:
        return []

    query = keyword
    if lang:
        query += f" lang:{lang}"

    posts: List[Post] = []
    try:
        scraper = sntwitter.TwitterSearchScraper(query)
        for idx, tweet in enumerate(scraper.get_items()):
            if idx >= limit:
                break
            # Gather media information when available. snscrape exposes a
            # ``media`` attribute on tweet objects which may contain
            # photos, videos or animated gifs. We normalise the
            # representation into a list of dictionaries to avoid
            # downstream code depending on snscrape internals.
            media_info: List[Dict[str, Any]] = []
            try:
                if hasattr(tweet, "media") and tweet.media:
                    for m in tweet.media:
                        info: Dict[str, Any] = {
                            "type": getattr(m, "type", "unknown"),
                            "url": getattr(m, "fullUrl", None) or getattr(m, "url", None),
                        }
                        # Some media objects expose alt text (photo/video
                        # descriptions). We try to include it when present.
                        if hasattr(m, "altText") and m.altText:
                            info["alt_text"] = m.altText
                        media_info.append(info)
            except Exception as exc_media:
                # Swallow media parsing errors; leave media list empty
                print(f"[trending.get_posts] warning: error parsing media: {exc_media}")
            # Capture quoted tweet content if available. snscrape
            # exposes ``quotedTweet`` on tweet objects; however it may be
            # None if the post does not quote another tweet. We store a
            # simplified representation consisting of the quoting
            # author's username and the text content.
            quoted_info: Dict[str, Any] | None = None
            try:
                if hasattr(tweet, "quotedTweet") and tweet.quotedTweet:
                    qt = tweet.quotedTweet
                    quoted_info = {
                        "user": getattr(qt.user, "username", ""),
                        "content": getattr(qt, "content", ""),
                    }
            except Exception as exc_quoted:
                print(f"[trending.get_posts] warning: error parsing quoted tweet: {exc_quoted}")
            posts.append(
                Post(
                    id=tweet.id,
                    url=tweet.url,
                    date=tweet.date.replace(tzinfo=None),
                    content=tweet.content,
                    user=tweet.user.username,
                    media=media_info,
                    quoted=quoted_info,
                )
            )
    except Exception as exc:
        # In network restricted environments the scraper will fail; swallow
        # and return what we have collected so far.
        print(f"[trending.get_posts] error while scraping: {exc}")
    return posts


# ---------------------------------------------------------------------------
# Extended post scraping
#
# Some downstream components require richer information about posts than the
# basic ``Post`` dataclass provides. For example, candidate selection and
# summarisation modules may wish to know whether a tweet contains images or
# videos, whether it quotes another tweet and how many followers the author
# has. The functions and dataclasses below implement these requirements.

@dataclass
class ExtendedPost:
    """Represents a post with additional metadata for multimodal analysis.

    In addition to the standard fields of ``Post``, this dataclass exposes
    follower counts, media URLs and quoted tweet information. These fields
    allow caller functions to perform more advanced heuristics without
    needing to re‑scrape the tweet.

    Attributes
    ----------
    id : int
        Unique identifier of the post.
    url : str
        URL pointing directly to the post on X.
    date : datetime
        The timestamp when the post was created (UTC).
    content : str
        The raw text content of the post.
    user : str
        The username of the post author (screen name).
    followers_count : int
        Number of followers the author has at the time of scraping.
    media_urls : List[str]
        List of URLs pointing to images, videos or animated gifs attached
        to the tweet. Empty list if none.
    quoted_url : Optional[str]
        URL of the quoted tweet, if any. ``None`` if no quoted tweet.
    quoted_content : Optional[str]
        Text content of the quoted tweet, if any.
    quoted_media_urls : List[str]
        Media URLs attached to the quoted tweet. Empty list if none or
        if there is no quoted tweet.
    """

    id: int
    url: str
    date: datetime
    content: str
    user: str
    followers_count: int
    media_urls: List[str]
    quoted_url: Optional[str]
    quoted_content: Optional[str]
    quoted_media_urls: List[str]


def get_posts_extended(keyword: str, limit: int = 20, lang: str = "tr") -> List[ExtendedPost]:
    """
    Retrieve a list of recent posts containing a keyword with extended metadata.

    This function behaves similarly to :func:`get_posts` but returns
    instances of :class:`ExtendedPost` with additional fields such as
    ``followers_count``, ``media_urls`` and quoted tweet information. It uses
    ``snscrape`` to scrape public tweets and attempts to extract media and
    quoted tweet details. In network‑restricted environments or where
    ``snscrape`` is unavailable the function falls back to returning an
    empty list.

    Parameters
    ----------
    keyword : str
        The search term used to filter posts.
    limit : int, optional
        Maximum number of posts to return. Defaults to 20.
    lang : str, optional
        ISO 639‑1 language code to restrict results. Defaults to Turkish
        (``"tr"``). Set to ``None`` or ``""`` to disable language filtering.

    Returns
    -------
    List[ExtendedPost]
        A list of ``ExtendedPost`` instances. If scraping fails or
        ``snscrape`` is not installed an empty list is returned.
    """

    if sntwitter is None:
        print(
            "[trending.get_posts_extended] warning: snscrape is not installed. "
            "Install it via `pip install snscrape` to enable scraping."
        )
        return []

    if not keyword:
        return []

    query = keyword
    if lang:
        query += f" lang:{lang}"

    extended_posts: List[ExtendedPost] = []
    try:
        scraper = sntwitter.TwitterSearchScraper(query)
        for idx, tweet in enumerate(scraper.get_items()):
            if idx >= limit:
                break

            # Extract user follower count; default to 0 if missing
            followers_count = getattr(tweet.user, 'followersCount', 0)

            # Extract media URLs attached to the tweet
            media_urls: List[str] = []
            try:
                if tweet.media:
                    for media in tweet.media:
                        url = getattr(media, 'url', None)
                        if url:
                            media_urls.append(url)
            except Exception:
                # On error, leave media_urls empty
                pass

            # Extract quoted tweet information, if available
            quoted_url: Optional[str] = None
            quoted_content: Optional[str] = None
            quoted_media_urls: List[str] = []
            try:
                # snscrape sets quotedTweet attribute on tweet object when there is a quoted tweet
                if hasattr(tweet, 'quotedTweet') and tweet.quotedTweet:
                    quoted = tweet.quotedTweet
                    # Compose URL of quoted tweet
                    quoted_url = f"https://twitter.com/{quoted.user.username}/status/{quoted.id}"
                    quoted_content = quoted.content
                    if quoted.media:
                        for q_media in quoted.media:
                            q_url = getattr(q_media, 'url', None)
                            if q_url:
                                quoted_media_urls.append(q_url)
            except Exception:
                pass

            extended_posts.append(
                ExtendedPost(
                    id=tweet.id,
                    url=tweet.url,
                    date=tweet.date.replace(tzinfo=None),
                    content=tweet.content,
                    user=tweet.user.username,
                    followers_count=followers_count,
                    media_urls=media_urls,
                    quoted_url=quoted_url,
                    quoted_content=quoted_content,
                    quoted_media_urls=quoted_media_urls,
                )
            )
    except Exception as exc:
        print(f"[trending.get_posts_extended] error while scraping: {exc}")
    return extended_posts
