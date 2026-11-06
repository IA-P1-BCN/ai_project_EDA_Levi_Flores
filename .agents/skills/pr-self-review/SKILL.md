---
name: pr-self-review
description: >-
  Execute the mandatory pre-PR quality gate, top-to-bottom Jupyter Notebook verification, Ruff and
  Flake8 linting, pytest execution, requirements.txt check, and GitHub Projects (#54) synchronization
  before opening or squash-merging any Pull Request.
---

# Pull Request Self-Review & Quality Gate Skill (`pr-self-review`)

This skill defines the operational runbook for `QualityReviewerAgent` and the Lead Author (`@levifvy`) before opening, reviewing, or squash-merging any Pull Request into `main`.

---

## 1. Local CI & Code Quality Gate (Same Checks as `.github/workflows/ci.yml`)

All check logic lives in `.github/scripts/`, so CI and the local gate run the **same code**. Run it with the `EDA` virtual environment (`.\EDA\Scripts\python.exe`) before pushing any branch:
```powershell
.\EDA\Scripts\python.exe -m pip install -r requirements.txt
.\EDA\Scripts\python.exe .github/scripts/run_local_ci.py          # full gate (~1 min)
.\EDA\Scripts\python.exe .github/scripts/run_local_ci.py --fast   # skip notebook re-execution
```
Every step is **blocking** in CI. Ruff is pinned in `requirements.txt` so local and CI apply the same rule set; settings come from `pyproject.toml`.

| CI job | Script / command | What fails the build |
|---|---|---|
| `lint` | `ruff check .` and `flake8 --select=E9,F63,F7,F82` | Any Ruff finding (including notebooks); syntax errors or undefined names. Fix most with `ruff check . --fix`. |
| `notebooks` | `check_notebooks.py --execute` | Invalid `nbformat` v4; stored error outputs; unexecuted cells or non-sequential `execution_count` (`1..N`); a failing cell on top-to-bottom re-execution; a CSV in `data/processed/` that changes on re-run (stale or non-deterministic) or is produced but not committed. |
| `tests` | `pytest` | Any failing test. Skipped with a notice until `tests/test_*.py` exists (`X3`). |
| `data-contract` | `check_data_contract.py` | `customers_clean_*.csv` breaking `specs/ontology.md`: missing columns, row count ≠ 10,000, non-sequential `customer_id`, values outside taxonomy or bounds, leaked raw sentinels, invalid email/phone/dates, or flags that disagree with their ontology formula. |
| `repo-hygiene` | `check_repo_hygiene.py`, `check_conventions.py` | `data/raw/messy_customer_data.csv` or `docs/Briefing.md` changed (hash in `.github/protected-files.txt`); tracked `.env`, venv, caches or IDE files; any file `>= 15 MB`; artifacts not named `<task_id>_<slug>`; PNG charts not at 300 DPI; handoffs missing the five sections in order. |
| `pr-metadata` (`pr-governance.yml`) | `check_pr_metadata.py` | PR title not `<type>(<scope>): <summary>`; branch not `<feature\|fix\|chore\|docs\|ci\|test\|refactor\|hotfix>/<kebab-name>`; `feature/*` PR without `Closes #<id>`; empty description. |

**Re-execution note:** the `notebooks` check rewrites the notebook outputs under `data/processed/` in place. If it reports a changed CSV, inspect `git diff data/processed/` and commit the regenerated file together with the notebook.

---

## 2. Analytical & Rubric Quality Gate Checklist

Before opening a Pull Request, verify compliance against [`docs/Briefing.md`](../../../docs/Briefing.md) and [`docs/Work_Plan.md`](../../../docs/Work_Plan.md):

- [ ] **100% English Compliance:** All code, comments, Markdown cells, chart titles/axes, commit messages, and PR text are written in English.
- [ ] **Raw Data Integrity:** `check_repo_hygiene.py` confirms `data/raw/messy_customer_data.csv` matches its pinned hash in `.github/protected-files.txt`.
- [ ] **Methodological Justification:** Every cleaning, imputation, outlier treatment, or transformation decision explains *why* it was chosen in Markdown.
- [ ] **Visual Rigor:** Every chart has a descriptive title, sample size ($n$), named axes with units, legend where needed, and written interpretation.
- [ ] **Dependency Sync:** Any newly imported third-party package (e.g., `streamlit`, `pytest`) is declared in `requirements.txt`.

---

## 3. Pull Request Lifecycle & GitHub Project (`#54`) Synchronization

### 3.1 Opening the Pull Request
1. Push the feature branch to `origin`:
   ```powershell
   git push -u origin <branch-name>
   ```
2. Create the PR using `.github/pull_request_template.md`, linking all resolved task issues via `Closes #<issue-number>`:
   ```powershell
   gh pr create --repo IA-P1-BCN/ai_project_EDA_Levi_Flores --base main --head <branch-name> --assignee levifvy --milestone "<Milestone>" --title "<type>(<scope>): <summary>" --body-file <pr_body.md>
   ```
3. Move all linked task issues in **Project `#54` (`EDA Project — Customer Messy Data`)** to `Status = "In Review"` and set `Pull Request = <PR_URL>`:
   ```powershell
   gh project item-edit 54 --owner IA-P1-BCN --url https://github.com/IA-P1-BCN/ai_project_EDA_Levi_Flores/issues/<N> --field "Status" --value "In Review"
   gh project item-edit 54 --owner IA-P1-BCN --url https://github.com/IA-P1-BCN/ai_project_EDA_Levi_Flores/issues/<N> --field "Pull Request" --text "<PR_URL>"
   ```

### 3.2 Self-Review, Squash-Merge & Local Branch Cleanup (`@levifvy`)
1. Confirm every GitHub Actions check (`lint`, `notebooks`, `tests`, `data-contract`, `repo-hygiene`, `pr-metadata`) is **green**:
   ```powershell
   gh pr checks <PR_NUMBER> --repo IA-P1-BCN/ai_project_EDA_Levi_Flores
   ```
2. Perform self-review and squash-merge into `main`. **Never pass `--delete-branch` and never delete remote branches**: the professor audits them. Delete only the local branch:
   ```powershell
   gh pr merge <PR_NUMBER> --repo IA-P1-BCN/ai_project_EDA_Levi_Flores --squash
   git checkout main
   git pull origin main
   git branch -D <branch-name>   # local only; -D because squash merges are not ancestors of main
   ```
3. Verify that all linked task issues are `CLOSED` and marked `Done` in **Project `#54`**, and update the active `[DAILY]` log issue.
