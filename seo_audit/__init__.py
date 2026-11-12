"""SEO Website Audit Tool.

Audit any web page (by URL or local HTML file) for on-page SEO issues and
get a scored report in Markdown, JSON or a styled HTML page.

Standard library only -- no third-party packages needed.

Usage (from the project root):
    python -m seo_audit https://example.com
    python -m seo_audit examples/good-page.html --keyword "seo audit"
    python -m seo_audit https://example.com --format html --output report.html
"""

__version__ = "1.0.0"
__author__ = "Hasnaat Anjum"
