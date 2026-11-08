# M3 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — Added `build_m3_demographic_spend_groupby`, `build_m3_country_age_pivot`, `build_m3_reachability_spend_tier_pivot`, and `export_m3_summaries` implementing multi-dimensional `groupby(..., observed=True).agg(...)` and `pd.pivot_table(..., observed=True)` aggregations on the 27-column enriched schema.
- `data/processed/summaries/m3_groupby_demographic_spend.csv` — 15-row `gender × age_group` multi-metric aggregation table (`account_count`, `account_share_pct`, `valid_spend_n`, `spend_coverage_pct`, `total_spend_usd`, `mean_spend_usd`, `std_spend_usd`, `median_spend_usd`, `iqr_spend_usd`, `rev_per_1k_valid_customers_usd` [`KPI-3`], `reachable_pct` [`KPI-4`], and `mean_completeness_score` [`KPI-1`]).
- `data/processed/summaries/m3_pivot_country_age_spend.csv` — 7-row × 25-column flattened `country × age_group` spend pivot table (`count`, `mean`, `median`, `sum` with `"All"` row/column margins).
- `data/processed/summaries/m3_pivot_reachability_spend_tier.csv` — 16-row `contact_reachability_tier × spend_tier` cross-aggregation quantifying account shares, verified revenue concentration, **unreachable VIP revenue at risk**, and `feedback_tier` Promoter/Detractor/Scale-10 shares per cell.

## Notebook Cells
```markdown
---

## 9. `[M3]` Multi-Dimensional Segment Aggregations (`groupby`, `agg` & `pivot_table`)

Univariate (`E4`) and single-factor bivariate (`E5`) summaries can obscure compound operational risks that emerge only at the intersection of **demographics, geography, commercial spend tiers, and CRM reachability**. Using explicit `observed=True` categorical grouping (`src/analysis.py` + `src/features.py`), we construct three multi-dimensional segment matrices:

1. **Demographic × Lifecycle Cohort Matrix (`groupby` + named `.agg()`):** `gender × age_group` (`3 × 5 = 15` cells) pairing raw spend totals with normalized **Revenue per 1,000 Valid Customers (`KPI-3`)**, **Omnichannel Reachability (`KPI-4`)**, and **Profile Completeness (`KPI-1`)**.
2. **Geographic × Age Cohort Spend Matrix (`pd.pivot_table` with margins):** `country × age_group` (`count`, `mean`, `median`, `sum` across `7 × 6` cells including `"All"` margins) auditing sample sizes ($n$) alongside transaction averages.
3. **CRM Reachability × Commercial Spend Tier Matrix (`pivot_table` + `groupby/agg`):** `contact_reachability_tier × spend_tier` (`4 × 4 = 16` cells) crossed with `feedback_tier` sentiment to isolate **unreachable VIP (`High > $3,500`) revenue exposure**.
```

```python
from src.analysis import (
    build_m3_country_age_pivot,
    build_m3_demographic_spend_groupby,
    build_m3_reachability_spend_tier_pivot,
    load_clean_customers,
)
from src.features import engineer_features

df_enriched_m3 = engineer_features(load_clean_customers("v2"))

m3_demo_groupby = build_m3_demographic_spend_groupby(df_enriched_m3)
m3_country_age_piv = build_m3_country_age_pivot(df_enriched_m3)
m3_reach_spend_piv = build_m3_reachability_spend_tier_pivot(df_enriched_m3)

print("=== [M3.1] DEMOGRAPHIC COHORT AGGREGATION: GENDER x AGE_GROUP (GROUPBY + AGG) ===")
print(m3_demo_groupby.round(2).to_string(index=False))

piv_display_cols = [
    "country",
    "n_age_18_29",
    "n_age_30_44",
    "n_age_45_59",
    "n_age_60_plus",
    "n_age_unknown",
    "n_all_ages",
    "mean_age_18_29",
    "mean_age_30_44",
    "mean_age_45_59",
    "mean_age_60_plus",
    "mean_all_ages",
    "sum_all_ages",
]
print("\n=== [M3.2] COUNTRY x AGE_GROUP SPEND PIVOT TABLE (COUNTS, MEANS & TOTALS) ===")
print(m3_country_age_piv[piv_display_cols].round(2).to_string(index=False))

reach_display_cols = [
    "contact_reachability_tier",
    "spend_tier",
    "account_count",
    "pct_of_spend_tier",
    "verified_revenue_usd",
    "pct_of_total_revenue",
    "mean_spend_usd",
    "promoter_4_5_pct_of_valid_fb",
    "detractor_1_2_pct_of_valid_fb",
]
print("\n=== [M3.3] REACHABILITY TIER x SPEND TIER PIVOT & SENTIMENT EXPOSURE ===")
print(m3_reach_spend_piv[reach_display_cols].round(2).to_string(index=False))
```

```markdown
**Quantitative & Strategic Interpretation (`M3`):**
- **Unreachable VIP Revenue Exposure (`Q2`, `Q3`):** Crossing `contact_reachability_tier` with `spend_tier` exposes the dataset's single largest commercial vulnerability: out of **`724` VIP `High (>$3,500)` accounts** (`$3,057,313.93`, or **`50.59%`** of all verified revenue), **`405` VIPs (`55.94%` of all VIPs)** are **`Unreachable (None)`**, locking **`$1,713,463.02` (`28.35%` of total company-wide verified revenue)** outside email and SMS retention workflows. Conversely, only **`58` VIPs (`8.01%`, `$246,953.52` / `4.09%` of revenue)** are reachable via `Omnichannel (Both)`. Worse still, within unreachable VIPs with valid feedback ($n = 201$), **`Detractors (1-2)` (`22.39%`) exceed `Promoters (4-5)` (`15.92%`)**, preventing proactive service recovery on high-value accounts.
- **Small-Cell Volatility vs. Normalized Parity in `gender × age_group` (`Q1`, `Q2`):** While `Unknown` gender × `60+ (Senior)` ($n_{\text{spend}} = 34$) exhibits a sample mean of `$2,950.09` (`$2,950,087.06` per 1k valid customers) vs. `$2,023.41` in `Unknown × 18-29` ($n_{\text{spend}} = 37$), larger known demographic cells (`Male` and `Female` across `18–60+`, $n_{\text{spend}} = 40\text{–}81$) cluster tightly between **`$2,269.95` and `$2,519.28`** (`KPI-3: $2.27M–$2.52M / 1k`), and `75.87%` (`$4,584,783.83`) of verified spend resides in `age_group == 'Unknown'` ($n_{\text{spend}} = 1,866$). Meanwhile, `mean_completeness_score` (`KPI-1`) rises from **`0.4721`** in `Unknown × Unknown` ($n = 1,852$) to **`0.6308–0.6407`** when both `gender` and `age_group` are populated.
- **Cross-Border × Age Spend Granularity (`Q1`, `Q2`):** The `country × age_group` pivot confirms why sample-size reporting ($n$) alongside means is mandatory: known country × known age cells contain only **`14–37` valid orders per cell** (e.g., `USA × 60+` $n = 14$, mean `$2,261.76`; `India × 30-44` $n = 33$, mean `$2,864.99`), whereas `age_unknown` accounts for `283–324` orders per country (`1,866 / 2,466 = 75.67%` overall), reinforcing that apparent cell-level spikes reflect small-sample variance rather than structural market premiums.
```

## Key Findings
- **`$1.71M` (`28.35%` of Total Revenue) Locked in Unreachable VIP Accounts (`Q2`, `Q3`):** `contact_reachability_tier × spend_tier` reveals that **`405` of `724` (`55.94%`) `High (>$3,500)` VIP customers** are `Unreachable (None)`, representing **`$1,713,463.02`** (`mean = $4,230.77`, `median = $4,223.87`) and carrying more Detractors (`22.39%`) than Promoters (`15.92%`) among rated accounts ($n_{\text{fb}} = 201$), whereas only `58` VIPs (`8.01%`, `$246,953.52`) are `Omnichannel (Both)`.
- **Combined Unreachable High + Medium Spend Exceeds `$3.17M` (`Q2`, `Q3`):** Adding `Unreachable (None) × Medium ($1,200-$3,500)` ($n = 622$, `$1,456,453.50`, `24.10%` of revenue) brings unreachable mid-to-high-tier revenue to **`$3,169,916.52` (`52.45%` of total verified spend)** across `1,027` accounts.
- **Demographic Completeness Stratification vs. Spend Parity (`Q1`, `Q2`):** Across the 15 `gender × age_group` cohorts, `mean_completeness_score` (`KPI-1`) stratifies sharply from `0.4721` (`Unknown × Unknown`, $n = 1,852$) to `0.6308–0.6407` in dual-known cohorts, while known-gender × known-age `KPI-3` (`rev_per_1k_valid_customers_usd`) remains tightly bounded between `$2,269,952.35` (`Male × 30-44`, $n = 81$) and `$2,519,276.62` (`Female × 30-44`, $n = 71$).
- **Sparse Known Sub-Cells in `country × age_group` (`Q1`, `Q2`):** Known `country × age_group` cells hold only `14` (`USA × 60+`) to `37` (`Canada × 30-44`) valid transactions each (`mean` range `$2,042.67–$2,864.99`), whereas `75.67%` ($1,866 / 2,466$) of spend records fall under `age_group == 'Unknown'`, preventing over-interpretation of small-cell fluctuations.

## Open Issues
- None. Section 9 (`[M3]`) is self-contained via `engineer_features(load_clean_customers("v2"))`, so it executes cleanly top-to-bottom regardless of whether Section 10 (`[M4]`) appears after it in `notebooks/01_eda_customers.ipynb`.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `observed=True` on every categorical `groupby` and `pd.pivot_table` call and confirmed exact margin/total reconciliation (`10,000` accounts; `2,466` valid orders; `$6,043,218.46` total spend) across all three `m3_*.csv` tables.
