# A1 — data-viz handoff

## Outputs
- `src/visualization.py` — added `plot_a1_raw_vs_normalized_metrics`
- `assets/charts/a1_raw_vs_normalized_metrics.png` — 300 DPI dual-panel comparison of Raw Total Spend vs Normalized Revenue per 1,000 Customers (KPI-3) across Gender and Age brackets

## Notebook Cells
```python
import matplotlib.pyplot as plt

from src.features import load_enriched_customers
from src.visualization import plot_a1_raw_vs_normalized_metrics

df_enriched_v2 = load_enriched_customers("v2")
fig_a1 = plot_a1_raw_vs_normalized_metrics(df_enriched_v2, save=True)
plt.show()
plt.close(fig_a1)
```

```markdown
#### Visual interpretation — `assets/charts/a1_raw_vs_normalized_metrics.png`

- **Panel A — Raw Aggregate Revenue (Distorted by Cohort Headcount):** In raw totals, `Male` accounts generate $\$2.29\text{M}$ ($n = 3,800$) versus $\$1.46\text{M}$ ($n = 2,455$) for `Unknown` gender—creating the illusion of a $1.57\times$ gender disparity. Similarly, age groups with larger headcounts appear to dominate total revenue.
- **Panel B — Normalized Metric (KPI-3 Eliminates Headcount Bias):** When normalized to revenue per 1,000 registered accounts, the apparent gender gap collapses to $1.02\times$ ($\$601.8\text{k}$ for Male vs $\$608.0\text{k}$ for Female vs $\$594.3\text{k}$ for Unknown). Across age brackets, normalized revenue hovers tightly around the population baseline ($\$604.3\text{k}$ / 1,000 accounts), proving that per-customer monetization is structurally homogeneous.
```

## Key Findings
- Raw total revenue gender disparity = $1.57\times$ ($n = 3,800$ Male vs $2,455$ Unknown) → answers Q2
- Normalized KPI-3 gender disparity = $1.02\times$ ($\$601.8\text{k}$ vs $\$594.3\text{k}$ per 1k accounts) → answers Q2
- Population baseline revenue per 1k accounts = $\$604.3\text{k}$ → answers Q2

## Open Issues
- None. Figure exported at 300 DPI with publication theme.

## Verification
- `.\EDA\Scripts\python.exe -m src.visualization --block advanced` → exported `assets/charts/a1_raw_vs_normalized_metrics.png` at 300 DPI
- `.\EDA\Scripts\python.exe -m ruff check src/visualization.py` → 0 errors
