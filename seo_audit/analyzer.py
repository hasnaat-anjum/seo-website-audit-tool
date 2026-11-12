"""Parse an HTML document and collect everything the SEO checks need.

Uses only the Python standard library (``html.parser``), so the tool works
offline and without installing anything.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlparse


class PageData:
    """Everything we know about one audited page."""

    def __init__(self, url: str = "") -> None:
        self.url = url
        self.title: str = ""
        self.meta: dict[str, str] = {}          # name/property -> content
        self.lang: str = ""
        self.headings: list[tuple[int, str]] = []  # (level, text)
        self.images: list[dict[str, str]] = []     # {"src": ..., "alt": ...}
        self.links: list[dict[str, str]] = []      # {"href": ..., "text": ...}
        self.canonical: str = ""
        self.favicon: bool = False
        self.has_json_ld: bool = False
        self.word_count: int = 0
        self.text: str = ""

    # -- helpers used by the checks -------------------------------------
    @property
    def h1_count(self) -> int:
        return sum(1 for level, _ in self.headings if level == 1)

    @property
    def internal_links(self) -> int:
        return sum(1 for link in self.links if self._is_internal(link["href"]))

    @property
    def external_links(self) -> int:
        return sum(1 for link in self.links if self._is_external(link["href"]))

    @property
    def images_missing_alt(self) -> int:
        return sum(1 for img in self.images if not img.get("alt", "").strip())

    @property
    def empty_links(self) -> int:
        return sum(
            1 for link in self.links
            if not link["href"] or link["href"].strip() in ("#", "javascript:void(0)")
        )

    def _is_internal(self, href: str) -> bool:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return False
        parsed = urlparse(href)
        if not parsed.netloc:
            return True  # relative link
        return parsed.netloc == urlparse(self.url).netloc

    def _is_external(self, href: str) -> bool:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return False
        parsed = urlparse(href)
        return bool(parsed.netloc) and parsed.netloc != urlparse(self.url).netloc


class _PageParser(HTMLParser):
    """Walk the document once and fill a PageData object."""

    def __init__(self, page: PageData) -> None:
        super().__init__(convert_charrefs=True)
        self.page = page
        self._in_title = False
        self._in_heading: int | None = None
        self._heading_text = ""
        self._in_script_ld = False
        self._in_link = False
        self._link_href = ""
        self._link_text = ""
        self._skip_content = False  # inside <script> or <style>
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "html":
            self.page.lang = attrs_d.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = int(tag[1])
            self._heading_text = ""
        elif tag == "meta":
            key = attrs_d.get("name") or attrs_d.get("property") or ""
            content = attrs_d.get("content", "")
            if key:
                self.page.meta[key.lower()] = content
            if attrs_d.get("name", "").lower() == "robots":
                self.page.meta["robots"] = content
        elif tag == "link":
            rel = (attrs_d.get("rel") or "").lower()
            if rel == "canonical":
                self.page.canonical = attrs_d.get("href", "")
            if "icon" in rel:
                self.page.favicon = True
        elif tag == "img":
            self.page.images.append(
                {"src": attrs_d.get("src", ""), "alt": attrs_d.get("alt", "")}
            )
        elif tag == "a":
            self._in_link = True
            self._link_href = attrs_d.get("href", "")
            self._link_text = ""
        elif tag == "script":
            if attrs_d.get("type", "") == "application/ld+json":
                self.page.has_json_ld = True
            self._skip_content = True
        elif tag == "style":
            self._skip_content = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._in_heading is not None:
            self.page.headings.append((self._in_heading, self._heading_text.strip()))
            self._in_heading = None
        elif tag == "a" and self._in_link:
            self.page.links.append(
                {"href": self._link_href, "text": self._link_text.strip()}
            )
            self._in_link = False
        elif tag in ("script", "style"):
            self._skip_content = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.page.title += data.strip()
        if self._in_heading is not None:
            self._heading_text += data
        if self._in_link:
            self._link_text += data
        if not self._skip_content:
            self._text_parts.append(data)

    def close(self) -> None:
        super().close()
        text = " ".join(self._text_parts)
        text = re.sub(r"\s+", " ", text).strip()
        self.page.text = text
        self.page.word_count = len(text.split()) if text else 0


def parse_html(html: str, url: str = "") -> PageData:
    """Parse an HTML string and return the collected page data."""
    page = PageData(url=url)
    parser = _PageParser(page)
    parser.feed(html)
    parser.close()
    return page
