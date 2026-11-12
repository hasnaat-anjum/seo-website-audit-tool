"""The SEO checks: each one returns a Check result with a pass / warning /
fail status, a plain-English message, and the points it is worth.

Weights add up to 100, so the total score is a percentage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .analyzer import PageData

# Recommended lengths from Google's own search documentation and common
# SEO practice.
TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 120, 160
MIN_WORDS = 300


@dataclass
class Check:
    """One audit result."""

    name: str
    status: str  # "pass" | "warning" | "fail"
    message: str
    weight: int
    points: int

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def _check(name: str, weight: int, ok: bool, message: str,
           warning: bool = False) -> Check:
    """Build a Check: full points on pass, half on warning, zero on fail."""
    if ok:
        return Check(name, "pass", message, weight, weight)
    if warning:
        return Check(name, "warning", message, weight, weight // 2)
    return Check(name, "fail", message, weight, 0)


def run_checks(page: PageData, keyword: str = "") -> list[Check]:
    """Run every check against a parsed page and return the results."""
    checks: list[Check] = []
    title = page.title
    desc = page.meta.get("description", "")

    # 1. Title tag -------------------------------------------------------
    if not title:
        checks.append(_check("Title tag", 10, False,
                             "No <title> tag found. Every page needs a unique title."))
    elif len(title) < TITLE_MIN:
        checks.append(_check("Title tag", 10, False,
                             f'Title is only {len(title)} characters '
                             f'("{title}"). Aim for {TITLE_MIN}-{TITLE_MAX}.',
                             warning=True))
    elif len(title) > TITLE_MAX:
        checks.append(_check("Title tag", 10, False,
                             f"Title is {len(title)} characters and will be cut off "
                             f'in search results. Aim for {TITLE_MIN}-{TITLE_MAX}.',
                             warning=True))
    else:
        checks.append(_check("Title tag", 10, True,
                             f'Title is {len(title)} characters: "{title}".'))

    # 2. Meta description ------------------------------------------------
    if not desc:
        checks.append(_check("Meta description", 10, False,
                             "No meta description. Add one to control the snippet "
                             "shown in search results."))
    elif len(desc) < DESC_MIN:
        checks.append(_check("Meta description", 10, False,
                             f"Meta description is only {len(desc)} characters. "
                             f"Aim for {DESC_MIN}-{DESC_MAX}.", warning=True))
    elif len(desc) > DESC_MAX:
        checks.append(_check("Meta description", 10, False,
                             f"Meta description is {len(desc)} characters and will "
                             f"be cut off. Aim for {DESC_MIN}-{DESC_MAX}.",
                             warning=True))
    else:
        checks.append(_check("Meta description", 10, True,
                             f"Meta description is {len(desc)} characters."))

    # 3. H1 heading ------------------------------------------------------
    if page.h1_count == 0:
        checks.append(_check("H1 heading", 8, False,
                             "No H1 heading found. Add exactly one H1 that "
                             "describes the page topic."))
    elif page.h1_count > 1:
        checks.append(_check("H1 heading", 8, False,
                             f"Found {page.h1_count} H1 headings. Use exactly one "
                             "H1 per page.", warning=True))
    else:
        checks.append(_check("H1 heading", 8, True,
                             f'One H1 found: "{page.headings[0][1][:60]}".'))

    # 4. Heading order ---------------------------------------------------
    skipped = any(
        page.headings[i + 1][0] > page.headings[i][0] + 1
        for i in range(len(page.headings) - 1)
    )
    checks.append(_check(
        "Heading structure", 5, not skipped,
        "Headings skip a level (e.g. H2 straight to H4). Keep headings in "
        "order so Google and screen readers understand the page."
        if skipped else
        f"Headings are in order ({len(page.headings)} headings found)."))

    # 5. Images with alt text -------------------------------------------
    if not page.images:
        checks.append(_check("Image alt text", 8, True,
                             "No images on this page, so nothing to fix here.",
                             ))
    elif page.images_missing_alt == 0:
        checks.append(_check("Image alt text", 8, True,
                             f"All {len(page.images)} images have alt text."))
    else:
        checks.append(_check(
            "Image alt text", 8, False,
            f"{page.images_missing_alt} of {len(page.images)} images are missing "
            "alt text. Alt text helps Google Images and screen readers.",
            warning=page.images_missing_alt < len(page.images) / 2))

    # 6. Content length --------------------------------------------------
    checks.append(_check(
        "Content length", 8, page.word_count >= MIN_WORDS,
        f"Only {page.word_count} words on the page. Thin pages rarely rank -- "
        f"aim for at least {MIN_WORDS} useful words."
        if page.word_count < MIN_WORDS else
        f"{page.word_count} words of content. Good depth for ranking."))

    # 7. Canonical URL ---------------------------------------------------
    checks.append(_check(
        "Canonical URL", 5, bool(page.canonical),
        "No canonical link. Add <link rel=\"canonical\"> so search engines "
        "know the preferred URL for this page."
        if not page.canonical else
        f"Canonical URL set: {page.canonical}"))

    # 8. Mobile viewport -------------------------------------------------
    checks.append(_check(
        "Mobile viewport", 7, "viewport" in page.meta,
        "No viewport meta tag. Without it the page will not display "
        "correctly on phones, and Google ranks mobile-first."
        if "viewport" not in page.meta else
        "Viewport meta tag is present (mobile-friendly)."))

    # 9. Language attribute ----------------------------------------------
    checks.append(_check(
        "Language attribute", 3, bool(page.lang),
        "The <html> tag has no lang attribute. Add lang=\"en\" (or your "
        "language) so search engines know the page language."
        if not page.lang else
        f'Language set to "{page.lang}".'))

    # 10. Open Graph tags -------------------------------------------------
    og = [k for k in page.meta if k.startswith("og:")]
    checks.append(_check(
        "Open Graph tags", 5, len(og) >= 3,
        "Missing Open Graph tags. Add og:title, og:description and og:image "
        "so the page looks good when shared on Facebook and LinkedIn."
        if len(og) < 3 else
        f"Open Graph tags present: {', '.join(sorted(og))}."))

    # 11. Twitter card ----------------------------------------------------
    checks.append(_check(
        "Twitter card", 3, "twitter:card" in page.meta,
        "No Twitter card meta tag. Add twitter:card so the page previews "
        "nicely when shared on X (Twitter)."
        if "twitter:card" not in page.meta else
        "Twitter card tag is present."))

    # 12. Structured data (Schema.org) ------------------------------------
    checks.append(_check(
        "Structured data", 5, page.has_json_ld,
        "No Schema.org JSON-LD found. Structured data can earn rich results "
        "(stars, prices, FAQs) in Google search."
        if not page.has_json_ld else
        "Schema.org JSON-LD structured data found."))

    # 13. Robots / noindex -------------------------------------------------
    robots = page.meta.get("robots", "").lower()
    checks.append(_check(
        "Indexable", 5, "noindex" not in robots,
        "This page has a noindex robots tag, so Google will not show it in "
        "search results. Remove it if the page should rank."
        if "noindex" in robots else
        "Page is indexable by search engines."))

    # 14. Favicon -----------------------------------------------------------
    checks.append(_check(
        "Favicon", 2, page.favicon,
        "No favicon link found. A favicon improves brand recognition in "
        "browser tabs and search results."
        if not page.favicon else
        "Favicon is set."))

    # 15. Links -------------------------------------------------------------
    if page.empty_links:
        checks.append(_check(
            "Broken / empty links", 6, False,
            f"{page.empty_links} link(s) point nowhere (empty href or '#'). "
            "Fix or remove them -- they hurt user experience and crawling.",
            warning=True))
    else:
        checks.append(_check(
            "Broken / empty links", 6, True,
            f"{len(page.links)} links checked "
            f"({page.internal_links} internal, {page.external_links} external), "
            "none empty."))

    # 16. HTTPS / URL structure (only when auditing a real URL) -------------
    if page.url.startswith("http"):
        parsed = urlparse(page.url)
        checks.append(_check(
            "HTTPS", 5, parsed.scheme == "https",
            "This page is served over plain HTTP. HTTPS is a Google ranking "
            "signal and browsers warn visitors about insecure pages."
            if parsed.scheme != "https" else
            "Page is served over HTTPS."))
        checks.append(_check(
            "Clean URL", 5, len(parsed.path) <= 100 and "_" not in parsed.path,
            "URL is very long or contains underscores. Short, hyphenated URLs "
            "are easier to read and share."
            if len(parsed.path) > 100 or "_" in parsed.path else
            f"URL is short and readable ({len(parsed.path)} characters)."))

    # 17. Target keyword (optional) -----------------------------------------
    if keyword:
        keyword = keyword.lower()
        body = page.text.lower()
        count = len(re.findall(rf"\b{re.escape(keyword)}\b", body))
        density = (count / page.word_count * 100) if page.word_count else 0
        in_title = keyword in title.lower()
        in_h1 = any(keyword in text.lower()
                    for level, text in page.headings if level == 1)
        if count == 0:
            checks.append(_check(
                "Target keyword", 0, False,
                f'The keyword "{keyword}" does not appear on the page at all.'))
        elif not in_title and not in_h1:
            checks.append(_check(
                "Target keyword", 0, False,
                f'Keyword "{keyword}" appears {count} times '
                f"(density {density:.2f}%) but is missing from the title and H1. "
                "Put it in both.", warning=True))
        else:
            checks.append(_check(
                "Target keyword", 0, True,
                f'Keyword "{keyword}" appears {count} times '
                f"(density {density:.2f}%) and is in the title/H1."))

    return checks


def score(checks: list[Check]) -> tuple[int, str]:
    """Return (score 0-100, letter grade) for a list of checks."""
    total = sum(c.weight for c in checks)
    earned = sum(c.points for c in checks)
    pct = round(earned / total * 100) if total else 0
    grade = (
        "A" if pct >= 90 else "B" if pct >= 80 else "C"
        if pct >= 70 else "D" if pct >= 60 else "F"
    )
    return pct, grade


def top_issues(checks: list[Check], limit: int = 5) -> list[Check]:
    """The most important failing checks, heaviest first."""
    failed = [c for c in checks if c.status != "pass"]
    return sorted(failed, key=lambda c: c.weight, reverse=True)[:limit]
