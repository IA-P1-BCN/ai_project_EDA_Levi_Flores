"""Export an executive report (Markdown) to an A4 PDF with its embedded charts.

The Markdown file stays the single source of truth; the PDF is a rendering of it.
It is converted to HTML with ``markdown`` and printed with headless Chrome or Edge.

Two print styles are available: ``compact`` (the 1-2 page CEO report, default) and ``story``
(the narrative executive report: cover page, larger type, one chart per block).

Usage:
    python scripts/export_report_pdf.py
    python scripts/export_report_pdf.py --source reports/executive_report_es.md --output reports/executive_report_es.pdf --lang es
    python scripts/export_report_pdf.py --source reports/executive_story.md --output reports/executive_story.pdf         --style story --max-pages 12

Set ``CHROME_PATH`` if Chrome or Edge is not found automatically.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "reports" / "executive_report.md"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "executive_report.pdf"

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
BROWSER_NAMES = ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]

# Compact A4 layout so the report fits the Briefing's 1-2 page limit.
COMPACT_CSS = """
@page { size: A4; margin: 11mm 13mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 8.3pt; line-height: 1.27; color: #1a1a1a; }
h1 { font-size: 15pt; margin: 0 0 2px; color: #0b3c5d; }
h2 { font-size: 11pt; margin: 9px 0 3px; color: #0b3c5d; border-bottom: 1px solid #c8d3dd; padding-bottom: 1px; }
h3 { font-size: 9.6pt; margin: 6px 0 2px; color: #0b3c5d; }
p { margin: 2px 0 4px; }
ul { margin: 2px 0 4px; padding-left: 16px; }
li { margin: 1px 0; }
img { display: block; max-width: 72%; max-height: 45mm; margin: 3px auto; }
table { border-collapse: collapse; width: 100%; font-size: 7.3pt; margin: 3px 0 5px; }
th, td { border: 1px solid #c8d3dd; padding: 1px 4px; text-align: left; vertical-align: top; }
th { background: #eef3f7; }
code { font-family: Consolas, monospace; font-size: 7.2pt; }
h2, h3 { break-after: avoid; }
img, tr { break-inside: avoid; }
"""

# Narrative layout modelled on the course example: cover page, readable type, large charts.
STORY_CSS = """
@page { size: A4; margin: 18mm 20mm 16mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2933; }
.cover { height: 245mm; display: flex; flex-direction: column; justify-content: center; text-align: center;
  break-after: page; }
.cover .kicker { font-size: 11pt; letter-spacing: .12em; text-transform: uppercase; color: #2e6a97; }
.cover h1 { font-size: 28pt; line-height: 1.15; color: #0b3c5d; border: 0; margin: 10px 0 14px; }
.cover .subtitle { font-size: 13pt; color: #4b5563; margin-bottom: 40px; }
.cover .meta { font-size: 10pt; color: #4b5563; line-height: 1.7; }
h1 { font-size: 20pt; color: #0b3c5d; margin: 0 0 8px; }
h2 { font-size: 15pt; color: #0b3c5d; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #d6e4f0; }
h3 { font-size: 12pt; color: #1b4f72; margin: 14px 0 6px; }
p { margin: 4px 0 9px; }
ul, ol { margin: 4px 0 10px; padding-left: 22px; }
li { margin: 3px 0; }
img { display: block; width: 100%; max-height: 92mm; object-fit: contain; margin: 10px auto 4px; }
blockquote { margin: 10px 0; padding: 8px 14px; background: #eef4f9; border-left: 4px solid #1b9e77;
  color: #1f2933; }
blockquote p { margin: 2px 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 8px 0 12px; }
th, td { border: 1px solid #c8d3dd; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #eef3f7; }
code { font-family: Consolas, monospace; font-size: 9pt; }
hr { border: 0; break-after: page; }
h2, h3 { break-after: avoid; }
img, tr, blockquote { break-inside: avoid; }
"""
STYLES = {"compact": COMPACT_CSS, "story": STORY_CSS}


def find_browser() -> str:
    """Return the path of a Chromium-based browser that can print to PDF."""
    env_path = os.environ.get("CHROME_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("No Chrome or Edge found; set CHROME_PATH to the browser executable.")


def render_html(source: Path, style: str = "compact", lang: str = "en") -> str:
    """Convert the Markdown report to a standalone HTML page with print CSS."""
    text = source.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else source.stem
    base = source.parent.resolve().as_uri() + "/"
    return (
        f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>"
        f"<base href='{base}'><title>{title}</title><style>{STYLES[style]}</style></head>"
        f"<body>{body}</body></html>"
    )


def count_pages(pdf: Path) -> int:
    """Count PDF page objects (enough for a page-limit check without extra dependencies)."""
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf.read_bytes()))


def export_pdf(source: Path, output: Path, style: str = "compact", lang: str = "en") -> int:
    """Write ``output`` from ``source`` and return the number of pages."""
    browser = find_browser()
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "report.html"
        html_path.write_text(render_html(source, style, lang), encoding="utf-8")
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--allow-file-access-from-files",
                f"--user-data-dir={Path(tmp) / 'profile'}",
                f"--print-to-pdf={output.resolve()}",
                html_path.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    if not output.exists():
        raise RuntimeError(f"The browser did not write {output}")
    return count_pages(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--style", choices=sorted(STYLES), default="compact")
    parser.add_argument("--lang", default="en", help="HTML language code used for hyphenation and fonts.")
    args = parser.parse_args()

    pages = export_pdf(args.source, args.output, args.style, args.lang)
    print(f"Wrote {args.output} ({pages} page(s))")
    if pages > args.max_pages:
        print(f"ERROR: {pages} pages exceed the {args.max_pages}-page limit")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
