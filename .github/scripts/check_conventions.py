"""Artifact naming and handoff contract gate (AGENTS.md Laws 2 and 3, eda-visualization skill).

  1. Charts in ``assets/charts/`` and tables in ``data/processed/summaries/`` start with a valid
     Task ID from docs/Work_Plan.md (``e4_univariate_age.png``, ``m3_segment_aggregations.csv``).
  2. Processed datasets follow ``customers_<clean|enriched>_v<N>.csv``.
  3. PNG charts are exported at 300 DPI.
  4. Handoffs are named ``<task_id>_<agent>.md`` and contain the five required sections in order.

Usage:
    python .github/scripts/check_conventions.py
"""

from __future__ import annotations

import re
import struct
import sys

from ci_utils import REPO_ROOT, Reporter, tracked_files

TASK_ID = r"(e[1-6]|m[1-7]|a[1-7]|x[1-6])"
SLUG = r"[a-z0-9]+(_[a-z0-9]+)*"
AGENTS = r"(data-cleaner|statistical-analyst|data-viz|executive-reporter)"
RULES = [
    ("assets/charts/", re.compile(rf"^{TASK_ID}_{SLUG}\.(png|html|svg)$"), "<task_id>_<slug>.png|html|svg"),
    ("data/processed/summaries/", re.compile(rf"^{TASK_ID}_{SLUG}\.csv$"), "<task_id>_<slug>.csv"),
    ("handoffs/", re.compile(rf"^({TASK_ID}_{AGENTS}\.md|README\.md)$"), "<task_id>_<agent>.md"),
]
PROCESSED_DATASET = re.compile(r"^customers_(clean|enriched)_v\d+\.csv$")
HANDOFF_SECTIONS = ["Outputs", "Notebook Cells", "Key Findings", "Open Issues", "Verification"]
TARGET_DPI = 300
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_dpi(path) -> float | None:
    """Read the horizontal DPI from a PNG ``pHYs`` chunk, or None if the file has none."""
    with open(path, "rb") as handle:
        if handle.read(8) != PNG_SIGNATURE:
            return None
        while header := handle.read(8):
            length, chunk_type = struct.unpack(">I4s", header)
            if chunk_type == b"pHYs":
                pixels_x, _pixels_y, unit = struct.unpack(">IIB", handle.read(9))
                return pixels_x * 0.0254 if unit == 1 else None
            if chunk_type == b"IDAT":
                return None
            handle.seek(length + 4, 1)  # skip chunk data and CRC
    return None


def handoff_headings(text: str) -> list[str]:
    """Return level-2 headings outside fenced code blocks."""
    headings, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def main() -> int:
    reporter = Reporter("Naming and handoff conventions")
    checked = 0
    for rel_path in tracked_files():
        name = rel_path.rsplit("/", 1)[-1]
        if name.startswith("."):
            continue  # .gitkeep placeholders keep empty artifact directories in Git
        for prefix, pattern, expected in RULES:
            if rel_path.startswith(prefix) and "/" not in rel_path[len(prefix):]:
                checked += 1
                if not pattern.match(name):
                    reporter.error(f"name must follow {expected} (AGENTS.md Law 3)", file=rel_path)

        if rel_path.startswith("data/processed/") and rel_path.count("/") == 2 and rel_path.endswith(".csv"):
            checked += 1
            if not PROCESSED_DATASET.match(name):
                reporter.error("processed dataset must be named customers_<clean|enriched>_v<N>.csv", file=rel_path)

        if rel_path.startswith("assets/charts/") and name.endswith(".png"):
            dpi = png_dpi(REPO_ROOT / rel_path)
            if dpi is None or abs(dpi - TARGET_DPI) > 1:
                found = "no DPI metadata" if dpi is None else f"{dpi:.0f} DPI"
                reporter.error(f"chart must be exported at {TARGET_DPI} DPI (found {found})", file=rel_path)

        if rel_path.startswith("handoffs/") and name != "README.md" and name.endswith(".md"):
            headings = handoff_headings((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
            required = [h for h in headings if h in HANDOFF_SECTIONS]
            if required != HANDOFF_SECTIONS:
                reporter.error(
                    f"handoff must contain sections {HANDOFF_SECTIONS} in this order (found {required})",
                    file=rel_path,
                )

    if not reporter.errors:
        reporter.ok(f"{checked} artifact(s) follow the naming conventions")
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
