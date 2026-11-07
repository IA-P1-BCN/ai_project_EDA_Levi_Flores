# E4 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — Pure, type-hinted quantitative analysis module (`load_clean_customers`, `compute_univariate_numeric_stats`, `compute_univariate_categorical_counts`, `compute_bivariate_segment_spend`, `run_bivariate_hypothesis_tests`, `compute_city_country_crosstab`, `compute_research_question_kpis`).
- `data/processed/summaries/e4_univariate_numeric_stats.csv` — Parametric (`n_valid`, `coverage_pct`, `mean`, `std`) and non-parametric (`min`, `q1`, `median`, `q3`, `max`, `iqr`, `skewness`, `kurtosis`) summary across `age`, `purchase_amount`, `feedback_score`, `feedback_score_1_to_5`, and chronologically valid `tenure_days`.
- `data/processed/summaries/e4_univariate_categorical_counts.csv` — Absolute counts (`n`), total dataset share (`pct_total`), and valid/known share (`pct_known`) across `gender`, `city`, `country`, discrete `feedback_score`, and 4-tier `contact_reachability`.

## Notebook Cells
```markdown
---

## 4. `[E4]` Univariate Analysis — Quantitative Profiling

Before constructing visual distributions, we compute both **parametric** (`mean`, `SD`) and **non-parametric** (`median`, `Q1`, `Q3`, `IQR`, `min`, `max`, `skewness`, `kurtosis`) univariate statistics across all valid numeric observations, alongside total and known-record frequency shares across categorical and reachability dimensions (`src/analysis.py`).
```

```python
import sys
from pathlib import Path

repo_root = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.analysis import (
    compute_univariate_categorical_counts,
    compute_univariate_numeric_stats,
    load_clean_customers,
)

df_clean_e4 = load_clean_customers("v1")
e4_num_stats = compute_univariate_numeric_stats(df_clean_e4)
e4_cat_counts = compute_univariate_categorical_counts(df_clean_e4)

print("=== [E4] UNIVARIATE NUMERIC STATISTICS (PARAMETRIC & NON-PARAMETRIC) ===")
print(e4_num_stats.round(2).to_string(index=False))

print("\n=== [E4] UNIVARIATE CATEGORICAL & REACHABILITY COUNTS ===")
print(e4_cat_counts.round(2).to_string(index=False))
```

```markdown
**Quantitative Interpretation (`E4`):**
- **Demographics (`Q1`):** Valid `age` covers **24.65%** of accounts ($n = 2,465$ of $10,000$; $7,535$ missing/sentinel remediated to `NaN`). Both parametric (`mean = 43.70` years, `SD = 15.30` years) and non-parametric (`median = 43.00` years, `IQR = 27.00` years, `Q1 = 31.00`, `Q3 = 58.00`, `range = 18.00–70.00`) metrics align closely, with near-zero skewness (`0.0602`) and negative excess kurtosis (`-1.1894`) characteristic of a flat, near-uniform age distribution. Known `gender` ($n = 7,545$, `75.45%` coverage) is balanced between `Male` ($n = 3,800$, `50.36%` of known) and `Female` ($n = 3,745$, `49.64%` of known). Known `city` ($n = 8,870$) is evenly split across 8 Indian cities (`11.91%` in `Kolkata` to `12.90%` in `Hyderabad`), while known `country` ($n = 8,296$) is evenly split (~`20%` each) across `USA`, `Australia`, `Canada`, `UK`, and `India`.
- **Transaction Spend (`Q2`):** Valid `purchase_amount` ($n = 2,466$, `24.66%` coverage) exhibits symmetric, platykurtic dispersion across `$10.31–$4,998.67`: `mean = $2,450.62` (`SD = $1,442.83`) and `median = $2,460.36` (`IQR = $2,574.50`, `Q1 = $1,159.39`, `Q3 = $3,733.88`, `skewness = 0.0139`, `kurtosis = -1.2150`), yielding `$6,043,218.46` in total verified spend.
- **Satisfaction, Lifecycle Tenure & Reachability (`Q3`):** Raw valid `feedback_score` ($n = 5,049$, `50.49%` coverage) has `mean = 6.48` (`median = 5.00`, `IQR = 7.00`) solely because an off-scale spike at `10` accounts for **49.93%** of all valid ratings ($n = 2,521$). Restricting to the standard Likert scale (`feedback_score_1_to_5`, $n = 2,528$) reveals a neutral central tendency (`mean = 2.96`, `SD = 1.42`, `median = 3.00`, `IQR = 2.00`). Chronologically valid `tenure_days` ($n = 855$ accounts where `last_purchase_date >= signup_date`) shows mild right skewness (`0.5179`), with `mean = 688.59` days (`SD = 464.11`) vs. `median = 638.00` days (`IQR = 710.50`, range `0–1,925` days). Across all $10,000$ accounts, **56.12%** ($n = 5,612$) are `Unreachable (None)`, leaving **43.88%** ($n = 4,388$) reachable via `Email Only` (`18.78%`), `Phone Only` (`18.76%`), or `Omnichannel (Both)` (`6.34%`).
```

## Key Findings
- **Near-Uniform Age & Balanced Gender Profile (`Q1`):** Valid `age` ($n = 2,465$, `24.65%` coverage) spans `18.0–70.0` years with `mean = 43.70` (`SD = 15.30`), `median = 43.00` (`IQR = 27.00`), `skewness = 0.0602`, and excess `kurtosis = -1.1894` (platykurtic/uniform); known `gender` ($n = 7,545$) splits `50.36%` `Male` ($3,800$) vs. `49.64%` `Female` ($3,745$).
- **Symmetric, Wide-Dispersion Transaction Value (`Q2`):** Valid `purchase_amount` ($n = 2,466$, `24.66%` coverage) yields `mean = $2,450.62` (`SD = $1,442.83`) and `median = $2,460.36` (`IQR = $2,574.50`, `Q1 = $1,159.39`, `Q3 = $3,733.88`, `skewness = 0.0139`, `kurtosis = -1.2150`), totaling `$6,043,218.46`.
- **Severe Bimodal Rating Distortion at Score `10` (`Q3`):** Across $n = 5,049$ valid `feedback_score` entries, `2,521` records (`49.93%` of valid ratings; `25.21%` of total) sit at `10`, inflating overall `mean` to `6.48` (`median = 5.00`), whereas standard `1–5` ratings ($n = 2,528$) center at `mean = 2.96` (`SD = 1.42`, `median = 3.00`, `IQR = 2.00`).
- **Right-Skewed Valid Lifecycle Tenure (`Q3`):** Among $1,684$ dual-date rows, excluding $829$ chronologically inverted records (`49.23%`) leaves $n = 855$ valid `tenure_days` observations (`8.55%` of total) with `mean = 688.59` days (`SD = 464.11`), `median = 638.00` days (`IQR = 710.50`), and `skewness = 0.5179`.
- **Majority Contact Unreachability (`Q3`):** Only $4,388$ customers (`43.88%`) have at least one valid contact channel (`634` [`6.34%`] `Omnichannel (Both)`, `1,878` [`18.78%`] `Email Only`, `1,876` [`18.76%`] `Phone Only`), while $5,612$ (`56.12%`) are `Unreachable (None)`.

## Open Issues
- Empirical reachability counts on `customers_clean_v1.csv` are `4,388` reachable (`43.88%`) and `634` omnichannel (`6.34%`), slightly refined from the pre-cleaning independence estimate (`43.96%` / `6.26%`) noted in `specs/ontology.md` §4; `DataVizAgent` and `ExecutiveReporterAgent` should cite the exact empirical `customers_clean_v1.csv` counts (`4,388` / `43.88%` and `634` / `6.34%`).

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --select=E9,F63,F7,F82` → `0 errors`
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `e4_univariate_numeric_stats.csv` (5 variables × 15 columns) and `e4_univariate_categorical_counts.csv` (29 category rows × 5 columns) deterministic generation against `data/processed/customers_clean_v1.csv`.
