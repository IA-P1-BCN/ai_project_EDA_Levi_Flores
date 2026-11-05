# 🧾 Issue Backlog — EDA Project

Complete list of issues for the project, aligned with [`docs/Work_Plan.md`](../Work_Plan.md) and the
project design in [`PROJECT_SETUP.md`](PROJECT_SETUP.md).

**Total:** 28 task issues + 8 daily logs = **36 issues**.

Each row is one issue. Use the **Task** template for task issues and the **Daily Log** template for daily
logs, then fill the project fields described in `PROJECT_SETUP.md`. The `Done when` column is the short
version of the acceptance criteria; expand it in the issue body.

---

## Foundation — milestone `Foundation` (due 2026-11-04)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| F1 | `[F1] Repository and environment setup` | 2026-11-03 | `feature/project-setup-and-docs` | `task`, `level:foundation`, `area:setup` | M | P0 | Repository, Python 3.12 environment, CI and templates are ready. |
| F2 | `[F2] Dataset research and work plan` | 2026-11-04 | `feature/work-plan-english` | `task`, `level:foundation`, `area:setup` | M | P0 | Dataset selected and `docs/Work_Plan.md` merged. |

---

## Essential — milestone `Essential` (due 2026-11-06)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| E1 | `[E1] Load and inspect the dataset` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:data` | M | P0 | Notebook shows `shape`, `info()`, `head()`, `describe()` and the 3 business questions. |
| E2 | `[E2] Diagnose data quality` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:cleaning` | M | P0 | Missing values and duplicates quantified with a documented decision per column. |
| E3 | `[E3] Fix data types and columns` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:cleaning` | M | P0 | Types corrected, columns renamed/removed and clean dataset v1 produced. |
| E4 | `[E4] Univariate analysis` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | M | P0 | At least 3 variables analysed with labelled charts and interpretation. |
| E5 | `[E5] Bivariate analysis` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | M | P0 | At least 3 variable relationships analysed and interpreted. |
| E6 | `[E6] Answer the research questions` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | S | P0 | The 3 initial questions answered and the notebook runs top to bottom. |

---

## Medium — milestone `Medium` (due 2026-11-08)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| M1 | `[M1] Justify every cleaning decision` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:cleaning` | S | P1 | Every imputation, removal and rename has an explicit rationale. |
| M2 | `[M2] Detect and treat outliers` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | M | P1 | Outliers identified with boxplots/IQR and a documented treatment rule. |
| M3 | `[M3] Summarise with aggregations` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | M | P1 | `groupby`, `agg` and `pivot_table` results presented and interpreted. |
| M4 | `[M4] Engineer new features` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | M | P1 | At least 3 new variables created and justified. |
| M5 | `[M5] Correlation analysis` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:analysis` | S | P1 | Correlation heatmap produced and interpreted without causal claims. |
| M6 | `[M6] Temporal or group evolution` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:analysis` | M | P1 | Trends over time or group comparisons visualised and explained. |
| M7 | `[M7] Executive report` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:reporting` | L | P1 | 1–2 page executive report with conclusions supported by key charts. |

---

## Advanced — milestone `Advanced` (due 2026-11-09)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| A1 | `[A1] Normalise metrics` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:analysis` | S | P2 | Ratios, percentages or per-100/1,000 metrics replace raw totals in comparisons. |
| A2 | `[A2] Enrich with a second source` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:data` | M | P2 | Public auxiliary dataset merged and the join validated. |
| A3 | `[A3] Audit suspicious data` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:cleaning` | M | P2 | Impossible values and inconsistencies logged with their treatment. |
| A4 | `[A4] Apply a justified transformation` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:analysis` | S | P2 | Log scale, scaling or moving average applied and explained. |
| A5 | `[A5] Compare segments` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:visualization` | M | P2 | Group/region/period differences shown with clear charts. |
| A6 | `[A6] Add interactive visuals` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:visualization` | S | P2 | At least one `plotly` chart added and interpreted. |
| A7 | `[A7] Make cleaning reusable` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:engineering` | L | P2 | Cleaning logic extracted into documented functions/module used by the notebook. |

---

## Expert — milestone `Expert` (due 2026-11-10)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| X1 | `[X1] Build a reproducible pipeline` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:engineering` | L | P2 | One command cleans the data and writes the processed dataset. |
| X2 | `[X2] Build an interactive dashboard` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:engineering` | L | P2 | Streamlit app runs locally with working filters. |
| X3 | `[X3] Write tests` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:engineering` | M | P2 | Cleaning functions covered by `pytest` tests written before implementation. |
| X4 | `[X4] Produce a data quality report` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:reporting` | M | P2 | Missing data, fixes and open issues documented with reasons. |
| X5 | `[X5] Prepare the presentation` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:reporting` | M | P2 | 5-minute storytelling script and slides for a non-technical audience. |
| X6 | `[X6] Publish and close` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:release` | S | P2 | Public link published, README and `requirements.txt` updated. |

---

## Daily logs — no milestone (one per working day)

Create the daily log at the start of each working day and close it at the end. Daily logs use the `daily`
label and `Workstream = Management`; they do not need a branch.

| ID | Issue title | Date | Labels | Est. | Done when |
|---|---|---|---|---|---|
| D1 | `[DAILY] 2026-11-03` | 2026-11-03 | `daily` | S | Report completed and placed in the Tue 03 Nov column. |
| D2 | `[DAILY] 2026-11-04` | 2026-11-04 | `daily` | S | Report completed and placed in the Wed 04 Nov column. |
| D3 | `[DAILY] 2026-11-05` | 2026-11-05 | `daily` | S | Report completed and placed in the Thu 05 Nov column. |
| D4 | `[DAILY] 2026-11-06` | 2026-11-06 | `daily` | S | Report completed and placed in the Fri 06 Nov column. |
| D5 | `[DAILY] 2026-11-07` | 2026-11-07 | `daily` | S | Report completed and placed in the Sat 07 Nov column. |
| D6 | `[DAILY] 2026-11-08` | 2026-11-08 | `daily` | S | Report completed and placed in the Sun 08 Nov column. |
| D7 | `[DAILY] 2026-11-09` | 2026-11-09 | `daily` | S | Report completed and placed in the Mon 09 Nov column. |
| D8 | `[DAILY] 2026-11-10` | 2026-11-10 | `daily` | S | Report completed and placed in the Tue 10 Nov column. |

---

## Creation order

1. Create the labels, milestones and project fields described in `PROJECT_SETUP.md`.
2. Create the issues in this order: `F1–F2`, `E1–E6`, `M1–M7`, `A1–A7`, `X1–X6`.
3. Add every issue to the project and complete its fields.
4. Create each daily log on its date; do not create all daily logs in advance unless they are left as
   `Backlog` placeholders.

> **Branch rule:** every task issue requires its own branch before work starts. Daily logs are reports,
> not development tasks, so they are updated directly in the issue without a branch.
