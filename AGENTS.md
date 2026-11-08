# 🤖 Multi-Agent Governance & Architecture Specification (`AGENTS.md`)

**Repository:** `IA-P1-BCN/ai_project_EDA_Levi_Flores`  
**Project:** Exploratory Data Analysis — Kaggle *"Customer Messy Data"* (`10,000` rows × `12` columns)  
**Sole Developer & Approver:** Levi Flores (`@levifvy`)  
**Supported AI Engines:** Google Antigravity (`Gemini Argon`), Anthropic `Claude Code`, and `OpenCode`  
**Canonical References:** [`docs/Briefing.md`](docs/Briefing.md) | [`docs/Work_Plan.md`](docs/Work_Plan.md) | [`docs/project/PROJECT_SETUP.md`](docs/project/PROJECT_SETUP.md) | [`specs/ontology.md`](specs/ontology.md)

---

## 1. Project Context & Boundaries

### 1.1 Mission Statement
Transform a highly corrupted real-world customer dataset (`data/raw/messy_customer_data.csv`) into **reproducible, statistically rigorous, executive-ready business intelligence**. Every deliverable must trace cleanly from raw data ingestion through deterministic data cleaning, univariate/bivariate exploration, outlier treatment, feature engineering, segment normalization, interactive visualization, automated testing, and executive storytelling.

### 1.2 Operating Model & Governance
| Role | Actor | Authority & Boundaries |
|---|---|---|
| **Lead Author & Approver** | Levi Flores (`@levifvy`) | Sole human owner of all branches, commits, notebooks, Pull Requests, self-reviews, approvals, and squash-merges into `main`. |
| **Academic Auditor** | Professor | **Read-only observer.** Audits GitHub Projects (`#54`), commit granularity, PR descriptions, and AI-assisted workflows. Never approves, requests changes, or merges PRs. |
| **AI Orchestrator & Subagents** | Gemini Argon (Antigravity), Claude Code, OpenCode | Execute specialized data engineering, statistical analysis, visualization, reporting, and QA tasks under strict write-zone isolation and human validation. |

### 1.3 Technical Stack & Execution Environment
- **Language Policy:** **100% Technical English** across all code, docstrings, notebook prose, chart titles/axes/annotations, commit messages, issue bodies, and PR descriptions.
- **Python Runtime:** `Python 3.12.10` inside the local isolated virtual environment `EDA` (`.\EDA\Scripts\python.exe` on Windows; `EDA/bin/python` on Linux/macOS).
- **Core Libraries:** `pandas>=2.2.0`, `numpy>=1.26.0`, `scipy>=1.12.0`, `matplotlib>=3.8.0`, `seaborn>=0.13.0`, `plotly>=5.20.0`, `nbformat>=5.9.0`, `pytest`, `ruff`, `flake8`, `streamlit`.
- **Canonical Domain Schema:** All agents MUST consult [`specs/ontology.md`](specs/ontology.md) before writing any data cleaning, imputation, filtering, or aggregation logic.

---

## 2. Multi-Engine Compatibility (`Gemini Argon` · `Claude` · `OpenCode`)

This repository is engineered so that **Google Antigravity (Gemini Argon)**, **Claude Code**, and **OpenCode** operate seamlessly as a unified agentic system:

1. **Shared Context Entrypoint:** All three engines automatically ingest this root `AGENTS.md` and resolve domain semantics from [`specs/ontology.md`](specs/ontology.md).
2. **Progressive Skill Activation (`.agents/skills/` is the single source of truth):**
   - [`data-cleaning`](.agents/skills/data-cleaning/SKILL.md): Mandatory protocol for type casting, sentinel removal, imputation, and audit table generation.
   - [`statistical-analysis`](.agents/skills/statistical-analysis/SKILL.md): Mandatory protocol for univariate/bivariate testing, IQR outlier rules, aggregations, and feature engineering.
   - [`eda-visualization`](.agents/skills/eda-visualization/SKILL.md): Mandatory publication standard for `matplotlib`, `seaborn`, and `plotly` figures exported to `assets/charts/`.
   - [`executive-reporting`](.agents/skills/executive-reporting/SKILL.md): Mandatory structure and evidence rules for the CEO report, presentation script, and research-question answers.
   - [`pr-self-review`](.agents/skills/pr-self-review/SKILL.md): Mandatory pre-PR quality gate, CI simulation, notebook execution verification, and GitHub Project `#54` sync.
3. **Engine Wiring (where each engine discovers agents and skills):**

   | Engine | Project instructions | Subagent definitions | Skill discovery |
   |---|---|---|---|
   | **Claude Code** | `AGENTS.md` (this file) | `.claude/agents/<agent>.md` | `.claude/skills/<skill>/SKILL.md` (thin pointers to `.agents/skills/`) |
   | **OpenCode** | `AGENTS.md` (this file) | `.opencode/agents/<agent>.md` (native subagents with write-zone permissions) | `.claude/skills/` and `.agents/skills/` |
   | **Antigravity / Gemini Argon** | `AGENTS.md` (this file) | Define subagents from the persona contract in Section 3 | `.agents/skills/` |

   **Rule:** Never edit a skill under `.claude/skills/`. Those files only point to `.agents/skills/`, so all engines read the same protocol. Engine-specific wiring that is not listed here must be verified against the engine's current documentation before use.
4. **Subagent Invocation Mapping:**
   - **Claude Code:** Invoke the `Agent` tool with `subagent_type` set to `data-cleaner`, `statistical-analyst`, `data-viz`, `executive-reporter`, or `quality-reviewer`. Each definition preloads its persona, skill, and write-zone; the prompt only needs the Task ID and inputs.
   - **Antigravity / Gemini Argon:** Create one subagent per persona in Section 3, passing the persona contract, its skill path, and its write-zone from Section 4.
   - **OpenCode:** Invoke the `subagent` tool with the agent ID (`data-cleaner`, `statistical-analyst`, `data-viz`, `executive-reporter`, `quality-reviewer`). Each `.opencode/agents/<agent>.md` definition preloads the persona, the skill pointer, the write-zone permissions and the handoff contract; the prompt only needs the Task ID and inputs.

---

## 3. Subagent Personas & Operational Contracts

### 3.1 `DataCleanerAgent` — Data Engineering & Quality Remediation Specialist
- **Primary Tasks:** `E1–E3`, `M1`, `A3`, `A7`, `X1`, `X4`.
- **Required Skill:** [`.agents/skills/data-cleaning/SKILL.md`](.agents/skills/data-cleaning/SKILL.md) + [`specs/ontology.md`](specs/ontology.md).
- **Core Responsibilities:**
  1. Audit raw strings and numeric distributions to separate explicit blanks (`""`) from domain sentinels (`-5` and `200` in `Age`, `-999` and `N/A` in `purchase_amount`, `-1` in `feedback_score`, `not_a_date` in `Signup_Date`, `missing` in `Last_purchase_date`, malformed emails lacking `@`, and `abc123`/`0` in `Phone_number`).
  2. Enforce `snake_case` naming, reconstruct sequential `customer_id` (`C00001`–`C10000`), standardize categorical taxonomy (`Male`, `Female`, `Unknown`), and cast dates (`%d/%m/%Y` → `datetime64[us]`, the pandas default resolution).
  3. Document explicit domain justifications (*why* keep `NaN` vs. median imputation vs. indicator flags) and own every **data-quality flag** in [`specs/ontology.md`](specs/ontology.md) §3.2 (`has_valid_email`, `has_valid_phone`, `is_date_inverted`, `is_geo_mismatch`, `is_age_missing`, `is_purchase_missing`, `feedback_score_1_to_5`, `is_score_10_spike`, `completeness_score`).
  4. Extract reusable, type-hinted, pure cleaning functions into `src/cleaning.py` and CLI orchestration into `src/pipeline.py`.
- **Exclusive Write-Zone:** `src/cleaning.py`, `src/pipeline.py`, `data/processed/customers_clean_*.csv`, `data/processed/summaries/*.csv`, `reports/data_quality_report.md`.

### 3.2 `StatisticalAnalystAgent` — Quantitative & Feature Engineering Specialist
- **Primary Tasks:** `E4–E6`, `M2–M6`, `A1`, `A2`, `A4`.
- **Required Skill:** [`.agents/skills/statistical-analysis/SKILL.md`](.agents/skills/statistical-analysis/SKILL.md) + [`specs/ontology.md`](specs/ontology.md).
- **Core Responsibilities:**
  1. Compute parametric (`mean`, `SD`) and non-parametric (`median`, `IQR`, quartiles, skewness) metrics across valid observations.
  2. Detect and treat outliers using formal Tukey IQR fences ($[Q_1 - 1.5 \times \text{IQR},\; Q_3 + 1.5 \times \text{IQR}]$), justifying retention vs. winsorization.
  3. Build multi-dimensional segment tables via `groupby`, `agg`, and `pivot_table` (`src/analysis.py`).
  4. Own every **analytical feature** in [`specs/ontology.md`](specs/ontology.md) §3.2 (`age_group`, `spend_tier`, `customer_tenure_days`, `contact_reachability_tier`, `feedback_tier`, `log_purchase_amount`) and the normalized KPI-3 metric (revenue per 1,000 customers), and integrate external enrichment tables (`data/external/`). Any new feature must be added to the ontology first (name, dtype, formula, owner) before it is used in code.
  5. Compute Pearson ($r$) and Spearman ($\rho$) correlation matrices without conflating correlation with causation.
- **Exclusive Write-Zone:** `src/analysis.py`, `src/features.py`, `data/external/*.csv`, `data/processed/customers_enriched_*.csv`, `data/processed/summaries/*.csv`.

### 3.3 `DataVizAgent` — Scientific Visualization & Interactive Dashboard Specialist
- **Primary Tasks:** `E4–E5`, `M2`, `M5–M6`, `A4–A6`, `X2`.
- **Required Skill:** [`.agents/skills/eda-visualization/SKILL.md`](.agents/skills/eda-visualization/SKILL.md).
- **Core Responsibilities:**
  1. Produce publication-grade `matplotlib` / `seaborn` static charts and interactive `plotly` visuals adhering to colorblind-safe palettes (`viridis`, `cividis`, `crest`, `flare`, or Okabe-Ito).
  2. Guarantee every figure includes: a declarative finding-oriented title, a subtitle with sample size ($n$) and scope, explicit axis labels with units (`USD ($)`, `Age (Years)`, `Share (%)`), direct data annotations (mean/median lines, outlier thresholds), and clean despined styling.
  3. Export all figures deterministically at `300 DPI` to `assets/charts/<task_id>_<slug>.png` (and interactive HTML to `assets/charts/<task_id>_<slug>.html`).
  4. Build the interactive executive `Streamlit` application in `app/dashboard.py`.
- **Exclusive Write-Zone:** `src/visualization.py`, `app/dashboard.py`, `assets/charts/*`.

### 3.4 `ExecutiveReporterAgent` — Business Strategy & Data Storytelling Specialist
- **Primary Tasks:** `E6`, `M7`, `X5`, `X6` (release notes text only; `README.md` and `requirements.txt` edits belong to the Lead Orchestrator). `X4` is owned by `DataCleanerAgent`.
- **Required Skill:** [`.agents/skills/executive-reporting/SKILL.md`](.agents/skills/executive-reporting/SKILL.md) + [`specs/ontology.md`](specs/ontology.md) + [`docs/Work_Plan.md`](docs/Work_Plan.md).
- **Core Responsibilities:**
  1. Synthesize quantitative outputs and exported charts from `assets/charts/` into C-level narratives answering the 3 core business questions (`Q1` Demographics & Geography, `Q2` Revenue & High-Value Segments, `Q3` Satisfaction, Retention & Reachability).
  2. Author the 1–2 page CEO Executive Report (`reports/executive_report.md`) and the 5-minute non-technical presentation script (`reports/presentation.md`).
  3. Quantify every claim with exact sample sizes ($n$), percentages, central tendency, and dispersion metrics, pairing each insight with an actionable business recommendation.
- **Exclusive Write-Zone:** `reports/executive_report.md`, `reports/presentation.md`.

### 3.5 `QualityReviewerAgent` — TDD, CI/CD & Reproducibility Auditor
- **Primary Tasks:** `X3`, plus continuous verification across every PR (`E1–X6`).
- **Required Skill:** [`.agents/skills/pr-self-review/SKILL.md`](.agents/skills/pr-self-review/SKILL.md).
- **Core Responsibilities:**
  1. Write `pytest` unit tests (`tests/test_cleaning.py`, `tests/test_analysis.py`) following TDD principles to verify sentinel replacement, schema contracts, idempotency, and boundary conditions.
  2. Execute the local CI gate (`.github/scripts/run_local_ci.py`): `ruff check .`, `flake8 .`, `nbformat` validation, top-to-bottom notebook execution with reproducibility check, the ontology data contract, and repository hygiene (`< 15 MB`, protected files, naming conventions).
  3. Verify Pull Request templates, issue closing keywords (`Closes #<id>`), and GitHub Project `#54` field synchronization (`Status`, `Branch`, `Pull Request`).
- **Exclusive Write-Zone:** `tests/test_*.py`, `tests/conftest.py`. (Read-only auditor over all other directories; reports findings to the Lead Orchestrator, who runs Git and `gh`.)

---

## 4. Parallel Execution & Non-Collision Protocol

To allow multiple subagents (across Antigravity, Claude Code, or OpenCode) to execute tasks **in parallel without file locks, race conditions, or `.ipynb` JSON corruption**, all agents MUST obey the **Four Laws of Concurrency**:

### Law 1 — Strict Write-Zone Partitioning
When two or more subagents run concurrently on the same workspace, each subagent may ONLY create or modify files inside its designated **Exclusive Write-Zone**. `data/processed/summaries/` is the only shared directory: each agent writes only the `<task_id>_*.csv` tables of the tasks it owns (Law 3), so two agents never write the same file:

| Subagent | Allowed Write Paths (Read/Write) | Read-Only Paths | Forbidden Write Paths |
|---|---|---|---|
| `DataCleanerAgent` | `src/cleaning.py`, `src/pipeline.py`, `data/processed/customers_clean_*.csv`, `data/processed/summaries/*.csv`, `reports/data_quality_report.md`, `handoffs/<task_id>_data-cleaner.md` | `data/raw/*`, `specs/*`, `docs/*` | `notebooks/*`, `assets/charts/*`, `tests/*` |
| `StatisticalAnalystAgent` | `src/analysis.py`, `src/features.py`, `data/external/*`, `data/processed/customers_enriched_*.csv`, `data/processed/summaries/*.csv`, `handoffs/<task_id>_statistical-analyst.md` | `data/processed/customers_clean_*.csv`, `src/cleaning.py`, `specs/*` | `data/raw/*`, `notebooks/*`, `assets/charts/*` |
| `DataVizAgent` | `src/visualization.py`, `app/dashboard.py`, `assets/charts/*`, `handoffs/<task_id>_data-viz.md` | `data/processed/*`, `src/cleaning.py`, `src/analysis.py`, `src/features.py`, `specs/*` | `data/raw/*`, `data/processed/*`, `notebooks/*` |
| `ExecutiveReporterAgent` | `reports/executive_report.md`, `reports/presentation.md`, `handoffs/<task_id>_executive-reporter.md` | `data/processed/summaries/*`, `assets/charts/*`, `handoffs/*`, `notebooks/*` | `src/*`, `data/*`, `notebooks/*` |
| `QualityReviewerAgent` | `tests/test_*.py`, `tests/conftest.py` | Entire repository (`*`) | `data/raw/*`, `src/*`, `notebooks/*`, `reports/*` |
| **Lead Orchestrator** | `notebooks/01_eda_customers.ipynb`, `README.md`, `requirements.txt`, `pyproject.toml`, Git & `gh` CLI | Entire repository (`*`) | `data/raw/messy_customer_data.csv`, `docs/Briefing.md` |

### Law 2 — Single-Writer Notebook Assembly (`01_eda_customers.ipynb`)
Jupyter Notebooks (`.ipynb`) are structured JSON files that cannot be edited concurrently by multiple processes without causing merge conflicts or invalid `nbformat` schemas.
- **Parallel Phase (Fan-Out):** Subagents execute in parallel by writing modular Python functions (`src/*.py`), summary tables (`data/processed/summaries/<task_id>.csv`), and high-resolution figures (`assets/charts/<task_id>_*.png`).
- **Handoff Contract:** Every subagent ends its task by writing `handoffs/<task_id>_<agent>.md` (e.g. `handoffs/e4_data-viz.md`) with these five sections, in this order:
  1. `## Outputs` — every file created or changed (paths only).
  2. `## Notebook Cells` — ready-to-paste cells, each fenced as ` ```python ` (code) or ` ```markdown ` (interpretation), in the order they must appear. Code cells must import from `src/` instead of duplicating logic.
  3. `## Key Findings` — 3–5 bullets, each with $n$, the metric, and the business question (`Q1`/`Q2`/`Q3`) it answers.
  4. `## Open Issues` — anything blocked, assumed, or left for another agent.
  5. `## Verification` — commands run and their result (e.g. `ruff check src/ → 0 errors`).
- **Integration Phase (Fan-In):** Once parallel subagents complete their tasks, **only the Lead Orchestrator** reads the handoffs, assembles and executes `notebooks/01_eda_customers.ipynb` top-to-bottom using `nbformat`, and validates it with `nbformat.validate()`. Handoff files are committed so the AI-assisted workflow stays auditable.

### Law 2b — Task Dependency Order
Agents sharing a task do not run blindly in parallel. Within a task, this order applies:

| Stage | Agent | Must finish before | Why |
|---|---|---|---|
| 1 | `DataCleanerAgent` | Any other agent reads the dataset | Downstream work needs a stable cleaned schema. |
| 2 | `StatisticalAnalystAgent` | `DataVizAgent` on the same Task ID | Finding-driven chart titles need the computed statistic. |
| 3 | `DataVizAgent` | `ExecutiveReporterAgent` | The reporter cites exported charts by path. |
| 4 | `ExecutiveReporterAgent` | Fan-in | Narrative closes the task. |
| any | `QualityReviewerAgent` | — | For `X3` (TDD), tests are written **before** stage 1 code; otherwise runs after fan-in. |

Shared tasks and their order: `E4`, `E5`, `M2`, `M5`, `M6`, `A4` → Statistical Analyst, then Data Viz. `E6`, `M7` → Statistical Analyst, then Executive Reporter. Different Task IDs with no shared inputs (e.g. `M2` and `M3`) may run in parallel.

### Law 3 — Artifact Naming & Idempotency
Every intermediate table or chart generated by a subagent MUST be prefixed with its official `Task ID` from [`docs/Work_Plan.md`](docs/Work_Plan.md):
- Charts: `assets/charts/e4_univariate_age_purchase.png`, `assets/charts/e5_bivariate_spend_by_segment.png`, `assets/charts/m5_correlation_heatmap.png`.
- Summary tables: `data/processed/summaries/m3_segment_aggregations.csv`, `data/processed/summaries/a3_suspicious_data_audit.csv`.
- All scripts and functions must be **100% deterministic and idempotent** (fixed `random_state = 42` whenever sampling or bootstrapping is used).

### Law 4 — Git Branch Sequencing & GitHub Project (`#54`) Sync
1. **One active feature branch per delivery block** as defined in [`docs/Work_Plan.md`](docs/Work_Plan.md):
   - `feature/01-data-loading-and-cleaning` (`E1–E3`) — *Merged (`PR #41`)*
   - `feature/02-essential-analysis` (`E4–E6`) — *Merged (`PR #53`)*
   - `feature/03-outliers-feature-engineering` (`M1–M4`) — *Merged (`PR #54`)*
   - `feature/04-correlation-trends-report` (`M5–M7`) — *Merged (`PR #55`)*
   - `feature/05-advanced-analysis` (`A1–A7`)
   - `feature/06-pipeline-and-tests` (`X1`, `X3`, `X4`)
   - `feature/07-dashboard-and-release` (`X2`, `X5`, `X6`)
2. **Parallel Subagents within a Branch:** Multiple tasks belonging to the *same* branch (e.g., `E4` Univariate, `E5` Bivariate, `E6` Research Answers inside `feature/02-essential-analysis`; or `M1`, `M2`, `M3`, `M4` inside `feature/03-outliers-feature-engineering`) may be developed in parallel by separate subagents following **Law 1** and **Law 2**.
3. **Cross-Branch Isolation:** If preparing a future block while the current PR is under review, the subagent MUST use an isolated local `git worktree` and never stage files onto the active branch. The future branch is **not pushed and no PR is opened** until the current PR is merged ([`docs/Work_Plan.md`](docs/Work_Plan.md) §5, rule 6).

---

## 5. Rules of Engagement & Safety Rails

### 5.1 Immutable Files (Strictly Read-Only)
- 🚫 **NEVER modify, overwrite, or delete `data/raw/messy_customer_data.csv`**. All transformations must read from `data/raw/` and write to `data/processed/`.
- 🚫 **NEVER modify or delete `docs/Briefing.md`**. It is the untouched academic rubric reference.

### 5.2 Prohibited Commands & Practices
- 🚫 Never run `git push --force` or commit directly to `main`. `main` changes only through a **squash-merged** Pull Request (GitHub Flow); the repository allows only squash merges and `.github/workflows/main-guard.yml` flags any commit on `main` that bypasses a PR.
- 🚫 Never use `git add .` blindly without first running `git status` to ensure `.env`, temporary scratch scripts, or files `> 15 MB` are excluded.
- 🚫 Never suppress exceptions silently (`except Exception: pass`) in data cleaning or pipeline code.
- 🚫 Never claim causal relationships (`"X causes Y"`) from observational correlation metrics ($r$ or $\rho$).
- 🚫 Never leave raw sentinel values (`-999`, `-5`, `200`, `-1`, `0`, `abc123`, `not_a_date`, `missing`) uncleaned in downstream charts or aggregations.

### 5.3 Mandatory Pre-Commit & Pre-PR Verification
Before opening or merging any Pull Request, execute the [`.agents/skills/pr-self-review/SKILL.md`](.agents/skills/pr-self-review/SKILL.md) checklist using the `EDA` virtual environment:
```powershell
.\EDA\Scripts\python.exe -m pip install -r requirements.txt
.\EDA\Scripts\python.exe .github/scripts/run_local_ci.py
```
`run_local_ci.py` runs the same checks as `.github/workflows/ci.yml`: Ruff (blocking, pinned version), Flake8 syntax errors, notebook structure + top-to-bottom execution + `data/processed/` reproducibility, the ontology data contract, repository hygiene (protected files, forbidden files, `< 15 MB`), artifact naming / 300 DPI / handoff sections, and `pytest`. Every check is **blocking** in CI. `.github/workflows/pr-governance.yml` additionally checks the PR title (Conventional Commits), branch name, and `Closes #<id>` link.
