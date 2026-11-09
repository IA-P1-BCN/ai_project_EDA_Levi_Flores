# A5 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — added `compute_a5_segment_profiles`
- `data/processed/summaries/a5_segment_profiles.csv` — multi-dimensional segmentation table crossing spend tiers and contact reachability

## Notebook Cells
```markdown
### 20.1 `[A5]` Multi-Dimensional Segment Comparison & Behavioural Profiles

To transition from isolated univariate slices to comprehensive customer profiling, we construct a multi-dimensional matrix crossing commercial value tiers (`spend_tier`) with operational marketing reachability (`contact_reachability_tier`) and geographic regions (`metro_region`).
```

```python
from src.analysis import compute_a5_segment_profiles
from src.features import load_enriched_customers

df_enriched_v2 = load_enriched_customers("v2")
a5_profiles_df = compute_a5_segment_profiles(df_enriched_v2)
a5_profiles_df[[
    "spend_tier", "contact_reachability_tier", "customer_count", "customer_share_pct",
    "valid_orders_count", "total_revenue_usd", "revenue_share_pct", "mean_order_value_usd"
]]
```

```markdown
**Multi-Dimensional Profiling Takeaways (`Q2`, `Q3`):**
- **The VIP Reachability Paradox:** High-tier accounts ($> \$3,500$) represent $724$ paying customers ($29.36\%$ of buyers) but generate $\$3,059,514$ ($50.63\%$ of total verified revenue). However, among these $724$ high-value buyers, **$405$ customers ($55.9\%$) are classified as `Unreachable (None)`**—holding $\$1,713,463$ in commercial transactions without an operational marketing channel.
- **Omnichannel Premium:** Customers reachable via both email and phone (`Omnichannel (Both)`) represent only $626$ total accounts ($6.26\%$) and $150$ active buyers, generating $\$364,577$ in revenue.
- **Actionable Strategic Priority:** Marketing and CRM efforts must focus immediate budget on contact data enrichment (re-engagement campaigns, SMS opt-ins, email validation) targeting the $405$ high-value unreachable accounts, protecting $\$1.71\text{M}$ from silent customer attrition.
```

## Key Findings
- High-tier revenue concentration = 724 customers generate $\$3,059,514$ (50.63% of revenue) → answers Q2
- Unreachable high-value accounts = 405 customers hold $\$1,713,463$ without contact channels → answers Q3
- Reachability distribution across spend = Low ($55.4\%$ unreachable), Medium ($56.5\%$ unreachable), High ($55.9\%$ unreachable) → answers Q3

## Open Issues
- `DataVizAgent` needs to generate publication chart `a5_segment_multidimensional_comparison.png` visualizing the spend tier vs reachability matrix and regional customer yields.

## Verification
- `ruff check src/analysis.py` → 0 errors
- Groupby completeness assertion passed: $10,000$ accounts accounted for without loss.
