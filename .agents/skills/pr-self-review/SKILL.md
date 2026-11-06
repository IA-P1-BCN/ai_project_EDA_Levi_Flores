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

## 1. Local CI & Code Quality Gate (Exact Replication of `.github/workflows/ci.yml`)

Run all checks locally using the `EDA` virtual environment (`.\EDA\Scripts\python.exe`) before pushing any branch. First make sure the quality tools are installed (`ruff`, `flake8`, `pytest` are declared in `requirements.txt`):
```powershell
.\EDA\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 1: Linting with Ruff & Syntax Verification with Flake8
**Ruff is blocking locally: 0 errors before opening a PR.** CI currently runs `ruff check . --exit-zero` (warning only), so a green CI does **not** prove Ruff is clean — the local run is the gate. Settings (line length, excludes) come from `pyproject.toml`.
```powershell
.\EDA\Scripts\python.exe -m ruff check .
.\EDA\Scripts\python.exe -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.idea,EDA,venv,.venv
.\EDA\Scripts\python.exe -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.idea,EDA,venv,.venv
```

### Step 2: Top-to-Bottom Notebook Execution & `nbformat` Schema Validation
Verify that every `.ipynb` file in `notebooks/` is valid v4 JSON, has sequential `execution_count` (`1..N`) with zero traceback outputs, and executes cleanly from top to bottom:
```powershell
.\EDA\Scripts\python.exe -c "
import os, sys, nbformat
for root, _, files in os.walk('notebooks'):
    for f in files:
        if f.endswith('.ipynb'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                nb = nbformat.read(fh, as_version=4)
            nbformat.validate(nb)
            for idx, cell in enumerate(nb.cells):
                if cell.cell_type == 'code':
                    for out in cell.get('outputs', []):
                        if out.get('output_type') == 'error':
                            print(f'ERROR output in {p} cell {idx}: {out.get(\"ename\")}: {out.get(\"evalue\")}', file=sys.stderr)
                            sys.exit(1)
            print(f'VALIDATED: {p} ({len(nb.cells)} cells)')
"
```

### Step 3: Automated Unit Tests (`pytest`)
When `tests/` exists, run the full test suite:
```powershell
.\EDA\Scripts\python.exe -m pytest -v
```

### Step 4: Repository Hygiene & File Size Check (`< 15 MB`)
Confirm no `.env` files, scratch files, or oversized binaries (`> 15 MB`) are tracked by Git:
```powershell
git status --short
```

---

## 2. Analytical & Rubric Quality Gate Checklist

Before opening a Pull Request, verify compliance against [`docs/Briefing.md`](../../../docs/Briefing.md) and [`docs/Work_Plan.md`](../../../docs/Work_Plan.md):

- [ ] **100% English Compliance:** All code, comments, Markdown cells, chart titles/axes, commit messages, and PR text are written in English.
- [ ] **Raw Data Integrity:** `git diff main -- data/raw/` confirms `data/raw/messy_customer_data.csv` was never modified after initial ingestion.
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

### 3.2 Self-Review, Squash-Merge & Branch Deletion (`@levifvy`)
1. Confirm GitHub Actions CI checks (`lint-and-validate` and `repo-hygiene`) are **green**:
   ```powershell
   gh pr checks <PR_NUMBER> --repo IA-P1-BCN/ai_project_EDA_Levi_Flores
   ```
2. Perform self-review and squash-merge into `main`, deleting the remote and local branch:
   ```powershell
   gh pr merge <PR_NUMBER> --repo IA-P1-BCN/ai_project_EDA_Levi_Flores --squash --delete-branch
   git checkout main
   git pull origin main
   ```
3. Verify that all linked task issues are `CLOSED` and marked `Done` in **Project `#54`**, and update the active `[DAILY]` log issue.
