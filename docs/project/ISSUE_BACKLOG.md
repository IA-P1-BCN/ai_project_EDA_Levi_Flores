# 🧾 Issue Backlog — EDA Project

Complete list of issues for the project, aligned with [`docs/Work_Plan.md`](../Work_Plan.md) and the project design in [`PROJECT_SETUP.md`](PROJECT_SETUP.md).

**Total:** 28 task issues + 8 daily logs = **36 issues**.

---

## 🎨 Visual Presentation Standards (Shields.io Badges)

Every issue in this repository follows a clean, executive Markdown layout featuring **Shields.io colored badges** for instant visual hierarchy and readability.

### Color Palette Specification

| Field | Value | Badge Code | Visual Render |
| :--- | :--- | :--- | :--- |
| **Level** | `Foundation` | `https://img.shields.io/badge/Level-Foundation-C5DEF5?style=flat-square&logoColor=black` | ![Level: Foundation](https://img.shields.io/badge/Level-Foundation-C5DEF5?style=flat-square&logoColor=black) |
| | `Essential` | `https://img.shields.io/badge/Level-Essential-0E8A16?style=flat-square` | ![Level: Essential](https://img.shields.io/badge/Level-Essential-0E8A16?style=flat-square) |
| | `Medium` | `https://img.shields.io/badge/Level-Medium-FBCA04?style=flat-square&logoColor=black` | ![Level: Medium](https://img.shields.io/badge/Level-Medium-FBCA04?style=flat-square&logoColor=black) |
| | `Advanced` | `https://img.shields.io/badge/Level-Advanced-D93F0B?style=flat-square` | ![Level: Advanced](https://img.shields.io/badge/Level-Advanced-D93F0B?style=flat-square) |
| | `Expert` | `https://img.shields.io/badge/Level-Expert-B60205?style=flat-square` | ![Level: Expert](https://img.shields.io/badge/Level-Expert-B60205?style=flat-square) |
| **Priority** | `P0 - Critical` | `https://img.shields.io/badge/Priority-P0--Critical-red?style=flat-square` | ![Priority: P0 - Critical](https://img.shields.io/badge/Priority-P0--Critical-red?style=flat-square) |
| | `P1 - High` | `https://img.shields.io/badge/Priority-P1--High-orange?style=flat-square` | ![Priority: P1 - High](https://img.shields.io/badge/Priority-P1--High-orange?style=flat-square) |
| | `P2 - Normal` | `https://img.shields.io/badge/Priority-P2--Normal-yellow?style=flat-square` | ![Priority: P2 - Normal](https://img.shields.io/badge/Priority-P2--Normal-yellow?style=flat-square) |
| **Workstream** | `Setup` | `https://img.shields.io/badge/Workstream-Setup-BFD4F2?style=flat-square&logoColor=black` | ![Workstream: Setup](https://img.shields.io/badge/Workstream-Setup-BFD4F2?style=flat-square&logoColor=black) |
| | `Data` | `https://img.shields.io/badge/Workstream-Data-1D76DB?style=flat-square` | ![Workstream: Data](https://img.shields.io/badge/Workstream-Data-1D76DB?style=flat-square) |
| | `Cleaning` | `https://img.shields.io/badge/Workstream-Cleaning-5319E7?style=flat-square` | ![Workstream: Cleaning](https://img.shields.io/badge/Workstream-Cleaning-5319E7?style=flat-square) |
| | `Analysis` | `https://img.shields.io/badge/Workstream-Analysis-006B75?style=flat-square` | ![Workstream: Analysis](https://img.shields.io/badge/Workstream-Analysis-006B75?style=flat-square) |
| | `Visualization` | `https://img.shields.io/badge/Workstream-Visualization-F9D0C4?style=flat-square&logoColor=black` | ![Workstream: Visualization](https://img.shields.io/badge/Workstream-Visualization-F9D0C4?style=flat-square&logoColor=black) |
| | `Reporting` | `https://img.shields.io/badge/Workstream-Reporting-D4C5F9?style=flat-square&logoColor=black` | ![Workstream: Reporting](https://img.shields.io/badge/Workstream-Reporting-D4C5F9?style=flat-square&logoColor=black) |
| | `Engineering` | `https://img.shields.io/badge/Workstream-Engineering-C2E0C6?style=flat-square&logoColor=black` | ![Workstream: Engineering](https://img.shields.io/badge/Workstream-Engineering-C2E0C6?style=flat-square&logoColor=black) |
| | `Release` | `https://img.shields.io/badge/Workstream-Release-FEF2C0?style=flat-square&logoColor=black` | ![Workstream: Release](https://img.shields.io/badge/Workstream-Release-FEF2C0?style=flat-square&logoColor=black) |

---

## Foundation — milestone `Foundation` (due 2026-11-04)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| F1 | `[F1] Repository and environment setup` | 2026-11-03 | `feature/project-setup-and-docs` | `task`, `level:foundation`, `area:setup` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | Repository, Python 3.12 environment, CI and templates are ready. |
| F2 | `[F2] Dataset research and work plan` | 2026-11-04 | `feature/work-plan-english` | `task`, `level:foundation`, `area:setup` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | Dataset selected and `docs/Work_Plan.md` merged. |
| F3 | `[F3] Multi-agent governance and skills setup` | 2026-11-05 | `feature/agents-and-ontology-setup` | `task`, `level:foundation`, `area:setup`, `area:engineering` | ![L](https://img.shields.io/badge/L-4--8h-0366d6?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | `AGENTS.md`, `specs/ontology.md` and `.agents/skills/` merged. |

---

## Essential — milestone `Essential` (due 2026-11-06)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| E1 | `[E1] Load and inspect the dataset` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:data` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | Notebook shows `shape`, `info()`, `head()`, `describe()` and the 3 business questions. |
| E2 | `[E2] Diagnose data quality` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:cleaning` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | Missing values and duplicates quantified with a documented decision per column. |
| E3 | `[E3] Fix data types and columns` | 2026-11-05 | `feature/01-data-loading-and-cleaning` | `task`, `level:essential`, `area:cleaning` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | Types corrected, columns renamed/removed and clean dataset v1 produced. |
| E4 | `[E4] Univariate analysis` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | At least 3 variables analysed with labelled charts and interpretation. |
| E5 | `[E5] Bivariate analysis` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | At least 3 variable relationships analysed and interpreted. |
| E6 | `[E6] Answer the research questions` | 2026-11-06 | `feature/02-essential-analysis` | `task`, `level:essential`, `area:analysis` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P0](https://img.shields.io/badge/P0-red?style=flat-square) | The 3 initial questions answered and the notebook runs top to bottom. |

---

## Medium — milestone `Medium` (due 2026-11-08)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| M1 | `[M1] Justify every cleaning decision` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:cleaning` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | Every imputation, removal and rename has an explicit rationale. |
| M2 | `[M2] Detect and treat outliers` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | Outliers identified with boxplots/IQR and a documented treatment rule. |
| M3 | `[M3] Summarise with aggregations` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | `groupby`, `agg` and `pivot_table` results presented and interpreted. |
| M4 | `[M4] Engineer new features` | 2026-11-07 | `feature/03-outliers-feature-engineering` | `task`, `level:medium`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | At least 3 new variables created and justified. |
| M5 | `[M5] Correlation analysis` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:analysis` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | Correlation heatmap produced and interpreted without causal claims. |
| M6 | `[M6] Temporal or group evolution` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:analysis` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | Trends over time or group comparisons visualised and explained. |
| M7 | `[M7] Executive report` | 2026-11-08 | `feature/04-correlation-trends-report` | `task`, `level:medium`, `area:reporting` | ![L](https://img.shields.io/badge/L-4--8h-0366d6?style=flat-square) | ![P1](https://img.shields.io/badge/P1-orange?style=flat-square) | 1–2 page executive report with conclusions supported by key charts. |

---

## Advanced — milestone `Advanced` (due 2026-11-09)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| A1 | `[A1] Normalise metrics` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:analysis` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Ratios, percentages or per-100/1,000 metrics replace raw totals in comparisons. |
| A2 | `[A2] Enrich with a second source` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:data` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Public auxiliary dataset merged and the join validated. |
| A3 | `[A3] Audit suspicious data` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:cleaning` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Impossible values and inconsistencies logged with their treatment. |
| A4 | `[A4] Apply a justified transformation` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:analysis` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Log scale, scaling or moving average applied and explained. |
| A5 | `[A5] Compare segments` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:visualization` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Group/region/period differences shown with clear charts. |
| A6 | `[A6] Add interactive visuals` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:visualization` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | At least one `plotly` chart added and interpreted. |
| A7 | `[A7] Make cleaning reusable` | 2026-11-09 | `feature/05-advanced-analysis` | `task`, `level:advanced`, `area:engineering` | ![L](https://img.shields.io/badge/L-4--8h-0366d6?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Cleaning logic extracted into documented functions/module used by the notebook. |

---

## Expert — milestone `Expert` (due 2026-11-10)

| ID | Issue title | Date | Branch | Labels | Est. | Priority | Done when |
|---|---|---|---|---|---|---|---|
| X1 | `[X1] Build a reproducible pipeline` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:engineering` | ![L](https://img.shields.io/badge/L-4--8h-0366d6?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | One command cleans the data and writes the processed dataset. |
| X2 | `[X2] Build an interactive dashboard` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:engineering` | ![L](https://img.shields.io/badge/L-4--8h-0366d6?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Streamlit app runs locally with working filters. |
| X3 | `[X3] Write tests` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:engineering` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Cleaning functions covered by `pytest` tests written before implementation. |
| X4 | `[X4] Produce a data quality report` | 2026-11-10 | `feature/06-pipeline-and-tests` | `task`, `level:expert`, `area:reporting` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Missing data, fixes and open issues documented with reasons. |
| X5 | `[X5] Prepare the presentation` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:reporting` | ![M](https://img.shields.io/badge/M-2--4h-5319E7?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | 5-minute storytelling script and slides for a non-technical audience. |
| X6 | `[X6] Publish and close` | 2026-11-10 | `feature/07-dashboard-and-release` | `task`, `level:expert`, `area:release` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | ![P2](https://img.shields.io/badge/P2-yellow?style=flat-square) | Public link published, README and `requirements.txt` updated. |

---

## Daily logs — no milestone (one per working day)

Create the daily log at the start of each working day and close it at the end. Daily logs use the `daily` label and `Workstream = Management`; they do not need a branch.

| ID | Issue title | Date | Labels | Est. | Done when |
|---|---|---|---|---|---|
| D1 | `[DAILY] 2026-11-03` | 2026-11-03 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Tue 03 Nov column. |
| D2 | `[DAILY] 2026-11-04` | 2026-11-04 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Wed 04 Nov column. |
| D3 | `[DAILY] 2026-11-05` | 2026-11-05 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Thu 05 Nov column. |
| D4 | `[DAILY] 2026-11-06` | 2026-11-06 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Fri 06 Nov column. |
| D5 | `[DAILY] 2026-11-07` | 2026-11-07 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Sat 07 Nov column. |
| D6 | `[DAILY] 2026-11-08` | 2026-11-08 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Sun 08 Nov column. |
| D7 | `[DAILY] 2026-11-09` | 2026-11-09 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Mon 09 Nov column. |
| D8 | `[DAILY] 2026-11-10` | 2026-11-10 | `daily` | ![S](https://img.shields.io/badge/S-Up_to_2h-2ea44f?style=flat-square) | Report completed and placed in the Tue 10 Nov column. |
