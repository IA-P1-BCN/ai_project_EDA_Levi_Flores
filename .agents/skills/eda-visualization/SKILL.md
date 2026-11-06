---
name: eda-visualization
description: >-
  Design, format, annotate, and export publication-grade static (matplotlib/seaborn) and interactive
  (plotly) visualizations to assets/charts/. Activate this skill when executing tasks E4, E5, M2,
  M5, M6, A4, A5, A6, or X2, and when ExecutiveReporterAgent needs supporting charts for X5.
---

# Scientific & Executive Visualization Skill (`eda-visualization`)

This skill defines the visual design system, accessibility standards, annotation rules, and deterministic export conventions for `DataVizAgent`.

---

## 1. Visual Design System & Colorblind-Safe Palettes

All figures produced in `notebooks/01_eda_customers.ipynb`, `src/visualization.py`, and `app/dashboard.py` must adhere to a cohesive visual identity:

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Global publication rcParams
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 15,
    "figure.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
})

# Colorblind-safe Okabe-Ito & institutional palette
PALETTE_PRIMARY = "#1B4F72"    # Deep Navy (Primary bars / distributions)
PALETTE_SECONDARY = "#2E86AB"  # Steel Blue
PALETTE_ACCENT = "#D95F02"     # High-contrast Orange (Outliers / mean markers / highlights)
PALETTE_TEAL = "#1B9E77"       # Emerald Teal (Positive / valid segments)
PALETTE_MUTED = "#7F8C8D"      # Neutral Slate ('Unknown' / missing categories)
CATEGORICAL_PALETTE = ["#1B4F72", "#2E86AB", "#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02"]
```

---

## 2. Mandatory Anatomy of Every Chart

Every chart must include **five mandatory structural elements**:

1. **Finding-Driven Title:** State the analytical takeaway (e.g., *"Customer Age Distribution Is Symmetric Around 43.7 Years Across Valid Records"*), not just *"Histogram of Age"*.
2. **Scope & Sample Size Subtitle (`n`):** Explicitly display the number of valid non-null observations plotted (e.g., `n = 2,465 valid records; 7,535 missing/sentinel excluded`).
3. **Axis Labels with Explicit Units:**
   - Monetary values: `Purchase Amount (USD $)`
   - Age: `Customer Age (Years)`
   - Tenure: `Customer Tenure (Days)`
   - Counts / Shares: `Customer Count (n)` or `Share of Segment (%)`
4. **Reference Lines & Direct Data Annotations:**
   - Univariate histograms/KDEs must overlay vertical dashed lines for **Mean** (`#D95F02`) and **Median** (`#1B9E77`) with numeric callouts.
   - Boxplots must annotate **IQR bounds** ($Q_1$, Median $Q_2$, $Q_3$) and Tukey fences ($Q_1 - 1.5\text{IQR}$, $Q_3 + 1.5\text{IQR}$).
   - Bar/count plots must display direct value labels (`n` and `%`) above or beside each bar.
5. **Source & Footnote Caption:** Add a bottom caption via `fig.text(0.01, -0.02, "Source: Customer Messy Data (customers_clean_v1.csv) | Author: @levifvy", fontsize=9, color="#555555")`.

---

## 3. Chart Type Selection Matrix

| Analytical Goal | Task IDs | Required Chart Type(s) | Key Encoding Rules |
|---|---|---|---|
| **Univariate Continuous** (`age`, `purchase_amount`) | `E4`, `M2`, `A4` | Combined Histogram + KDE (`sns.histplot(..., kde=True)`) + horizontal Boxplot (`gridspec_kw={'height_ratios': [3, 1]}`) | Show mean, median, SD, and IQR fences on the same canvas. |
| **Univariate Categorical** (`gender`, `city`, `country`, `feedback_score`) | `E4`, `A1` | Ordered horizontal/vertical Bar Chart (`sns.countplot` / `ax.barh`) | Sort categories descending by count/rate; render `'Unknown'` in muted grey (`#7F8C8D`). |
| **Bivariate Continuous × Categorical** (`purchase_amount` by `gender`, `city`, `age_group`) | `E5`, `M3`, `A5` | Violin + Boxplot overlay or Grouped Bar Chart with 95% CI error bars | Annotate group medians and sample sizes ($n_k$) per category. |
| **Bivariate Continuous × Continuous** (`age` vs. `purchase_amount`) | `E5` | Binned Hexbin / Regplot with marginal distributions or Cohort Mean/Median Line Plot | Avoid overplotting 2,000+ raw scatter points without alpha transparency (`alpha=0.35`) and trend line. |
| **Multivariate Correlation** | `M5` | Lower-triangle Annotated Heatmap (`sns.heatmap(..., mask=mask, annot=True, fmt=".2f", cmap="vlag", vmin=-1, vmax=1)`) | Include explicit subtitle: *"Pearson r / Spearman ρ — Correlation does not imply causation"*. |
| **Temporal Evolution** (`signup_date`, `last_purchase_date`) | `M6`, `A4` | Monthly/Quarterly Time-Series Line Chart with 3-month rolling average | Highlight chronological inversion cleaning before plotting trends. |
| **Interactive Exploration** | `A6`, `X2` | `plotly.express` interactive chart (`px.scatter`, `px.box`, `px.sunburst`, or `px.histogram`) | Configure rich `hover_data`, human-readable `labels={...}`, and export to HTML + static summary. |

---

## 4. Deterministic Export Protocol (`assets/charts/`)

Every figure generated in code or notebooks must be saved deterministically to `assets/charts/` using the task ID prefix:

This helper lives in `src/visualization.py`. The path is anchored to the repository root, so it works the same from `notebooks/`, `src/pipeline.py`, `pytest`, or `streamlit run app/dashboard.py` (a `".."`-relative path only works from `notebooks/`):

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHARTS_DIR = REPO_ROOT / "assets" / "charts"


def save_publication_figure(fig, task_id: str, slug: str) -> Path:
    """Save figure at 300 DPI with tight bounding box and return its path."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)  # empty dirs are not tracked by Git
    out_path = CHARTS_DIR / f"{task_id.lower()}_{slug}.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved figure: {out_path.relative_to(REPO_ROOT)}")
    return out_path
```

The notebook imports it (`from src.visualization import save_publication_figure`) instead of redefining it.

---

## 5. Quality Verification Checklist for `DataVizAgent`

- [ ] Does the chart title state a clear finding in English?
- [ ] Is the valid sample size ($n$) stated in the title or subtitle?
- [ ] Do both axes have human-readable labels (no raw `snake_case` variable names) and explicit units?
- [ ] Are `'Unknown'` / missing categories visually distinguished in muted grey (`#7F8C8D`)?
- [ ] Is the PNG exported to `assets/charts/<task_id>_<slug>.png` at `300 DPI` without clipped labels?
- [ ] Does `handoffs/<task_id>_data-viz.md` contain, under `## Notebook Cells`, each chart's code cell followed immediately by a Markdown interpretation cell explaining *what* is observed and *how* it answers `Q1`, `Q2`, or `Q3`? (`DataVizAgent` never edits the notebook; the Lead Orchestrator pastes these cells — see `AGENTS.md` Law 2.)
- [ ] Is the finding in the title backed by a number from the `StatisticalAnalystAgent` handoff or summary table for the same Task ID (`AGENTS.md` Law 2b)?
