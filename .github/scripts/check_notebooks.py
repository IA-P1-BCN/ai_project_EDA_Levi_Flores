"""Notebook quality gate (pr-self-review skill, Step 2).

Checks every tracked ``.ipynb``:
  1. valid nbformat v4 schema;
  2. no stored error outputs;
  3. every non-empty code cell executed, with sequential execution counts 1..N
     (proof of a clean ``Kernel > Restart & Run All``);
  4. file size below a soft limit (embedded images bloat the repository).

With ``--execute`` it also re-runs each notebook top to bottom in its own folder and checks
reproducibility: CSV files under ``data/processed/`` must be byte-identical before and after
the run, and the run must not create processed files that are missing from the repository.

Usage:
    python .github/scripts/check_notebooks.py [--execute] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import nbformat
from ci_utils import REPO_ROOT, Reporter, tracked_files

NOTEBOOK_SOFT_LIMIT_MB = 5
EXECUTION_TIMEOUT_SECONDS = 600
REPRODUCIBLE_DIR = REPO_ROOT / "data" / "processed"


def check_structure(nb: nbformat.NotebookNode, rel_path: str, reporter: Reporter) -> None:
    """Check stored outputs and execution order of an already-saved notebook."""
    if not nb.metadata.get("kernelspec"):
        reporter.warning("notebook has no kernelspec metadata", file=rel_path)

    for index, cell in enumerate(nb.cells):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                reporter.error(
                    f"cell {index} stores an error output ({output.get('ename')}: {output.get('evalue')})",
                    file=rel_path,
                )

    code_cells = [cell for cell in nb.cells if cell.cell_type == "code" and cell.source.strip()]
    counts = [cell.execution_count for cell in code_cells]
    never_run = sum(count is None for count in counts)
    if never_run:
        reporter.error(
            f"{never_run} of {len(counts)} code cells were never executed; run Kernel > Restart & Run All",
            file=rel_path,
        )
    elif counts != list(range(1, len(counts) + 1)):
        reporter.error(
            f"execution counts are not sequential 1..{len(counts)} (found {counts}); "
            "run Kernel > Restart & Run All before committing",
            file=rel_path,
        )


def snapshot(directory: Path) -> dict[str, str]:
    """Map every file under ``directory`` to its SHA-256 digest."""
    if not directory.exists():
        return {}
    return {
        path.relative_to(REPO_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def execute(nb: nbformat.NotebookNode, path: Path, rel_path: str, output_dir: Path | None, reporter: Reporter) -> None:
    """Run the notebook top to bottom from its own folder, as Jupyter would."""
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    client = NotebookClient(
        nb,
        timeout=EXECUTION_TIMEOUT_SECONDS,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    try:
        client.execute()
        reporter.ok(f"executed top to bottom: {rel_path}")
    except CellExecutionError as exc:
        summary = str(exc).strip().splitlines()
        reporter.error(f"execution failed: {summary[-1] if summary else exc}", file=rel_path)
    finally:
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            nbformat.write(nb, output_dir / path.name)


def check_reproducibility(before: dict[str, str], after: dict[str, str], reporter: Reporter) -> None:
    """Compare ``data/processed/`` before and after executing the notebooks."""
    errors_before = reporter.errors
    for rel_path, digest in after.items():
        if rel_path not in before:
            reporter.error("notebook creates this file but it is not committed", file=rel_path)
        elif before[rel_path] != digest:
            if rel_path.endswith(".csv"):
                reporter.error(
                    "re-running the notebook changes this CSV: the committed version is stale "
                    "or the pipeline is not deterministic (AGENTS.md Law 3)",
                    file=rel_path,
                )
            else:
                reporter.warning("re-running the notebook changes this file", file=rel_path)
    if reporter.errors == errors_before:
        reporter.ok("data/processed/ is reproducible from the notebooks")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true", help="re-run notebooks and check reproducibility")
    parser.add_argument("--output-dir", type=Path, help="where to save executed copies (default: not saved)")
    args = parser.parse_args()

    reporter = Reporter("Notebook checks")
    notebooks = [p for p in tracked_files() if p.endswith(".ipynb")]
    if not notebooks:
        reporter.ok("no tracked notebooks")
        return reporter.finish()

    before = snapshot(REPRODUCIBLE_DIR) if args.execute else {}
    for rel_path in notebooks:
        path = REPO_ROOT / rel_path
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > NOTEBOOK_SOFT_LIMIT_MB:
            reporter.warning(f"notebook is {size_mb:.1f} MB; consider clearing large image outputs", file=rel_path)
        try:
            nb = nbformat.read(path, as_version=4)
            nbformat.validate(nb)
        except Exception as exc:  # noqa: BLE001 - any parse or schema error must be reported, not raised
            reporter.error(f"invalid notebook: {exc}", file=rel_path)
            continue

        errors_before = reporter.errors
        check_structure(nb, rel_path, reporter)
        if reporter.errors == errors_before:
            reporter.ok(f"valid, {len(nb.cells)} cells, clean sequential outputs: {rel_path}")
        if args.execute:
            execute(nb, path, rel_path, args.output_dir, reporter)

    if args.execute:
        check_reproducibility(before, snapshot(REPRODUCIBLE_DIR), reporter)
    return reporter.finish()


if __name__ == "__main__":
    sys.exit(main())
