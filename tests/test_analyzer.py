"""Tests for the SEO Website Audit Tool (standard library unittest)."""

import unittest

from seo_audit.analyzer import parse_html
from seo_audit.checks import run_checks, score
from seo_audit.reporters import to_json, to_markdown


GOOD = """
<!DOCTYPE html><html lang="en"><head>
<title>Handmade Soap Shop - Natural, Organic Soap Bars in Pakistan</title>
<meta name="description" content="Shop handmade natural soap bars made with organic oils and shea butter. Free delivery across Pakistan on orders over Rs. 1500.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://example.com/shop">
<link rel="icon" href="/favicon.ico">
<meta property="og:title" content="Soap">
<meta property="og:description" content="Soap">
<meta property="og:image" content="https://example.com/soap.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{"@type": "Product"}</script>
</head><body>
<h1>Handmade Natural Soap Bars</h1>
<p>""" + "word " * 400 + """</p>
<h2>Why handmade</h2><p>Text.</p>
<img src="a.jpg" alt="Lavender soap bar">
<a href="/shop">Shop</a>
<a href="https://facebook.com/example">Facebook</a>
</body></html>
"""

BAD = """
<!DOCTYPE html><html><head><title>Shop</title></head><body>
<h1>Welcome</h1><h1>Again</h1><h4>Deals</h4>
<p>Buy now.</p>
<img src="a.jpg"><a href="#">Click</a>
</body></html>
"""


class TestAnalyzer(unittest.TestCase):
    def test_title_and_meta_parsed(self):
        page = parse_html(GOOD, url="https://example.com/shop")
        self.assertTrue(page.title.startswith("Handmade Soap"))
        self.assertIn("description", page.meta)
        self.assertEqual(page.lang, "en")
        self.assertEqual(page.canonical, "https://example.com/shop")
        self.assertTrue(page.favicon)
        self.assertTrue(page.has_json_ld)

    def test_headings_and_images(self):
        page = parse_html(GOOD)
        self.assertEqual(page.h1_count, 1)
        self.assertEqual(page.images_missing_alt, 0)
        self.assertEqual(page.internal_links, 1)
        self.assertEqual(page.external_links, 1)

    def test_word_count(self):
        page = parse_html(GOOD)
        self.assertGreaterEqual(page.word_count, 400)

    def test_bad_page_detection(self):
        page = parse_html(BAD)
        self.assertEqual(page.h1_count, 2)
        self.assertEqual(page.images_missing_alt, 1)
        self.assertEqual(page.empty_links, 1)


class TestChecks(unittest.TestCase):
    def test_good_page_scores_high(self):
        page = parse_html(GOOD, url="https://example.com/shop")
        checks = run_checks(page, keyword="soap")
        pct, grade = score(checks)
        self.assertGreaterEqual(pct, 90)
        self.assertEqual(grade, "A")

    def test_bad_page_scores_low(self):
        page = parse_html(BAD, url="http://example.com/shop")
        checks = run_checks(page)
        pct, grade = score(checks)
        self.assertLess(pct, 60)
        self.assertEqual(grade, "F")

    def test_missing_title_fails(self):
        page = parse_html("<html><body><p>hi</p></body></html>")
        by_name = {c.name: c for c in run_checks(page)}
        self.assertEqual(by_name["Title tag"].status, "fail")
        self.assertEqual(by_name["Meta description"].status, "fail")
        self.assertEqual(by_name["H1 heading"].status, "fail")

    def test_keyword_check(self):
        page = parse_html(GOOD, url="https://example.com/shop")
        checks = run_checks(page, keyword="soap")
        by_name = {c.name: c for c in checks}
        self.assertEqual(by_name["Target keyword"].status, "pass")

        page2 = parse_html(GOOD, url="https://example.com/shop")
        checks2 = run_checks(page2, keyword="unicorn")
        by_name2 = {c.name: c for c in checks2}
        self.assertEqual(by_name2["Target keyword"].status, "fail")

    def test_noindex_flagged(self):
        html = GOOD.replace("</head>", '<meta name="robots" content="noindex">\n</head>')
        page = parse_html(html)
        by_name = {c.name: c for c in run_checks(page)}
        self.assertEqual(by_name["Indexable"].status, "fail")


class TestReporters(unittest.TestCase):
    def test_markdown_report(self):
        page = parse_html(GOOD, url="https://example.com/shop")
        checks = run_checks(page)
        pct, grade = score(checks)
        report = to_markdown(page, checks, pct, grade)
        self.assertIn("SEO Audit Report", report)
        self.assertIn(str(pct), report)

    def test_json_report_is_valid(self):
        import json

        page = parse_html(GOOD, url="https://example.com/shop")
        checks = run_checks(page)
        pct, grade = score(checks)
        report = json.loads(to_json(page, checks, pct, grade))
        self.assertEqual(report["score"], pct)
        self.assertEqual(len(report["checks"]), len(checks))


if __name__ == "__main__":
    unittest.main()
