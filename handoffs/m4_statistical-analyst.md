# M4 — statistical-analyst handoff

## Outputs
- `src/features.py` — Pure, deterministic, idempotent feature engineering module (`engineer_features`, `validate_enriched_customers`, `load_enriched_customers`, `summarize_engineered_features`, `export_m4_features`) implementing the exact 6 `StatisticalAnalystAgent`-owned ontology features (`specs/ontology.md` §3.2).
- `data/processed/customers_enriched_v1.csv` *(materialized deterministically via `.\EDA\Scripts\python.exe -m src.features` / `export_m4_features()`)* — Full `10,000` rows × `27` columns enriched dataset (`21` `v2` columns + `6` analytical features).
- `data/processed/summaries/m4_engineered_features_summary.csv` — Unified 20-row × 22-column profile of all 6 engineered features (tier counts, total/known shares `%`, valid spend means/medians/revenue shares `%`, and continuous parametric/non-parametric distribution metrics).

## Notebook Cells
```markdown
---

## 10. `[M4]` Feature Engineering & Analytical Value (`customers_enriched_v1.csv`)

To unlock executive segmentation, lifecycle retention modeling (`M6`), normalized revenue benchmarking (`A1`), and variance-stabilized parametric analysis (`A4`), we implement the six canonical analytical features defined in `specs/ontology.md` §3.2 (`src/features.py`), expanding the `21`-column `v2` schema into the **`27`-column `customers_enriched_v1.csv` dataset**:

| Engineered Feature | Dtype | Exact Ontology Rule (`specs/ontology.md` §3.2) | Analytical Value |
|---|---|---|---|
| `age_group` | ordered `category` | `18-29 (Young Adult)`, `30-44 (Early Career)`, `45-59 (Mid-Senior)`, `60+ (Senior)`, `Unknown` | Demographic cohort profiling without losing the `75.35%` missing-age population (`Q1`, `Q2`). |
| `spend_tier` | ordered `category` | Fixed thresholds: `< $1,200` (`Low`), `$1,200–$3,500` (`Medium`), `> $3,500` (`High`), `Missing` | Isolates commercial VIP revenue concentration independent of sample quantiles (`Q2`). |
| `feedback_tier` | ordered `category` | `Detractor (1-2)`, `Passive (3)`, `Promoter (4-5)`, `Scale-10 Spike (10)`, `Missing` | Separates standard NPS-style sentiment tiers from the `2,521`-row off-scale `10` anomaly (`Q3`). |
| `contact_reachability_tier` | ordered `category` | `Omnichannel (Both)`, `Email Only`, `Phone Only`, `Unreachable (None)` | Routes CRM retention campaigns by verified channel availability (`Q3`). |
| `customer_tenure_days` | `float64` | `(last_purchase_date - signup_date).dt.days` where `~is_date_inverted` (`else NaN`) | Quantifies true active customer lifecycle duration in days, free of `829` inverted timestamps (`Q3`, `M6`). |
| `log_purchase_amount` | `float64` | `np.log1p(purchase_amount).round(6)` | Compresses the `484.8×` dollar range (`$10.31–$4,998.67`) to `[2.43, 8.52]` for elasticity/scale evaluation (`A4`). |
```

```python
from src.analysis import load_clean_customers
from src.features import (
    engineer_features,
    summarize_engineered_features,
    validate_enriched_customers,
)

df_v2_m4 = load_clean_customers("v2")
df_enriched = engineer_features(df_v2_m4)
validate_enriched_customers(df_enriched)
m4_profile = summarize_engineered_features(df_enriched)

print(f"Enriched dataset shape: {df_enriched.shape[0]:,} rows × {df_enriched.shape[1]} columns")
print("Engineered columns added:", list(df_enriched.columns[21:]))

cat_profile = m4_profile[m4_profile["feature_type"] == "ordered_category"][
    [
        "feature_name",
        "level_or_scope",
        "n_records",
        "pct_of_total",
        "pct_of_known",
        "valid_spend_n",
        "mean_spend_usd",
        "median_spend_usd",
        "total_spend_usd",
        "spend_share_pct",
    ]
]
print("\n=== [M4.1] ORDERED CATEGORICAL ENGINEERED FEATURES PROFILE ===")
print(cat_profile.round(2).to_string(index=False))

cont_profile = m4_profile[m4_profile["feature_type"] == "continuous_float64"][
    [
        "feature_name",
        "n_records",
        "pct_of_total",
        "cont_mean",
        "cont_std",
        "cont_min",
        "cont_q1",
        "cont_median",
        "cont_q3",
        "cont_max",
        "cont_iqr",
        "cont_skewness",
        "cont_kurtosis",
    ]
]
print("\n=== [M4.2] CONTINUOUS ENGINEERED FEATURES PROFILE ===")
print(cont_profile.round(4).to_string(index=False))
```

```markdown
**Quantitative Interpretation (`M4`):**
- **VIP Revenue Concentration via `spend_tier` (`Q2`):** Fixed commercial thresholds demonstrate that **`High (>$3,500)` VIP orders** account for **`29.36%` of valid transactions** ($n = 724$; `7.24%` of all `10,000` accounts) yet generate **`$3,057,313.93` — over half (`50.59%`) of all verified revenue** (`mean = $4,222.81`, `median = $4,213.43`). `Medium ($1,200-$3,500)` ($n = 1,105$, `44.81%` of valid orders) contributes **`43.07%`** (`$2,602,998.72`), while `Low (<$1,200)` ($n = 637$, `25.83%` of valid orders) contributes just **`6.34%`** (`$382,905.81`). Because demographic and geographic segments show uniform average spend (`E5`), **`spend_tier` is the primary actionable value discriminator**.
- **Sentiment & Reachability Tiering (`Q3`):** `feedback_tier` cleanly separates `Scale-10 Spike (10)` ($n = 2,521$, `49.93%` of valid ratings; `$1,476,038.15` spend) from standard Likert respondents, where `Detractor (1-2)` ($n = 1,027$, `20.34%` of valid) exceeds `Promoter (4-5)` ($n = 945$, `18.72%`) and `Passive (3)` ($n = 556$, `11.01%`). `contact_reachability_tier` confirms that `Unreachable (None)` ($n = 5,612$, `56.12%`) holds **`56.06%` (`$3,388,004.29`)** of total verified spend, vs. `6.62%` (`$400,214.23`) in `Omnichannel (Both)` ($n = 634$).
- **Lifecycle Duration & Logarithmic Spend Compression (`Q2`, `Q3`):** Valid `customer_tenure_days` ($n = 855$, `8.55%` of total) spans `0–1,925` days with `mean = 688.59` days (`SD = 464.11`) and `median = 638.00` days (`IQR = 710.50`, `Q1 = 299.50`, `Q3 = 1,010.00`, `skewness = +0.5179`). Meanwhile, `log_purchase_amount` ($n = 2,466$) compresses the `484.8×` raw dollar span (`$10.31–$4,998.67`, `SD = $1,442.83`, `skewness = +0.0139`) into `[2.4257, 8.5171]` (`mean = 7.4910`, `SD = 0.9879`, `median = 7.8085`, `IQR = 1.1690`), while empirically introducing left-skewness (`skewness = -1.6273`, `kurtosis = +2.9457`) because raw spend is uniform rather than right-skewed — a key diagnostic benchmark for `[A4]`.
```

## Key Findings
- **`High (>$3,500)` Spend Tier Drives `50.59%` of Total Revenue (`Q2`):** Across $n = 2,466$ valid transactions, `724` `High (>$3,500)` VIP accounts (`29.36%` of valid orders; `mean = $4,222.81`, `median = $4,213.43`) generate **`$3,057,313.93`** (`50.59%` of `$6,043,218.46`), outperforming `Medium ($1,200-$3,500)` (`43.07%`, $n = 1,105$) and `Low (<$1,200)` (`6.34%`, $n = 637$).
- **Demographic Lifecycle Cohort Distribution (`Q1`, `Q2`):** Among $n = 2,465$ known-age customers (`24.65%` of total), `30-44 (Early Career)` is the largest cohort ($n = 742$, `30.10%` of known), followed by `45-59 (Mid-Senior)` ($n = 648$, `26.29%`), `18-29 (Young Adult)` ($n = 571$, `23.16%`), and `60+ (Senior)` ($n = 504$, `20.45%`), with explicit `'Unknown'` ($n = 7,535$) preventing row attrition.
- **Actionable Sentiment & Channel Tiers (`Q3`):** `feedback_tier` isolates `Scale-10 Spike (10)` ($n = 2,521$, `25.21%` of total) from `Detractor (1-2)` ($1,027$, `10.27%`), `Promoter (4-5)` ($945$, `9.45%`), and `Passive (3)` ($556$, `5.56%`); `contact_reachability_tier` segments `Unreachable (None)` (`56.12%`, `$3.39M` spend) from `Email Only` (`18.78%`), `Phone Only` (`18.76%`), and `Omnichannel (Both)` (`6.34%`).
- **Continuous Lifecycle & Log-Scale Diagnostics (`Q2`, `Q3`):** Chronologically valid `customer_tenure_days` ($n = 855$) centers at `median = 638.00` days (`IQR = 710.50`, `mean = 688.59`, `skewness = 0.5179`), while `log_purchase_amount` ($n = 2,466$, rounded to 6 decimals) compresses `SD` from `1,442.83` to `0.9879` (`IQR = 1.1690`) and documents left-skewness (`-1.6273`) on uniform spend.

## Open Issues
- Because `run_command` executes in the read-only sandbox (`BypassSandbox: false`) and `customers_enriched_v1.csv` (`10,000 × 27`, ~`2.3 MB`) exceeds inline tool text size, `export_m4_features()` was verified in scratch storage (`SHA-256 = 6613a0abfbbd4fa6...` across repeated runs). Please run `.\EDA\Scripts\python.exe -m src.features` on the host before `run_local_ci.py` to materialize `data/processed/customers_enriched_v1.csv` on disk.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `engineer_features(engineer_features(df_v2))` idempotency (`pd.testing.assert_frame_equal` → `PASS`), `load_enriched_customers("v1")` round-trip dtype restoration (`10,000 × 27`), `validate_enriched_customers` schema contract, and identical SHA-256 digests across repeated `export_m4_features()` runs.
