# A2 — statistical-analyst handoff

## Outputs
- `data/external/indian_cities_metadata.csv` — auxiliary catalog mapping 8 Indian Tier-1 metropolitan areas to macroeconomic regions, states, and populations
- `src/features.py` — added `enrich_with_external_metro_data`, `export_a2_features`, and updated `load_enriched_customers("v2")`
- `data/processed/customers_enriched_v2.csv` — 30-column customer dataset augmented with `metro_region`, `metro_state`, and `metro_population_m`
- `src/analysis.py` — added `audit_external_enrichment`
- `data/processed/summaries/a2_external_enrichment_audit.csv` — join integrity audit
- `data/processed/summaries/a2_regional_performance.csv` — 5-zone macroeconomic regional performance table

## Notebook Cells
```markdown
### 17.1 `[A2]` Auxiliary Dataset Enrichment — Indian Metropolitan Classification

To enable spatial and macroeconomic cohort analysis, the customer dataset was enriched with an auxiliary demographic catalog (`data/external/indian_cities_metadata.csv`) derived from Census of India and RBI urban classifications. 

The catalog maps each of the 8 Indian cities to its macroeconomic geographic zone (`metro_region`), state/territory (`metro_state`), metropolitan population in millions (`metro_population_m`), and urban tier (`Tier-1`).
```

```python
from src.analysis import audit_external_enrichment
from src.features import load_enriched_customers

df_enriched_v2 = load_enriched_customers("v2")
a2_audit_df, a2_perf_df = audit_external_enrichment(df_enriched_v2)

print("=== Merge Quality & Join Coverage Audit ===")
display(a2_audit_df)

print("=== Regional Macroeconomic Performance ===")
display(a2_perf_df)
```

```markdown
**Enrichment Audit & Regional Findings (`Q1`, `Q2`):**
- **100.0% Known Match Rate:** All 8,870 records with known city values successfully matched against the auxiliary catalog without dropping any rows or introducing many-to-many cardinality expansion. The 1,130 records with `city == 'Unknown'` were mapped to `metro_region == 'Unknown'` and `np.nan` population, strictly adhering to ontology rules.
- **Geographic Concentration:** The customer base is heavily concentrated in South India ($3,373$ accounts, $33.73\%$, $\$2,028,212$ revenue) and West India ($3,350$ accounts, $33.50\%$, $\$2,042,428$ revenue), followed by North India ($1,091$ accounts, $10.91\%$) and East India ($1,056$ accounts, $10.56\%$).
- **Regional Spending Homogeneity:** Normalized revenue per 1,000 customers remains virtually flat across geographic zones: $\$609,680$ in West India, $\$601,308$ in South India, $\$610,696$ in North India, and $\$581,399$ in East India. Average Order Value ranges narrowly from $\$2,427.35$ (North) to $\$2,488.62$ (West), confirming national commercial consistency.
```

## Key Findings
- Merge coverage = 8,870 of 8,870 known city records matched (100.0% coverage) → answers Q1
- South & West concentration = 6,723 of 10,000 customers (67.23%) across 6 Tier-1 agglomerations → answers Q1
- Regional revenue per 1k accounts = $\$609.7\text{k}$ (West) vs $\$601.3\text{k}$ (South) vs $\$610.7\text{k}$ (North) vs $\$581.4\text{k}$ (East) → answers Q2

## Open Issues
- `DataVizAgent` can leverage `metro_region` in multi-dimensional segment comparisons (`A5`).

## Verification
- `ruff check src/features.py src/analysis.py` → 0 errors
- Schema check passed: `customers_enriched_v2.csv` has 10,000 rows and 30 columns.
