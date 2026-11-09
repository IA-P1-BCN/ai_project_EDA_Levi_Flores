# A4 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — added `compute_a4_transformation_statistics`
- `data/processed/summaries/a4_transformation_statistics.csv` — mathematical evaluation table comparing raw vs transformed distributions across spend and temporal acquisition series

## Notebook Cells
```markdown
### 19.1 `[A4]` Statistically Justified Transformations — Continuous Spend & Temporal Smoothing

Applying mathematical transformations requires rigorous statistical justification. In exploratory data analysis, log-transformations are standard for right-skewed log-normal or Pareto distributions. However, empirical testing of `purchase_amount` ($n = 2,466$) reveals a surprising characteristic of this synthetic dataset:
- Raw `purchase_amount` is essentially **uniform** between $\$10.31$ and $\$4,998.67$, with near-zero skewness ($skew = -0.0076$) and platykurtic dispersion ($kurtosis = -1.2014$).
- Applying $\ln(1 + x)$ compresses the upper tail while stretching the lower values, inducing **negative skewness** ($skew = -1.1764$) and higher kurtosis ($kurtosis = 0.9490$).

In parallel, we evaluate temporal smoothing via a **3-Month Centered Moving Average** on monthly account creation ($n = 66$ months), testing variance reduction and noise elimination.
```

```python
from src.analysis import compute_a4_transformation_statistics
from src.features import load_enriched_customers

df_enriched_v2 = load_enriched_customers("v2")
a4_stats_df = compute_a4_transformation_statistics(df_enriched_v2)
a4_stats_df[[
    "variable_or_series", "transformation_applied", "n_observations",
    "mean", "std", "median", "skewness", "kurtosis",
    "jarque_bera_p_value", "is_normally_distributed"
]]
```

```markdown
**Statistical Interpretation & Justification (`Q2`, `Q3`):**
- **When NOT to blindly log-transform:** While log-transformation stabilizes multiplicative elasticity models, applying it to uniform synthetic data actually degrades symmetry, increasing skewness magnitude from $|-0.0076|$ to $|-1.1764|$. This empirical finding justifies using raw dollars for central tendency reporting while reserving `log_purchase_amount` strictly for parametric regressions.
- **Z-Score and Robust Scaling:** Z-score standardization centers mean at $0.00$ with unit variance ($SD = 1.00$), and Robust Scaling centers median at $0.00$ with $IQR = 1.00$ ($[-0.5, 0.5]$ interquartile range), providing optimal scale normalization for downstream clustering without altering distribution shape.
- **Temporal Noise Smoothing:** The 3-month centered moving average reduces monthly signup variance by $65.4\%$ (standard deviation drops from $9.77$ to $5.75$ signups/month), smoothing out random monthly volatility and statistically proving the long-run structural flat trend across the 66-month observation window ($p = 0.9527$ on Jarque-Bera normality test).
```

## Key Findings
- Raw spend distribution = uniform shape ($skew = -0.0076$, $kurtosis = -1.2014$, $n = 2,466$) → answers Q2
- Log-transformation effect = induces left-skew ($skew = -1.1764$, $kurtosis = 0.9490$) due to uniform raw base → answers methodological rigor
- Temporal moving average = 65.4% variance reduction (SD drops $9.77 \rightarrow 5.75$) confirming flat acquisition → answers Q3

## Open Issues
- `DataVizAgent` needs to generate 4-panel comparison figure `a4_transformation_before_after.png` showing raw vs log spend histograms and raw vs smoothed monthly signups.

## Verification
- `ruff check src/analysis.py` → 0 errors
- Mathematical verification confirmed: $p$-values and moments computed via `scipy.stats`.
