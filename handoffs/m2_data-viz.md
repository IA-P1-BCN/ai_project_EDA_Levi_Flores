# M2 — data-viz handoff

## Outputs
- `src/visualization.py` — Added `output_dir` support to `save_publication_figure`, `SOURCE_CAPTION_V2` (`customers_clean_v2.csv`), `plot_m2_iqr_outlier_boxplots`, `plot_m2_imputation_variance_distortion`, `generate_m2_charts`, and `--block m2` CLI orchestration.
- `assets/charts/m2_iqr_outlier_boxplots.png` — 300 DPI 2×2 publication panel auditing Tukey $1.5 \times \text{IQR}$ fences across `age` ($n = 2,465$), `purchase_amount` ($n = 2,466$, with `[P01, P99]` winsorization check), `customer_tenure_days` ($n = 855$), and `feedback_score` quartile-masking proof ($n = 5,049$ full scale vs. $n = 2,528$ clean `1–5` Likert).
- `assets/charts/m2_imputation_variance_distortion.png` — 300 DPI 1×2 multi-row distribution + boxplot proof comparing `NaN Retention (Chosen)` against the `Naive Median Imputation + Tukey IQR (Rejected)` anti-pattern across `age` and `purchase_amount`.

## Notebook Cells
```markdown
### 8.1 `[M2]` Visual Outlier Audit & Imputation-Distortion Proof

To verify our quantitative treatment rules visually, we render two publication diagnostics (`src/visualization.py`):
1. **Tukey $1.5 \times \text{IQR}$ Domain Fence Audit (`m2_iqr_outlier_boxplots.png`):** Plots valid continuous distributions directly inside their formal inner fences alongside `[P01, P99]` winsorization bounds and the `feedback_score = 10` quartile-breakdown masking proof.
2. **Imputation-Before-Filtering Anti-Pattern Proof (`m2_imputation_variance_distortion.png`):** Demonstrates why applying Tukey's IQR rule after single-median imputation destroys `97.77%–100.00%` of genuine observations when missingness exceeds `75%`.
```

```python
import matplotlib.pyplot as plt

from src.analysis import load_clean_customers
from src.visualization import (
    plot_m2_imputation_variance_distortion,
    plot_m2_iqr_outlier_boxplots,
)

df_v2_m2 = load_clean_customers("v2")

fig_m2_iqr = plot_m2_iqr_outlier_boxplots(df_v2_m2, save=True)
plt.show()
plt.close(fig_m2_iqr)
```

```markdown
**Visual Interpretation — Tukey IQR Fences & Quartile-Breakdown Masking (`Q1`, `Q2`, `Q3`):**
- **Panels (a)–(c) — Zero Continuous Domain Outliers (`Q1` Age, `Q2` Spend, `Q3` Tenure):** Once upstream ingestion sentinels (`4,959` rows of `-5`/`200` in `age`, `5,034` rows of `-999`/`'N/A'` in `purchase_amount`, and `829` inverted date pairs in `customer_tenure_days`) are isolated to `NaN`, 100% of observed values sit comfortably inside formal Tukey inner fences (`age` range `18–70` yrs inside `[-9.5, 98.5]`, $n = 2,465$; `purchase_amount` range `$10.31–$4,998.67` inside `[-$2,702.36, $7,595.62]`, $n = 2,466$; `customer_tenure_days` range `0–1,925` days inside `[-766.25, 2,075.75]`, $n = 855$). On `purchase_amount`, `[P01 = $57.52, P99 = $4,941.58]` winsorization lowers `SD` by just `-0.07%` (`$1,442.83 → $1,441.83`) while needlessly censoring `50` genuine orders, confirming **unclipped retention** as optimal.
- **Panel (d) — Quartile Masking of the `feedback_score = 10` Spike (`Q3` Satisfaction):** Across all $n = 5,049$ valid ratings, the `2,521` observations at `score = 10` (`49.93%` of valid) exceed the `25%` breakdown point of sample quartiles, pulling raw `Q3` from `4.0` to `10.0` (`IQR = 7.0`) and pushing the raw upper fence to `20.5` — completely masking the anomaly. Evaluated against the true `1–5` Likert scale (`feedback_score_1_to_5`, $n = 2,528$, `Q1 = 2.0`, `Median = 3.0`, `Q3 = 4.0`, `upper fence = 7.0`), `score = 10` stands `+1.5 × IQR` above the fence. Rather than capping `10 → 5` (which fabricates a `+266.77%` Promoter surge from `945` to `3,466`), isolating the anomaly via `is_score_10_spike` preserves unbiased `1–5` sentiment metrics.
```

```python
fig_m2_imp = plot_m2_imputation_variance_distortion(df_v2_m2, save=True)
plt.show()
plt.close(fig_m2_imp)
```

```markdown
**Visual Interpretation — Why Outlier Filtering Must Precede or Exclude Single Imputation (`Q1`, `Q2`):**
- **Artificial Variance Compression (`M1` Link):** Filling `75.35%` missing `age` ($7,535$ rows at `43.0` yrs) and `75.34%` missing `purchase_amount` ($7,534$ rows at `$2,460.36`) injects a massive needle spike exceeding `7,630` accounts in a single central bin (`symlog` top panels), slashing parametric `SD` by **`-50.32%`** (`15.30 → 7.60` yrs) on `age` and **`-50.35%`** (`$1,442.83 → $716.40`) on `purchase_amount`.
- **Catastrophic IQR & Tukey Fence Collapse (`M2` Link):** Because `>75%` of the imputed column equals the median, `Q1 = Median = Q3` (`IQR = 0.00`, a **`-100.00%`** collapse). Consequently, the $1.5 \times \text{IQR}$ fences degenerate to zero-width points (`[43.0, 43.0]` yrs and `[$2,460.36, $2,460.36]`), **falsely destroying `2,410 / 2,465` (`97.77%`) of genuine customer ages and `2,466 / 2,466` (`100.00%`) of genuine transactions** as supposed "outliers" (`bottom panels`). Retaining `NaN` on primary analytical columns preserves 100% of genuine customer variance (`0.00%` false outlier loss).
```

## Key Findings
- **Zero Statistical Outliers Across Clean Continuous Domains (`Q1`, `Q2`, `Q3`):** `age` ($n = 2,465$, fences `[-9.5, 98.5]` yrs), `purchase_amount` ($n = 2,466$, fences `[-$2,702.36, $7,595.62]`), and `customer_tenure_days` ($n = 855$, fences `[-766.25, 2,075.75]` days) exhibit `0` Tukey (`1.5×IQR`) and `0` extreme (`3.0×IQR`) outliers; `[P01, P99]` winsorization alters `purchase_amount` `SD` by `-0.07%` while censoring `50` genuine orders, justifying unclipped retention.
- **Empirical Quartile-Masking Proof on `feedback_score` (`Q3`):** The `2,521` ratings at `score = 10` (`49.93%` of $n = 5,049$ valid) breach Tukey's `25%` quartile breakdown point (`raw Q3 = 10.0, fence = 20.5`), whereas clean `1–5` Likert (`n = 2,528`, `Q1 = 2.0, Q3 = 4.0, fence = 7.0`) proves `10` is `+1.5×IQR` off-scale; `is_score_10_spike` isolation avoids the `+266.77%` Promoter distortion caused by `10 → 5` capping.
- **Rejection of Impute-Then-Filter Anti-Pattern (`Q1`, `Q2`):** Naive median imputation at `75.35%` / `75.34%` missingness slashes `SD` by `-50.32%` / `-50.35%`, collapses `IQR` by `-100.00%` (`0.00`), and causes Tukey's IQR filter to falsely wipe out `97.77%` (`2,410 / 2,465`) of valid ages and `100.00%` (`2,466 / 2,466`) of valid transactions.

## Open Issues
- None. Both `M2` charts verified at `300 DPI` (`seed=42`, `0` warnings) in `$env:TEMP`; Lead Orchestrator can materialize `assets/charts/m2_iqr_outlier_boxplots.png` and `assets/charts/m2_imputation_variance_distortion.png` via `.\EDA\Scripts\python.exe -m src.visualization --block m2`.

## Verification
- `.\EDA\Scripts\python.exe -m src.visualization --block m2 --output-dir "$env:TEMP"` → `0 warnings`, `0 errors`, exported both PNGs at `300.0 DPI`.
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/visualization.py` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/visualization.py --max-line-length=127` → `0 errors`
- Visual inspection completed via `read_file` on `$env:TEMP\m2_iqr_outlier_boxplots.png` and `$env:TEMP\m2_imputation_variance_distortion.png` confirming zero overlapping labels, crisp margins, and exact `check_conventions.py` compliance.
