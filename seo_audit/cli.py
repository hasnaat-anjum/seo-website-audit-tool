"""Command-line interface for the SEO Website Audit Tool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import parse_html
from .checks import run_checks, score, top_issues
from .fetcher import FetchError, fetch_url
from .reporters import to_html, to_json, to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo-audit",
        description="Audit a web page for on-page SEO issues and get a scored report.",
    )
    parser.add_argument(
        "source",
        help="URL (https://example.com) or path to a local HTML file.",
    )
    parser.add_argument(
        "--keyword", "-k", default="",
        help='Target keyword to check, e.g. --keyword "handmade soap".',
    )
    parser.add_argument(
        "--format", "-f", choices=["text", "markdown", "json", "html"],
        default="text", help="Report format (default: text).",
    )
    parser.add_argument(
        "--output", "-o", default="",
        help="Write the report to this file instead of printing it.",
    )
    return parser


def load_source(source: str) -> tuple[str, str]:
    """Return (html, display_url) for a URL or a local file path."""
    path = Path(source)
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    # Not a file: treat it as a URL.
    return fetch_url(source), source


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        html_text, display_url = load_source(args.source)
    except FetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: cannot read {args.source}: {exc}", file=sys.stderr)
        return 1

    page = parse_html(html_text, url=display_url)
    checks = run_checks(page, keyword=args.keyword)
    pct, grade = score(checks)

    if args.format == "json":
        report = to_json(page, checks, pct, grade)
    elif args.format == "markdown":
        report = to_markdown(page, checks, pct, grade)
    elif args.format == "html":
        report = to_html(page, checks, pct, grade)
    else:
        report = to_markdown(page, checks, pct, grade)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report saved to {args.output}")
    else:
        print(report)

    # Always show the top fixes on stderr-free stdout summary for text runs.
    if args.format == "text" and not args.output:
        print("\nTop fixes:")
        for issue in top_issues(checks):
            print(f"  - {issue.name}: {issue.message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
