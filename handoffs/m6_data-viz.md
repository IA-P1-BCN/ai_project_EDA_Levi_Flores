# M6 — data-viz handoff

## Outputs

- `src/visualization.py` (appended: `plot_m6_signup_and_activity_trends`, `plot_m6_cohort_tenure_censoring`, `generate_m5m6_charts`, CLI blocks `--block m5`, `--block m6`, `--block m5m6`)
- `assets/charts/m6_signup_and_activity_trends.png` (300 DPI, 4798 x 2280 px)
- `assets/charts/m6_cohort_tenure_censoring.png` (300 DPI, 4419 x 2368 px)

## Notebook Cells

```python
from src.visualization import plot_m6_signup_and_activity_trends

fig_m6_trends = plot_m6_signup_and_activity_trends(df_enriched_m6)
```

```markdown
#### Visual interpretation — `assets/charts/m6_signup_and_activity_trends.png`

Panel (a) shows the `66` monthly signup cohorts (`2020-08` to `2026-01`): monthly volume oscillates between `57` and `106` accounts around a full-period mean of `75.70`, and the orange 3-month trailing mean is a flat ribbon with no slope. The Spearman test against the month index gives `ρ = +0.0609` (`p = 0.6271`), so acquisition volume is *trend-free* within the `n = 4,996` dated signups. Panel (b) repeats the exercise for transaction recency: monthly last-purchase activity stays between `36` and `69` (`mean = 50.73`) with `ρ = +0.0520` (`p = 0.6785`) across the `n = 3,348` dated last purchases. The light grey columns at both edges flag the two partial months (`2020-08` starts on the 6th, `2026-01` ends on the 26th), and the subtitle states the date-integrity rule: the `829` `is_date_inverted` rows are **retained** in these single-date series because each date is individually valid, while `NaT` dates are excluded (`5,004` signups, `6,652` last purchases).

**Business reading (`Q2`, `Q3`):** acquisition and recency are stable, so there is no organic growth or collapse to explain and no seasonal spike to exploit — revenue variation must come from order value and segment mix (see `M5`), not from volume drift. The explicit retention rule matters because the rejected sensitivity check in `m6_trend_tests.csv` shows that dropping the `829` inverted pairs would manufacture `ρ = -0.6079` (signups) and `ρ = +0.7664` (activity) — a spurious trend that the chart deliberately avoids.
```

```python
from src.visualization import plot_m6_cohort_tenure_censoring

fig_m6_censoring = plot_m6_cohort_tenure_censoring(df_enriched_m6)
```

```markdown
#### Visual interpretation — `assets/charts/m6_cohort_tenure_censoring.png`

The navy bars (mean `customer_tenure_days`) fall monotonically from `920.3` days for the `2020` cohort (`n = 124` valid tenures) to `127.0` days for `2025` (`n = 41`), a `-86.2%` drop that would look like a retention collapse in isolation. The steel-blue bars show why it is not: the mean observation window `max(last_purchase_date) − mean(signup_date)` shrinks in the same direction, from `1,920` to `207` days (`-89.2%`), because recent cohorts have simply had less calendar time in which a last purchase could occur. The orange secondary axis makes the point quantitatively — the tenure-to-window ratio stays inside `0.479`–`0.614` across the six full-detail cohorts (shaded band) and the line is flat, so equal *shares* of the observable window convert to purchases every year. The `2020` and `2026` cohorts are hatched and labelled "partial" (data starts `2020-08-06`, ends `2026-01-26`), and the `2026` cohort carries `n = 1` valid tenure, so its `0.667` ratio is plotted but flagged non-interpretable.

**Business reading (`Q3`):** the apparent tenure decline is right-censoring, not retention decay — `ρ = -1.0000` (`p < 0.000001`) across the six ordered cohort years reflects the observation window, which is not a behavioural metric. Any churn claim built on cohort tenure alone would be an artefact; retention must be measured on cohorts observed for comparable windows. The `829` `is_date_inverted` pairs are excluded from tenure by construction (`n = 855` valid tenures of `10,000` accounts), so all cohort means describe the `8.55%` of accounts with two chronologically valid dates.
```

## Key Findings

- **Acquisition and recency volume are flat (`Q2`, `Q3`):** `66` months, monthly signups `57`–`106` (`mean = 75.70`, `n = 4,996`, `ρ = +0.0609`, `p = 0.6271`) and monthly last-purchase activity `36`–`69` (`mean = 50.73`, `n = 3,348`, `ρ = +0.0520`, `p = 0.6785`) — `assets/charts/m6_signup_and_activity_trends.png`.
- **The retention rule is visible in the chart design (`Q3`):** the `829` `is_date_inverted` rows are retained in both single-date series (each date is valid) and `NaT` dates are excluded (`5,004` signups, `6,652` last purchases); dropping the inverted pairs would fabricate `ρ = -0.6079` and `+0.7664` in `m6_trend_tests.csv`.
- **Cohort tenure declines `920.3 → 127.0` days (`-86.2%`) while the observation window declines `1,920 → 207` days (`-89.2%`) (`Q3`):** `ρ = -1.0000` (`p < 0.000001`) over the `6` cohort years with `n ≥ 30` valid tenures (`2020`–`2025`), on `n = 855` valid tenures in total.
- **The tenure-to-window ratio is flat at `0.479`–`0.614` (`Q3`):** the secondary-axis line stays inside the shaded band for all six full-detail cohorts, so shorter recent tenures are right-censoring, not faster churn — `assets/charts/m6_cohort_tenure_censoring.png`.
- **Per-cohort tenure-valid `n` is annotated on every bar:** `124`, `281`, `189`, `138`, `81`, `41`, `1` for `2020`–`2026`; the `2026` cohort (`n = 1`, `9`-day window) is hatched, labelled partial, and explicitly non-interpretable.

## Open Issues

- Temporal conclusions are bounded by missingness: only `49.96%` of accounts carry a signup date and `33.48%` a last-purchase date, so "no trend" applies to the dated subpopulation only. The subtitle says so; no imputation is used or implied.
- The `2026` cohort is retained in the plot for completeness with `n = 1` tenure: its bars, ratio point (`0.667`) and `n = 1*` label are drawn hollow/hatched and footnoted as non-interpretable. If a reviewer prefers, it can be dropped without changing any conclusion.
- Mean-spend trend (`ρ = -0.0464`, `p = 0.7111`; quarterly `ρ = +0.0346`, `p = 0.8755`) is **not** charted here because `M6` chart scope covers volume and cohort censoring; it is available in `m6_signup_cohorts_monthly.csv` / `m6_last_purchase_monthly.csv` if `M7`/`X5` needs a spend-panel figure.
- Both functions read `m6_*.csv` summaries from `data/processed/summaries/`; if a table is absent they recompute it in memory from `df_enriched` via `src.analysis` (no writes to `data/`).
- Interactive (`plotly`) counterparts belong to `X2` (`app/dashboard.py`) and are not part of this block.

## Verification

- `.\EDA\Scripts\python.exe -m src.visualization --block m5m6` → `Saved figure:` for all three PNGs; `--block m5` and `--block m6` also verified individually.
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/ app/` → `All checks passed!` (`0 errors`).
- `.\EDA\Scripts\python.exe -m flake8 src/visualization.py --max-line-length=127` → `0 errors` (exit code 0).
- DPI / size check via `PIL.Image`: `m6_signup_and_activity_trends.png` = `4798 x 2280` px and `m6_cohort_tenure_censoring.png` = `4419 x 2368` px, both at `(299.9994, 299.9994)` DPI (300 DPI).
- Idempotency: repeated renders produced identical SHA-256 digests (`CF83E147…33C91`, `A8304EAE…985987`).
- Reconciliation against the analyst tables: the trend boxes, per-cohort `n` labels and the censoring callout are computed from `m6_trend_tests.csv` / `m6_cohort_evolution_summary.csv` at render time, and the finding-driven titles quote the same rounded values; monthly sums re-checked at `4,996` signups and `3,348` purchases.
- Visual inspection of both exported PNGs: trend boxes clear of all bars, partial-month shading visible at both edges, legend outside the data area, no clipped axis labels, and the censoring callout box clear of the `2020`/`2021` bars, legend and secondary axis.
