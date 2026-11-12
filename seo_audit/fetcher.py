"""Fetch a page over HTTP(S) with a polite browser user-agent."""

from __future__ import annotations

import urllib.error
import urllib.request

USER_AGENT = "SEO-Audit-Tool/1.0 (+https://github.com/hasnaat-anjum/seo-website-audit-tool)"


class FetchError(Exception):
    """Raised when a URL cannot be downloaded."""


def fetch_url(url: str, timeout: int = 15) -> str:
    """Download a URL and return its HTML as text.

    Raises FetchError with a plain-English reason on any failure.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise FetchError(
            f"Server returned HTTP {exc.code} for {url}."
        ) from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Could not reach {url}: {exc.reason}.") from exc
    except TimeoutError as exc:
        raise FetchError(f"Timed out while loading {url}.") from exc
