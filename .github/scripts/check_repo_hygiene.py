"""Repository hygiene gate (AGENTS.md sections 5.1 and 5.2).

  1. Protected files are unchanged: their Git blob hash must match ``.github/protected-files.txt``.
     ``git hash-object`` applies the same line-ending rules as Git, so the hash is identical on
     Windows and Linux.
  2. No forbidden files are tracked (``.env``, virtual environments, caches, IDE folders, local
     Claude settings).
  3. No tracked file is 15 MB or larger.

Usage:
    python .github/scripts/check_repo_hygiene.py
"""

from __future__ import annotations

import re
import subprocess
import sys

from ci_utils import REPO_ROOT, Reporter, tracked_files

MANIFEST = REPO_ROOT / ".github" / "protected-files.txt"
MAX_FILE_MB = 15
FORBIDDEN = {
    r"(^|/)\.env($|\.)": "environment/credential file",
    r"\.env$": "environment/credential file",
    r"(^|/)(EDA|venv|\.venv|env)/": "virtual environment",
    r"(^|/)__pycache__/|\.py[cod]$": "Python bytecode cache",
    r"(^|/)\.ipynb_checkpoints/": "Jupyter checkpoint",
    r"(^|/)\.(pytest_cache|ruff_cache|mypy_cache)/": "tool cache",
    r"(^|/)\.(idea|vscode)/": "IDE settings",
    r"(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$": "OS metadata file",
    r"^\.claude/settings\.local\.json$": "personal Claude Code settings",
}


def check_protected_files(reporter: Reporter) -> None:
    entries = [
        line.split(maxsplit=1)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    for expected_hash, rel_path in entries:
        path = REPO_ROOT / rel_path
        if not path.exists():
            reporter.error("protected file was deleted", file=rel_path)
            continue
        actual = subprocess.run(
            ["git", "hash-object", rel_path], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        if actual != expected_hash:
            reporter.error("protected file was modified; it must stay read-only (AGENTS.md 5.1)", file=rel_path)
        else:
            reporter.ok(f"protected file unchanged: {rel_path}")


def check_tracked_files(reporter: Reporter) -> None:
    files = tracked_files()
    patterns = [(re.compile(pattern), label) for pattern, label in FORBIDDEN.items()]
    forbidden_found = 0
    for rel_path in files:
        for pattern, label in patterns:
            if pattern.search(rel_path):
                reporter.error(f"{label} must not be tracked; remove it with 'git rm --cached'", file=rel_path)
                forbidden_found += 1
                break
    if not forbidden_found:
        reporter.ok(f"no forbidden files among {len(files)} tracked files")

    oversized = 0
    for rel_path in files:
        path = REPO_ROOT / rel_path
        if path.is_file():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb >= MAX_FILE_MB:
                reporter.error(f"file is {size_mb:.1f} MB (limit < {MAX_FILE_MB} MB)", file=rel_path)
                oversized += 1
    if not oversized:
        reporter.ok(f"every tracked file is below {MAX_FILE_MB} MB")


def main() -> int:
    reporter = Reporter("Repository hygiene")
    check_protected_files(reporter)
    check_tracked_files(reporter)
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
