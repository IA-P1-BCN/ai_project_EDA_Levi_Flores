# M5 — statistical-analyst handoff

## Outputs
- `src/analysis.py`
- `data/processed/summaries/m5_correlation_pearson.csv`
- `data/processed/summaries/m5_correlation_spearman.csv`
- `data/processed/summaries/m5_correlation_pairwise_n.csv`
- `data/processed/summaries/m5_correlation_matrix_long.csv`
- `data/processed/summaries/m5_correlation_pairwise_tests.csv`
- `data/processed/summaries/m5_correlation_highlights.csv`

## Notebook Cells
```markdown
---

## 12. `[M5]` Correlation Analysis (`Pearson r` & `Spearman rho`) — Association, Not Causation

Univariate (`E4`) and single-factor bivariate (`E5`) results describe variables one at a time. To test whether the analytical features carry **shared linear or rank signal**, we compute a full correlation matrix in `src/analysis.py` (`compute_correlation_matrices`, `compute_correlation_pairwise_tests`, `compute_correlation_highlights`) and export it to `data/processed/summaries/m5_*.csv`.

**Variable selection (six columns, justified in code):** `age`, `purchase_amount`, `customer_tenure_days`, `feedback_score_1_to_5`, `completeness_score`, and `log_purchase_amount`. Raw `feedback_score` (which mixes `1–5` with the `2,521` off-scale `10` ratings) is deliberately excluded in favour of the clean Likert column; `customer_id`, `name`, and raw dates are excluded because they are identifiers or non-numeric. `log_purchase_amount` is a deterministic `np.log1p` rescaling of `purchase_amount`, so it is reported **only as a collinearity/transformation check** and flagged with `is_monotone_transform = True` in the pairwise table.

**Method:** every coefficient is computed on complete pairwise observations only (`pandas.dropna()` per pair, `scipy.stats.pearsonr`, `scipy.stats.spearmanr`), so the pairwise $n$ is reported for every cell and ranges from `206` to `2,528`. All correlations are **observational associations** — none of the statements below implies that one variable drives another.
```

```python
from src.analysis import (
    compute_correlation_highlights,
    compute_correlation_matrices,
    compute_correlation_pairwise_tests,
    load_clean_customers,
)
from src.features import engineer_features

df_enriched_m5 = engineer_features(load_clean_customers("v2"))

m5_matrices = compute_correlation_matrices(df_enriched_m5)
m5_tests = compute_correlation_pairwise_tests(df_enriched_m5)
m5_highlights = compute_correlation_highlights(m5_tests)

print("=== [M5.1] PEARSON r CORRELATION MATRIX (pairwise-complete observations) ===")
print(m5_matrices["pearson"].round(4).to_string())

print("\n=== [M5.2] SPEARMAN rho CORRELATION MATRIX ===")
print(m5_matrices["spearman"].round(4).to_string())

print("\n=== [M5.3] PAIRWISE VALID n PER MATRIX CELL ===")
print(m5_matrices["n_pair"].to_string())

print("\n=== [M5.4] TOP 5 INDEPENDENT ASSOCIATIONS (monotone transform excluded) ===")
print(
    m5_highlights[
        [
            "rank",
            "variable_x",
            "variable_y",
            "n_pair",
            "pearson_r",
            "pearson_p",
            "spearman_rho",
            "spearman_p",
            "pearson_strength_label",
        ]
    ]
    .round(4)
    .to_string(index=False)
)

print("\n=== [M5.5] MONOTONE-TRANSFORM COLLINEARITY CHECK ===")
print(
    m5_tests.loc[
        m5_tests["is_monotone_transform"],
        ["variable_x", "variable_y", "n_pair", "pearson_r", "spearman_rho"],
    ].to_string(index=False)
)
```

```markdown
**Quantitative Interpretation (`M5`):**
- **The matrix is dominated by near-zero coefficients (`Q2`, `Q3`):** across the `14` independent variable pairs in `data/processed/summaries/m5_correlation_pairwise_tests.csv`, the largest association is only **`|r| = 0.1263` / `|rho| = 0.1216`** for `age` × `customer_tenure_days` ($n = 206$; $p = 0.0704$ / $0.0817$), i.e. roughly **`1.6%` shared variance** ($r^2 = 0.0159$). **No independent pair reaches $p < 0.05$**; the smallest p-value is $p = 0.0662$ for `feedback_score_1_to_5` × `completeness_score` ($\rho = -0.0365$, $n = 2{,}528$).
- **Spend is statistically indistinguishable from independent of every other analytical variable (`Q2`):** `purchase_amount` versus `age` ($r = 0.0430$, $p = 0.2930$, $n = 600$), `customer_tenure_days` ($r = -0.0560$, $p = 0.4098$, $n = 219$), `feedback_score_1_to_5` ($r = -0.0178$, $p = 0.6508$, $n = 648$), and `completeness_score` ($r = -0.0038$, $p = 0.8504$, $n = 2{,}466$). This is the multivariate counterpart of the `E5` result that segment mean spend is homogeneous: within this dataset, transaction value varies almost entirely on its own rather than jointly with demographics, lifecycle, satisfaction, or record completeness.
- **The only strong coefficient is a transformation artefact (`Q2`):** `purchase_amount` × `log_purchase_amount` reports $r = 0.8845$ and $\rho = 1.0000$ across $n = 2{,}466$ valid orders, flagged `is_monotone_transform = True` in `m5_correlation_pairwise_tests.csv` and excluded from `m5_correlation_highlights.csv`. The perfect Spearman rank identity proves the two columns carry the same ordering (they must never enter the same model, `A4`), while $r < 1$ quantifies the curvature the `log1p` transform introduces.
- **Sample-size caveat, always reported:** coverage of the underlying attributes is uneven, so pairwise $n$ ranges from **`206`** (`age` × `customer_tenure_days`, the intersection of `24.65%` age and `8.55%` tenure coverage) to **`2,528`** (`feedback_score_1_to_5` × `completeness_score`), as recorded in `m5_correlation_pairwise_n.csv`. The diagonal of that table holds univariate valid counts (`completeness_score = 10,000`) and must not be read as pair overlap. Correlations are associations only; no causal interpretation is warranted.
```

## Key Findings
- **No material linear or rank association survives variable selection, and nothing is significant (`Q2`, `Q3`):** across the `14` independent pairs in `data/processed/summaries/m5_correlation_pairwise_tests.csv`, $\max |r| = 0.1263$ and $\max |\rho| = 0.1216$ (`age` × `customer_tenure_days`, $n = 206$, $p = 0.0704$ / $0.0817$); no pair reaches $p < 0.05$, with the smallest p-value $p = 0.0662$ (`feedback_score_1_to_5` × `completeness_score`, $\rho = -0.0365$, $n = 2{,}528$).
- **Spend is orthogonal to demographics, lifecycle, satisfaction and completeness (`Q2`):** `purchase_amount` correlations are $r = 0.0430$ ($n = 600$) with `age`, $r = -0.0560$ ($n = 219$) with `customer_tenure_days`, $r = -0.0178$ ($n = 648$) with `feedback_score_1_to_5`, and $r = -0.0038$ ($n = 2{,}466$) with `completeness_score` — all $p \ge 0.2930$ (`m5_correlation_pearson.csv`).
- **The single strong coefficient is a deterministic transformation, not evidence (`Q2`, `A4` input):** `purchase_amount` × `log_purchase_amount` shows $r = 0.8845$ and $\rho = 1.0000$ at $n = 2{,}466$; the row is flagged `is_monotone_transform = True` and removed from the highlight ranking, so the `log1p` column must be treated as a rescaling of the same variable (collinearity warning for downstream modelling), never as an independent predictor.
- **Pairwise $n$ must accompany every coefficient:** coverage-driven sample sizes span `206` to `2,528` (`m5_correlation_pairwise_n.csv`), so each exported statistic is only as reliable as its own pair intersection; the diagonal cell `completeness_score = 10,000` is a univariate count, not a pair overlap.

## Open Issues
- Statistical power is the binding constraint, not effect size: for the sparsest pair (`age` × `customer_tenure_days`, $n = 206$) only moderate-to-strong associations ($|r| \gtrsim 0.2$) would be detectable at $\alpha = 0.05$, so the near-zero coefficients should be read as "no detectable linear/rank signal at this $n$", not as proof of exact independence.
- `DataVizAgent` (M5 heatmap) should build from `m5_correlation_matrix_long.csv` (36 ordered cells including the diagonal, with `n_pair`, `is_diagonal`, `is_monotone_transform`) rather than re-deriving the matrix, and should annotate or mask the `purchase_amount` × `log_purchase_amount` cell as a transformation.
- No new engineered feature was required for `M5`; the variable set is a strict subset of `specs/ontology.md` §3.2, so no ontology change is requested.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `All checks passed!` (`0 errors`)
- `.\EDA\Scripts\python.exe -m flake8 src/analysis.py --max-line-length=127` → `0 errors`
- `export_m5_summaries()` executed twice; all 6 `m5_*.csv` files materialized on disk and SHA-256 digests were identical across runs (deterministic / idempotent).
- Reconciliation checks: Pearson/Spearman diagonals equal `1.0` for all 6 variables; `m5_correlation_matrix_long.csv` has exactly `36` rows (`6 × 6`); pairwise table has `15` unique pairs (`14` independent + `1` flagged transform); every `n_pair` equals the count of complete observation pairs (e.g. `age` × `customer_tenure_days = 206`, `completeness_score` diagonal `= 10,000`).
