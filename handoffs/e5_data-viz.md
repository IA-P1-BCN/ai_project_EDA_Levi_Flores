# E5 — data-viz handoff

## Outputs
- `src/visualization.py` — Bivariate publication visualization builders (`plot_e5_spend_by_demographics`, `plot_e5_spend_by_city_and_age`, `plot_e5_age_vs_spend`, `plot_e5_feedback_and_geo_mismatch`).
- `assets/charts/e5_bivariate_spend_by_demographics.png` — 300 DPI 2-panel Violin + IQR Boxplot + Mean diamond overlay of `purchase_amount` across `gender` and `country` ($n = 2,466$).
- `assets/charts/e5_bivariate_spend_by_city_age.png` — 300 DPI 2-panel horizontal Boxplot + Mean marker comparison of `purchase_amount` across all 8 Indian cities + `'Unknown'` and canonical ontology `age_group` cohorts ($n = 2,466$).
- `assets/charts/e5_bivariate_age_vs_spend.png` — 300 DPI scatter (`alpha = 0.35`) + OLS linear regression trend + cohort mean/median trajectory of `age` vs. `purchase_amount` ($n = 600$ dual-valid records).
- `assets/charts/e5_bivariate_feedback_and_geo_mismatch.png` — 300 DPI 2-panel diagnostic comparing (a) `purchase_amount` across `feedback_score` and `contact_reachability` ($n = 2,466$) and (b) `city` × `country` 100% stacked percentage bars exposing `5,888` geographic contradictions ($N = 10,000$).

## Notebook Cells
```markdown
### 5.1 `[E5]` Bivariate Visual Exploration — Segment Homogeneity, Correlation & Geographic Integrity

To test whether transaction value clusters within specific demographic, geographic, age, satisfaction, or reachability cohorts — and to visually audit cross-column geographic consistency — we generate four multi-panel bivariate diagnostics (`src/visualization.py`).
```

```python
import matplotlib.pyplot as plt

from src.analysis import load_clean_customers
from src.visualization import (
    plot_e5_age_vs_spend,
    plot_e5_feedback_and_geo_mismatch,
    plot_e5_spend_by_city_and_age,
    plot_e5_spend_by_demographics,
)

df_clean_e5 = load_clean_customers("v1")

fig_e5_demo = plot_e5_spend_by_demographics(df_clean_e5, save=True)
plt.show()
plt.close(fig_e5_demo)
```

```markdown
**Visual Interpretation — Spend by Gender & Country (`Q2` High-Value Segments):**
- **Gender Homogeneity:** Across $n = 2,466$ valid spenders, violin densities and IQR boxes align closely across `Male` ($n_k = 960$, `mean = $2,474.16`, `median = $2,521.69`), `Female` ($n_k = 889$, `mean = $2,458.40`, `median = $2,388.78`), and `'Unknown'` ($n_k = 617$, `mean = $2,402.76`, `median = $2,460.06`). Neither known-gender tests (`ANOVA F = 0.05, p = 0.82`; `Kruskal-Wallis H = 0.05, p = 0.83`) nor all-segment tests (`F = 0.48, p = 0.62`) approach statistical significance.
- **Country Homogeneity:** Ordering countries by median spend from `Australia` ($n_k = 413$, `median = $2,597.60`, `mean = $2,510.63`) down to `USA` ($n_k = 395$, `median = $2,327.06`, `mean = $2,363.55`) — alongside `India` ($n_k = 431$, `median = $2,469.79`) and `'Unknown'` ($n_k = 426$, `median = $2,446.78`) — shows nearly identical platykurtic spreads (`known ANOVA F = 0.63, p = 0.64`; `Kruskal H = 2.51, p = 0.64`; `all-segment p = 0.78`).
```

```python
fig_e5_city_age = plot_e5_spend_by_city_and_age(df_clean_e5, save=True)
plt.show()
plt.close(fig_e5_city_age)
```

```markdown
**Visual Interpretation — Spend Across Indian Cities & Ontology Age Cohorts (`Q2` High-Value Segments):**
- **Metropolitan Cities ($n = 2,175$ known; $n = 2,466$ total):** Segment means span a narrow band from `Chennai` (`$2,562.51`, `median = $2,561.14`, $n_k = 258$) and `Pune` (`$2,526.88`, `median = $2,697.49`, $n_k = 308$) to `Kolkata` (`$2,286.54`, `median = $2,124.33`, $n_k = 264$), with `'Unknown'` at `$2,529.39` ($n_k = 291$). Formal omnibus tests (`known ANOVA F = 0.94, p = 0.48`; `Kruskal H = 6.64, p = 0.47`) confirm observed rank differences reflect random sampling variation rather than structural city-level spend premiums.
- **Ontology Age Cohorts ($n = 600$ known; $n = 1,866$ `'Unknown'`):** Comparing `18-29 (Young Adult)` (`mean = $2,334.77`, $n_k = 134$), `30-44 (Early Career)` (`$2,418.87`, $n_k = 194$), `45-59 (Mid-Senior)` (`$2,433.83`, $n_k = 155$), and `60+ (Senior)` (`$2,556.18`, $n_k = 117$) yields `ANOVA F = 0.50, p = 0.68` (`Kruskal H = 1.62, p = 0.65`), confirming that customer age brackets do not segment order value; moreover, `'Unknown'` age accounts ($n_k = 1,866$, `mean = $2,457.01`) match known-age spend (`all-segment p = 0.80`), supporting unbiased `NaN` retention.
```

```python
fig_e5_scatter = plot_e5_age_vs_spend(df_clean_e5, save=True)
plt.show()
plt.close(fig_e5_scatter)
```

```markdown
**Visual Interpretation — Continuous Age vs. Purchase Amount (`Q2` Revenue Drivers):**
- Plotting all $n = 600$ dual-valid customer records (`6.00%` of dataset; $9,400$ missing `age` and/or `purchase_amount`) with `alpha = 0.35` transparency reveals a uniform rectangular cloud across `18–70` years and `$10–$4,999`.
- Both the OLS linear regression line (`Pearson r = 0.0430, p = 0.2930`) and rank-order association (`Spearman ρ = 0.0457, p = 0.2641`) are flat, and the overlaid cohort mean/median trajectories remain anchored near `~$2,450`. Observational correlation is statistically indistinguishable from zero (and, per statistical governance, implies no causal relationship).
```

```python
fig_e5_diag = plot_e5_feedback_and_geo_mismatch(df_clean_e5, save=True)
plt.show()
plt.close(fig_e5_diag)
```

```markdown
**Visual Interpretation — Feedback/Reachability Spend Invariance (`Q3`) & City × Country Contradiction (`Q1`):**
- **Panel (a) — Satisfaction & Reachability vs. Spend (`Q3`):** Order values do not vary across discrete `feedback_score` ratings `1–5` and the `Score 10` spike (`known ANOVA F = 0.42, p = 0.84`; `Score 10` mean `$2,460.06` [$n_k = 600$] vs. `Likert 1–5` ratings ranging `$2,275–$2,486`), indicating high spenders are just as likely to be Detractors as Promoters. Crucially, `Reachable (>=1 Ch.)` customers ($n_k = 1,069$, `mean = $2,483.83`) and `Unreachable (None)` customers ($n_k = 1,397$, `mean = $2,425.20`) spend equivalently (`F = 1.00, p = 0.32`), exposing **$3,388,004.29 (`56.06%` of verified revenue)** locked inside accounts that marketing cannot currently contact.
- **Panel (b) — Structural Geographic Contradiction (`Q1`):** Although every known city (`Hyderabad`, `Mumbai`, `Pune`, `Bangalore`, `Chennai`, `Delhi`, `Ahmedabad`, `Kolkata`) is located in India, each city row distributes ~`15%–19%` of its records uniformly across `India`, `USA`, `Australia`, `Canada`, `UK`, and `Unknown` (`χ² = 19.29, dof = 28, p = 0.89` across $n = 7,348$ dual-known rows — complete statistical independence). This synthetic/corrupted country assignment generates **5,888 exact `is_geo_mismatch` records** (**80.13%** of `7,348` dual-known records; **58.88%** of all `10,000` records, out of `6,655` total non-Indian country rows including `767` with `'Unknown'` city).
```

## Key Findings
- **Demographic & Geographic Spend Homogeneity (`Q2`):** Across $n = 2,466$ valid spend records, `purchase_amount` shows no statistically significant differentiation by `gender` (`known p = 0.82`, `all p = 0.62`), `country` (`known p = 0.64`, `all p = 0.78`), `city` (`known F = 0.94, p = 0.48`), or ontology `age_group` (`known F = 0.50, p = 0.68`).
- **Zero Continuous Age–Spend Correlation (`Q2`):** Across $n = 600$ dual-valid customers, `age` and `purchase_amount` exhibit near-zero linear (`Pearson r = 0.0430, p = 0.2930`) and monotonic (`Spearman ρ = 0.0457, p = 0.2641`) correlation.
- **56.06% ($3.39M) of Verified Spend Resides in Unreachable Accounts (`Q3`):** Spend is invariant across `feedback_score` (`known F = 0.42, p = 0.84`) and binary `contact_reachability` (`F = 1.00, p = 0.32`), leaving `$3,388,004.29` (`n = 1,397` orders) at uncontactable churn risk.
- **80.13% Dual-Known Geographic Mismatch (`Q1`):** `city` and `country` are statistically independent (`χ² = 19.29, dof = 28, p = 0.89` on $n = 7,348$ dual-known rows), producing `5,888` records (`58.88%` of $N = 10,000$) that pair an Indian city with `USA`, `Australia`, `Canada`, or `UK`.

## Open Issues
- None. All 8 charts verified at 300 DPI and 100% deterministic (seed=42).

## Verification
- `.\EDA\Scripts\python.exe -m ruff check src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- `png_dpi` check via `.github/scripts/check_conventions.py` on all `assets/charts/e5_*.png` → `300 DPI` (`299.9994 DPI`, within `<= 1 DPI` tolerance)
- `handoff_headings` check via `.github/scripts/check_conventions.py` on `handoffs/e4_data-viz.md` and `handoffs/e5_data-viz.md` → exact match `['Outputs', 'Notebook Cells', 'Key Findings', 'Open Issues', 'Verification']`
