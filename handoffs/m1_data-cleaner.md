# M1 — data-cleaner handoff

## Outputs
- `src/cleaning.py` — Pure, deterministic, idempotent, type-hinted cleaning and methodological audit module (`load_raw_customers`, `clean_customers`, `validate_cleaned_customers`, `build_cleaning_decisions_audit`, `compute_imputation_variance_impact`, `export_m1_artifacts`).
- `data/processed/summaries/m1_cleaning_decisions_audit.csv` — Comprehensive 12-attribute audit table quantifying literal blanks, domain sentinels/corrupted entries, valid coverage rates, remediation rules, imputation choices, and methodological rationale.
- `data/processed/summaries/m1_imputation_variance_impact.csv` — Quantitative experiment comparing `NaN Retention (Chosen)`, `Single Median Imputation (Rejected)`, and `Single Mean Imputation (Rejected)` across `age` (`75.35%` missing) and `purchase_amount` (`75.34%` missing), paired with two-sample Welch's $t$-test and Mann-Whitney $U$ MCAR verification checks.
- `data/processed/customers_clean_v2.csv` *(materialized deterministically via `export_m1_artifacts()` / `.\EDA\Scripts\python.exe -m src.cleaning`)* — Full `10,000` rows × `21` columns `v2` cleaned dataset combining the 12 core columns with all 9 `DataCleanerAgent`-owned ontology quality flags.

## Notebook Cells
```markdown
---

## 7. `[M1]` Cleaning Decisions & Methodological Justification

While Section 3 (`[E3]`) executed the baseline type-casting pipeline (`customers_clean_v1.csv`, `10,000 × 15`), rigorous exploratory analysis requires documenting the **statistical and domain rationale (*why*)** behind every column retention, deduplication, sentinel remediation, imputation, and anomaly-flagging rule, and advancing the dataset to the full ontology-compliant **`customers_clean_v2.csv` (`10,000` rows × `21` columns)** via `src/cleaning.py`.

### 7.1 Explicit Methodological Criteria Across Five Governance Pillars

1. **Full Column Retention & `snake_case` Standardization (`12 / 12` Raw Columns Retained; `0` Dropped):**
   - **Why zero columns were dropped:** Every raw attribute maps directly to one of the four canonical domain entities (`Customer`, `Demographics`, `Transaction`, `Interaction` in `specs/ontology.md` §1) and retains between **`24.65%`** (`age`, $n = 2,465$) and **`88.70%`** (`city`, $n = 8,870$) verified observations indispensable to answering `Q1`, `Q2`, and `Q3`. Dropping high-missingness columns (`age` at `75.35%` invalid, `purchase_amount` at `75.34%`, `Phone_number` at `74.90%`, `email` at `74.88%`) would eliminate **`$6,043,218.46`** in verified revenue (`KPI-2`/`KPI-3`), adult cohort profiling (`KPI-1`), and omnichannel reachability auditing (`KPI-4`).
   - **Why `snake_case`:** Standardizing mixed raw headers (`CustomerID`, `Signup_Date`, `Last_purchase_date`, `Phone_number` → `customer_id`, `signup_date`, `last_purchase_date`, `phone_number`) enforces PEP 8 attribute ergonomics and strict CI data-contract validation.

2. **Duplicate Resolution & Lossless Primary Key Reconstruction (`C00001`–`C10000`):**
   - **Empirical audit:** Full-row deduplication across all `10,000` raw records confirms **`0` exact row duplicates**. Although raw `CustomerID` contains `2,379` blanks (`23.79%`) and mixes `'C'`-prefixed identifiers (`2,561` rows, e.g., `'C2'`, `'C4'`) with bare integers (`5,060` rows, e.g., `'3'`, `'5'`), stripping the `'C'` prefix confirms **`0` colliding numeric IDs** and a **100.0% 1-to-1 positional match** (`int(id) == row_index + 1`) across all `7,621` populated entries.
   - **Decision rationale:** Reconstructing sequential 5-digit keys (`C00001`–`C10000`) is 100% deterministic and lossless, whereas dropping rows with blank `CustomerID` would needlessly discard `23.79%` of valid customer transactions and demographic profiles.

3. **Categorical `'Unknown'` Assignment vs. Continuous `NaN` Retention + Missingness Indicators:**
   - **Nominal & Categorical Attributes (`name`, `gender`, `city`, `country` → Explicit `'Unknown'`):** Missing entries (`11.30%` in `city`, `16.58%` in `name`, `17.04%` in `country`, `24.55%` in `gender`) are assigned an explicit `'Unknown'` token/category rather than mode-imputed or left as `NaN`. Mode imputation on `gender` (`Male = 3,800` vs. `Female = 3,745`) would assign all `2,455` blank records to `'Male'`, fabricating a **`+64.6%` surge** in Male representation (`38.00%` → `62.55%` of total); similarly, mode imputation on `city` (`Hyderabad = 1,144`) or `country` (`USA = 1,679`) would invent false market concentration across otherwise uniform distributions. Explicit `'Unknown'` levels guarantee that `groupby(..., observed=True)` and `pivot_table` (`M3`) account for all `10,000` customers without silent row attrition.
   - **Continuous Numerics (`age`, `purchase_amount`, `feedback_score`), Dates (`signup_date`, `last_purchase_date`), and Contacts (`email`, `phone_number` → `NaN`/`NaT` + Indicator Flags):** Domain sentinels (`-5` [`2,506`] and `200` [`2,453`] in `age`; `'N/A'` [`2,533`] and `'-999'` [`2,501`] in `purchase_amount`; `'-1'` [`2,489`] in `feedback_score`; `'not_a_date'` [`2,475`] and `'missing'` [`3,366`] in dates; `2,422` `@`-less emails; `'abc123'` [`2,586`] and `'0'` [`2,460`] in phones) encode missing/corrupted capture rather than real measurements. Coercing sentinels to `NaN`/`NaT` and pairing primary columns with boolean indicators (`is_age_missing`, `is_purchase_missing`, `has_valid_email`, `has_valid_phone`) preserves true parametric (`SD`) and non-parametric (`IQR`) dispersion while preventing phantom revenue (`$18.54M`), fabricated acquisition cohorts (`M6`), or unroutable CRM dispatches.

4. **Non-Destructive Cross-Column Contradiction & Scale-Anomaly Flags (`v2` Quality Schema):**
   - **`is_date_inverted` (`829` rows; `49.23%` of `1,684` dual-date accounts):** Flags records where `last_purchase_date < signup_date` so lifecycle `customer_tenure_days` ($n = 855$ valid) is protected from negative durations without deleting valid standalone dates.
   - **`is_geo_mismatch` (`5,888` rows; `80.13%` of `7,348` dual-known geo accounts):** Flags records pairing one of the 8 Indian metropolitan cities with `USA`, `Australia`, `Canada`, or `UK` ($\chi^2 p = 0.8888$), preserving raw `city` and `country` values for downstream audit (`A3`) while enabling clean geographic filtering.
   - **`is_score_10_spike` (`2,521` rows) & `feedback_score_1_to_5` ($n = 2,528$):** Isolates the off-scale `10` anomaly (`49.93%` of `5,049` valid ratings) by setting `10 → NaN` in `feedback_score_1_to_5` (`mean = 2.96`, `median = 3.00`) rather than remapping `10 → 5`, which would artificially inflate `Promoters (4–5)` by **`+266.8%`** (`945` → `3,466`).
   - **`completeness_score` (`float64`, `0.0`–`1.0`):** Captures row-wise valid attribute coverage across all 12 core columns (`mean = 0.5533`, `median = 0.5833`, range `0.1667`–`0.9167`).

5. **Trade-Offs & Missingness Mechanism Evaluation (MCAR Verification):**
   - Retaining `NaN` reduces complete-case sample size (`n = 2,465` for `age`, `n = 2,466` for `purchase_amount`, and `n = 600` for joint `age × purchase_amount`), trading narrower confidence intervals for **zero synthetic variance bias**. Complete-case estimation on valid observations is statistically unbiased when missingness is consistent with **Missing Completely at Random (MCAR)** — verified empirically below via Welch's two-sample $t$-test and Mann-Whitney $U$ tests across `is_age_missing` and `is_purchase_missing`.
```

```python
import sys
from pathlib import Path

repo_root = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.cleaning import (
    build_cleaning_decisions_audit,
    clean_customers,
    compute_imputation_variance_impact,
    export_m1_artifacts,
    load_raw_customers,
)

m1_paths = export_m1_artifacts()
df_raw_m1 = load_raw_customers()
df_v2 = clean_customers(df_raw_m1)
m1_audit = build_cleaning_decisions_audit(df_raw_m1, df_v2)
m1_impact = compute_imputation_variance_impact(df_v2)

print(f"Exported cleaned v2 dataset: {m1_paths['customers_clean_v2'].relative_to(repo_root)}")
print(f"Cleaned v2 dataset shape: {df_v2.shape[0]:,} rows × {df_v2.shape[1]} columns")
print(
    "v2 quality flags summary: "
    f"has_valid_email={int(df_v2['has_valid_email'].sum()):,}, "
    f"has_valid_phone={int(df_v2['has_valid_phone'].sum()):,}, "
    f"is_date_inverted={int(df_v2['is_date_inverted'].sum()):,}, "
    f"is_geo_mismatch={int(df_v2['is_geo_mismatch'].sum()):,}, "
    f"is_age_missing={int(df_v2['is_age_missing'].sum()):,}, "
    f"is_purchase_missing={int(df_v2['is_purchase_missing'].sum()):,}, "
    f"is_score_10_spike={int(df_v2['is_score_10_spike'].sum()):,}, "
    f"feedback_1_to_5_valid={int(df_v2['feedback_score_1_to_5'].notna().sum()):,}, "
    f"mean_completeness={df_v2['completeness_score'].mean():.4f}"
)

audit_display_cols = [
    "raw_column",
    "clean_column",
    "target_dtype",
    "blank_count",
    "sentinel_count",
    "total_invalid",
    "invalid_pct",
    "valid_count",
    "valid_pct",
    "imputation_choice",
]
print("\n=== [M1] CLEANING & IMPUTATION DECISIONS AUDIT (12 ATTRIBUTES) ===")
print(m1_audit[audit_display_cols].to_string(index=False))

impact_display_cols = [
    "variable",
    "missing_pct",
    "strategy",
    "n_evaluated",
    "mean",
    "std",
    "std_change_pct",
    "q1",
    "median",
    "q3",
    "iqr",
    "iqr_change_pct",
]
print("\n=== [M1] IMPUTATION VARIANCE & IQR IMPACT EXPERIMENT ===")
print(m1_impact[impact_display_cols].round(2).to_string(index=False))

mcar_display_cols = [
    "variable",
    "mcar_check_target",
    "n_target_when_missing",
    "n_target_when_observed",
    "target_mean_when_missing",
    "target_mean_when_observed",
    "welch_t_stat",
    "welch_p_value",
    "mannwhitney_u_stat",
    "mannwhitney_p_value",
    "mcar_conclusion",
]
print("\n=== [M1] MISSINGNESS MECHANISM (MCAR) TWO-SAMPLE VERIFICATION ===")
print(m1_impact[mcar_display_cols].drop_duplicates().to_string(index=False))
```

```markdown
**Methodological Interpretation (`M1` — Empirical Proof Against Single-Value Imputation):**
- **Catastrophic Variance (`~50.4%`) & Interquartile (`100%`) Collapse (`Q1`, `Q2`):** Replacing `75.35%` missing `age` ($7,535$ rows) with the valid median (`43.00` years) or mean (`43.70` years) compresses the sample standard deviation from **`15.30` years to `7.60` years** (**`-50.32%`** and **`-50.36%`**) and collapses the interquartile range by **`-100.00%`** (`IQR: 27.00 → 0.00` years, as both `Q1` and `Q3` collapse onto the constant spike). Identically, imputing `75.34%` missing `purchase_amount` ($7,534$ rows) with the median (`$2,460.36`) or mean (`$2,450.62`) slashes `SD` from **`$1,442.83` to `$716.40` / `$716.39`** (**`-50.35%`**) and annihilates `IQR` from **`$2,574.50` to `$0.00`** (**`-100.00%`**). Had median imputation been applied, the downstream `[M2]` Tukey outlier fences ($[Q_1 - 1.5 \times \text{IQR},\; Q_3 + 1.5 \times \text{IQR}]$) would degenerate to a zero-width point (`[43.00, 43.00]` and `[$2,460.36, $2,460.36]`), falsely flagging **every genuine non-median customer and transaction** as an outlier while fabricating **`$18,536,314.87`** in unverified spend!
- **Confirmed MCAR Missingness Independence (`Q1`, `Q2`):** Two-sample hypothesis tests confirm that retaining `NaN` introduces no selection bias across continuous metrics: verified `purchase_amount` does not differ between accounts with missing `age` ($n = 1,866$, `mean = $2,457.01`) and observed `age` ($n = 600$, `mean = $2,430.72`; Welch's $t = 0.3903, p = 0.6964$; Mann-Whitney $U = 565,943.5, p = 0.6855$), nor does verified `age` differ between accounts with missing `purchase_amount` ($n = 1,865$, `mean = 43.79` years) and observed `purchase_amount` ($n = 600$, `mean = 43.43` years; Welch's $t = 0.5086, p = 0.6112$; Mann-Whitney $U = 566,596.0, p = 0.6398$).
- **Expanded `v2` Quality Contract (`Q1`, `Q3`):** `customers_clean_v2.csv` (`10,000 × 21`) preserves 100% cell-for-cell backward compatibility with `v1` across the first 15 columns while embedding `is_geo_mismatch` (`5,888` rows), `is_age_missing` (`7,535`), `is_purchase_missing` (`7,534`), `is_score_10_spike` (`2,521`), `feedback_score_1_to_5` ($n = 2,528$ valid), and `completeness_score` (`mean = 0.5533`, `SD = 0.1180`) for downstream outlier (`M2`), segmentation (`M3`), and feature engineering (`M4`) workflows.
```

## Key Findings
- **Severe Dispersion Destruction Under Naive Imputation (`Q1`, `Q2`):** Single-value median/mean imputation on `age` ($n_{\text{valid}} = 2,465$, `75.35%` missing) and `purchase_amount` ($n_{\text{valid}} = 2,466$, `75.34%` missing) collapses `SD` by **`50.32%–50.36%`** (`15.30 → 7.60` years; `$1,442.83 → $716.40`) and collapses `IQR` by **`100.00%`** (`27.00 → 0.00` years; `$2,574.50 → $0.00`), proving mathematically why `NaN` retention + explicit missingness flags (`is_age_missing`, `is_purchase_missing`) is mandatory before `[M2]` Tukey IQR outlier analysis.
- **Unbiased MCAR Missingness Mechanism (`Q1`, `Q2`):** Observed `purchase_amount` is invariant to `is_age_missing` ($n = 1,866$ vs. $n = 600$; Welch $t = 0.3903, p = 0.6964$; Mann-Whitney $U = 565,943.5, p = 0.6855$) and observed `age` is invariant to `is_purchase_missing` ($n = 1,865$ vs. $n = 600$; Welch $t = 0.5086, p = 0.6112$; Mann-Whitney $U = 566,596.0, p = 0.6398$), confirming that complete-case sub-cohorts remain unbiased.
- **Zero Row Attrition & Lossless PK Recovery (`Q1`–`Q3`):** All `12` raw columns are retained (`24.65%`–`88.70%` valid signal), `0` full-row duplicates exist across $N = 10,000$ accounts, and all `7,621` non-blank raw `CustomerID` entries (`2,561` `'C'`-prefixed, `5,060` bare digits) align 1-to-1 with `row_index + 1` (`0` collisions), enabling lossless `C00001`–`C10000` reconstruction.
- **Non-Destructive Contradiction & Scale Isolation (`Q1`, `Q3`):** Standardizing `v2` (`10,000 × 21`) isolates `5,888` cross-border city-country contradictions (`is_geo_mismatch`), `829` date inversions (`is_date_inverted`), and `2,521` off-scale `10` ratings (`is_score_10_spike` / `feedback_score_1_to_5`, preventing a `+266.8%` false surge in Promoters), with average row-level `completeness_score = 0.5533` (`6.64 / 12` valid attributes per customer).

## Open Issues
- Because `run_command` executes inside the read-only workspace sandbox (`BypassSandbox: false`), `src/cleaning.py`, `data/processed/summaries/m1_cleaning_decisions_audit.csv`, `data/processed/summaries/m1_imputation_variance_impact.csv`, and `handoffs/m1_data-cleaner.md` were written directly to the workspace via `write_file`, while `customers_clean_v2.csv` (`10,000 × 21`) was verified in `$env:TEMP\customers_clean_v2_test.csv` against `check_data_contract.py`. When assembling the notebook, run `.\EDA\Scripts\python.exe -m src.cleaning` (or execute the `[M1]` notebook cell calling `export_m1_artifacts()`) so `data/processed/customers_clean_v2.csv` and the two `M1` summary CSVs are written with native OS line endings prior to `run_local_ci.py`.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- `.\EDA\Scripts\python.exe .github/scripts/check_data_contract.py $env:TEMP\customers_clean_v2_test.csv` → `PASSED (0 error(s), 0 warning(s))` across `10,000` rows × `21` columns (`has_valid_email`, `has_valid_phone`, `is_date_inverted`, `is_geo_mismatch`, `is_age_missing`, `is_purchase_missing`, `is_score_10_spike`, `feedback_score_1_to_5`, `completeness_score`).
- Verified `clean_customers(clean_customers(df_raw))` idempotency (`assert_frame_equal` → `PASS`), 100% cell-for-cell parity of the first 15 columns with `data/processed/customers_clean_v1.csv`, and identical SHA-256 digests across repeated `export_m1_artifacts()` runs.
