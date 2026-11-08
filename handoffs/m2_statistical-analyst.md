# M2 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — Updated `load_clean_customers` to support `version="v2"` (`21` columns including `feedback_score_1_to_5`, `completeness_score`, and all 7 boolean flags) while retaining default `version="v1"`, plus added `compute_iqr_outlier_summary`, `evaluate_outlier_treatment`, and `export_m2_summaries`.
- `data/processed/summaries/m2_iqr_outlier_summary.csv` — Formal Tukey $1.5 \times \text{IQR}$ and extreme $3.0 \times \text{IQR}$ outlier audit across `age`, `purchase_amount`, `customer_tenure_days`, `feedback_score`, `feedback_score_1_to_5`, and `completeness_score` (`6` rows × `25` columns).
- `data/processed/summaries/m2_outlier_treatment_comparison.csv` — Empirical evaluation of central tendency, dispersion, and sample retention across candidate treatment regimes (`Retain Valid Unclipped`, `Winsorize [P01, P99]`, `Naive Median-Imputed + Tukey IQR`, and `feedback_score` scale/capping regimes; `13` rows × `17` columns).

## Notebook Cells
```markdown
---

## 8. `[M2]` Outlier Detection & Treatment (Tukey IQR Rule)

Rigorous outlier governance in corrupted real-world data requires separating **two fundamentally distinct phenomena** before applying any mathematical filter (`src/analysis.py`):

1. **Layer 1 — Upstream Ingestion Sentinels (Measurement & Schema Corruption → Remediated in `E3`/`M1`):**
   - `age = -5` (`2,506` rows) and `age = 200` (`2,453` rows), `purchase_amount = -999` (`2,501` rows) and `'N/A'` (`2,533` rows), `feedback_score = -1` (`2,489` rows), and `829` chronologically inverted date pairs (`last_purchase_date < signup_date`) are **not** extreme tail customers — they are deterministic placeholder codes coerced to `NaN` in `customers_clean_v2.csv`.
2. **Layer 2 — Statistical Domain Outliers (Extreme Plausible Observations → Audited via Tukey's IQR Fences):**
   - Across valid non-null observations, we compute standard **Tukey inner fences** ($[Q_1 - 1.5 \times \text{IQR},\; Q_3 + 1.5 \times \text{IQR}]$) and **outer extreme fences** ($[Q_1 - 3.0 \times \text{IQR},\; Q_3 + 3.0 \times \text{IQR}]$), then evaluate candidate treatment regimes (**unclipped retention**, **`[P01, P99]` winsorization**, **scale isolation vs. `10 → 5` capping**, and the **naive median-imputation + IQR removal anti-pattern**).
```

```python
from src.analysis import (
    compute_iqr_outlier_summary,
    evaluate_outlier_treatment,
    load_clean_customers,
)

df_v2_m2 = load_clean_customers("v2")
m2_iqr_summary = compute_iqr_outlier_summary(df_v2_m2)
m2_treatment_eval = evaluate_outlier_treatment(df_v2_m2)

iqr_display_cols = [
    "variable",
    "n_valid",
    "missing_pct",
    "min",
    "q1",
    "median",
    "q3",
    "max",
    "iqr",
    "tukey_lower_fence",
    "tukey_upper_fence",
    "n_tukey_outliers",
    "outlier_pct_of_valid",
    "n_extreme_outliers",
    "treatment_rule",
]
print("=== [M2] TUKEY IQR (1.5x & 3.0x) OUTLIER AUDIT ON VALID DOMAIN OBSERVATIONS ===")
print(m2_iqr_summary[iqr_display_cols].round(2).to_string(index=False))

treat_display_cols = [
    "variable",
    "regime",
    "decision",
    "n_evaluated",
    "n_modified_or_dropped",
    "pct_valid_affected",
    "mean",
    "std",
    "std_change_pct",
    "median",
    "iqr",
    "iqr_change_pct",
    "min",
    "max",
]
print("\n=== [M2] CANDIDATE OUTLIER TREATMENT REGIMES COMPARISON ===")
print(m2_treatment_eval[treat_display_cols].round(2).to_string(index=False))
```

```markdown
**Quantitative & Methodological Justification (`M2`):**
- **Zero Statistical Outliers Across Core Continuous Metrics (`Q1`, `Q2`, `Q3`):** Once ingestion sentinels are removed, `age` ($n = 2,465$, range `18.0–70.0` yrs vs. Tukey fences `[-9.50, 98.50]`), `purchase_amount` ($n = 2,466$, range `$10.31–$4,998.67` vs. fences `[-$2,702.36, $7,595.62]`), and chronologically valid `customer_tenure_days` ($n = 855$, range `0–1,925` days vs. fences `[-766.25, 2,075.75]`) exhibit **`0` Tukey ($1.5 \times \text{IQR}$) outliers and `0` extreme ($3.0 \times \text{IQR}$) outliers**. Sensitivity checks with `[P01, P99]` winsorization shift `SD` by less than `0.26%` (`$1,442.83 → $1,441.83` on spend; `464.11 → 462.91` days on tenure) while arbitrarily censoring `50` genuine VIP/micro orders (`$4,941.58–$4,998.67` and `$10.31–$57.52`) and `17` loyal/same-day lifecycle records. **Decision: Retain all valid continuous observations unclipped.**
- **Quartile Masking & Bimodal Scale Jump in `feedback_score` (`Q3`):** Applying Tukey's rule blindly to raw valid `feedback_score` ($n = 5,049$) yields `0` flagged outliers (`fences = [-7.50, 20.50]`) because **`49.93%` ($n = 2,521$) of valid ratings sit at `10`**, exceeding the `25%` quartile breakdown point and pulling `Q3` from `4.0` up to `10.0` (`IQR = 7.0`). Evaluated against the true `1–5` Likert distribution (`feedback_score_1_to_5`, $n = 2,528$: `Q1 = 2.0`, `Q3 = 4.0`, `IQR = 2.0`), the `1.5 × IQR` upper fence is **`7.00`**, proving that `10` is an off-scale survey anomaly rather than organic dispersion. Capping `10 → 5` is rejected because it shifts the median from `3.0` to `5.0` (`mean: 2.96 → 3.98`) and fabricates a **`+266.77%` Promoter surge** (`945 → 3,466`). **Decision: Isolate via `is_score_10_spike` and analyze Likert sentiment on `feedback_score_1_to_5`.**
- **Record-Quality Tail in `completeness_score` (`Q1` / Data Quality):** Across all $N = 10,000$ accounts (`Q1 = 0.5000`, `Q3 = 0.6667`, `IQR = 0.1667`), exactly **`9` accounts (`0.09%`)** with only `2 / 12` valid attributes (`0.1667`) fall below the lower inner fence (`0.2500`), with `0` extreme outliers. All `9` accounts are retained so `N = 10,000` KPI denominators (`KPI-1`, `KPI-4`) remain uninflated and low-completeness records stay auditable in `A3`/`X4`.
- **Why Outlier Detection Must Never Follow Single-Value Imputation (`M1` → `M2` Link):** Because missingness exceeds `74%` on `age` (`75.35%`), `purchase_amount` (`75.34%`), `feedback_score_1_to_5` (`74.72%`), and `customer_tenure_days` (`91.45%`), naive median imputation collapses `Q1 = median = Q3` (`IQR = 0.00`), shrinking Tukey fences to a zero-width point and **falsely destroying `97.77%` (`2,410 / 2,465`) of valid ages, `100.00%` (`2,466 / 2,466`) of valid transactions, `99.65%` (`852 / 855`) of valid tenures, and `78.01%` (`1,972 / 2,528`) of valid Likert ratings** (`post-filter SD = 0.00`).
```

## Key Findings
- **Zero Tukey Outliers on Valid Continuous Domains (`Q1`, `Q2`, `Q3`):** After Layer 1 sentinel removal, `age` ($n = 2,465$, fences `[-9.50, 98.50]` yrs), `purchase_amount` ($n = 2,466$, fences `[-$2,702.36, $7,595.62]`), and `customer_tenure_days` ($n = 855$, fences `[-766.25, 2,075.75]` days) contain **`0` inner ($1.5 \times \text{IQR}$) and `0` outer ($3.0 \times \text{IQR}$) outliers**, justifying 100% unclipped retention over `[P01, P99]` winsorization (`<0.26%` SD impact, `67` genuine tail records needlessly censored).
- **Quartile Breakdown Masks the `feedback_score = 10` Scale Anomaly (`Q3`):** Because `2,521` of `5,049` valid ratings (`49.93%`) equal `10` (exceeding Tukey's `25%` breakdown threshold), raw `Q3` shifts to `10.0` (`fences = [-7.50, 20.50]`), masking the anomaly; against clean `feedback_score_1_to_5` ($n = 2,528$, `fences = [-1.00, 7.00]`), `10` sits `+1.5` IQRs above the upper fence, and capping `10 → 5` is rejected to prevent a `+266.77%` false Promoter inflation (`945 → 3,466`).
- **Low-Completeness Tail Quantified Without Denominator Bias (`Q1`):** `completeness_score` ($N = 10,000$, `mean = 0.5533`, `median = 0.5833`, `IQR = 0.1667`, `fences = [0.2500, 0.9167]`) flags `9` sparse accounts (`0.09%`, `2/12` valid fields = `0.1667`) below the lower Tukey fence and `0` extreme outliers (`max = 0.9167`, `11/12` valid fields across `33` accounts); retaining all `9` preserves exact `10,000`-row KPI denominators.
- **Empirical Proof Against Naive Impute-Then-Filter Pipelines (`Q1`–`Q3`):** Applying Tukey's IQR rule after single median imputation collapses `IQR → 0.00` and falsely flags **`2,466 / 2,466` (`100.00%`)** of valid `purchase_amount` orders, **`2,410 / 2,465` (`97.77%`)** of valid `age` records, and **`852 / 855` (`99.65%`)** of valid `customer_tenure_days` records as outliers (`SD → 0.00`).

## Open Issues
- Ready for `DataVizAgent` (`M2`) to append boxplot/distribution panels (`assets/charts/m2_*.png`) right after the quantitative `[M2]` cells above, annotating the Layer 1 raw sentinels (`-999`, `-5`, `200`, `-1`), the inner Tukey fences (`[-9.5, 98.5]` yrs, `[-$2,702.36, $7,595.62]`, `[-1.0, 7.0]` Likert), and the `2,521`-row `feedback_score = 10` quartile-masking spike.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `load_clean_customers("v1")` (`10,000 × 15`) backward compatibility and `load_clean_customers("v2")` (`10,000 × 21`) schema casting.
- Verified `m2_iqr_outlier_summary.csv` (`6 × 25`) and `m2_outlier_treatment_comparison.csv` (`13 × 17`) naming conventions, deterministic 4-decimal rounding, and `check_conventions.py` handoff section ordering.
