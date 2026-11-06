# 📊 Exploratory Data Analysis (EDA) — Customer Messy Data

![Project Banner](assets/minidatathon.PNG)

Welcome to the **`ai_project_EDA_Levi_Flores`** repository!

This project simulates a real-world data consulting engagement performing an end-to-end **Exploratory Data Analysis (EDA)** on a dirty customer dataset (**"Customer Messy Data"**). The objective is not merely to clean records, but to diagnose structural data quality flaws, uncover actionable patterns, and deliver executive-ready visualisations and strategic insights.

> 📌 **Academic Briefing:** The original project specification is preserved intact in [`docs/Briefing.md`](docs/Briefing.md). The detailed operational schedule and task breakdown are documented in [`docs/Work_Plan.md`](docs/Work_Plan.md).

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

# 3. Commit incremental changes following Conventional Commits
git add .
git commit -m "feat(eda): load dataset, diagnose quality and export clean v1"

# 4. Push and open Pull Request
git push -u origin feature/01-data-loading-and-cleaning
```

---

## 📂 Repository Structure

```text
ai_project_EDA_Levi_Flores/
│
├── .github/                      # GitHub automation and project governance
│   ├── ISSUE_TEMPLATE/           # Structured YAML forms for Tasks and Daily Logs
│   ├── workflows/                # CI gate (ci.yml), PR governance, Main Guard (main-guard.yml)
│   ├── scripts/                  # CI check scripts; run_local_ci.py replays the gate locally
│   └── pull_request_template.md  # Pull Request checklist and review template
│
├── assets/                       # Visual assets and project banner
│   └── minidatathon.PNG
│
├── data/                         # Dataset storage
│   ├── raw/                      # Original immutable CSV (messy_customer_data.csv)
│   └── processed/                # Cleaned and feature-engineered datasets
│
├── docs/                         # Project documentation and planning
│   ├── Briefing.md               # Original academic specification (untouched)
│   ├── Work_Plan.md              # Sprint schedule, task breakdown (E1–X6) and branch plan
│   └── project/                  # GitHub Projects v2 setup and issue backlog
│       ├── PROJECT_SETUP.md
│       └── ISSUE_BACKLOG.md
│
├── notebooks/                    # Jupyter Notebooks for Exploratory Data Analysis
│   └── 01_eda_customers.ipynb    # Core EDA notebook (Essential, Medium & Advanced levels)
│
├── EDA/                          # Local Python 3.12 virtual environment (git-ignored)
├── .gitignore                    # Git exclusion rules
├── requirements.txt              # Python package dependencies
└── README.md                     # Main project documentation
```
