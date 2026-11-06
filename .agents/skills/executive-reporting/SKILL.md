---
name: executive-reporting
description: >-
  Turn statistical summaries and exported charts into evidence-backed answers to the three business
  questions, the 1–2 page CEO executive report, and the 5-minute non-technical presentation script.
  Activate this skill when executing tasks E6, M7, X5, or X6 (release notes text).
---

# Executive Reporting & Data Storytelling Skill (`executive-reporting`)

This skill defines the structure, evidence rules, and tone for `ExecutiveReporterAgent`. The reporter **never computes new numbers**: every figure it cites must already exist in a summary table, a handoff, or the notebook.

---

## 1. Inputs (Read-Only)

| Input | Path | Used for |
|---|---|---|
| Summary tables | `data/processed/summaries/<task_id>_*.csv` | Every number in the narrative. |
| Agent handoffs | `handoffs/<task_id>_*.md` (`## Key Findings`) | Findings already stated with $n$ and metric. |
| Charts | `assets/charts/<task_id>_<slug>.png` | Visual support, cited by relative path. |
| KPIs & definitions | [`specs/ontology.md`](../../../specs/ontology.md) §4 | KPI names, formulas, baselines. |
| Scope & deadlines | [`docs/Work_Plan.md`](../../../docs/Work_Plan.md) | Task outputs expected for each ID. |

If a number you need is not in these inputs, **do not calculate it**. List it under `## Open Issues` in `handoffs/<task_id>_executive-reporter.md` so the Lead Orchestrator routes it to `StatisticalAnalystAgent`.

---

## 2. Evidence Rules

1. **Every claim carries its evidence:** metric + sample size + source. Example: *"Median spend is $2,460 (n = 2,466 valid purchases; KPI-2, `e4_summary_stats.csv`)."*
2. **State coverage up front.** Only ~25% of rows have a valid `age` or `purchase_amount`. Each section that uses them must say so once, in plain words.
3. **No causal language** from correlations. Use *"is associated with"*, *"moves together with"*, never *"drives"*, *"causes"*, *"leads to"*.
4. **No significance claims** without the test result from the analyst ($p$-value and test name).
5. **Flag data-quality caveats** that change the reading: the `10` feedback spike, the `is_geo_mismatch` cities, the `is_date_inverted` rows.
6. **Round for executives:** currency to whole dollars, shares to one decimal (`43.9%`), counts with thousands separators.

---

## 3. Deliverable Templates

### 3.1 Research Question Answers (`E6`) — handoff only
For each of `Q1` (Demographics & Geography), `Q2` (Revenue & High-Value Segments), `Q3` (Satisfaction, Retention & Reachability), write a Markdown cell for the notebook with:
- **Answer** (1–2 sentences, plain language).
- **Evidence** (2–3 bullets, each with $n$ and metric).
- **Caveat** (1 bullet on data coverage or quality).

### 3.2 CEO Executive Report (`M7`) — `reports/executive_report.md`
Maximum 2 printed pages. Sections, in order:
1. **Bottom Line** — 3 bullets the CEO can repeat.
2. **Data We Could Trust** — one short paragraph with KPI-1 coverage.
3. **Findings by Question** — `Q1`, `Q2`, `Q3`, each with one chart (`![...](../assets/charts/...)`) and 2–3 quantified insights.
4. **Recommendations** — each tied to one finding, with owner type (Marketing, CRM, Data team) and expected effect.
5. **Limitations** — what this data cannot answer.

### 3.3 Presentation Script (`X5`) — `reports/presentation.md`
5 minutes ≈ 650–750 spoken words, 3–4 charts. Structure: **Hook → Problem (messy data) → 3 findings (one per question) → Ask (recommendations) → Close**. Each slide block lists: slide title, chart path, speaker notes. Request any missing chart from `DataVizAgent` through `## Open Issues`.

### 3.4 Release Notes (`X6`) — handoff only
Draft the README "Results" and "How to run" text inside the handoff. The Lead Orchestrator applies it to `README.md`.

---

## 4. Quality Checklist

- [ ] Every number traces to a summary table, handoff, or ontology KPI.
- [ ] Every section states $n$ and coverage.
- [ ] No causal verbs; no significance claims without a test.
- [ ] Every recommendation maps to a specific finding.
- [ ] Charts are referenced by relative path and exist in `assets/charts/`.
- [ ] 100% English, no jargon left unexplained (`IQR`, `Spearman` → one-line plain explanation or removed).
- [ ] `handoffs/<task_id>_executive-reporter.md` written with the five sections from `AGENTS.md` Law 2.
