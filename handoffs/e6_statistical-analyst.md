# E6 — statistical-analyst handoff

## Outputs
- `src/analysis.py` — Canonical business question KPI synthesis function (`compute_research_question_kpis`) mapping `KPI-1` through `KPI-6` to `Q1`, `Q2`, and `Q3` per `specs/ontology.md` §4.
- `data/processed/summaries/e6_research_questions_kpis.csv` — Consolidated 8-row executive KPI summary table covering `KPI-1` through `KPI-6` with exact numerators, denominators, primary/secondary metrics, units, and diagnostic notes.

## Notebook Cells
```markdown
---

## 6. `[E6]` Quantitative KPI Synthesis — Answering the Three Guiding Business Questions

To close the Essential EDA block, we consolidate canonical metrics **KPI-1 through KPI-6** (`specs/ontology.md` §4) from `src/analysis.py` to provide evidence-backed quantitative answers to `Q1`, `Q2`, and `Q3`.
```

```python
from src.analysis import compute_research_question_kpis, load_clean_customers

df_clean_e6 = load_clean_customers("v1")
e6_kpis = compute_research_question_kpis(df_clean_e6)

print("=== [E6] CANONICAL RESEARCH QUESTION KPI SUMMARY (KPI-1 TO KPI-6) ===")
print(e6_kpis.round(2).to_string(index=False))
```

```markdown
### Preliminary Evidence-Backed Answers (`E6`)

1. **`Q1` — Customer Demographics & Geographic Footprint (`KPI-1`):**
   - **Coverage & Profile:** After removing `-5` (`2,506`) and `200` (`2,453`) sentinels, valid `age` is available for **24.65%** of accounts ($n = 2,465$), centered at `mean = 43.70` years (`SD = 15.30`) and `median = 43.00` years (`IQR = 27.00`, range `18–70`). Known `gender` (`75.45%` coverage, $n = 7,545$) is evenly split between `Male` (`50.36%`, $n = 3,800$) and `Female` (`49.64%`, $n = 3,745$).
   - **Geographic Contradiction:** While `city` (`88.70%` known, $n = 8,870$) comprises exclusively 8 Indian metros (`1,056–1,144` records each), `country` (`82.96%` known, $n = 8,296$) distributes records uniformly (~`20%` each) across `USA`, `Australia`, `Canada`, `UK`, and `India` ($6,655$ non-Indian country rows overall). Exactly **5,888 accounts** (`58.88%` of all rows; **80.13%** of $7,348$ dual-known geo rows) pair an Indian city with a non-Indian country ($\chi^2 = 19.29, p = 0.8888$), proving `country` cannot be trusted for regional reporting without upstream CRM geo-validation.

2. **`Q2` — Revenue Distribution & High-Value Segments (`KPI-2`, `KPI-3`):**
   - **Order Value Baseline:** Across $n = 2,466$ valid transactions (`24.66%` coverage; `$6,043,218.46` total spend), `purchase_amount` is symmetrically and broadly distributed (`mean AOV = $2,450.62`, `SD = $1,442.83`; `median MOV = $2,460.36`, `IQR = $2,574.50`), corresponding to a baseline **KPI-3** of **`$2,450,615.76` per 1,000 valid customers**.
   - **Absence of True Segment Differentiation:** Although sample point estimates range from `$2,286,536.33/1k` (`Kolkata`, $n = 264$) to `$2,562,508.53/1k` (`Chennai`, $n = 258$) by city and `$2,334,765.97/1k` (`18-29`, $n = 134$) to `$2,556,179.32/1k` (`60+`, $n = 117$) by age cohort, formal ANOVA and Kruskal-Wallis tests confirm **zero statistically significant differences** across `gender` ($p = 0.8161$), `country` ($p = 0.6413$), `city` ($p = 0.4752$), or `age_group` ($p = 0.6798$). Marketing budgets should therefore prioritize transaction-level spend tiers rather than demographic or geographic targeting.

3. **`Q3` — Customer Satisfaction, Lifecycle Tenure & Channel Reachability (`KPI-4`, `KPI-5`, `KPI-6`):**
   - **Satisfaction (`KPI-6`):** Among $n = 5,049$ valid ratings (`50.49%` coverage), **49.93%** ($n = 2,521$) sit at an off-scale value of `10` (likely a `1–10` survey instrument merged into a `1–5` schema without normalization). On the clean `1–5` Likert scale ($n = 2,528$), sentiment is neutral-to-critical (`mean = 2.96`, `SD = 1.42`, `median = 3.00`, `IQR = 2.00`), with `Detractors (1-2)` ($1,027$; `40.62%` of Likert) slightly outnumbering `Promoters (4-5)` ($945$; `37.38%` of Likert), and shows no correlation with spend ($r = -0.0178, p = 0.6508$).
   - **Chronological Integrity & Tenure (`KPI-5`):** Only **50.77%** ($855$ of $1,684$ dual-date rows) satisfy `last_purchase_date >= signup_date` ($829$ rows [`49.23%`] are chronologically inverted). Valid customer tenure ($n = 855$) averages `688.59` days (`SD = 464.11`; `median = 638.00` days, `IQR = 710.50`) and does not correlate with spend ($r = -0.0560, p = 0.4098$).
   - **Reachability Risk (`KPI-4`):** Only **43.88%** ($4,388$ of $10,000$) of accounts have at least one valid contact channel (`25.12%` valid email [$2,512$], `25.10%` valid phone [$2,510$], `6.34%` omnichannel [$634$]). Critically, **56.12%** ($5,612$) of accounts — representing **`$3,388,004.29` (`56.06%`) of verified revenue** — cannot be reached by email or phone, making checkout/CRM contact validation the highest-ROI operational intervention.
```

## Key Findings
- **`KPI-1` (`Q1` — Coverage & Geo Integrity):** Valid `age` covers `24.65%` ($n = 2,465$, `mean = 43.70y`, `median = 43.00y`), while `5,888` of `7,348` dual-known geo records (`80.13%`; `58.88%` of total) pair an Indian city with `USA`, `Australia`, `Canada`, or `UK` ($\chi^2 = 19.29, p = 0.8888$).
- **`KPI-2` & `KPI-3` (`Q2` — Revenue & Segment Parity):** Valid spend ($n = 2,466$, `24.66%` coverage) averages `$2,450.62` (`SD = $1,442.83`, `median = $2,460.36`, `IQR = $2,574.50`, `$2,450,615.76` per 1,000 valid customers), with all segment differences statistically non-significant ($p \ge 0.31$).
- **`KPI-4` (`Q3` — Reachability Exposure):** Only `43.88%` ($4,388$) of accounts are reachable (`6.34%` [`634`] both channels), leaving `56.12%` ($5,612$) unreachable and exposing `$3,388,004.29` (`56.06%` of verified spend) to unmitigated churn risk.
- **`KPI-5` (`Q3` — Chronological Integrity & Tenure):** Chronological integrity across dual-date records is `50.77%` (`855` valid vs. `829` inverted of `1,684`); valid tenure ($n = 855$) has `mean = 688.59` days (`median = 638.00` days, `IQR = 710.50` days) and zero spend correlation ($r = -0.0560, p = 0.4098$).
- **`KPI-6` (`Q3` — Satisfaction Split):** Score `10` makes up `49.93%` ($2,521$ of $5,049$) of valid ratings; standard `1–5` ratings ($n = 2,528$) average `2.96` (`median = 3.00`), with `1,027` Detractors (`20.34%` of all valid / `40.62%` of Likert `1–5`) vs. `945` Promoters (`18.72%` of all valid / `37.38%` of Likert `1–5`).

## Open Issues
- Ready for `ExecutiveReporterAgent` (`E6`) to polish final narrative prose and cross-reference `DataVizAgent`'s exported `E4`/`E5` figures (`assets/charts/e4_*.png`, `assets/charts/e5_*.png`). Notice that `$3,388,004.29 / $6,043,218.46 = 56.06%` of verified spend sits in unreachable accounts (`1,397 / 2,466 = 56.65%` of valid orders) — a high-impact business hook for `Q3`.

## Verification
- `.\EDA\Scripts\python.exe -m ruff check --no-cache src/` → `0 errors` (`All checks passed!`)
- `.\EDA\Scripts\python.exe -m flake8 src/ --select=E9,F63,F7,F82` → `0 errors`
- `.\EDA\Scripts\python.exe -m flake8 src/ --max-line-length=127` → `0 errors`
- Verified `e6_research_questions_kpis.csv` (8 KPI rows × 11 columns) matches all upstream `E4` and `E5` summary tables identically.
