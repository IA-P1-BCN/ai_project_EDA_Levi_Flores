# 📊 Exploratory Data Analysis (EDA) — Customer Messy Data

![Project Banner](assets/minidatathon.PNG)

Welcome to the **`ai_project_EDA_Levi_Flores`** repository!

This project simulates a real-world data consulting engagement performing an end-to-end **Exploratory Data Analysis (EDA)** on a dirty customer dataset (**"Customer Messy Data"**). The objective is not merely to clean records, but to diagnose structural data quality flaws, uncover actionable patterns, and deliver executive-ready visualisations and strategic insights.

> 📌 **Academic Briefing:** The original project specification is preserved intact in [`docs/Briefing.md`](docs/Briefing.md). The detailed operational schedule and task breakdown are documented in [`docs/Work_Plan.md`](docs/Work_Plan.md).

---

## 📑 Deliverables

| Deliverable | Level | File |
|---|---|---|
| 💻 **Interactive Executive Dashboard** (Streamlit app: segment filters, KPI scorecards, one tab per business question, data-quality audit, methodology, CSV export) | Expert (`X2`) | [`app/dashboard.py`](app/dashboard.py) · Launch: `streamlit run app/dashboard.py` |
| 🎙️ **5-Minute Storytelling Script** (Executive presentation script for non-technical audience) | Expert (`X5`) | [`reports/presentation.md`](reports/presentation.md) |
| 📄 **CEO Executive Report** (1–2 pages, conclusions and supporting charts) | Medium (`M7`) | [**PDF**](reports/executive_report.pdf) · [Markdown](reports/executive_report.md) |
| 🛡️ **Data Quality Audit Report** (Forensic quality audit, sentinels & flag catalog) | Expert (`X4`) | [`reports/data_quality_report.md`](reports/data_quality_report.md) |
| 🧪 **Automated Pipeline & Test Suite** (End-to-end CLI pipeline & pytest unit tests) | Expert (`X1`, `X3`) | `python -m src.pipeline` · [`tests/`](tests/) |
| 📓 **EDA Notebook** (cleaning, analysis, charts, interpretations) | Essential → Expert | [`notebooks/01_eda_customers.ipynb`](notebooks/01_eda_customers.ipynb) |
| 📊 **Charts** (300 DPI, named by task ID) | Essential → Expert | [`assets/charts/`](assets/charts/) |
| 🧹 **Clean & enriched datasets** | Essential → Expert | [`data/processed/`](data/processed/) |

> The PDF is generated from the Markdown source with `python scripts/export_report_pdf.py`, which fails if the report exceeds 2 pages.

---

## 🗂️ Dataset Attribution & Metadata

| Property | Details |
|---|---|
| **Dataset Title** | **Customer Messy Data** (`messy_customer_data.csv`) |
| **Source / URL** | [Kaggle — Customer Messy Data (`ruchikakumbhar1806/customer-messy-data`)](https://www.kaggle.com/datasets/ruchikakumbhar1806/customer-messy-data) |
| **Download Date** | `2026-11-05` |
| **Dimensions** | `10,000` rows × `12` columns |
| **Licence / Attribution** | Public dataset on Kaggle by author *Ruchika Kumbhar* (used for educational & exploratory data analysis purposes). |
| **Local Raw Path** | `data/raw/messy_customer_data.csv` *(read-only, never modified in place)* |
| **Processed Data Path** | `data/processed/customers_clean_v1.csv` *(generated deterministically by notebooks / pipeline)* |

---

## 👥 Operating Model & Roles

| Role | Responsibilities |
|---|---|
| **Author / Sole Developer (`@levifvy`)** | Levi Flores — owns all branches, commits, notebooks, Pull Requests, self-reviews, approvals and squash-merges. |
| **Professor (Read-Only Auditor)** | Observes development progress, GitHub Projects boards, commit history and AI-assisted workflows. **Does not approve or merge Pull Requests.** |
| **Language Policy** | All repository artifacts (code, notebooks, Markdown documentation, chart labels, commits, Issues and PRs) are written in **English**. |

---

## ⚙️ Execution Environment

To ensure full reproducibility, the project uses an isolated Python virtual environment:

- **Virtual Environment Name:** `EDA`
- **Python Version:** `Python 3.12.10` (`3.12.x`)

### 🔌 Activating the Virtual Environment

#### Windows (PowerShell):
```powershell
.\EDA\Scripts\Activate.ps1
```

#### Windows (CMD):
```cmd
.\EDA\Scripts\activate.bat
```

#### Linux / macOS:
```bash
source EDA/bin/activate
```

### 📦 Installing Dependencies
```bash
pip install -r requirements.txt
```

### 🚀 Quickstart & Execution Commands

```bash
# 1. Launch the interactive Streamlit executive dashboard (X2); theme lives in .streamlit/config.toml
streamlit run app/dashboard.py

# 2. Execute the reproducible end-to-end data pipeline (X1)
python -m src.pipeline            # options: --quiet, --skip-summaries, --raw-path, --output-dir, --summary-dir

# 3. Execute the automated unit test suite (X3, TDD)
pytest

# 4. Replay the full CI quality gate locally (Ruff, Flake8, nbformat, ontology contract, hygiene)
python .github/scripts/run_local_ci.py

# 5. Open and execute the primary EDA notebook
jupyter notebook notebooks/01_eda_customers.ipynb
```

### 📋 Project #54 Automation
Task and daily issues created from the templates are added to Project `#54` automatically. Their `Status` then follows the Pull Request (GitHub Flow: every PR targets `main`):

| Event | Task issue linked with `Closes #N` | Daily log |
|---|---|---|
| Issue created from template | Added to the project, `Backlog` | Added to the project, `Backlog` |
| Draft PR opened | `In Progress` + `Branch` + `Pull Request` | — |
| PR ready for review | `In Review` | — |
| PR squash-merged into `main` | Issue closed by GitHub, `Done` | Merge recorded as a comment on that day's log |
| PR closed without merge | `In Progress` | — |
| Every morning (06:00 Madrid) | — | Today's log → `In Progress`; earlier open logs → `Done` and closed |

PR-driven updates run in `.github/workflows/project-sync.yml` and need the repository secret `PROJECT_TOKEN` (a fine-grained token with organization **Projects: Read and write** and repository **Issues: Read and write**, **Pull requests: Read-only**). The project's built-in workflows *Item added*, *Item reopened*, *Item closed* and *Auto-close issue* are enabled in the project settings as a second layer.

### 🪝 Enabling the GitHub Flow Git Hooks (once per clone)
```bash
git config core.hooksPath .githooks
```
The hooks in `.githooks/` block, before anything reaches GitHub: commits on `main`, pushes to `main`, deleting remote branches (they are the professor's audit trail), and force-pushes. They are a local safety net for both the author and the AI agents.

---

## 🔀 Workflow: Simplified GitHub Flow

1. **`main` changes only through Pull Requests:** `main` is always stable and executable, and every change enters via a Pull Request with green CI checks. Branch protection is not available for private repositories on the GitHub Free plan, so the rule is enforced by repository settings (squash merge only) and audited by the `Main Guard` workflow, which turns red if a commit reaches `main` without a squash-merged PR.
2. **Short-lived feature branches:** One branch per delivery block (`feature/01-data-loading-and-cleaning`, `feature/02-essential-analysis`, etc.), created from an up-to-date `main`.
3. **Self-review & Squash Merge:** Once CI passes and the Definition of Done checklist is complete, the author (`@levifvy`) performs a self-review, squash-merges the PR into `main`, and deletes the merged branch **locally only**. Remote branches are **kept** so the professor can audit how the project evolved.

```bash
# 1. Start from an up-to-date main branch
git checkout main
git pull origin main

# 2. Create the short-lived feature branch
git checkout -b feature/01-data-loading-and-cleaning

# 3. Review what changed, then stage explicit paths (never `git add .`)
git status
git add src/cleaning.py src/pipeline.py tests/test_cleaning.py
git commit -m "feat(eda): load dataset, diagnose quality and export clean v1"

# 4. Push and open Pull Request
git push -u origin feature/01-data-loading-and-cleaning
```

---

## 📂 Repository Structure

```text
ai_project_EDA_Levi_Flores/
│
├── .agents/                      # Canonical skills (single source of truth for all engines)
│   ├── README.md                 # Skill index and discovery rules
│   └── skills/                   # data-cleaning, statistical-analysis, eda-visualization,
│                                 # executive-reporting, pr-self-review
│
├── .claude/                      # Claude Code wiring (thin pointers to .agents/skills)
│   ├── agents/                   # Five subagent definitions
│   └── skills/                   # Pointer SKILL.md files (never edited directly)
│
├── .opencode/                    # OpenCode-native subagents with write-zone permissions
│   └── agents/                   # data-cleaner, statistical-analyst, data-viz,
│                                 # executive-reporter, quality-reviewer
│
├── .github/                      # GitHub automation and project governance
│   ├── ISSUE_TEMPLATE/           # Structured YAML forms for Tasks and Daily Logs
│   ├── workflows/                # CI gate (ci.yml), PR governance, Main Guard (main-guard.yml)
│   ├── scripts/                  # CI check scripts; run_local_ci.py replays the gate locally
│   └── pull_request_template.md  # Pull Request checklist and review template
│
├── app/                          # Interactive Streamlit executive dashboard (task X2)
│
├── assets/                       # Visual assets and project banner
│   ├── charts/                   # Exported figures: <task_id>_<slug>.png / .html
│   └── minidatathon.PNG
│
├── data/                         # Dataset storage
│   ├── raw/                      # Original immutable CSV (messy_customer_data.csv)
│   ├── external/                 # Optional enrichment tables (task A2)
│   └── processed/                # Cleaned and feature-engineered datasets
│       └── summaries/            # Exported summary tables: <task_id>_<slug>.csv
│
├── docs/                         # Project documentation and planning
│   ├── Briefing.md               # Original academic specification (untouched)
│   ├── Work_Plan.md              # Sprint schedule, task breakdown (E1–X6) and branch plan
│   ├── agents/                   # Agent system map and spec-driven development workflow
│   │   ├── README.md
│   │   └── SPEC_DRIVEN_DEVELOPMENT.md
│   └── project/                  # GitHub Projects v2 setup and issue backlog
│       ├── PROJECT_SETUP.md
│       └── ISSUE_BACKLOG.md
│
├── handoffs/                     # Per-task agent handoffs: <task_id>_<agent>.md
│
├── notebooks/                    # Jupyter Notebooks for Exploratory Data Analysis
│   └── 01_eda_customers.ipynb    # Complete EDA notebook (Essential, Medium, Advanced & Expert levels)
│
├── reports/                      # Data quality report, CEO report and presentation script
│   ├── data_quality_report.md    # ISO/DAMA data quality audit report (X4)
│   ├── executive_report.md       # CEO executive report (M7), source of truth
│   ├── executive_report.pdf      # Same report as a 2-page PDF (scripts/export_report_pdf.py)
│   └── presentation.md           # 5-minute storytelling presentation script (X5)
├── specs/                        # Domain specification
│   ├── README.md                 # Spec index and change-control rules
│   └── ontology.md               # Single source of truth: schema, flags, features, KPIs
│
├── src/                          # Reusable, type-hinted Python modules
│   ├── cleaning.py               # Sentinel remediation and data-quality flags
│   ├── pipeline.py               # CLI orchestration for the cleaning pipeline
│   ├── features.py               # Engineered features from specs/ontology.md §3.2
│   ├── analysis.py               # Statistics, outliers and segment aggregations
│   └── visualization.py          # Publication-grade chart builders
│
├── tests/                        # pytest suite and shared fixtures
│
├── AGENTS.md                     # Multi-agent governance, personas and concurrency laws
├── opencode.jsonc                # OpenCode project configuration
├── EDA/                          # Local Python 3.12 virtual environment (git-ignored)
├── .gitignore                    # Git exclusion rules
├── requirements.txt              # Python package dependencies
└── README.md                     # Main project documentation
```

---

## 🤖 AI-Assisted Development (Agents, Subagents & SDD)

The repository is built **spec-first** and can be driven by three interchangeable engines: **OpenCode**, **Claude Code** and **Google Antigravity (Gemini Argon)**. All of them read the same governance file and the same skills.

### The four sources of truth

| Artifact | Question it answers |
|---|---|
| [`AGENTS.md`](AGENTS.md) | How do humans and agents collaborate? (personas, write zones, concurrency laws) |
| [`specs/ontology.md`](specs/ontology.md) | What does each column, flag, feature and KPI mean? |
| [`docs/Work_Plan.md`](docs/Work_Plan.md) | What is in scope, in which order and on which branch? |
| [`.github/scripts/`](.github/scripts/) | How is the specification enforced automatically? |

### Five specialist subagents

| Subagent | Owns | Tasks |
|---|---|---|
| `DataCleanerAgent` | `src/cleaning.py`, `src/pipeline.py`, cleaned datasets, audit tables, data quality report | E1–E3, M1, A3, A7, X1, X4 |
| `StatisticalAnalystAgent` | `src/analysis.py`, `src/features.py`, enrichment, summary tables | E4–E6, M2–M6, A1, A2, A4 |
| `DataVizAgent` | `src/visualization.py`, `app/dashboard.py`, `assets/charts/` | E4–E5, M2, M5–M6, A4–A6, X2 |
| `ExecutiveReporterAgent` | `reports/executive_report.md`, `reports/presentation.md` | E6, M7, X5, X6 |
| `QualityReviewerAgent` | `tests/`, the pre-PR gate report | X3 + every PR |

Each subagent has a **deny-by-default** permission set: it can read the whole repository and run Python/lint tools, but it can only *edit* inside its own write zone, and it can never run state-changing Git commands. Git, notebooks and Pull Requests stay with the Lead Orchestrator.

### Where things live

- **Canonical skills:** [`.agents/skills/`](.agents/skills/) — edit only here. [`.claude/skills/`](.claude/skills/) contains pointers.
- **OpenCode subagents:** [`.opencode/agents/`](.opencode/agents/) — native definitions with permissions.
- **Claude Code subagents:** [`.claude/agents/`](.claude/agents/) — persona preloads.
- **Operational map:** [`docs/agents/README.md`](docs/agents/README.md).
- **Spec-driven workflow:** [`docs/agents/SPEC_DRIVEN_DEVELOPMENT.md`](docs/agents/SPEC_DRIVEN_DEVELOPMENT.md).

### Fan-out / fan-in

1. **Fan-out:** subagents work in parallel on separate Task IDs, writing code, summary tables, charts and a handoff in `handoffs/<task_id>_<agent>.md`.
2. **Fan-in:** only the Lead Orchestrator assembles and executes `notebooks/01_eda_customers.ipynb` from the handoffs and opens the Pull Request.

Dependency order for shared tasks: **Data Cleaner → Statistical Analyst → Data Viz → Executive Reporter**.

### Pre-PR gate

```powershell
.\EDA\Scripts\python.exe -m pip install -r requirements.txt
.\EDA\Scripts\python.exe .github/scripts/run_local_ci.py
```

The gate runs Ruff, Flake8, `nbformat` validation, notebook execution, the `data/processed/` reproducibility check, the ontology data contract, repository hygiene, artifact naming and `pytest` (when `tests/test_*.py` exists). Every check is blocking in CI.
