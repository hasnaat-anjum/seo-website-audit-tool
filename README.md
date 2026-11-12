# SEO Website Audit Tool

Audit any web page for on-page SEO issues and get a clear, scored report — in seconds, with no sign-up and no API key.

Built for **freelancers, sellers, marketers and small business owners** who want to know exactly why a page is not ranking on Google — and what to fix first.

## What it does

Give it a URL or a local HTML file and it checks 18 on-page SEO factors:

| Area | What is checked |
|---|---|
| Title & description | Present, and the right length (30–60 / 120–160 characters) |
| Headings | Exactly one H1, headings in the right order |
| Images | Every image has alt text |
| Content | At least 300 words of useful content |
| Mobile | Viewport tag present (Google ranks mobile-first) |
| Sharing | Open Graph + Twitter card tags |
| Structured data | Schema.org JSON-LD for rich results |
| Technical | Canonical URL, language attribute, favicon, HTTPS, clean URL |
| Links | Empty/broken links, internal vs external count |
| Keyword | Optional target keyword — is it in the title, H1 and body? |

Each check is scored, and you get a total **score out of 100 with a grade (A–F)** plus a prioritised list of fixes.

## Who it benefits

- **Freelancers** — audit a client's site in a minute and hand them a professional report.
- **Online sellers** — check product pages before launch so they rank from day one.
- **Marketers & small business owners** — find the quick SEO wins on your own website without hiring an agency.

## Installation

Python 3.8+ is all you need. **No third-party packages required** — the tool uses only the Python standard library.

```bash
git clone https://github.com/hasnaat-anjum/seo-website-audit-tool.git
cd seo-website-audit-tool
```

## How to use

Audit a live website:

```bash
python -m seo_audit https://example.com
```

Audit a local HTML file:

```bash
python -m seo_audit examples/good-page.html
```

Check a target keyword at the same time:

```bash
python -m seo_audit https://example.com --keyword "handmade soap"
```

### Report formats

```bash
# Markdown report (default, good for pasting into a doc)
python -m seo_audit https://example.com --format markdown

# JSON report (good for scripts and CI pipelines)
python -m seo_audit https://example.com --format json

# Styled HTML report you can send to a client
python -m seo_audit https://example.com --format html --output report.html
```

## Demo

Two sample pages are included in `examples/`:

```bash
python -m seo_audit examples/good-page.html   # Score: 100/100 (Grade A)
python -m seo_audit examples/bad-page.html    # Score: 19/100 (Grade F)
```

## Example output

```
# SEO Audit Report — examples/bad-page.html

**Score: 19/100 (Grade F)** — 1/15 checks passed.

- ⚠️ Title tag (5/10) — Title is only 4 characters ("Shop"). Aim for 30-60.
- ❌ Meta description (0/10) — No meta description. Add one to control the snippet shown in search results.
- ⚠️ H1 heading (4/8) — Found 2 H1 headings. Use exactly one H1 per page.
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
seo-website-audit-tool/
├── seo_audit/
│   ├── __init__.py      # Package info
│   ├── __main__.py      # Lets you run: python -m seo_audit
│   ├── analyzer.py      # HTML parsing (stdlib html.parser)
│   ├── checks.py        # The 18 SEO checks + scoring
│   ├── fetcher.py       # Downloads a page over HTTP(S)
│   ├── reporters.py     # Markdown / JSON / HTML report output
│   └── cli.py           # Command-line interface
├── examples/
│   ├── good-page.html   # A page that scores 100/100
│   └── bad-page.html    # A page that scores 19/100
└── tests/
    └── test_analyzer.py # 11 unit tests (unittest)
```

## Technologies

- **Python 3** (standard library only — `html.parser`, `urllib`, `argparse`)
- No external dependencies, works fully offline on local files

## License

MIT — free to use, modify and share.
