# A1 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — added `compute_a1_normalized_metrics_comparison`
- `data/processed/summaries/a1_normalized_metrics_comparison.csv` — 27-row summary comparing raw totals vs normalized KPI-3 metrics across `gender`, `age_group`, `city`, and `country`

## Notebook Cells
```markdown
### 16.1 `[A1]` Metric Normalisation — Revenue per 1,000 Customers (KPI-3)

Comparing raw transaction totals across unevenly populated customer cohorts introduces severe headcount distortion. For instance, `Male` accounts generate $\$2,286,839$ in raw total revenue versus $\$1,458,954$ for `Unknown` gender—creating the false commercial impression that male customers are $1.57\times$ more lucrative.

By normalising metrics against cohort headcount ($N_k$) using **KPI-3: Revenue per 1,000 Registered Customers**:
$$\text{Revenue per 1,000 Customers} = \frac{\sum_{i \in S} \text{purchase\_amount}_i}{N_{\text{headcount}, S}} \times 1,000$$
and measuring **Average Order Value (AOV)** across valid paying transactions, we eliminate sample-size bias and reveal true underlying customer spend behaviour.
```

```python
from src.analysis import compute_a1_normalized_metrics_comparison
from src.features import load_enriched_customers

df_enriched_v2 = load_enriched_customers("v2")
a1_df = compute_a1_normalized_metrics_comparison(df_enriched_v2)
a1_df[[
    "dimension", "segment_value", "total_headcount", "headcount_share_pct",
    "valid_orders_count", "raw_total_revenue_usd", "raw_revenue_share_pct",
    "mean_order_value_usd", "revenue_per_1k_registered_usd", "headcount_bias_factor"
]]
```

```markdown
**Quantitative Findings & Rationale (`Q2`):**
- **Disparity Illusion Dispelled:** Across `gender`, Male accounts generate $\$601,799$ per 1,000 registered accounts (AOV $=\$2,459.01$), Female accounts generate $\$608,014$ per 1,000 accounts (AOV $=\$2,442.22$), and Unknown gender generates $\$594,278$ per 1,000 accounts (AOV $=\$2,452.02$). The disparity ratio collapses from $1.57\times$ on raw totals down to $1.02\times$ on normalized metrics.
- **Demographic Uniformity:** Across `age_group`, normalized revenue per 1,000 customers remains tightly clustered between $\$582,164$ (`45-59 Mid-Senior`) and $\$632,426$ (`30-44 Early Career`), confirming that per-capita monetization is structurally uniform across age brackets.
- **Strategic Implication:** Marketing resource allocation must not prioritize segments based on aggregate transaction volume; instead, growth strategy must focus on customer acquisition and contact reachability, since per-customer economic yield is homogeneous.
```

## Key Findings
- Male vs Unknown raw total revenue disparity = $1.57\times$ ($n = 3,800$ vs $2,455$) → answers Q2
- Male vs Unknown normalized revenue disparity = $1.02\times$ ($\$601.8\text{k}$ vs $\$594.3\text{k}$ per 1k accounts) → answers Q2
- Demographics AOV = $\$2,442.22$ (Female, $n = 933$) vs $\$2,459.01$ (Male, $n = 930$) → answers Q2

## Open Issues
- `DataVizAgent` needs to generate comparative visualization `a1_raw_vs_normalized_metrics.png` displaying side-by-side bar plots of raw totals versus normalized KPI-3 values.

## Verification
- `ruff check src/analysis.py` → 0 errors
- `data/processed/summaries/a1_normalized_metrics_comparison.csv` generated and validated across 27 distinct segment rows.
