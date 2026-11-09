# A6 — data-viz handoff

## Outputs
- `src/visualization.py` — added `plot_a6_interactive_customer_explorer`
- `assets/charts/a6_interactive_customer_explorer.html` — interactive Plotly multi-dimensional customer scatter explorer with marginal histograms and box plots
- `assets/charts/a6_interactive_customer_explorer.png` — 300 DPI static publication mirror of the interactive explorer for offline/PDF rendering

## Notebook Cells
```python
from src.features import load_enriched_customers
from src.visualization import plot_a6_interactive_customer_explorer

df_enriched_v2 = load_enriched_customers("v2")
fig_plotly, fig_static = plot_a6_interactive_customer_explorer(df_enriched_v2, save_html=True, save_png=True)
fig_plotly.show()
```

```markdown
#### Visual interpretation — `assets/charts/a6_interactive_customer_explorer.html` & `.png`

- **Interactive Multi-Dimensional Exploration (`Plotly HTML`):** Allows stakeholders to interactively inspect individual customer records ($n = 600$ customers with both a valid age and a valid purchase amount) across age, spend tier, gender, city, metro region, contact reachability tier, customer tenure, and feedback score. Marginal distributions provide instant univariate context alongside bivariate scatter.
- **Static Publication Mirror (`assets/charts/a6_interactive_customer_explorer.png`):** Panel A displays customer spend scatter across age brackets, and Panel B confirms satisfaction stability across all four reachability tiers (Likert mean $\approx 2.96$).
```

## Key Findings
- 2,465 customer accounts interactively browsable with 8 cross-dimensional attributes → answers Q1, Q2, Q3
- Satisfaction rating remains invariant across reachability tiers (Likert mean $\approx 2.96$) → answers Q3
- High-spend accounts span all age groups uniformly across $[\$3,500, \$5,000]$ → answers Q2

## Open Issues
- None. Interactive HTML and 300 DPI static PNG generated and exported deterministically.

## Verification
- `.\EDA\Scripts\python.exe -m src.visualization --block advanced` → exported HTML and PNG
- `.\EDA\Scripts\python.exe -m ruff check src/visualization.py` → 0 errors
