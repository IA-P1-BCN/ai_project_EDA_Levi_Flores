"""Pull Request governance gate (pr-self-review skill, section 3; AGENTS.md Law 4).

Reads the PR title, body and head branch from the environment (set by the workflow, never
interpolated into shell code) and checks:
  1. the title follows Conventional Commits: ``<type>(<scope>): <summary>``;
  2. the branch follows ``<feature|fix|chore|docs|ci|test|refactor|hotfix>/<kebab-name>``;
  3. ``feature/*`` PRs link their task issue with a closing keyword (``Closes #12``);
  4. the body is filled in, and title/body look like English (warning only).

Usage (local dry run):
    PR_TITLE="feat(eda): add E4" PR_BRANCH="feature/02-essential-analysis" PR_BODY="Closes #5" \
        python .github/scripts/check_pr_metadata.py
"""

from __future__ import annotations

import os
import re
import sys

from ci_utils import Reporter

TITLE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?!?: \S.{2,}$"
)
BRANCH = re.compile(r"^(feature|fix|chore|docs|ci|test|refactor|hotfix)/[a-z0-9][a-z0-9._-]*$")
CLOSING_KEYWORD = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#\d+", re.IGNORECASE)
# Characters and words that only appear in Spanish text; the project policy is 100% English.
SPANISH_HINT = re.compile(r"[ñ¿¡]|\b(el|los|las|del|para|con|una|análisis|datos)\b", re.IGNORECASE)
MIN_BODY_CHARS = 80


def main() -> int:
    reporter = Reporter("Pull Request metadata")
    title = os.environ.get("PR_TITLE", "").strip()
    body = os.environ.get("PR_BODY", "") or ""
    branch = os.environ.get("PR_BRANCH", "").strip()

    if TITLE.match(title):
        reporter.ok(f"title follows Conventional Commits: {title}")
    else:
        reporter.error(f"title must look like '<type>(<scope>): <summary>' (got: {title!r})")

    if BRANCH.match(branch):
        reporter.ok(f"branch name follows the convention: {branch}")
    else:
        reporter.error(f"branch must look like 'feature/<kebab-name>' or 'fix/...', 'chore/...' (got: {branch!r})")

    if CLOSING_KEYWORD.search(body):
        reporter.ok("body links an issue with a closing keyword")
    elif branch.startswith("feature/"):
        reporter.error("feature PRs must link their task issue in the body, e.g. 'Closes #12'")
    else:
        reporter.warning("no 'Closes #<issue>' found; add it if this PR resolves an issue")

    if len(body.strip()) < MIN_BODY_CHARS:
        reporter.error("PR description is empty or too short; fill in .github/pull_request_template.md")

    if SPANISH_HINT.search(f"{title}\n{body}"):
        reporter.warning("title or body may contain non-English text; project policy is 100% technical English")

    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
