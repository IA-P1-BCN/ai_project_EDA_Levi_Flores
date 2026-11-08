# M6 — statistical-analyst handoff

## Outputs
- `src/analysis.py`
- `data/processed/summaries/m6_date_coverage_audit.csv`
- `data/processed/summaries/m6_signup_cohorts_monthly.csv`
- `data/processed/summaries/m6_last_purchase_monthly.csv`
- `data/processed/summaries/m6_cohort_evolution_summary.csv`
- `data/processed/summaries/m6_signup_quarter_evolution.csv`
- `data/processed/summaries/m6_trend_tests.csv`

## Notebook Cells
```markdown
---

## 13. `[M6]` Temporal & Cohort Evolution (Signup Cohorts and Last-Purchase Activity)

The cleaned dataset contains two independent date fields with heavy missingness, so every temporal statement must start from an explicit **coverage and exclusion audit**. `build_m6_date_coverage_audit` (`src/analysis.py`) reports, per metric, the numerator, denominator, share, and exclusion rule; the series builders (`build_m6_signup_cohorts_monthly`, `build_m6_last_purchase_monthly`, `build_m6_cohort_evolution_summary`, `build_m6_signup_quarter_evolution`) then produce four ordered `m6_*.csv` tables, and `compute_m6_trend_tests` tests each series for a monotone trend with a Spearman rank correlation against the time index.

**Date-integrity rule (explicit, and quantitatively defended):** `signup_date` and `last_purchase_date` are each valid standing alone, so the `829` `is_date_inverted` rows are **retained in the single-date signup and last-purchase series** and excluded only where the two dates are combined (`customer_tenure_days`, `KPI-5`). Dropping them from the single-date series would discard disproportionately late signups (`4,996 → 4,167`) and early last purchases (`3,348 → 2,519`) and manufacture trends; that counterfactual is exported as two rejected sensitivity rows in `m6_trend_tests.csv`. All `NaT` dates are excluded everywhere and pairwise/period $n$ is printed for every series.
```

```python
from src.analysis import (
    build_m6_cohort_evolution_summary,
    build_m6_date_coverage_audit,
    build_m6_last_purchase_monthly,
    build_m6_signup_cohorts_monthly,
    build_m6_signup_quarter_evolution,
    compute_m6_trend_tests,
    load_clean_customers,
)
from src.features import engineer_features

df_enriched_m6 = engineer_features(load_clean_customers("v2"))

m6_coverage = build_m6_date_coverage_audit(df_enriched_m6)
m6_signup_monthly = build_m6_signup_cohorts_monthly(df_enriched_m6)
m6_activity_monthly = build_m6_last_purchase_monthly(df_enriched_m6)
m6_cohorts = build_m6_cohort_evolution_summary(df_enriched_m6)
m6_quarters = build_m6_signup_quarter_evolution(df_enriched_m6)
m6_trends = compute_m6_trend_tests(df_enriched_m6)

print("=== [M6.1] TEMPORAL COVERAGE & DATE-EXCLUSION AUDIT ===")
print(m6_coverage[["metric", "n", "base_n", "pct_of_base"]].to_string(index=False))

signup_cols = [
    "cohort_month",
    "n_signups",
    "n_valid_spend",
    "mean_spend_usd",
    "n_valid_tenure",
    "mean_tenure_days",
    "reachable_pct",
]
print("\n=== [M6.2] MONTHLY SIGNUP COHORTS — FIRST & LAST 6 OF 66 MONTHS ===")
print(pd.concat([m6_signup_monthly[signup_cols].head(6), m6_signup_monthly[signup_cols].tail(6)]).to_string(index=False))

activity_cols = [
    "activity_month",
    "n_purchases",
    "n_valid_spend",
    "mean_spend_usd",
    "median_spend_usd",
    "reachable_pct",
]
print("\n=== [M6.3] MONTHLY LAST-PURCHASE ACTIVITY — FIRST & LAST 6 OF 66 MONTHS ===")
print(pd.concat([m6_activity_monthly[activity_cols].head(6), m6_activity_monthly[activity_cols].tail(6)]).to_string(index=False))

cohort_cols = [
    "signup_year",
    "is_partial_year",
    "n_signups",
    "n_valid_spend",
    "mean_spend_usd",
    "n_valid_tenure",
    "mean_tenure_days",
    "mean_observation_window_days",
    "tenure_to_window_ratio",
    "reachable_pct",
    "mean_feedback_1_to_5",
    "mean_completeness_score",
]
print("\n=== [M6.4] ORDERED SIGNUP-YEAR COHORT EVOLUTION ===")
print(m6_cohorts[cohort_cols].round(4).to_string(index=False))

print("\n=== [M6.5] TREND TESTS (Spearman rho vs. time index; sensitivity rows rejected) ===")
print(
    m6_trends[
        [
            "series",
            "grain",
            "n_points",
            "spearman_rho_vs_time_index",
            "p_value",
            "trend_label",
            "is_sensitivity_check",
        ]
    ].to_string(index=False)
)

print(f"\nQuarterly grain rows: {len(m6_quarters)} | signups covered: {m6_quarters['n_signups'].sum():,}")
```

```markdown
**Quantitative Interpretation (`M6`):**
- **Coverage is the dominant limitation and is now explicit (`Q3`):** of the `10,000` accounts, only **`4,996` (`49.96%`)** have a valid `signup_date`, **`3,348` (`33.48%`)** a valid `last_purchase_date`, and **`1,684` (`16.84%`)** both; **`829` of the `1,684` dual-date rows (`49.23%`)** are `is_date_inverted`, leaving **`855` (`50.77%` of dual dates, `8.55%` of all accounts)** chronologically valid tenures (`data/processed/summaries/m6_date_coverage_audit.csv`).
- **Acquisition and recency are flat, not trending (`Q2`, `Q3`):** across all **`66`** calendar months (`2020-08` to `2026-01`), monthly signups range **`57–106`** (mean **`75.70`**; $n = 4{,}996$ dated signups) with $\rho = +0.0609$ ($p = 0.6271$), and monthly last-purchase activity ranges **`36–69`** (mean **`50.73`**; $n = 3{,}348$) with $\rho = +0.0520$ ($p = 0.6785$) in `m6_signup_cohorts_monthly.csv` / `m6_last_purchase_monthly.csv` / `m6_trend_tests.csv`. Signup volume per full year stays within **`887–946`** accounts (`2021–2025`) in `m6_cohort_evolution_summary.csv`.
- **Spend level shows no temporal drift (`Q2`):** monthly mean spend oscillates between **`$1,131.28` and `$3,570.71`** on only **`5–24`** valid orders per activity month ($\rho = -0.0464$, $p = 0.7111$), and the quarterly series over **`23`** quarters is equally trend-free ($\rho = +0.0346$, $p = 0.8755$). Cohort mean spend sits in a tight band of **`$2,239.02–$2,545.73`** across `2020–2025` cohorts ($n = 87$ to $232$ valid orders each).
- **The apparent tenure collapse is right-censoring, not retention decay (`Q3`):** mean `customer_tenure_days` falls monotonically from **`920.27` days** (`2020` cohort, $n = 124$) to **`127.05` days** (`2025` cohort, $n = 41$; $\rho = -1.0000$, $p < 0.000001$), yet the mean observation window `max(last_purchase_date) − mean(signup_date)` shrinks in lockstep from **`1,920` to `207` days**, so the observed-to-window ratio stays between **`0.4793` and `0.6138`** (`m6_cohort_evolution_summary.csv`). Shorter tenures for recent cohorts are therefore an artefact of a shorter observable window; they are not evidence that newer customers churn faster.
- **Quality and reachability profiles are stable across cohorts (`Q1`, `Q3`):** cohort `reachable_pct` stays within **`43.09%–45.78%`**, `mean_feedback_1_to_5` within **`2.8719–3.0651`**, and `mean_completeness_score` within **`0.5904–0.6043`** across the `2020–2025` signup years, so no cohort shows a material shift in contactability, satisfaction, or record quality.
```

## Key Findings
- **Temporal coverage, exclusions and the inverted-row rule are audited explicitly (`Q3`):** `4,996` valid `signup_date` (`49.96%`), `3,348` valid `last_purchase_date` (`33.48%`), `1,684` dual-date rows (`16.84%`), `829` of them inverted (`49.23%` of dual dates) and `855` valid tenures (`8.55%` of accounts) — `data/processed/summaries/m6_date_coverage_audit.csv`.
- **No monotone trend in acquisition or recency volume (`Q2`, `Q3`):** `66` months, monthly signups `57–106` (mean `75.70`, $n = 4{,}996$, $\rho = +0.0609$, $p = 0.6271$) and monthly last-purchase activity `36–69` (mean `50.73`, $n = 3{,}348$, $\rho = +0.0520$, $p = 0.6785$); full-year signup counts stay within `887–946` for `2021–2025`.
- **No monotone trend in spend level (`Q2`):** monthly mean spend spans `$1,131.28–$3,570.71` on `5–24` valid orders per month ($\rho = -0.0464$, $p = 0.7111$) and the `23`-quarter series gives $\rho = +0.0346$ ($p = 0.8755$); signup-cohort mean spend stays within `$2,239.02–$2,545.73` ($n = 87–232$).
- **Cohort tenure decline is fully consistent with right-censoring (`Q3`):** mean tenure `920.27` days (`2020`, $n = 124$) → `127.05` days (`2025`, $n = 41$), $\rho = -1.0000$, while the observable window falls `1,920 → 207` days and the tenure-to-window ratio remains `0.4793–0.6138`; recent cohorts are observed for less time, not shown to churn faster.
- **Dropping the `829` inverted rows from single-date series would fabricate trends (`Q3`, methodological):** the rejected sensitivity rows in `m6_trend_tests.csv` show `4,167` retained signups (`83.41%` of `4,996`) with $\rho = -0.6079$ ($p < 0.000001$) and `2,519` retained activity rows (`75.24%` of `3,348`) with $\rho = +0.7664$ ($p < 0.000001$), versus the unbiased $\rho = +0.0609$ and $+0.0520$ — which is why inverted pairs are excluded only from dual-date metrics.

## Open Issues
- Temporal conclusions are bounded by missingness: only `49.96%` of accounts carry a signup date and `33.48%` a last-purchase date, so "no trend" means no trend **within the dated subpopulation**; whether undated accounts differ cannot be tested without imputing dates, which the ontology forbids.
- `m6_cohort_evolution_summary.csv` labels the `2020` (data starts `2020-08-06`) and `2026` (data ends `2026-01-26`) cohorts with `is_partial_year = True`; the `2026` cohort holds only `58` signups and `1` valid tenure, so its ratios are retained for completeness but must not be interpreted.
- `pct_with_valid_last_purchase` is computed on the signup-dated cohort and therefore counts inverted pairs as activity presence (they do have a last-purchase date); `DataVizAgent` should pair it with `customer_tenure_days` coverage rather than treating it as a retention rate.
- `DataVizAgent` (M6 trend charts) should read `m6_signup_cohorts_monthly.csv`, `m6_last_purchase_monthly.csv`, and `m6_cohort_evolution_summary.csv` directly; the censoring narrative needs the `mean_observation_window_days` and `tenure_to_window_ratio` columns plotted alongside `mean_tenure_days`.
- No new engineered feature was introduced; `M6` uses only `specs/ontology.md` §3.2 features and shipped date/flag columns, so no ontology change is requested.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `All checks passed!` (`0 errors`)
- `.\EDA\Scripts\python.exe -m flake8 src/analysis.py --max-line-length=127` → `0 errors`
- `export_m6_summaries()` executed twice; all 6 `m6_*.csv` files materialized on disk and SHA-256 digests were identical across runs (deterministic / idempotent).
- Reconciliation checks: monthly signup table has `66` rows summing to `4,996` signups (`100.00%` of dated signups); monthly activity table has `66` rows summing to `3,348` purchases (`100.00%` of dated last purchases); signup-year cohort table sums to `4,996` signups and `855` valid tenures; quarterly table has `23` rows summing to `4,996` signups; coverage audit reconciles `10,000 = 4,996 valid signup + 5,004 NaT` and `10,000 = 855 valid tenure + 829 inverted + 8,316 missing-date`.
