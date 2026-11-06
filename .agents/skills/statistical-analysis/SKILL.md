---
name: statistical-analysis
description: >-
  Execute rigorous univariate and bivariate statistical analysis, Tukey IQR outlier detection,
  multi-dimensional aggregations (groupby, agg, pivot_table), feature engineering, metric
  normalization, and correlation analysis. Activate this skill for tasks E4, E5, E6, M2, M3, M4,
  M5, M6, A1, A2, or A4.
---

# Statistical Analysis & Feature Engineering Skill (`statistical-analysis`)

This skill defines the quantitative methodology and output standards for `StatisticalAnalystAgent` across the Essential (`E4–E6`), Medium (`M2–M6`), and Advanced (`A1–A4`) milestones.

---

## 1. Univariate & Bivariate Statistical Protocol (`E4–E6`)

1. **Dual Central Tendency & Dispersion Reporting:**
   For every continuous variable (`age`, `purchase_amount`, `customer_tenure_days`), always compute and report **both parametric and non-parametric statistics**:
   - Parametric: `count` ($n$), `mean` ($\bar{x}$), `std` ($s$).
   - Non-parametric: `median` ($Q_2$), `Q1` ($25\text{th}$ percentile), `Q3` ($75\text{th}$ percentile), `IQR` ($Q_3 - Q_1$), `min`, `max`, `skewness`, and `kurtosis`.
2. **Categorical Frequency & Valid Share Reporting:**
   For every categorical variable (`gender`, `city`, `country`, `age_group`, `spend_tier`), report:
   - Absolute count ($n_k$)
   - Share of total records ($\frac{n_k}{10,000} \times 100\%$)
   - Share of known/valid records excluding `'Unknown'` ($\frac{n_k}{N_{\text{known}}} \times 100\%$)
3. **Bivariate Hypothesis & Effect Size:**
   - **Continuous × Categorical (`purchase_amount` across `gender`, `city`, `country`, `age_group`):** Compare group means, medians, IQRs, and run one-way ANOVA ($F$-statistic, $p$-value) or Kruskal-Wallis ($H$-statistic, $p$-value) to test whether observed segment differences are statistically significant or consistent with random noise.
   - **Continuous × Continuous (`age` vs. `purchase_amount`, `tenure` vs. `purchase_amount`):** Compute both Pearson's linear correlation ($r$) and Spearman's rank correlation ($\rho$) with $p$-values.

---

## 2. Outlier Detection & Treatment Protocol (`M2`)

Use Tukey's Interquartile Range (IQR) fences on valid non-null numeric series:

$$\text{IQR} = Q_3 - Q_1, \quad \text{Lower Fence} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Upper Fence} = Q_3 + 1.5 \times \text{IQR}$$

```python
def compute_iqr_outlier_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        s = df[col].dropna()
        q1, med, q3 = s.quantile([0.25, 0.50, 0.75])
        iqr = q3 - q1
        low_fence = q1 - 1.5 * iqr
        high_fence = q3 + 1.5 * iqr
        outliers = s[(s < low_fence) | (s > high_fence)]
        rows.append({
            "variable": col,
            "n_valid": len(s),
            "q1": round(q1, 2),
            "median": round(med, 2),
            "q3": round(q3, 2),
            "iqr": round(iqr, 2),
            "lower_fence": round(low_fence, 2),
            "upper_fence": round(high_fence, 2),
            "n_outliers": len(outliers),
            "outlier_pct": round(len(outliers) / len(s) * 100, 2),
        })
    return pd.DataFrame(rows)
```

- **Distinguish Data Corruption Sentinels from Statistical Outliers:**
  - Sentinels (`Age = -5`, `Age = 200`, `purchase_amount = -999`, `feedback_score = -1`) are **measurement/ingestion errors** remediated to `NaN` in `E3`.
  - Statistical outliers evaluated in `M2` are extreme observations *within* the plausible domain (`18 <= age <= 100`, `purchase_amount > 0`), plus the rating anomaly `feedback_score = 10`.

---

## 3. Aggregations & Feature Engineering Protocol (`M3`, `M4`, `A1`, `A4`)

1. **Multi-Dimensional Segment Tables (`M3`):**
   Export reproducible summary tables to `data/processed/summaries/` using `groupby`, `.agg()`, and `pd.pivot_table()` with explicit `observed=True`.
2. **Engineered Features (`M4`):**
   Implement in `src/features.py` the analytical features owned by `StatisticalAnalystAgent` in [`specs/ontology.md`](../../../specs/ontology.md) §3.2. **Copy labels, bins, and thresholds exactly from the ontology** — the list below is a reminder, not a second definition:
   - `age_group` (`18-29 (Young Adult)`, `30-44 (Early Career)`, `45-59 (Mid-Senior)`, `60+ (Senior)`, `Unknown`)
   - `spend_tier` (`Low (<$1,200)`, `Medium ($1,200-$3,500)`, `High (>$3,500)`, `Missing`) — fixed thresholds, not quantiles
   - `customer_tenure_days` (`(last_purchase_date - signup_date).dt.days` for valid chronological rows)
   - `contact_reachability_tier` (`Omnichannel (Both)`, `Email Only`, `Phone Only`, `Unreachable (None)`)
   - `feedback_tier` (`Detractor (1-2)`, `Passive (3)`, `Promoter (4-5)`, `Scale-10 Spike (10)`, `Missing`)
   - `log_purchase_amount` (`np.log1p(purchase_amount)`)

   Data-quality flags (`is_geo_mismatch`, `is_age_missing`, `feedback_score_1_to_5`, ...) belong to `DataCleanerAgent`; read them, never recreate them. To add a feature not listed in the ontology, record it in the handoff's `## Open Issues` so the Lead Orchestrator adds it to the ontology first.
3. **Metric Normalization (`A1`):**
   Always pair raw segment revenue totals with **Revenue per 1,000 Valid Customers** and **Average Order Value (AOV)** so unevenly sized segments are compared fairly.
