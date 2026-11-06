"""Shared helpers for the CI check scripts.

Every check prints GitHub annotations (``::error file=...::``) when it runs inside GitHub Actions,
and plain ``[ERROR] ...`` lines when it runs locally, so the same script serves both places.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IN_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

# Keep output readable on Windows consoles that are not UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


def _escape(text: str) -> str:
    """Escape a message so GitHub keeps it on one annotation line."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


class Reporter:
    """Collects errors and warnings for one check and turns them into an exit code."""

    def __init__(self, check_name: str) -> None:
        self.check_name = check_name
        self.errors = 0
        self.warnings = 0

    def _emit(self, level: str, message: str, file: str | None) -> None:
        if IN_GITHUB_ACTIONS:
            location = f" file={file}" if file else ""
            print(f"::{level}{location}::{_escape(message)}")
        else:
            where = f"{file}: " if file else ""
            print(f"[{level.upper()}] {where}{message}")

    def error(self, message: str, file: str | None = None) -> None:
        self.errors += 1
        self._emit("error", message, file)

    def warning(self, message: str, file: str | None = None) -> None:
        self.warnings += 1
        self._emit("warning", message, file)

    def ok(self, message: str) -> None:
        print(f"[OK] {message}")

    def finish(self) -> int:
        status = "FAILED" if self.errors else "PASSED"
        print(f"\n{self.check_name}: {status} ({self.errors} error(s), {self.warnings} warning(s))")
        return 1 if self.errors else 0


def tracked_files() -> list[str]:
    """Return every path tracked by Git, relative to the repository root, with forward slashes."""
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, check=True, capture_output=True
    ).stdout.decode("utf-8")
    return [path for path in output.split("\0") if path]
