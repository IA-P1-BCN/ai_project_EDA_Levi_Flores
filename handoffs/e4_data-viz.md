# E4 — data-viz handoff

## Outputs
- `src/visualization.py` — Publication-grade visualization module (`apply_publication_theme`, `save_publication_figure`, `plot_e4_age_distribution`, `plot_e4_purchase_distribution`, `plot_e4_demographics_counts`, `plot_e4_feedback_and_reachability`, `plot_e5_spend_by_demographics`, `plot_e5_spend_by_city_and_age`, `plot_e5_age_vs_spend`, `plot_e5_feedback_and_geo_mismatch`, `generate_essential_charts`).
- `assets/charts/e4_univariate_age_distribution.png` — 300 DPI combined Histogram + KDE and horizontal Boxplot of valid `age` ($n = 2,465$).
- `assets/charts/e4_univariate_purchase_distribution.png` — 300 DPI combined Histogram + KDE and horizontal Boxplot of valid `purchase_amount` ($n = 2,466$).
- `assets/charts/e4_univariate_demographics_counts.png` — 300 DPI 3-panel ordered horizontal bar chart of `gender`, `city`, and `country` ($N = 10,000$).
- `assets/charts/e4_univariate_feedback_reachability.png` — 300 DPI 2-panel chart of discrete `feedback_score` (`1–5` vs. `10` spike vs. `Missing`) and 4-tier omnichannel reachability ($N = 10,000$).

## Notebook Cells
```markdown
### 4.1 `[E4]` Univariate Visual Profiling — Continuous, Categorical & Reachability Distributions

Each visualization pairs parametric (`mean`, `SD`) and non-parametric (`median`, `Q1`, `Q3`, `IQR`, Tukey fences) markers directly on the canvas and exports deterministically at `300 DPI` to `assets/charts/` via `src/visualization.py`.
```

```python
import matplotlib.pyplot as plt

from src.analysis import load_clean_customers
from src.visualization import (
    plot_e4_age_distribution,
    plot_e4_demographics_counts,
    plot_e4_feedback_and_reachability,
    plot_e4_purchase_distribution,
)

df_clean_e4 = load_clean_customers("v1")

fig_e4_age = plot_e4_age_distribution(df_clean_e4, save=True)
plt.show()
plt.close(fig_e4_age)
```

```markdown
**Visual Interpretation — Customer Age Distribution (`Q1` Demographics):**
- Across valid observations ($n = 2,465$, **24.65%** coverage; $7,535$ blank or `-5`/`200` sentinel records excluded to `NaN` rather than single-value median imputation, which would artificially compress `SD` from `15.30` to `~7.6` years), `age` spans **18.0 to 70.0 years** smoothly.
- Parametric (`mean = 43.70` years, `SD = 15.30` years) and non-parametric (`median = 43.00` years, `Q1 = 31.0`, `Q3 = 58.0`, `IQR = 27.0` years) central tendencies converge tightly, with near-zero skewness (`0.06`) and negative excess kurtosis (`-1.19`) confirming a symmetric, platykurtic (near-uniform) adult age profile.
- Formal Tukey fences ($[-9.5,\; 98.5]$ years) lie well outside the observed `[18.0, 70.0]` support, confirming **0 univariate age outliers** after sentinel removal.
```

```python
fig_e4_spend = plot_e4_purchase_distribution(df_clean_e4, save=True)
plt.show()
plt.close(fig_e4_spend)
```

```markdown
**Visual Interpretation — Transaction Spend Distribution (`Q2` Revenue Distribution):**
- Valid `purchase_amount` covers **24.66%** of accounts ($n = 2,466$; $7,534$ blanks and `-999`/`'N/A'` sentinels excluded), generating **$6,043,218.46** in verified transaction volume across `$10.31–$4,998.67`.
- Both `mean` (**$2,450.62**, `SD = $1,442.83`) and `median` (**$2,460.36**, `Q1 = $1,159.39`, `Q3 = $3,733.88`, `IQR = $2,574.50`) sit virtually at the midpoint of the `$0–$5,000` range (`skewness = 0.01`, excess `kurtosis = -1.22`), demonstrating uniform dispersion across low, mid, and high ticket sizes.
- Formal Tukey fences ($[-\$2,702.36,\; \$7,595.62]$) confirm **0 statistical spend outliers** among valid transactions, meaning top-tier orders (`>$3,500`) represent genuine broad-spectrum demand rather than isolated extreme anomalies.
```

```python
fig_e4_demo = plot_e4_demographics_counts(df_clean_e4, save=True)
plt.show()
plt.close(fig_e4_demo)
```

```markdown
**Visual Interpretation — Demographic & Geographic Counts (`Q1` Customer Profile):**
- **Gender (`75.45%` known, $n = 7,545$):** Nearly 50/50 parity between `Male` ($n = 3,800$, `38.0%` total / `50.36%` known) and `Female` ($n = 3,745$, `37.5%` total / `49.64%` known), alongside `2,455` (`24.6%`) `'Unknown'` accounts rendered in slate grey.
- **Metropolitan City (`88.70%` known, $n = 8,870$):** All 8 known cities are major Indian metropolitan hubs (`Hyderabad` `1,144` [`11.4%`] to `Kolkata` `1,056` [`10.6%`], averaging `1,109` accounts per city), with `1,130` (`11.3%`) `'Unknown'`.
- **Assigned Country (`82.96%` known, $n = 8,296$):** `'Unknown'` is the single largest country bucket (`1,704`, `17.0%`), while known entries split uniformly (~`16.4%–16.8%` of total; ~`20.0%` of known) across `USA` (`1,679`), `Australia` (`1,660`), `Canada` (`1,658`), `UK` (`1,658`), and `India` (`1,641`) — foreshadowing the severe city-vs-country geographic contradiction audited in `E5`.
```

```python
fig_e4_fb = plot_e4_feedback_and_reachability(df_clean_e4, save=True)
plt.show()
plt.close(fig_e4_fb)
```

```markdown
**Visual Interpretation — Feedback Scale Distortion & Omnichannel Reachability (`Q3` Satisfaction & Retention):**
- **Bimodal Rating Scale Distortion (`KPI-6`):** Almost half of all accounts (`4,951`, `49.5%`) lack valid feedback (blanks or `-1` sentinel). Among the $n = 5,049$ valid ratings, **2,521 records (`49.93%` of valid; `25.2%` of total)** sit at an off-scale score of `10`, artificially inflating the unadjusted mean to `6.48`. Isolating the clean `1–5` Likert cohort ($n = 2,528$) reveals a balanced, neutral satisfaction baseline (`mean = 2.96`, `SD = 1.42`, `median = 3.00`, `IQR = 2.00`), with Detractors (`1–2`: `1,027` [`40.6%` of Likert]) slightly outnumbering Promoters (`4–5`: `945` [`37.4%` of Likert]).
- **Severe Contact Unreachability (`KPI-4`):** Across $N = 10,000$ accounts, **5,612 (`56.12%`) are completely `Unreachable (None)`** due to missing or malformed emails/phone numbers. Only **4,388 (`43.88%`)** can be contacted via at least one verified channel (`1,878` [`18.78%`] `Email Only`, `1,876` [`18.76%`] `Phone Only`, and just `634` [`6.34%`] `Omnichannel (Both)`), creating an immediate CRM bottleneck for retention campaigns.
```

## Key Findings
- **Symmetric Platykurtic Age Profile (`Q1`):** Valid `age` ($n = 2,465$, `24.65%` coverage) centers at `mean = 43.70` years (`SD = 15.30`) and `median = 43.00` years (`IQR = 27.00`, `Q1 = 31.0`, `Q3 = 58.0`, `skewness = 0.06`, `kurtosis = -1.19`) with `0` Tukey outliers (`fences = [-9.5, 98.5]`).
- **Wide, Outlier-Free Transaction Value (`Q2`):** Valid `purchase_amount` ($n = 2,466$, `24.66%` coverage) totals `$6,043,218.46` with `mean = $2,450.62` (`SD = $1,442.83`), `median = $2,460.36` (`IQR = $2,574.50`), and `0` Tukey outliers (`fences = [-$2,702.36, $7,595.62]`).
- **Uniform Demographic Splits (`Q1`):** Known `gender` ($n = 7,545$) is balanced (`50.36%` `Male` vs. `49.64%` `Female`), known `city` ($n = 8,870$) splits ~`12.5%` across 8 Indian metros, and known `country` ($n = 8,296$) splits ~`20.0%` across 5 countries while `'Unknown'` accounts for `11.3%–24.6%`.
- **Scale-10 Feedback Spike & 56.12% CRM Unreachability (`Q3`):** Score `10` represents `49.93%` ($n = 2,521$) of valid ratings ($n = 5,049$), masking a neutral `1–5` Likert mean of `2.96` ($n = 2,528$, `median = 3.00`), while `5,612` accounts (`56.12%`) lack both valid email and valid phone reachability (`only 6.34%` omnichannel).

## Open Issues
- `src/visualization.py` was updated after visual PNG inspection to disable Matplotlib MathText `$...$` parsing (`"text.parse_math": False`) and expand subplot bottom `ylim` headroom; re-run `.\EDA\Scripts\python.exe -m src.visualization` once outside the sandbox so the on-disk PNGs in `assets/charts/` reflect the polished typography and badge spacing.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- `png_dpi` check via `.github/scripts/check_conventions.py` on all `assets/charts/e4_*.png` → `300 DPI` (`299.9994 DPI`, within `<= 1 DPI` tolerance)
- Visual inspection completed via `read_file` on all 4 `E4` PNGs + scratch re-renders confirming crisp `$` currency rendering and zero text overlap.
