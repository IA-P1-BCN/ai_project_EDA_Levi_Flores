# M7 — executive-reporter handoff

## Outputs
- `reports/executive_report.md` (audited OpenCode draft; minimal edits only)
- `handoffs/m7_executive-reporter.md`

## Notebook Cells
```markdown
---

### 10.x `[M7]` Executive Report

The full 1–2 page CEO report is in [`reports/executive_report.md`](../reports/executive_report.md). Every figure in it traces to a `data/processed/summaries/*.csv` table or an analyst handoff (see its Evidence Map). It has five parts: Bottom Line, Data We Could Trust, Findings by Question (`Q1`–`Q3`, one chart each), Recommendations and Limitations.

**Bottom line:**
- **Revenue is concentrated:** 724 High-tier orders (> $3,500; 29.4% of n = 2,466 verified orders) hold $3,057,314, or 50.6% of $6,043,218 verified spend (`KPI-2`, `m4_engineered_features_summary.csv`).
- **Reachability is the main constraint:** 5,612 accounts (56.1%) have no valid email or phone and hold $3,388,004 (56.1%) of verified revenue, including 405 of the 724 High-tier customers ($1,713,463) (`KPI-4`, `m3_pivot_reachability_spend_tier.csv`).
- **Demographic targeting has no support in this data:** spend does not differ by gender, country, city or age group (ANOVA, all p ≥ 0.4752), and none of the 14 independent correlation pairs is significant (max |r| = 0.13, n = 206; smallest p = 0.0662) (`e5_bivariate_hypothesis_tests.csv`, `m5_correlation_pairwise_tests.csv`).
```

```markdown
**How to read it (`M7` caveats):** age and spend are valid for about 24.7% of accounts, valid tenure for 8.6% (n = 855). The drop in cohort tenure from 920.3 days (2020) to 127.0 days (2025) is right-censoring, because newer customers have been observed for less time. It is not evidence of churn. All results are observational associations, not causes. Supporting charts: `assets/charts/e4_univariate_demographics_counts.png`, `assets/charts/e5_bivariate_spend_by_demographics.png`, `assets/charts/m6_cohort_tenure_censoring.png`, `assets/charts/m5_correlation_heatmap.png`, `assets/charts/m6_signup_and_activity_trends.png`.
```

## Key Findings
- **`Q2` revenue concentration:** 724 High-tier orders (29.4% of n = 2,466) generate $3,057,314 = 50.6% of verified spend (`m4_engineered_features_summary.csv`).
- **`Q3` reachability:** 5,612 unreachable accounts (56.1% of n = 10,000) hold $3,388,004 (56.1% of verified revenue); 405 of 724 High-tier customers (55.9%, $1,713,463) are unreachable (`e6_research_questions_kpis.csv` KPI-4, `m3_pivot_reachability_spend_tier.csv`).
- **`Q1`/`Q2` no segment signal:** spend is flat across gender (p = 0.8161), country (p = 0.6413), city (p = 0.4752) and age group (p = 0.6798); max |r| = 0.1263 across 14 pairs (n = 206, p = 0.0704) (`e5_bivariate_hypothesis_tests.csv`, `m5_correlation_highlights.csv`).
- **`Q1` data defect:** 5,888 of 7,348 dual-known records (80.1%) pair an Indian city with a non-Indian country; χ² = 19.29, p = 0.8888 (`e6_research_questions_kpis.csv` KPI-1, `e5_bivariate_hypothesis_tests.csv`).
- **`Q3` tenure:** median tenure 638 days (n = 855). The cohort decline 920.3 → 127.0 days (ρ = −1.00) matches a shrinking observation window (1,920 → 207 days, ratio 0.479–0.614), i.e. right-censoring (`m6_cohort_evolution_summary.csv`, `m6_trend_tests.csv`).

## Open Issues
- **No number mismatches found.** Every figure checked in sections 1–5 and the Evidence Map matches a summary CSV or analyst handoff, within executive rounding (one decimal, whole dollars).
- **Handoff-sourced numbers (not in any CSV):** the Likert shares 40.6% Detractors and 37.4% Promoters of n = 2,528 come only from `handoffs/e6_statistical-analyst.md`. The power caveat (detectable |r| near 0.2 at n = 206) comes only from `handoffs/m5_statistical-analyst.md`. The monthly signup range 57–106 comes from `handoffs/m6_statistical-analyst.md` and `m6_signup_cohorts_monthly.csv`. The report keeps all three, and the Evidence Map now cites their sources. If CSV-only traceability is required, `StatisticalAnalystAgent` could add Likert-base shares to `e6_research_questions_kpis.csv`.
- **Chart embedding decision:** the M5 heatmap and the M6 trend chart are **not embedded** as images. The skill template allows one chart per question, and three embedded images already bring the report close to the 2-page limit. Both charts are cited by path in the Evidence Map. If the Lead Orchestrator prefers the heatmap for Q2, the simplest swap is to replace `e5_bivariate_spend_by_demographics.png`, keeping one chart per question.
- **Page length:** not checked in a rendered PDF. About 1,250 words plus 3 charts should come to about 2 printed pages. Confirm when exporting.
- **Recommendation effects** ("Makes up to $3.39M addressable", etc.) are the revenue currently held by each segment. They are not forecasts of new revenue.
- `reports/presentation.md` (X5) is not part of this task and was not written.

## Verification
- Cross-checked every figure against `e6_research_questions_kpis.csv`, `m4_engineered_features_summary.csv`, `e5_bivariate_hypothesis_tests.csv`, `e4_univariate_categorical_counts.csv`, `m1_imputation_variance_impact.csv`, `m3_pivot_reachability_spend_tier.csv`, `m5_correlation_highlights.csv`, `m5_correlation_pairwise_tests.csv`, `m6_cohort_evolution_summary.csv`, `m6_trend_tests.csv`, and the e6/m5/m6 analyst handoffs. Result: 0 mismatches.
- Chart paths: `e4_univariate_demographics_counts.png`, `e5_bivariate_spend_by_demographics.png`, `m6_cohort_tenure_censoring.png`, `m5_correlation_heatmap.png` and `m6_signup_and_activity_trends.png` all exist in `assets/charts/` (Glob).
- Edits made to `reports/executive_report.md`:
  1. Bottom Line: added a plain-language gloss for ANOVA ("a test comparing group averages").
  2. Q3: added a gloss for Spearman ("a rank-trend test"), and changed "not faster churn" to "not evidence of faster churn" to match the M6 analyst wording. Churn is not measured.
  3. Recommendation 3: changed the expected effect from "caps top-tier churn" (an unsupported effect claim) to "Puts $1,713,463 of top-tier revenue back in contact".
  4. Evidence Map: added sources for 22.4%/15.9% (n = 201), 40.6%/37.4%, the n = 206 power caveat, 634 omnichannel, the 829/1,684 inverted pairs, and SD $1,443 → $716. Added the `m6_signup_and_activity_trends.png` chart path, and split the combined M6/M1 row.
- No code was run. This task only edits Markdown, so no new statistics were computed.
