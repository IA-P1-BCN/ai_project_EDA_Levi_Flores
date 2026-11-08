# M5 — data-viz handoff

## Outputs

- `src/visualization.py` (appended: `plot_m5_correlation_heatmap`, M5 label constants, shared `_load_summary_or_build`, `_format_p_value`, `_trend_row` helpers)
- `assets/charts/m5_correlation_heatmap.png` (300 DPI, 4863 x 2456 px)

## Notebook Cells

```python
from src.visualization import plot_m5_correlation_heatmap

fig_m5_heatmap = plot_m5_correlation_heatmap(df_enriched_m5)
```

```markdown
#### Visual interpretation — `assets/charts/m5_correlation_heatmap.png`

The lower-triangle Pearson heatmap (panel a) paints almost the whole matrix in the neutral centre of the `vlag` scale: every off-diagonal cell sits between `|r| = 0.0017` and `|r| = 0.1263`, and the strongest cell (`Customer Age` × `Customer Tenure`, `r = 0.13`, `n = 206`) is only just visible. Each cell prints its own pairwise `n`, which spans `206` (Age × Tenure) to `2,528` (Feedback × Completeness), so no coefficient is read without its sample size. The single `purchase_amount` × `log_purchase_amount` cell is hatched and labelled "log1p only" (`r = 0.8845`, `ρ = 1.0000`, `n = 2,466`) and is explicitly excluded from the narrative: it is a deterministic rescaling of the same variable, not an association. The `1.00` diagonal cells are masked so they cannot be mistaken for findings.

The companion dumbbell panel (b) plots Pearson `r` (circles) and Spearman `ρ` (diamonds) for the `14` non-transform pairs, sorted by strength. All fourteen markers fall inside or immediately beside the shaded "negligible" band (`|coefficient| < 0.10`); the maximum is `r = +0.126` / `ρ = +0.122` (Age × Tenure, `n = 206`, `p = 0.0704` / `0.0817`) and the smallest p-value in the whole matrix is `0.0662` (Feedback × Completeness, `n = 2,528`). Nothing reaches `α = 0.05`.

**Business reading:** this is the multivariate confirmation of `E5`, answering `Q2` and `Q3`. Spend (`purchase_amount`) is not linearly or monotonically associated with age (`r = 0.0430`, `n = 600`), tenure (`r = -0.0560`, `n = 219`), satisfaction (`r = -0.0178`, `n = 648`) or record completeness (`r = -0.0038`, `n = 2,466`) — all `p ≥ 0.2930` — so revenue must be modelled and targeted on its own, never inferred from demographic, lifecycle or satisfaction proxies. The chart states "correlation does not imply causation" because no coefficient here licenses either direction of a causal claim; the near-zero coefficients mean *no detectable linear/rank signal at this n*, not proven independence.
```

## Key Findings

- **Near-zero association matrix (`Q2`, `Q3`):** across `14` non-transform pairs the largest coefficient is `|r| = 0.1263` / `|ρ| = 0.1216` (Age × Tenure, `n = 206`, `p = 0.0704` / `0.0817`), i.e. about `1.6%` shared variance; no pair reaches `p < 0.05` (smallest `p = 0.0662`, Feedback × Completeness, `ρ = -0.0365`, `n = 2,528`) — `assets/charts/m5_correlation_heatmap.png`.
- **Spend is visually orthogonal to every other analytical variable (`Q2`):** the `purchase_amount` row shows `r = 0.0430` (`n = 600`, Age), `r = -0.0560` (`n = 219`, Tenure), `r = -0.0178` (`n = 648`, Feedback) and `r = -0.0038` (`n = 2,466`, Completeness); every marker sits within `±0.07` of zero in panel (b).
- **The only strong cell is a labelled transformation (`Q2`, `A4` input):** `purchase_amount` × `log_purchase_amount` shows `r = 0.8845`, `ρ = 1.0000` at `n = 2,466`; it is hatched, annotated "log1p only", and excluded from the ranking panel — the two columns must never enter the same model.
- **Sample size is printed with every coefficient (`Q3`, methodological):** pairwise `n` ranges `206` to `2,528`; the sparsest pair (Age × Tenure) cannot detect `|r| < 0.2` at `α = 0.05`, so "no association" is a statement about the age- and spend-covered subpopulation, not about all `10,000` accounts.

## Open Issues

- Power, not effect size, binds the interpretation: for `n = 206` only `|r| ≳ 0.2` is detectable at `α = 0.05`. The chart therefore labels coefficients "near zero", never "independent".
- Four of the `14` plotted pairs involve `log1p Spend`; they are rank mirrors of the `purchase_amount` pairs. They are retained for consistency with `m5_correlation_pairwise_tests.csv` (the analyst counts `14` non-transform pairs) but add no independent signal.
- The heatmap reads `data/processed/summaries/m5_correlation_matrix_long.csv` and `m5_correlation_pairwise_tests.csv`; both are required by the notebook path. If absent, the function recomputes them in memory from `df_enriched` via `src.analysis` (it never writes to `data/`).
- An interactive version of the matrix is out of scope here; it belongs to `X2` (`app/dashboard.py`).

## Verification

- `.\EDA\Scripts\python.exe -m src.visualization --block m5m6` → all three PNGs written (`Saved figure: assets/charts/...`).
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/ app/` → `All checks passed!` (`0 errors`).
- `.\EDA\Scripts\python.exe -m flake8 src/visualization.py --max-line-length=127` → `0 errors` (exit code 0).
- DPI / size check via `PIL.Image`: `m5_correlation_heatmap.png` = `4863 x 2456` px at `(299.9994, 299.9994)` DPI (300 DPI).
- Idempotency: the block was rendered three times; SHA-256 digests of the PNG were identical across runs (`E481C7FD…97B0A`).
- Fallback path: with `SUMMARY_DIR` pointed at a non-existent directory, `plot_m5_correlation_heatmap(df_enriched)` still renders (`3` axes: heatmap, colourbar, ranking panel) by recomputing from `src.analysis`.
- Visual inspection of the exported PNG: no clipped or overlapping labels; colourbar label clear of panel (b) tick labels; footnote above the source caption; all `14` pair labels and `14` cell `n` annotations legible.
