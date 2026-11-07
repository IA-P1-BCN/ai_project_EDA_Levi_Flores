# 🤖 Agent System — OpenCode, Claude Code and Antigravity

This document is the operational map of the multi-agent system defined in
[`AGENTS.md`](../../AGENTS.md). It explains where each engine discovers agents and skills, how to
invoke the five personas, and how write-zone permissions work.

## 1. The five personas

| Persona | OpenCode definition | Claude Code definition | Canonical skill | Write zone | Tasks |
|---|---|---|---|---|---|
| `DataCleanerAgent` | `.opencode/agents/data-cleaner.md` | `.claude/agents/data-cleaner.md` | `.agents/skills/data-cleaning/SKILL.md` | `src/cleaning.py`, `src/pipeline.py`, `data/processed/customers_clean_*.csv`, `data/processed/summaries/*.csv`, `reports/data_quality_report.md`, `handoffs/*_data-cleaner.md` | E1–E3, M1, A3, A7, X1, X4 |
| `StatisticalAnalystAgent` | `.opencode/agents/statistical-analyst.md` | `.claude/agents/statistical-analyst.md` | `.agents/skills/statistical-analysis/SKILL.md` | `src/analysis.py`, `src/features.py`, `data/external/*`, `data/processed/customers_enriched_*.csv`, `data/processed/summaries/*.csv`, `handoffs/*_statistical-analyst.md` | E4–E6, M2–M6, A1, A2, A4 |
| `DataVizAgent` | `.opencode/agents/data-viz.md` | `.claude/agents/data-viz.md` | `.agents/skills/eda-visualization/SKILL.md` | `src/visualization.py`, `app/dashboard.py`, `assets/charts/*`, `handoffs/*_data-viz.md` | E4–E5, M2, M5–M6, A4–A6, X2 |
| `ExecutiveReporterAgent` | `.opencode/agents/executive-reporter.md` | `.claude/agents/executive-reporter.md` | `.agents/skills/executive-reporting/SKILL.md` | `reports/executive_report.md`, `reports/presentation.md`, `handoffs/*_executive-reporter.md` | E6, M7, X5, X6 |
| `QualityReviewerAgent` | `.opencode/agents/quality-reviewer.md` | `.claude/agents/quality-reviewer.md` | `.agents/skills/pr-self-review/SKILL.md` | `tests/test_*.py`, `tests/conftest.py` | X3 + every PR gate |

## 2. Discovery by engine

| Engine | Project instructions | Subagent definitions | Skill discovery |
|---|---|---|---|
| **OpenCode** | `AGENTS.md` (automatic) | `.opencode/agents/*.md` | `.agents/skills/` (canonical) and `.claude/skills/` (pointers) |
| **Claude Code** | `AGENTS.md` | `.claude/agents/*.md` | `.claude/skills/` (pointers) |
| **Antigravity / Gemini Argon** | `AGENTS.md` | Define one subagent per persona from `AGENTS.md` §3 | `.agents/skills/` |

> In OpenCode, `.agents/skills/` has higher precedence than `.claude/skills/` when both define the
> same skill ID, so the canonical protocol always wins.

## 3. Invoking a subagent in OpenCode

Use the `subagent` tool with the persona ID. The child session starts with fresh context, receives
`AGENTS.md`, and loads the skill named in its definition.

```text
Use the data-cleaner subagent to execute task E3. Inputs: data/raw/messy_customer_data.csv and
specs/ontology.md. Write handoffs/e3_data-cleaner.md when done.
```

```text
Launch statistical-analyst and data-viz in parallel for M2. The analyst owns
data/processed/summaries/m2_*.csv and handoffs/m2_statistical-analyst.md; data-viz waits for that
handoff before drawing assets/charts/m2_*.png.
```

The Lead Orchestrator keeps Git, the notebook and Pull Requests. Subagents never run state-changing
Git commands.

## 4. Permissions and write-zone enforcement

Each `.opencode/agents/<persona>.md` file starts from **deny-all** and then allows:

1. `read`, `glob`, `grep` and `skill` for the whole repository;
2. `shell` for Python, Ruff, Flake8 and pytest;
3. `edit` only inside the persona's write zone.

State-changing Git commands (`git add`, `commit`, `push`, `checkout`, `switch`, `merge`, `rebase`,
`reset`) are denied for every subagent. The Quality Reviewer additionally cannot run
`gh pr merge` or `gh project item-edit`.

This is the OpenCode counterpart of `AGENTS.md` §4 Law 1. If a subagent needs a path outside its
zone, it must report it under `## Open Issues` in its handoff.

## 5. Fan-out and fan-in

- **Fan-out:** each subagent writes modular code (`src/*.py`), summary tables
  (`data/processed/summaries/<task_id>_*.csv`), figures (`assets/charts/<task_id>_*.png`) and a
  handoff (`handoffs/<task_id>_<agent>.md`).
- **Fan-in:** only the Lead Orchestrator edits and executes `notebooks/01_eda_customers.ipynb`,
  pasting the cells from the handoffs (`AGENTS.md` Law 2).
- **Dependency order:** Data Cleaner → Statistical Analyst → Data Viz → Executive Reporter
  (`AGENTS.md` Law 2b).

## 6. Adding or changing an agent

1. Update `AGENTS.md` §3 (persona contract) and §4 (write zone) first.
2. Create or edit `.opencode/agents/<persona>.md` and `.claude/agents/<persona>.md`.
3. Keep the canonical skill in `.agents/skills/<skill>/SKILL.md`; never edit the
   `.claude/skills/` pointer.
4. Add the new persona to the table above.
5. Run `.\EDA\Scripts\python.exe .github/scripts/run_local_ci.py` before opening the PR.

## 7. Troubleshooting

- **The agent does not appear in OpenCode:** confirm the file is
  `.opencode/agents/<id>.md`, has `mode: subagent` and a `description`; then run `/reload`.
- **A write is denied:** the path is outside the persona's zone; update `AGENTS.md` §4 and the
  agent permissions together, or route the change to the owning agent.
- **A skill is not advertised:** confirm `.agents/skills/<id>/SKILL.md` exists and has a
  `description`; check the ID (it comes from the directory name, not the frontmatter `name`).
