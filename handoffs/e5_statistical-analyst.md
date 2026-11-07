# E5 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — Bivariate segment spend aggregation (`compute_bivariate_segment_spend`), parametric/non-parametric hypothesis testing (`run_bivariate_hypothesis_tests`), and `city` × `country` cross-tabulation (`compute_city_country_crosstab`).
- `data/processed/summaries/e5_bivariate_spend_by_segment.csv` — Segment-level `purchase_amount` statistics (`n_segment`, `n_valid_spend`, `spend_coverage_pct`, `mean_spend`, `std_spend`, `median_spend`, `q1_spend`, `q3_spend`, `iqr_spend`, `total_spend`, `revenue_per_1k_valid`) across `gender`, `country`, `city`, `age_group`, `feedback_score`, `contact_reachability`, and `contact_reachability_tier`.
- `data/processed/summaries/e5_bivariate_hypothesis_tests.csv` — One-way ANOVA (`F`, `p_anova`), Kruskal-Wallis (`H`, `p_kruskal`), Pearson (`r`, `p_pearson`), Spearman (`rho`, `p_spearman`), and Chi-square (`chi2_stat`, `p_chi2`, `dof`, `n_geo_mismatch`) test results across 19 bivariate specifications.
- `data/processed/summaries/e5_city_country_crosstab.csv` — Cross-tabulation of `city` × `country` counts, row percentages, and per-city geographic mismatch totals.

## Notebook Cells
```markdown
---

## 5. `[E5]` Bivariate Analysis — Segment Comparisons & Hypothesis Testing

We next evaluate pairwise relationships across three analytical families using `src/analysis.py`:
1. **Continuous × Categorical (`Q2`, `Q3`):** `purchase_amount` compared across `gender`, `country`, `city`, ontology `age_group` cohorts, discrete `feedback_score`, and `contact_reachability` via One-way ANOVA ($F$) and Kruskal-Wallis ($H$) tests (both including and excluding `'Unknown'`/`'Missing'`).
2. **Continuous × Continuous (`Q2`, `Q3`):** Pairwise linear (Pearson $r$) and monotonic rank (Spearman $\rho$) correlations of `age`, `feedback_score_1_to_5`, `feedback_score` (all), and chronologically valid `tenure_days` with `purchase_amount`.
3. **Categorical × Categorical (`Q1`):** `city` × `country` contingency table, Pearson $\chi^2$ test of independence, and exact audit of cross-border geographic mismatches.
```

```python
from src.analysis import (
    compute_bivariate_segment_spend,
    compute_city_country_crosstab,
    load_clean_customers,
    run_bivariate_hypothesis_tests,
)

df_clean_e5 = load_clean_customers("v1")
e5_seg_spend = compute_bivariate_segment_spend(df_clean_e5)
e5_tests = run_bivariate_hypothesis_tests(df_clean_e5)
e5_crosstab = compute_city_country_crosstab(df_clean_e5)

print("=== [E5] BIVARIATE SEGMENT SPEND SUMMARY ===")
print(e5_seg_spend.round(2).to_string(index=False))

print("\n=== [E5] FORMAL BIVARIATE HYPOTHESIS TESTS (ANOVA / KRUSKAL / CORRELATION / CHI2) ===")
print(e5_tests.round(4).to_string(index=False))

print("\n=== [E5] CITY x COUNTRY CROSS-TABULATION & GEOGRAPHIC MISMATCHES ===")
print(e5_crosstab.round(2).to_string(index=False))
```

```markdown
**Quantitative Interpretation (`E5`):**
- **Segment Spend Homogeneity (`Q2`):** Across every demographic, geographic, satisfaction, and reachability dimension, observed `purchase_amount` variations lie well within random sampling noise (`significant_at_0_05 == False` for all 13 categorical comparisons, all $p \ge 0.31$). Specifically, among known segments: `gender` (`Male` mean `$2,474.16` / median `$2,521.69` [$n = 960$] vs. `Female` mean `$2,458.40` / median `$2,388.78` [$n = 889$]; ANOVA $F = 0.0541, p = 0.8161$; Kruskal $H = 0.0481, p = 0.8265$), `country` (ranging from `USA` mean `$2,363.55` [$n = 395$] to `Australia` mean `$2,510.63` [$n = 413$]; $F = 0.6297, p = 0.6413$; $H = 2.5092, p = 0.6430$), `city` (ranging from `Kolkata` mean `$2,286.54` [$n = 264$] to `Chennai` mean `$2,562.51` [$n = 258$]; $F = 0.9386, p = 0.4752$; $H = 6.6429, p = 0.4670$), and `age_group` (ranging from `18-29` mean `$2,334.77` [$n = 134$] to `60+` mean `$2,556.18` [$n = 117$]; $F = 0.5038, p = 0.6798$; $H = 1.6209, p = 0.6547$) show no statistically significant differentiation.
- **Zero Linear or Monotonic Association with Spend (`Q2`, `Q3`):** Pairwise correlations with `purchase_amount` are near zero across `age` ($n = 600$, $r = 0.0430 [p = 0.2930]$, $\rho = 0.0457 [p = 0.2641]$), `feedback_score_1_to_5` ($n = 648$, $r = -0.0178 [p = 0.6508]$, $\rho = -0.0168 [p = 0.6688]$), all valid `feedback_score` ($n = 1,248$, $r = 0.0174 [p = 0.5384]$, $\rho = 0.0168 [p = 0.5527]$), and valid `tenure_days` ($n = 219$, $r = -0.0560 [p = 0.4098]$, $\rho = -0.0700 [p = 0.3027]$). Observational correlations neither indicate statistical dependence nor imply causal effects.
- **Structural Geographic Contradiction (`Q1`):** Although all 8 known cities (`Hyderabad`, `Mumbai`, `Pune`, `Bangalore`, `Chennai`, `Delhi`, `Ahmedabad`, `Kolkata`) are Indian metropolitan areas, `city` and `country` are statistically independent ($\chi^2 = 32.1845, \text{dof} = 40, p = 0.8057$ across all $10,000$ rows; $\chi^2 = 19.2934, \text{dof} = 28, p = 0.8888$ across $7,348$ dual-known rows). Consequently, **5,888 records** (`58.88%` of the entire dataset; **80.13%** of the $7,348$ dual-known city-country records) pair an Indian city with `USA`, `Australia`, `Canada`, or `UK` (`63.85%–69.03%` row mismatch across every Indian city).
```

## Key Findings
- **No Statistically Significant Spend Gap Across Demographics or Locations (`Q2`):** Known-segment ANOVA and Kruskal-Wallis tests on `purchase_amount` confirm statistical homogeneity across `gender` ($n = 1,849$, $F = 0.0541, p = 0.8161$; $H = 0.0481, p = 0.8265$), `country` ($n = 2,040$, $F = 0.6297, p = 0.6413$), `city` ($n = 2,175$, $F = 0.9386, p = 0.4752$), and `age_group` ($n = 600$, $F = 0.5038, p = 0.6798$).
- **Satisfaction & Lifecycle Tenure Are Uncorrelated with Order Value (`Q3`):** `purchase_amount` exhibits negligible correlation with `feedback_score_1_to_5` ($n = 648$, $r = -0.0178, p = 0.6508$; $\rho = -0.0168, p = 0.6688$), full `feedback_score` ($n = 1,248$, $r = 0.0174, p = 0.5384$), `age` ($n = 600$, $r = 0.0430, p = 0.2930$), and valid `tenure_days` ($n = 219$, $r = -0.0560, p = 0.4098$; $\rho = -0.0700, p = 0.3027$).
- **Reachable vs. Unreachable Customers Spend Equivalently (`Q3`):** `Reachable (>=1 channel)` customers ($n_{\text{spend}} = 1,069$, `mean = $2,483.83`, `median = $2,525.94`) and `Unreachable (None)` customers ($n_{\text{spend}} = 1,397$, `mean = $2,425.20`, `median = $2,421.13`) do not differ significantly ($F = 1.0000, p = 0.3174$; $H = 1.0236, p = 0.3117$), meaning **56.06%** of verified spend (`$3,388,004.29` of `$6,043,218.46`) sits in unreachable accounts.
- **5,888 Cross-Column Geographic Mismatches Proven via Independence Test (`Q1`):** Every Indian city distributes ~`15%–19%` of its rows into each of `USA`, `Australia`, `Canada`, `UK`, `India`, and `Unknown` ($\chi^2 = 19.2934, \text{dof} = 28, p = 0.8888$ on $n = 7,348$ dual-known rows), producing $5,888$ `is_geo_mismatch` records (`80.13%` of dual-known; `58.88%` of all $10,000$ rows, within $6,655$ total non-Indian country rows).

## Open Issues
- Note for `DataVizAgent` (`E5` chart titles) and `ExecutiveReporterAgent`: `specs/ontology.md` §2/§3.1 mentions `6,655` as the total count of non-Indian country rows (`USA + Australia + Canada + UK = 1,679 + 1,660 + 1,658 + 1,658 = 6,655`), of which `767` have `city == 'Unknown'` and **`5,888`** (`58.88%` of total; `80.13%` of `7,348` dual-known rows) match the exact `is_geo_mismatch` formula `(city != 'Unknown') & country.isin(['USA', 'UK', 'Canada', 'Australia'])`. Cite both numbers clearly so readers see the exact decomposition.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --select=E9,F63,F7,F82` → `0 errors`
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `observed=True` on all categorical `groupby` operations and confirmed deterministic output across `e5_bivariate_spend_by_segment.csv` (36 rows), `e5_bivariate_hypothesis_tests.csv` (19 rows), and `e5_city_country_crosstab.csv` (9 rows).
