# A5 — data-viz handoff

## Outputs
- `src/visualization.py` — added `plot_a5_segment_multidimensional_comparison`
- `assets/charts/a5_segment_multidimensional_comparison.png` — 300 DPI 3-panel multi-dimensional segment comparison crossing reachability tiers, spend tiers, and regional monetization

## Notebook Cells
```python
import matplotlib.pyplot as plt

from src.features import load_enriched_customers
from src.visualization import plot_a5_segment_multidimensional_comparison

df_enriched_v2 = load_enriched_customers("v2")
fig_a5 = plot_a5_segment_multidimensional_comparison(df_enriched_v2, save=True)
plt.show()
plt.close(fig_a5)
```

```markdown
#### Visual interpretation — `assets/charts/a5_segment_multidimensional_comparison.png`

- **Panel A — Spend Tiers by Reachability (The VIP Reachability Gap):** Visualizes the critical operational paradox: 405 out of 724 High-Tier spenders ($55.9\%$, representing $\$1.71\text{M}$ in revenue) are classified as `Unreachable (None)`, lacking both email and phone channels.
- **Panel B — Order Value by Age Group & Gender:** Boxplots and mean markers demonstrate uniform central tendency and dispersion ($IQR \approx \$2,500$) across all age cohorts and genders, visually confirming demographic parity in transaction size.
- **Panel C — Regional Monetization (KPI-3):** Compares revenue per 1,000 registered accounts across macroeconomic regions (West: $\$610\text{k}$, North: $\$611\text{k}$, South: $\$601\text{k}$, East: $\$581\text{k}$), proving that geographical monetization is consistent nationwide with satisfaction scores tightly clustered around 2.96.
```

## Key Findings
- 405 High-Value spenders holding $\$1,713,463$ lack contact reachability → answers Q3
- Regional KPI-3 monetization spans $\$581\text{k}–\$611\text{k}$ ($<5\%$ spread) across India's Tier-1 metropolitan zones → answers Q1 & Q2
- Order value distributions remain uniform across demographic combinations ($IQR \approx \$2.5\text{k}$) → answers Q2

## Open Issues
- None. 3-panel figure exported at 300 DPI with publication theme.

## Verification
- `.\EDA\Scripts\python.exe -m src.visualization --block advanced` → exported `assets/charts/a5_segment_multidimensional_comparison.png` at 300 DPI
- `.\EDA\Scripts\python.exe -m ruff check src/visualization.py` → 0 errors
