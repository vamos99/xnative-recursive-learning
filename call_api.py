"""
call_api module
================

This module provides a simple helper for making HTTP GET requests with
resilient error handling. Several parts of the project (notably
``trending.py``) make use of this helper to fetch HTML or JSON from
external services. The original code referenced a ``call_api`` function
imported from a missing module, which meant that network requests were
not performed at all and many features silently failed. This module
restores that missing functionality and adds sensible defaults to
improve reliability.

Key features:

* Uses ``requests`` with a configurable timeout to avoid hangs.
* Provides a ``User‑Agent`` header so requests look more like a normal
  browser and are less likely to be blocked.
* Catches common exceptions and returns ``None`` rather than raising,
  allowing callers to handle failures gracefully.

Typical usage::

    from xnative_recursive_learning.call_api import call_api

    result = call_api("https://example.com/api.json")
    if result is not None:
        data = result
    else:
        # handle error or fallback
        ...

"""

from typing import Optional, Dict, Any

import logging

import requests


def call_api(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Optional[str]:
    """Perform a HTTP GET request and return the response text.

    Parameters
    ----------
    url: str
        The fully qualified URL to fetch.
    headers: dict, optional
        Additional headers to include in the request. A sensible
        ``User‑Agent`` will always be added if not provided to avoid
        triggering anti‑scraping measures.
    params: dict, optional
        Query parameters to append to the URL. Useful for APIs that
        expect GET parameters.
    timeout: float, optional
        Maximum number of seconds to wait for a response before
        aborting. Defaults to 10 seconds. A smaller timeout prevents
        the program from hanging indefinitely on slow or unresponsive
        hosts.

    Returns
    -------
    Optional[str]
        The response body as a string if the request succeeds, or
        ``None`` if an error occurs.
    """
    # Prepare headers with a default User‑Agent to emulate a real browser.
    default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.0.0 Safari/537.36"
        )
    }
    if headers:
        default_headers.update(headers)

    try:
        response = requests.get(url, headers=default_headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logging.warning("call_api: failed to fetch %s: %s", url, exc)
        return None