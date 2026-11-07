# 📐 Spec-Driven Development (SDD) Workflow

This project is developed **spec-first**: the specification is written and agreed before code, and
every artifact is traceable back to it.

## 1. The four sources of truth

| Artifact | Question it answers | Owner |
|---|---|---|
| `AGENTS.md` | How do humans and agents collaborate? | Lead Orchestrator |
| `specs/ontology.md` | What does each column, flag and KPI mean? | Lead Orchestrator |
| `docs/Work_Plan.md` | What is in scope, in which order and by when? | Lead Orchestrator |
| `.github/scripts/` + `.github/workflows/` | How is the spec enforced automatically? | Quality Reviewer / Lead |

## 2. The flow

```text
1. Spec      → change specs/ontology.md (name, dtype, formula, owner) before any code
2. Plan      → map the change to a task ID in docs/Work_Plan.md and an issue in Project #54
3. Branch    → docs/..., feature/..., chore/... from an up-to-date main
4. Fan-out   → subagents implement, export tables/charts and write handoffs/<task_id>_<agent>.md
5. Fan-in    → the Lead assembles notebooks/01_eda_customers.ipynb from the handoffs
6. Gate      → .\EDA\Scripts\python.exe .github/scripts/run_local_ci.py
7. PR        → Conventional Commits title, self-review, green CI, squash merge
```

## 3. Change-control rules

1. **A new feature or data-quality flag is added to `specs/ontology.md` first**, with name, dtype,
   formula and owner. Then it is implemented in `src/features.py` or `src/cleaning.py`.
2. **The data contract follows the spec.** If a new column becomes mandatory, update
   `.github/scripts/check_data_contract.py` in the same PR.
3. **The skills follow the spec.** Update the canonical skill in `.agents/skills/`, never the
   `.claude/skills/` pointer.
4. **The reporter never computes new numbers.** It cites summary tables, handoffs or ontology KPIs.
5. **No causal language** from correlations; use "is associated with".
6. **Raw data is immutable.** All outputs go to `data/processed/` or `assets/`.

## 4. Artifact traceability

| Artifact | Pattern | Example |
|---|---|---|
| Task issue | `[<ID>] <title>` | `[E4] Univariate analysis` |
| Branch | `<type>/<kebab-name>` | `feature/02-essential-analysis` |
| Summary table | `data/processed/summaries/<task_id>_<slug>.csv` | `m3_segment_aggregations.csv` |
| Chart | `assets/charts/<task_id>_<slug>.png` | `e4_univariate_age_purchase.png` |
| Handoff | `handoffs/<task_id>_<agent>.md` | `e4_data-viz.md` |
| Processed dataset | `customers_<clean\|enriched>_v<N>.csv` | `customers_enriched_v1.csv` |
| PR | `<type>(<scope>): <summary>` + `Closes #<id>` | `feat(analysis): add univariate charts` |

## 5. Definition of Done

- [ ] The spec change is documented in `specs/ontology.md`.
- [ ] The code lives in `src/` and the notebook imports it (no duplicated logic).
- [ ] Summary tables and charts follow the naming convention.
- [ ] The handoff has the five sections in order (`Outputs`, `Notebook Cells`, `Key Findings`,
      `Open Issues`, `Verification`).
- [ ] The notebook runs top to bottom and `data/processed/` is reproducible.
- [ ] `run_local_ci.py` is green.
- [ ] The PR is self-reviewed and squash-merged; the remote branch is kept.

## 6. Anti-patterns

- Editing `data/raw/messy_customer_data.csv` or `docs/Briefing.md`.
- Imputing 75% missing values with a single mean/median and hiding the variance loss.
- Leaving sentinels (`-999`, `-5`, `200`, `-1`, `0`, `abc123`, `not_a_date`, `missing`) in outputs.
- Multiple agents editing `notebooks/01_eda_customers.ipynb` at the same time.
- Creating a feature that is not in `specs/ontology.md` §3.2.
- Claiming causation from Pearson `r` or Spearman `rho`.
