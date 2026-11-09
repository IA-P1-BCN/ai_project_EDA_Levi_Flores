# A3 — data-cleaner handoff

## Outputs
- `src/cleaning.py` — added `build_suspicious_data_audit` and `export_a3_artifacts`
- `data/processed/summaries/a3_suspicious_data_audit.csv` — formal 10-row issue log across ISO/DAMA quality dimensions

## Notebook Cells
```markdown
### 18.1 `[A3]` Formal Suspicious Data Audit & Multi-Dimensional Remediation Log

Following ISO/DAMA Data Quality Dimensions (**Validity**, **Consistency**, **Uniqueness**, and **Accuracy**), this audit evaluates 10 critical data corruption anomalies in the raw customer dataset, documenting empirical frequencies, severity ratings, applied cleaning transformations, and downstream analytical safeguards.
```

```python
from src.cleaning import load_raw_customers, clean_customers, build_suspicious_data_audit

raw_df = load_raw_customers()
clean_df = clean_customers(raw_df)
a3_audit_df = build_suspicious_data_audit(raw_df, clean_df)
a3_audit_df[[
    "anomaly_id", "anomaly_name", "dimension", "corrupted_count",
    "total_evaluated", "corrupted_pct", "severity", "remediation_action"
]]
```

```markdown
**Quantitative Interpretation (`Q1`, `Q2`, `Q3`):**
- **Validity:** Out-of-bounds sentinels affect 49.59% of `Age` records (`-5` in 2,506 rows, `200` in 2,453 rows) and 50.34% of `purchase_amount` records (`-999` in 2,501 rows, `N/A` in 2,533 rows). Coercing these to `NaN` instead of imputing preserves the true variance ($SD = 15.34$ years vs $7.61$ imputed; $SD = \$1,442.83$ vs $\$720.59$ imputed).
- **Consistency:** 49.23% of dual-date customer records ($829$ of $1,684$) suffer from chronological inversion (`last_purchase_date < signup_date`). Rather than dropping rows or computing negative tenures (ranging from $-1,960$ to $-1$ days), records are preserved and tenure is safely masked to `NaN` for inverted rows (`KPI-5`). Furthermore, 58.88% of records ($5,888$ rows) feature Indian metropolitan cities paired with non-Indian countries (`is_geo_mismatch`), confirming synthetic cross-field corruption.
- **Accuracy & Uniqueness:** Primary key gaps affect 23.79% of rows ($2,379$ blank `CustomerID` cells), which are reconstructed into uniform `C00001`–`C10000` identifiers. The bimodal score 10 rating spike affects $2,521$ rows ($49.93\%$ of valid feedback scores) and is isolated via `feedback_score_1_to_5` to prevent distortion of genuine 1–5 customer satisfaction ratings ($mean = 2.96$).
```

## Key Findings
- Total corrupted records audited = 10 anomaly types across 10,000 records → answers Q1, Q2, Q3
- Dual-date chronological inversions = 829 of 1,684 records (49.23%) flagged via `is_date_inverted` → answers Q3 (KPI-5)
- Demographic sentinels remediated to NaN = 4,959 age records (49.59%) and 5,034 purchase records (50.34%) → answers Q1 & Q2
- Geographic cross-column mismatch = 5,888 records (58.88%) flagged via `is_geo_mismatch` → answers Q1

## Open Issues
- None. All audit tables and flags are fully synchronized with `specs/ontology.md` and verified by data contracts.

## Verification
- `ruff check src/cleaning.py` → 0 errors
- `pytest` / verification assertions passed: 10,000 rows, 100% unique primary keys, zero unhandled exceptions.
