# 🧬 Specifications (`specs/`)

`specs/ontology.md` is the **single source of truth** for the domain: entities, column names,
dtypes, sentinels, data-quality flags, engineered features and KPIs.

## What is inside

| Section | Content |
|---|---|
| §1 | Entities and conceptual model |
| §2 | Five data-quality dimensions and raw baselines |
| §3.1 | Cleaned schema and sentinel catalog |
| §3.2 | Data-quality flags (Data Cleaner) and analytical features (Statistical Analyst) |
| §4 | Business KPIs and research-question mapping |

## How to change the spec

1. Open or reuse a task issue that explains the change.
2. Edit `specs/ontology.md` first: name, dtype, formula, owner and analytical purpose.
3. If a column becomes mandatory, update `.github/scripts/check_data_contract.py`.
4. Update the owning skill in `.agents/skills/`.
5. Implement in `src/` and run `run_local_ci.py`.

## Ownership

| Object | Owner |
|---|---|
| Data-quality flags (`has_valid_email`, `is_date_inverted`, ...) | `DataCleanerAgent` |
| Analytical features (`age_group`, `spend_tier`, ...) | `StatisticalAnalystAgent` |
| KPI definitions and schema changes | Lead Orchestrator |

## Enforcement

`python .github/scripts/check_data_contract.py` validates every `customers_clean_*.csv` against
§3.1 and the flags in §3.2. The check runs locally and in CI. Optional flags are validated only
when the column exists, so a new flag must be added to the contract when it becomes mandatory.
