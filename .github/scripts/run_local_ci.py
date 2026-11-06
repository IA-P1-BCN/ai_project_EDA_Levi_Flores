"""Run the same quality gate as .github/workflows/ci.yml on your machine.

Usage (from the repository root, inside the EDA virtual environment):
    .\\EDA\\Scripts\\python.exe .github/scripts/run_local_ci.py          # full gate
    .\\EDA\\Scripts\\python.exe .github/scripts/run_local_ci.py --fast   # skip notebook re-execution

Note: re-execution rewrites the notebook outputs under data/processed/ in place; if a CSV changes,
the check fails and ``git diff`` shows what is stale.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from ci_utils import REPO_ROOT

PY = sys.executable
SCRIPTS = ".github/scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description="Local replica of the CI quality gate.")
    parser.add_argument("--fast", action="store_true", help="skip notebook re-execution")
    args = parser.parse_args()

    steps = [
        ("Ruff (blocking)", [PY, "-m", "ruff", "check", "."]),
        ("Flake8 syntax errors", [PY, "-m", "flake8", ".", "--count", "--select=E9,F63,F7,F82",
                                  "--show-source", "--statistics", "--exclude=.idea,EDA,venv,.venv"]),
        ("Notebooks", [PY, f"{SCRIPTS}/check_notebooks.py"] + ([] if args.fast else ["--execute"])),
        ("Data contract", [PY, f"{SCRIPTS}/check_data_contract.py"]),
        ("Repository hygiene", [PY, f"{SCRIPTS}/check_repo_hygiene.py"]),
        ("Naming and handoffs", [PY, f"{SCRIPTS}/check_conventions.py"]),
    ]
    if (REPO_ROOT / "tests").is_dir():
        steps.append(("Pytest", [PY, "-m", "pytest"]))

    results = []
    for name, command in steps:
        print(f"\n=== {name} ===", flush=True)
        results.append((name, subprocess.run(command, cwd=REPO_ROOT, check=False).returncode))

    print("\n=== Summary ===")
    for name, code in results:
        print(f"{'PASS' if code == 0 else 'FAIL'}  {name}")
    return 1 if any(code for _, code in results) else 0


if __name__ == "__main__":
    sys.exit(main())
