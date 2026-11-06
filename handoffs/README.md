# Subagent Handoffs

Each subagent ends its task by writing `handoffs/<task_id>_<agent>.md` here (e.g. `e4_statistical-analyst.md`, `e4_data-viz.md`). The Lead Orchestrator reads these files to assemble `notebooks/01_eda_customers.ipynb` (see `AGENTS.md` Law 2 and Law 2b). They are committed so the AI-assisted workflow stays auditable.

Agent slugs: `data-cleaner`, `statistical-analyst`, `data-viz`, `executive-reporter`.

## Template

````markdown
# <TASK_ID> — <agent> handoff

## Outputs
- `path/to/file` — what it contains

## Notebook Cells
```markdown
### <Section title>
```
```python
from src.<module> import <function>
...
```
```markdown
**Interpretation:** what is observed, with n, and which question (Q1/Q2/Q3) it answers.
```

## Key Findings
- <metric> = <value> (n = <n>) → answers Q<k>

## Open Issues
- None / <blocked item, assumption, or request for another agent>

## Verification
- `ruff check src/` → 0 errors
````
