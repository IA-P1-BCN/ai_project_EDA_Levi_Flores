"""Publication-grade static visualization module for Essential EDA tasks E4 and E5.

Implements the visual design system, Okabe-Ito colorblind-safe palette, five-element chart
anatomy, and deterministic 300 DPI export protocol defined in ``specs/ontology.md`` and
``.agents/skills/eda-visualization/SKILL.md``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from src.analysis import (
    AGE_GROUP_BINS,
    AGE_GROUP_CATEGORIES,
    AGE_GROUP_LABELS,
    CITY_CATEGORIES,
    COUNTRY_CATEGORIES,
    GENDER_CATEGORIES,
    NON_INDIAN_COUNTRIES,
    load_clean_customers,
)

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
CHARTS_DIR: Path = REPO_ROOT / "assets" / "charts"

# Colorblind-safe Okabe-Ito & institutional palette (.agents/skills/eda-visualization/SKILL.md)
PALETTE_PRIMARY: str = "#1B4F72"    # Deep Navy (Primary bars / distributions)
PALETTE_SECONDARY: str = "#2E86AB"  # Steel Blue
PALETTE_ACCENT: str = "#D95F02"     # High-contrast Orange (Outliers / mean markers / highlights)
PALETTE_TEAL: str = "#1B9E77"       # Emerald Teal (Median markers / valid positive segments)
PALETTE_MUTED: str = "#7F8C8D"      # Neutral Slate ('Unknown' / 'Missing' / 'Unreachable')
CATEGORICAL_PALETTE: list[str] = [
    "#1B4F72",
    "#2E86AB",
    "#1B9E77",
    "#D95F02",
    "#7570B3",
    "#E7298A",
    "#66A61E",
    "#E6AB02",
]

SOURCE_CAPTION: str = "Source: Customer Messy Data (customers_clean_v1.csv) | Author: @levifvy"


def apply_publication_theme() -> None:
    """Configure global matplotlib rcParams for publication-grade static figures."""
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
            "text.parse_math": False,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelweight": "bold",
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 9.5,
            "figure.titlesize": 14,
            "figure.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def save_publication_figure(fig: plt.Figure, task_id: str, slug: str) -> Path:
    """Save figure deterministically at exact 300 DPI with tight white bounding box."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTS_DIR / f"{task_id.lower()}_{slug}.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved figure: {out_path.relative_to(REPO_ROOT).as_posix()}")
    return out_path


def _add_publication_chrome(
    fig: plt.Figure,
    title: str,
    subtitle: str,
    title_y: float = 0.985,
    subtitle_y: float = 0.938,
    caption_y: float = 0.008,
) -> None:
    """Attach finding-driven title, sample-size subtitle, and source footnote caption."""
    fig.text(
        0.01,
        title_y,
        title,
        ha="left",
        va="top",
        fontsize=13.5,
        fontweight="bold",
        color="#111827",
    )
    fig.text(
        0.01,
        subtitle_y,
        subtitle,
        ha="left",
        va="top",
        fontsize=10,
        color="#374151",
    )
    fig.text(
        0.01,
        caption_y,
        SOURCE_CAPTION,
        ha="left",
        va="bottom",
        fontsize=9,
        color="#555555",
    )


def _derive_age_cohorts(df: pd.DataFrame) -> pd.Series:
    """Derive canonical ontology age cohorts with 'Unknown' for missing values."""
    if "age_group" in df.columns:
        return df["age_group"].astype(
            pd.CategoricalDtype(categories=AGE_GROUP_CATEGORIES, ordered=True)
        )
    cut_s = pd.cut(df["age"], bins=AGE_GROUP_BINS, labels=AGE_GROUP_LABELS, right=True)
    return cut_s.cat.add_categories(["Unknown"]).fillna("Unknown").astype(
        pd.CategoricalDtype(categories=AGE_GROUP_CATEGORIES, ordered=True)
    )


def _usd_formatter() -> mticker.FuncFormatter:
    """Format numeric axis ticks as USD currency ($1,000)."""
    return mticker.FuncFormatter(lambda x, _pos: f"${x:,.0f}")


# =============================================================================
# E4 UNIVARIATE CHARTS (4 FIGURES)
# =============================================================================


def plot_e4_age_distribution(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E4 combined Histogram + KDE and horizontal Boxplot of valid customer age."""
    apply_publication_theme()
    valid_age = df["age"].dropna().astype("float64")
    n_total = len(df)
    n_valid = len(valid_age)
    n_missing = n_total - n_valid

    mean_v = float(valid_age.mean())
    std_v = float(valid_age.std(ddof=1))
    med_v = float(valid_age.median())
    q1_v = float(valid_age.quantile(0.25))
    q3_v = float(valid_age.quantile(0.75))
    iqr_v = q3_v - q1_v
    fence_low = q1_v - 1.5 * iqr_v
    fence_high = q3_v + 1.5 * iqr_v
    skew_v = float(valid_age.skew())
    kurt_v = float(valid_age.kurt())

    fig, (ax_hist, ax_box) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11.5, 7.4),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1.05], "hspace": 0.14},
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.11)

    bins = np.arange(18, 73, 2)
    sns.histplot(
        valid_age,
        bins=bins,
        kde=True,
        ax=ax_hist,
        color=PALETTE_PRIMARY,
        edgecolor="white",
        alpha=0.78,
        line_kws={"linewidth": 2.3, "color": PALETTE_SECONDARY},
    )

    ax_hist.axvspan(
        q1_v,
        q3_v,
        color=PALETTE_TEAL,
        alpha=0.09,
        label=f"IQR Band: {q1_v:.1f}–{q3_v:.1f} yrs (IQR = {iqr_v:.1f})",
    )
    ax_hist.axvline(
        mean_v,
        color=PALETTE_ACCENT,
        linestyle="--",
        linewidth=2.2,
        label=f"Mean: {mean_v:.2f} yrs (SD = {std_v:.2f})",
    )
    ax_hist.axvline(
        med_v,
        color=PALETTE_TEAL,
        linestyle="-.",
        linewidth=2.2,
        label=f"Median: {med_v:.2f} yrs",
    )

    y_max = ax_hist.get_ylim()[1]
    ax_hist.set_ylim(0, y_max * 1.28)
    ax_hist.annotate(
        f"Mean = {mean_v:.2f} yrs",
        xy=(mean_v, y_max * 1.02),
        xytext=(mean_v + 1.8, y_max * 1.08),
        fontsize=9.2,
        fontweight="bold",
        color=PALETTE_ACCENT,
        arrowprops={"arrowstyle": "->", "color": PALETTE_ACCENT, "lw": 1.3},
    )
    ax_hist.annotate(
        f"Median = {med_v:.2f} yrs",
        xy=(med_v, y_max * 1.05),
        xytext=(med_v - 11.2, y_max * 1.15),
        fontsize=9.2,
        fontweight="bold",
        color=PALETTE_TEAL,
        arrowprops={"arrowstyle": "->", "color": PALETTE_TEAL, "lw": 1.3},
    )

    stats_badge = (
        f"Parametric: Mean = {mean_v:.2f} yrs | SD = {std_v:.2f} yrs\n"
        f"Non-Parametric: Q1 = {q1_v:.1f} | Med = {med_v:.1f} | Q3 = {q3_v:.1f} (IQR = {iqr_v:.1f})\n"
        f"Shape: Skewness = {skew_v:.2f} | Excess Kurtosis = {kurt_v:.2f} (Platykurtic)"
    )
    ax_hist.text(
        0.985,
        0.95,
        stats_badge,
        transform=ax_hist.transAxes,
        ha="right",
        va="top",
        fontsize=8.6,
        color="#1F2937",
        bbox={"boxstyle": "round,pad=0.42", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1", "alpha": 0.95},
    )
    ax_hist.set_ylabel("Customer Count (n)")
    ax_hist.set_xlabel("")
    ax_hist.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#CBD5E1")

    sns.boxplot(
        x=valid_age,
        ax=ax_box,
        color=PALETTE_SECONDARY,
        width=0.38,
        boxprops={"alpha": 0.65, "edgecolor": PALETTE_PRIMARY, "linewidth": 1.5},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.6},
        whiskerprops={"color": PALETTE_PRIMARY, "linewidth": 1.5},
        capprops={"color": PALETTE_PRIMARY, "linewidth": 1.5},
    )
    ax_box.axvline(mean_v, color=PALETTE_ACCENT, linestyle="--", linewidth=2.0)
    ax_box.scatter([mean_v], [0], color=PALETTE_ACCENT, marker="D", s=55, zorder=5)
    ax_box.set_ylim(-0.72, 0.62)
    ax_box.set_yticks([])
    ax_box.set_ylabel("Boxplot")
    ax_box.set_xlabel("Customer Age (Years)")
    ax_box.set_xlim(14, 74)

    for x_pos, label_txt, col in [
        (float(valid_age.min()), f"Min: {valid_age.min():.0f}", "#374151"),
        (q1_v, f"Q1: {q1_v:.1f}", PALETTE_PRIMARY),
        (med_v, f"Med: {med_v:.1f}", PALETTE_TEAL),
        (q3_v, f"Q3: {q3_v:.1f}", PALETTE_PRIMARY),
        (float(valid_age.max()), f"Max: {valid_age.max():.0f}", "#374151"),
    ]:
        ax_box.text(x_pos, -0.32, label_txt, ha="center", va="top", fontsize=8.5, fontweight="bold", color=col)

    ax_box.text(
        0.5,
        0.86,
        f"Tukey IQR Fences: [{fence_low:.1f}, {fence_high:.1f}] yrs (Q1 - 1.5×IQR = {fence_low:.1f}; "
        f"Q3 + 1.5×IQR = {fence_high:.1f}) → 0 Outliers",
        transform=ax_box.transAxes,
        ha="center",
        va="center",
        fontsize=8.7,
        fontweight="bold",
        color="#1E293B",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#FEF3C7", "edgecolor": "#F59E0B", "alpha": 0.92},
    )

    _add_publication_chrome(
        fig,
        title="Customer Age Distribution Is Symmetric and Platykurtic Around 43.70 Years Across Valid Records",
        subtitle=(
            f"Scope: Valid age observations (n = {n_valid:,} [{n_valid / n_total * 100:.2f}%]; "
            f"{n_missing:,} blanks and -5/200 sentinels excluded) | Range: 18.0–70.0 Years"
        ),
    )

    if save:
        save_publication_figure(fig, "e4", "univariate_age_distribution")
    return fig


def plot_e4_purchase_distribution(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E4 combined Histogram + KDE and horizontal Boxplot of valid purchase_amount."""
    apply_publication_theme()
    valid_spend = df["purchase_amount"].dropna().astype("float64")
    n_total = len(df)
    n_valid = len(valid_spend)
    n_missing = n_total - n_valid

    mean_v = float(valid_spend.mean())
    std_v = float(valid_spend.std(ddof=1))
    med_v = float(valid_spend.median())
    q1_v = float(valid_spend.quantile(0.25))
    q3_v = float(valid_spend.quantile(0.75))
    iqr_v = q3_v - q1_v
    fence_low = q1_v - 1.5 * iqr_v
    fence_high = q3_v + 1.5 * iqr_v
    total_spend = float(valid_spend.sum())
    skew_v = float(valid_spend.skew())
    kurt_v = float(valid_spend.kurt())

    fig, (ax_hist, ax_box) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(11.5, 7.4),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1.05], "hspace": 0.14},
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.11)

    bins = np.linspace(0, 5000, 26)
    sns.histplot(
        valid_spend,
        bins=bins,
        kde=True,
        ax=ax_hist,
        color=PALETTE_SECONDARY,
        edgecolor="white",
        alpha=0.78,
        line_kws={"linewidth": 2.3, "color": PALETTE_PRIMARY},
    )

    ax_hist.axvspan(
        q1_v,
        q3_v,
        color=PALETTE_TEAL,
        alpha=0.09,
        label=f"IQR Band: ${q1_v:,.2f}–${q3_v:,.2f} (IQR = ${iqr_v:,.2f})",
    )
    ax_hist.axvline(
        mean_v,
        color=PALETTE_ACCENT,
        linestyle="--",
        linewidth=2.2,
        label=f"Mean: ${mean_v:,.2f} (SD = ${std_v:,.2f})",
    )
    ax_hist.axvline(
        med_v,
        color=PALETTE_TEAL,
        linestyle="-.",
        linewidth=2.2,
        label=f"Median: ${med_v:,.2f}",
    )

    y_max = ax_hist.get_ylim()[1]
    ax_hist.set_ylim(0, y_max * 1.28)
    ax_hist.annotate(
        f"Mean = ${mean_v:,.2f}",
        xy=(mean_v, y_max * 1.02),
        xytext=(mean_v - 720, y_max * 1.06),
        fontsize=9.2,
        fontweight="bold",
        color=PALETTE_ACCENT,
        arrowprops={"arrowstyle": "->", "color": PALETTE_ACCENT, "lw": 1.3},
    )
    ax_hist.annotate(
        f"Median = ${med_v:,.2f}",
        xy=(med_v, y_max * 1.05),
        xytext=(med_v + 240, y_max * 1.15),
        fontsize=9.2,
        fontweight="bold",
        color=PALETTE_TEAL,
        arrowprops={"arrowstyle": "->", "color": PALETTE_TEAL, "lw": 1.3},
    )

    stats_badge = (
        f"Total Verified Spend: ${total_spend:,.2f}\n"
        f"Q1 = ${q1_v:,.2f} | Q3 = ${q3_v:,.2f} | IQR = ${iqr_v:,.2f}\n"
        f"Skewness = {skew_v:.2f} | Excess Kurtosis = {kurt_v:.2f}"
    )
    ax_hist.text(
        0.985,
        0.95,
        stats_badge,
        transform=ax_hist.transAxes,
        ha="right",
        va="top",
        fontsize=8.6,
        color="#1F2937",
        bbox={"boxstyle": "round,pad=0.42", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1", "alpha": 0.95},
    )
    ax_hist.set_ylabel("Customer Count (n)")
    ax_hist.set_xlabel("")
    ax_hist.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#CBD5E1")

    sns.boxplot(
        x=valid_spend,
        ax=ax_box,
        color=PALETTE_PRIMARY,
        width=0.38,
        boxprops={"alpha": 0.62, "edgecolor": PALETTE_PRIMARY, "linewidth": 1.5},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.6},
        whiskerprops={"color": PALETTE_PRIMARY, "linewidth": 1.5},
        capprops={"color": PALETTE_PRIMARY, "linewidth": 1.5},
    )
    ax_box.axvline(mean_v, color=PALETTE_ACCENT, linestyle="--", linewidth=2.0)
    ax_box.scatter([mean_v], [0], color=PALETTE_ACCENT, marker="D", s=55, zorder=5)
    ax_box.set_ylim(-0.72, 0.62)
    ax_box.set_yticks([])
    ax_box.set_ylabel("Boxplot")
    ax_box.set_xlabel("Purchase Amount (USD $)")
    ax_box.set_xlim(-220, 5280)
    ax_box.xaxis.set_major_formatter(_usd_formatter())

    for x_pos, label_txt, col in [
        (float(valid_spend.min()), f"Min: ${valid_spend.min():,.0f}", "#374151"),
        (q1_v, f"Q1: ${q1_v:,.0f}", PALETTE_PRIMARY),
        (med_v, f"Med: ${med_v:,.0f}", PALETTE_TEAL),
        (q3_v, f"Q3: ${q3_v:,.0f}", PALETTE_PRIMARY),
        (float(valid_spend.max()), f"Max: ${valid_spend.max():,.0f}", "#374151"),
    ]:
        ax_box.text(x_pos, -0.32, label_txt, ha="center", va="top", fontsize=8.5, fontweight="bold", color=col)

    ax_box.text(
        0.5,
        0.86,
        f"Tukey IQR Fences: [-${abs(fence_low):,.2f}, ${fence_high:,.2f}] → 0 Outliers Across $10.31–$4,998.67",
        transform=ax_box.transAxes,
        ha="center",
        va="center",
        fontsize=8.7,
        fontweight="bold",
        color="#1E293B",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#FEF3C7", "edgecolor": "#F59E0B", "alpha": 0.92},
    )

    _add_publication_chrome(
        fig,
        title="Valid Purchase Amount Spans $10–$4,999 Symmetrically Around $2,450.62 Mean ($2,460.36 Median)",
        subtitle=(
            f"Scope: Valid purchase_amount records (n = {n_valid:,} [{n_valid / n_total * 100:.2f}%]; "
            f"{n_missing:,} blanks and -999/'N/A' sentinels excluded) | Total Spend = ${total_spend:,.2f}"
        ),
    )

    if save:
        save_publication_figure(fig, "e4", "univariate_purchase_distribution")
    return fig


def plot_e4_demographics_counts(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E4 3-panel ordered horizontal bar chart of gender, city, and country counts."""
    apply_publication_theme()
    n_total = len(df)

    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15.5, 6.5))
    fig.subplots_adjust(left=0.06, right=0.98, top=0.76, bottom=0.13, wspace=0.34)

    panel_specs: list[tuple[plt.Axes, str, str, str]] = [
        (axes[0], "gender", "(a) Gender Balance (75.5% Known)", "Customer Gender"),
        (axes[1], "city", "(b) 8 Indian Cities + Unknown (88.7% Known)", "Metropolitan City"),
        (axes[2], "country", "(c) Country Assignment (83.0% Known)", "Assigned Country"),
    ]

    for ax, col_name, panel_title, y_label in panel_specs:
        raw_counts = df[col_name].astype(str).value_counts(dropna=False)
        ordered = raw_counts.sort_values(ascending=False)
        labels = [str(k) for k in ordered.index]
        values = [int(v) for v in ordered.to_numpy()]

        colors = []
        for lbl in labels:
            if lbl == "Unknown":
                colors.append(PALETTE_MUTED)
            elif col_name == "country" and lbl == "India":
                colors.append(PALETTE_TEAL)
            elif col_name == "gender" and lbl == "Female":
                colors.append(PALETTE_SECONDARY)
            else:
                colors.append(PALETTE_PRIMARY)

        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=colors, edgecolor="white", height=0.64, alpha=0.92)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontweight="bold")
        ax.set_ylim(len(labels) - 0.15, -0.6)
        ax.set_title(panel_title, pad=10, loc="left")
        ax.set_xlabel("Customer Count (n)")
        ax.set_ylabel(y_label)

        max_v = max(values)
        ax.set_xlim(0, max_v * 1.46)
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

        known_vals = [v for lbl, v in zip(labels, values) if lbl != "Unknown"]
        if known_vals:
            mean_known = float(np.mean(known_vals))
            ax.axvline(mean_known, color=PALETTE_ACCENT, linestyle="--", linewidth=1.4, alpha=0.85)
            ax.text(
                0.97,
                0.03,
                f"Known avg: {mean_known:,.0f}",
                transform=ax.transAxes,
                color=PALETTE_ACCENT,
                fontsize=8.3,
                fontweight="bold",
                ha="right",
                va="bottom",
                bbox={"boxstyle": "round,pad=0.22", "facecolor": "#FFF7ED", "edgecolor": PALETTE_ACCENT, "alpha": 0.92},
            )

        for bar, val in zip(bars, values):
            pct = val / n_total * 100.0
            ax.text(
                val + max_v * 0.025,
                bar.get_y() + bar.get_height() / 2.0,
                f"{val:,} ({pct:.1f}%)",
                va="center",
                ha="left",
                fontsize=8.8,
                fontweight="bold",
                color="#1F2937",
            )

    legend_handles = [
        mpatches.Patch(color=PALETTE_PRIMARY, label="Known Demographic / Non-Indian Country"),
        mpatches.Patch(color=PALETTE_SECONDARY, label="Female Segment"),
        mpatches.Patch(color=PALETTE_TEAL, label="India (Matches Indian Cities)"),
        mpatches.Patch(color=PALETTE_MUTED, label="'Unknown' (Missing Remediated)"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.90),
        ncol=2,
        frameon=True,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=8.7,
    )

    _add_publication_chrome(
        fig,
        title="Known Demographics Split Uniformly Across Gender, 8 Indian Cities, and 5 Countries",
        subtitle=(
            f"Scope: All customer accounts (N = {n_total:,}) | Known records: Gender n = 7,545 "
            "(50.4% Male / 49.6% Female), City n = 8,870 (~12.5% each), Country n = 8,296 (~20.0% each)"
        ),
    )

    if save:
        save_publication_figure(fig, "e4", "univariate_demographics_counts")
    return fig


def plot_e4_feedback_and_reachability(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E4 2-panel discrete feedback_score anomaly and omnichannel reachability tiers."""
    apply_publication_theme()
    n_total = len(df)

    fb_mapped = pd.Series("Missing", index=df.index, dtype="object")
    valid_fb_mask = df["feedback_score"].notna()
    fb_mapped.loc[valid_fb_mask] = df.loc[valid_fb_mask, "feedback_score"].astype(int).astype(str)
    fb_order = ["1", "2", "3", "4", "5", "10", "Missing"]
    fb_counts = [int((fb_mapped == k).sum()) for k in fb_order]

    fb_1_5 = df["feedback_score"].where(df["feedback_score"] <= 5.0).dropna()
    n_fb_valid = int(valid_fb_mask.sum())
    n_fb_1_5 = len(fb_1_5)
    n_spike_10 = int((df["feedback_score"] == 10.0).sum())
    mean_1_5 = float(fb_1_5.mean())
    raw_mean = float(df["feedback_score"].dropna().mean())

    email_ok = df["has_valid_email"].astype(bool)
    phone_ok = df["has_valid_phone"].astype(bool)
    reach_labels = np.select(
        [email_ok & phone_ok, email_ok & ~phone_ok, ~email_ok & phone_ok],
        ["Omnichannel (Both)", "Email Only", "Phone Only"],
        default="Unreachable (None)",
    )
    reach_series = pd.Series(reach_labels, index=df.index)
    reach_counts = reach_series.value_counts().sort_values(ascending=False)
    r_names = [str(k) for k in reach_counts.index]
    r_vals = [int(v) for v in reach_counts.to_numpy()]
    n_reachable = int((email_ok | phone_ok).sum())

    fig, (ax_fb, ax_reach) = plt.subplots(nrows=1, ncols=2, figsize=(15.0, 6.4))
    fig.subplots_adjust(left=0.06, right=0.98, top=0.82, bottom=0.13, wspace=0.32)

    fb_colors = [
        PALETTE_PRIMARY,
        PALETTE_PRIMARY,
        PALETTE_SECONDARY,
        PALETTE_TEAL,
        PALETTE_TEAL,
        PALETTE_ACCENT,
        PALETTE_MUTED,
    ]
    x_pos = np.arange(len(fb_order))
    bars_fb = ax_fb.bar(x_pos, fb_counts, color=fb_colors, edgecolor="white", width=0.64, alpha=0.92)
    ax_fb.set_xticks(x_pos)
    ax_fb.set_xticklabels(
        ["1\n(Detr.)", "2\n(Detr.)", "3\n(Pass.)", "4\n(Prom.)", "5\n(Prom.)", "10\n(Spike)", "Missing\n(Blank/-1)"]
    )
    ax_fb.set_ylabel("Customer Count (n)")
    ax_fb.set_xlabel("Discrete Feedback Score Category")
    ax_fb.set_title("(a) Feedback Score: Likert 1–5 vs. Scale-10 Spike", loc="left", pad=10)
    ax_fb.set_ylim(0, max(fb_counts) * 1.24)
    ax_fb.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    for bar, cnt in zip(bars_fb, fb_counts):
        pct = cnt / n_total * 100.0
        ax_fb.text(
            bar.get_x() + bar.get_width() / 2.0,
            cnt + max(fb_counts) * 0.018,
            f"{cnt:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8.4,
            fontweight="bold",
            color="#1F2937",
        )

    fb_callout = (
        f"Likert 1–5 (n = {n_fb_1_5:,}): Mean = {mean_1_5:.2f}, Median = 3.00\n"
        f"Score-10 Spike (n = {n_spike_10:,} | {n_spike_10 / n_fb_valid * 100:.2f}% of valid)\n"
        f"→ Inflates unadjusted mean to {raw_mean:.2f}"
    )
    ax_fb.text(
        0.03,
        0.95,
        fb_callout,
        transform=ax_fb.transAxes,
        ha="left",
        va="top",
        fontsize=8.7,
        color="#1F2937",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#FFF7ED", "edgecolor": PALETTE_ACCENT, "alpha": 0.95},
    )

    reach_color_map = {
        "Unreachable (None)": PALETTE_MUTED,
        "Email Only": PALETTE_SECONDARY,
        "Phone Only": PALETTE_PRIMARY,
        "Omnichannel (Both)": PALETTE_TEAL,
    }
    r_colors = [reach_color_map[name] for name in r_names]
    y_pos = np.arange(len(r_names))
    bars_r = ax_reach.barh(y_pos, r_vals, color=r_colors, edgecolor="white", height=0.58, alpha=0.92)
    ax_reach.set_yticks(y_pos)
    ax_reach.set_yticklabels(r_names, fontweight="bold")
    ax_reach.invert_yaxis()
    ax_reach.set_xlabel("Customer Count (n)")
    ax_reach.set_ylabel("Contact Reachability Tier")
    ax_reach.set_title("(b) Omnichannel Marketing Reachability", loc="left", pad=10)
    ax_reach.set_xlim(0, max(r_vals) * 1.36)
    ax_reach.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))

    for bar, cnt in zip(bars_r, r_vals):
        pct = cnt / n_total * 100.0
        ax_reach.text(
            cnt + max(r_vals) * 0.02,
            bar.get_y() + bar.get_height() / 2.0,
            f"{cnt:,} ({pct:.1f}%)",
            va="center",
            ha="left",
            fontsize=9.2,
            fontweight="bold",
            color="#1F2937",
        )

    reach_callout = (
        f"Reachable (>=1 Channel): {n_reachable:,} ({n_reachable / n_total * 100:.2f}%)\n"
        f"  • Email Valid: {int(email_ok.sum()):,} ({email_ok.mean() * 100:.2f}%)\n"
        f"  • Phone Valid: {int(phone_ok.sum()):,} ({phone_ok.mean() * 100:.2f}%)\n"
        f"  • Both Channels: {int((email_ok & phone_ok).sum()):,} ({(email_ok & phone_ok).mean() * 100:.2f}%)"
    )
    ax_reach.text(
        0.97,
        0.06,
        reach_callout,
        transform=ax_reach.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.7,
        color="#1F2937",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#F0FDF4", "edgecolor": PALETTE_TEAL, "alpha": 0.95},
    )

    _add_publication_chrome(
        fig,
        title="Anomalous Score-10 Spike (49.93% of Valid Ratings) Skews Feedback While 56.12% Are Unreachable",
        subtitle=(
            f"Scope: All customer accounts (N = {n_total:,}) | Valid feedback n = {n_fb_valid:,} "
            f"(4,951 missing/-1 excluded); Valid email/phone regex-verified"
        ),
    )

    if save:
        save_publication_figure(fig, "e4", "univariate_feedback_reachability")
    return fig


# =============================================================================
# E5 BIVARIATE CHARTS (4 FIGURES)
# =============================================================================


def plot_e5_spend_by_demographics(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E5 2-panel Violin + Boxplot overlay of purchase_amount across gender and country."""
    apply_publication_theme()
    sub = df[df["purchase_amount"].notna()].copy()
    sub["purchase_amount"] = sub["purchase_amount"].astype("float64")
    sub["gender_str"] = sub["gender"].astype(str)
    sub["country_str"] = sub["country"].astype(str)
    n_spend = len(sub)
    overall_med = float(sub["purchase_amount"].median())

    fig, (ax_gen, ax_cnt) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(15.5, 6.8),
        sharey=True,
        gridspec_kw={"width_ratios": [1, 1.55], "wspace": 0.14},
    )
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.14)

    # Panel (a): Gender
    gen_order = GENDER_CATEGORIES
    gen_colors = [PALETTE_PRIMARY, PALETTE_SECONDARY, PALETTE_MUTED]
    sns.violinplot(
        data=sub,
        x="gender_str",
        y="purchase_amount",
        order=gen_order,
        hue="gender_str",
        hue_order=gen_order,
        palette=gen_colors,
        legend=False,
        inner=None,
        cut=0,
        alpha=0.35,
        ax=ax_gen,
    )
    sns.boxplot(
        data=sub,
        x="gender_str",
        y="purchase_amount",
        order=gen_order,
        width=0.24,
        boxprops={"facecolor": "white", "edgecolor": "#1F2937", "linewidth": 1.4, "zorder": 3},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.4, "zorder": 4},
        whiskerprops={"color": "#1F2937", "linewidth": 1.3},
        capprops={"color": "#1F2937", "linewidth": 1.3},
        showfliers=False,
        ax=ax_gen,
    )
    ax_gen.axhline(overall_med, color=PALETTE_TEAL, linestyle="--", linewidth=1.4, alpha=0.8)

    gen_xticks = []
    for idx, g_lbl in enumerate(gen_order):
        vals = sub.loc[sub["gender_str"] == g_lbl, "purchase_amount"]
        med_g = float(vals.median())
        mean_g = float(vals.mean())
        ax_gen.scatter([idx], [mean_g], color=PALETTE_ACCENT, marker="D", s=52, zorder=5)
        ax_gen.text(
            idx,
            5160,
            f"Med: ${med_g:,.0f}\nMean: ${mean_g:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8.3,
            fontweight="bold",
            color="#1F2937",
        )
        gen_xticks.append(f"{g_lbl}\n(n={len(vals):,})")

    gen_groups_all = [sub.loc[sub["gender_str"] == g, "purchase_amount"].to_numpy() for g in gen_order]
    gen_groups_known = gen_groups_all[:2]
    f_all_g, p_all_g = stats.f_oneway(*gen_groups_all)
    f_kn_g, p_kn_g = stats.f_oneway(*gen_groups_known)
    h_kn_g, pk_kn_g = stats.kruskal(*gen_groups_known)

    ax_gen.set_xticks(range(len(gen_order)))
    ax_gen.set_xticklabels(gen_xticks, fontweight="bold")
    ax_gen.set_xlabel("Customer Gender (Valid Spend Sample Size n_k)")
    ax_gen.set_ylabel("Purchase Amount (USD $)")
    ax_gen.yaxis.set_major_formatter(_usd_formatter())
    ax_gen.set_ylim(-150, 6450)
    ax_gen.set_title("(a) Spend Distribution by Gender", loc="left", pad=10)
    ax_gen.text(
        0.5,
        0.965,
        f"Known ANOVA F = {f_kn_g:.2f} (p = {p_kn_g:.2f}) | Kruskal H = {h_kn_g:.2f} (p = {pk_kn_g:.2f})\n"
        f"All Segments (incl. Unknown): F = {f_all_g:.2f} (p = {p_all_g:.2f}) — Not Significant",
        transform=ax_gen.transAxes,
        ha="center",
        va="top",
        fontsize=8.3,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1"},
    )

    # Panel (b): Country (known sorted descending by median spend + Unknown last)
    known_countries = [c for c in COUNTRY_CATEGORIES if c != "Unknown"]
    known_countries = sorted(
        known_countries,
        key=lambda c: float(sub.loc[sub["country_str"] == c, "purchase_amount"].median()),
        reverse=True,
    )
    cnt_order = [*known_countries, "Unknown"]
    cnt_colors = [
        PALETTE_TEAL if c == "India" else (PALETTE_MUTED if c == "Unknown" else PALETTE_SECONDARY)
        for c in cnt_order
    ]

    sns.violinplot(
        data=sub,
        x="country_str",
        y="purchase_amount",
        order=cnt_order,
        hue="country_str",
        hue_order=cnt_order,
        palette=cnt_colors,
        legend=False,
        inner=None,
        cut=0,
        alpha=0.35,
        ax=ax_cnt,
    )
    sns.boxplot(
        data=sub,
        x="country_str",
        y="purchase_amount",
        order=cnt_order,
        width=0.26,
        boxprops={"facecolor": "white", "edgecolor": "#1F2937", "linewidth": 1.4, "zorder": 3},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.4, "zorder": 4},
        whiskerprops={"color": "#1F2937", "linewidth": 1.3},
        capprops={"color": "#1F2937", "linewidth": 1.3},
        showfliers=False,
        ax=ax_cnt,
    )
    ax_cnt.axhline(overall_med, color=PALETTE_TEAL, linestyle="--", linewidth=1.4, alpha=0.8)

    cnt_xticks = []
    for idx, c_lbl in enumerate(cnt_order):
        vals = sub.loc[sub["country_str"] == c_lbl, "purchase_amount"]
        med_c = float(vals.median())
        mean_c = float(vals.mean())
        ax_cnt.scatter([idx], [mean_c], color=PALETTE_ACCENT, marker="D", s=48, zorder=5)
        ax_cnt.text(
            idx,
            5160,
            f"Med: ${med_c:,.0f}\nMean: ${mean_c:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8.0,
            fontweight="bold",
            color="#1F2937",
        )
        cnt_xticks.append(f"{c_lbl}\n(n={len(vals):,})")

    cnt_groups_all = [sub.loc[sub["country_str"] == c, "purchase_amount"].to_numpy() for c in cnt_order]
    cnt_groups_known = cnt_groups_all[:-1]
    f_all_c, p_all_c = stats.f_oneway(*cnt_groups_all)
    f_kn_c, p_kn_c = stats.f_oneway(*cnt_groups_known)
    h_kn_c, pk_kn_c = stats.kruskal(*cnt_groups_known)

    ax_cnt.set_xticks(range(len(cnt_order)))
    ax_cnt.set_xticklabels(cnt_xticks, fontweight="bold")
    ax_cnt.set_xlabel("Assigned Country (Ordered by Median Spend; Unknown Separated)")
    ax_cnt.set_ylabel("")
    ax_cnt.set_title("(b) Spend Distribution by Country", loc="left", pad=10)
    ax_cnt.text(
        0.5,
        0.965,
        f"Known ANOVA F = {f_kn_c:.2f} (p = {p_kn_c:.2f}) | Kruskal H = {h_kn_c:.2f} (p = {pk_kn_c:.2f})\n"
        f"All Segments (incl. Unknown): F = {f_all_c:.2f} (p = {p_all_c:.2f}) — Not Significant",
        transform=ax_cnt.transAxes,
        ha="center",
        va="top",
        fontsize=8.3,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1"},
    )

    legend_items = [
        mlines.Line2D([0], [0], marker="D", color="w", markerfacecolor=PALETTE_ACCENT, markersize=7, label="Segment Mean ($)"),
        mlines.Line2D([0], [0], color=PALETTE_TEAL, linestyle="--", lw=1.6, label=f"Overall Median (${overall_med:,.2f})"),
        mpatches.Patch(color=PALETTE_MUTED, alpha=0.6, label="'Unknown' Category"),
    ]
    fig.legend(
        handles=legend_items,
        loc="upper right",
        bbox_to_anchor=(0.98, 0.92),
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=8.8,
    )

    _add_publication_chrome(
        fig,
        title="Purchase Amount Is Homogeneous Across Gender (p = 0.62) and Country Segments (p = 0.64)",
        subtitle=(
            f"Scope: Valid purchase_amount records (n = {n_spend:,}; known gender n = 1,849, known country n = 2,040) "
            "| Violin + IQR Boxplot & Mean Diamonds"
        ),
    )

    if save:
        save_publication_figure(fig, "e5", "bivariate_spend_by_demographics")
    return fig


def plot_e5_spend_by_city_and_age(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E5 2-panel horizontal Boxplot + mean markers across Indian cities and ontology age cohorts."""
    apply_publication_theme()
    sub = df[df["purchase_amount"].notna()].copy()
    sub["purchase_amount"] = sub["purchase_amount"].astype("float64")
    sub["city_str"] = sub["city"].astype(str)
    sub["age_group"] = _derive_age_cohorts(sub).astype(str)
    n_spend = len(sub)
    overall_mean = float(sub["purchase_amount"].mean())
    overall_med = float(sub["purchase_amount"].median())

    fig, (ax_city, ax_age) = plt.subplots(nrows=1, ncols=2, figsize=(15.8, 7.2))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.81, bottom=0.13, wspace=0.38)

    # Panel (a): 8 Indian cities ordered by mean spend descending + Unknown at bottom
    known_cities = [c for c in CITY_CATEGORIES if c != "Unknown"]
    known_cities = sorted(
        known_cities,
        key=lambda c: float(sub.loc[sub["city_str"] == c, "purchase_amount"].mean()),
        reverse=True,
    )
    city_order = [*known_cities, "Unknown"]
    city_colors = [PALETTE_MUTED if c == "Unknown" else PALETTE_PRIMARY for c in city_order]

    sns.boxplot(
        data=sub,
        y="city_str",
        x="purchase_amount",
        order=city_order,
        hue="city_str",
        hue_order=city_order,
        palette=city_colors,
        legend=False,
        width=0.55,
        boxprops={"alpha": 0.72, "edgecolor": "#1F2937", "linewidth": 1.2},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.5},
        whiskerprops={"color": "#1F2937", "linewidth": 1.2},
        capprops={"color": "#1F2937", "linewidth": 1.2},
        ax=ax_city,
    )
    ax_city.axvline(overall_med, color=PALETTE_TEAL, linestyle="--", linewidth=1.5, alpha=0.85)

    city_ylabels = []
    for idx, c_lbl in enumerate(city_order):
        vals = sub.loc[sub["city_str"] == c_lbl, "purchase_amount"]
        mean_c = float(vals.mean())
        med_c = float(vals.median())
        ax_city.scatter(
            [mean_c], [idx], color=PALETTE_ACCENT, marker="D", s=48, zorder=5, edgecolors="white", linewidths=0.6
        )
        ax_city.text(
            5120,
            idx,
            f"Mean ${mean_c:,.0f} | Med ${med_c:,.0f}",
            va="center",
            ha="left",
            fontsize=8.2,
            fontweight="bold",
            color="#1F2937",
        )
        city_ylabels.append(f"{c_lbl} (n={len(vals)})")

    city_groups_kn = [sub.loc[sub["city_str"] == c, "purchase_amount"].to_numpy() for c in known_cities]
    f_city, p_city = stats.f_oneway(*city_groups_kn)
    h_city, pk_city = stats.kruskal(*city_groups_kn)

    ax_city.set_yticks(range(len(city_order)))
    ax_city.set_yticklabels(city_ylabels, fontweight="bold")
    ax_city.set_ylim(len(city_order) + 0.45, -0.65)
    ax_city.set_xlim(-100, 7100)
    ax_city.xaxis.set_major_formatter(_usd_formatter())
    ax_city.set_xlabel("Purchase Amount (USD $)")
    ax_city.set_ylabel("Metropolitan City")
    ax_city.set_title(f"(a) Spend Across 8 Indian Cities + Unknown (F = {f_city:.2f}, p = {p_city:.2f})", loc="left", pad=10)
    ax_city.text(
        0.985,
        0.02,
        f"Known Cities (n = 2,175): ANOVA F = {f_city:.2f}, p = {p_city:.2f} | Kruskal H = {h_city:.2f}, p = {pk_city:.2f}",
        transform=ax_city.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.1,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1"},
    )

    # Panel (b): Canonical Ontology Age Cohorts
    age_order = AGE_GROUP_CATEGORIES
    age_colors = [PALETTE_SECONDARY, PALETTE_SECONDARY, PALETTE_PRIMARY, PALETTE_PRIMARY, PALETTE_MUTED]
    sns.boxplot(
        data=sub,
        y="age_group",
        x="purchase_amount",
        order=age_order,
        hue="age_group",
        hue_order=age_order,
        palette=age_colors,
        legend=False,
        width=0.50,
        boxprops={"alpha": 0.72, "edgecolor": "#1F2937", "linewidth": 1.2},
        medianprops={"color": PALETTE_TEAL, "linewidth": 2.5},
        whiskerprops={"color": "#1F2937", "linewidth": 1.2},
        capprops={"color": "#1F2937", "linewidth": 1.2},
        ax=ax_age,
    )
    ax_age.axvline(overall_med, color=PALETTE_TEAL, linestyle="--", linewidth=1.5, alpha=0.85)

    age_ylabels = []
    for idx, a_lbl in enumerate(age_order):
        vals = sub.loc[sub["age_group"] == a_lbl, "purchase_amount"]
        mean_a = float(vals.mean())
        med_a = float(vals.median())
        ax_age.scatter(
            [mean_a], [idx], color=PALETTE_ACCENT, marker="D", s=52, zorder=5, edgecolors="white", linewidths=0.6
        )
        ax_age.text(
            5120,
            idx,
            f"Mean ${mean_a:,.0f} | Med ${med_a:,.0f}",
            va="center",
            ha="left",
            fontsize=8.3,
            fontweight="bold",
            color="#1F2937",
        )
        short_lbl = a_lbl.replace(" (", "\n(") if a_lbl != "Unknown" else "Unknown\n(Missing Age)"
        age_ylabels.append(f"{short_lbl}\n[n={len(vals):,}]")

    age_groups_kn = [sub.loc[sub["age_group"] == a, "purchase_amount"].to_numpy() for a in AGE_GROUP_LABELS]
    f_age, p_age = stats.f_oneway(*age_groups_kn)
    h_age, pk_age = stats.kruskal(*age_groups_kn)

    ax_age.set_yticks(range(len(age_order)))
    ax_age.set_yticklabels(age_ylabels, fontweight="bold", fontsize=8.8)
    ax_age.set_ylim(len(age_order) + 0.35, -0.65)
    ax_age.set_xlim(-100, 7100)
    ax_age.xaxis.set_major_formatter(_usd_formatter())
    ax_age.set_xlabel("Purchase Amount (USD $)")
    ax_age.set_ylabel("Ontology Age Cohort")
    ax_age.set_title(f"(b) Spend Across Ontology Age Cohorts (F = {f_age:.2f}, p = {p_age:.2f})", loc="left", pad=10)
    ax_age.text(
        0.985,
        0.02,
        f"Known Age Cohorts (n = 600): ANOVA F = {f_age:.2f}, p = {p_age:.2f} | Kruskal H = {h_age:.2f}, p = {pk_age:.2f}",
        transform=ax_age.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.1,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1"},
    )

    legend_items = [
        mlines.Line2D(
            [0],
            [0],
            marker="D",
            color="w",
            markerfacecolor=PALETTE_ACCENT,
            markersize=7,
            label=f"Segment Mean (Overall ${overall_mean:,.2f})",
        ),
        mlines.Line2D([0], [0], color=PALETTE_TEAL, linestyle="--", lw=1.8, label=f"Overall Median (${overall_med:,.2f})"),
        mpatches.Patch(color=PALETTE_MUTED, alpha=0.72, label="'Unknown' Cohort"),
    ]
    fig.legend(
        handles=legend_items,
        loc="upper right",
        bbox_to_anchor=(0.98, 0.915),
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=8.8,
    )

    _add_publication_chrome(
        fig,
        title="Segment Order Values Remain Uniform Across All 8 Indian Cities (p = 0.48) and Age Cohorts (p = 0.68)",
        subtitle=(
            f"Scope: Valid purchase_amount records (n = {n_spend:,}; known city n = 2,175, known age cohort n = 600) "
            "| Horizontal Boxplots & Mean Markers"
        ),
    )

    if save:
        save_publication_figure(fig, "e5", "bivariate_spend_by_city_age")
    return fig


def plot_e5_age_vs_spend(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E5 scatter + OLS trend + ontology age-cohort mean/median trajectory for age vs spend."""
    apply_publication_theme()
    sub = df[["age", "purchase_amount"]].dropna().copy()
    sub["age"] = sub["age"].astype("float64")
    sub["purchase_amount"] = sub["purchase_amount"].astype("float64")
    n_pair = len(sub)
    n_excluded = len(df) - n_pair

    r_res = stats.pearsonr(sub["age"], sub["purchase_amount"])
    s_res = stats.spearmanr(sub["age"], sub["purchase_amount"])
    r_val, p_r = float(r_res.statistic), float(r_res.pvalue)
    rho_val, p_rho = float(s_res.statistic), float(s_res.pvalue)

    sub["cohort"] = pd.cut(sub["age"], bins=AGE_GROUP_BINS, labels=AGE_GROUP_LABELS, right=True)
    cohort_stats = (
        sub.groupby("cohort", observed=True)["purchase_amount"]
        .agg(mean="mean", median="median", count="count")
        .reindex(AGE_GROUP_LABELS)
    )
    midpoints = [23.5, 37.0, 52.0, 65.0]

    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.83, bottom=0.12)

    pts_handle = ax.scatter(
        sub["age"],
        sub["purchase_amount"],
        alpha=0.35,
        s=36,
        color=PALETTE_SECONDARY,
        edgecolors="none",
        label=f"Dual-Valid Customers (n = {n_pair:,}, alpha = 0.35)",
    )
    sns.regplot(
        data=sub,
        x="age",
        y="purchase_amount",
        scatter=False,
        ci=95,
        ax=ax,
        color=PALETTE_PRIMARY,
        line_kws={"linewidth": 2.2, "linestyle": "--"},
    )
    ols_handle = mlines.Line2D(
        [0],
        [0],
        color=PALETTE_PRIMARY,
        linewidth=2.2,
        linestyle="--",
        label=f"OLS Linear Trend (r = {r_val:.4f}, p = {p_r:.4f})",
    )

    (mean_line,) = ax.plot(
        midpoints,
        cohort_stats["mean"].to_numpy(),
        color=PALETTE_ACCENT,
        linewidth=2.5,
        marker="D",
        markersize=8,
        zorder=5,
        label="Age-Cohort Mean Spend ($)",
    )
    (med_line,) = ax.plot(
        midpoints,
        cohort_stats["median"].to_numpy(),
        color=PALETTE_TEAL,
        linewidth=2.3,
        linestyle="-.",
        marker="o",
        markersize=7.5,
        zorder=5,
        label="Age-Cohort Median Spend ($)",
    )

    for boundary in (29.5, 44.5, 59.5):
        ax.axvline(boundary, color="#94A3B8", linestyle=":", linewidth=1.2, alpha=0.8)

    for x_mid, lbl, (_, row) in zip(midpoints, ["18–29", "30–44", "45–59", "60+"], cohort_stats.iterrows()):
        ax.text(
            x_mid,
            5220,
            f"Cohort {lbl} (n={int(row['count'])})\nMean ${row['mean']:,.0f} | Med ${row['median']:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8.4,
            fontweight="bold",
            color="#1E293B",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1", "alpha": 0.92},
        )

    corr_box = (
        f"Parametric Pearson r = {r_val:.4f} (p = {p_r:.4f})\n"
        f"Non-Parametric Spearman ρ = {rho_val:.4f} (p = {p_rho:.4f})\n"
        "Finding: Near-zero correlation; age does not predict order value\n"
        "(Note: Observational correlation ≠ causation)"
    )
    ax.text(
        0.02,
        0.03,
        corr_box,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        color="#1F2937",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#FFFBEB", "edgecolor": "#F59E0B", "alpha": 0.95},
    )

    ax.set_xlim(16, 72)
    ax.set_ylim(-380, 6150)
    ax.yaxis.set_major_formatter(_usd_formatter())
    ax.set_xlabel("Customer Age (Years)")
    ax.set_ylabel("Purchase Amount (USD $)")
    ax.legend(
        handles=[pts_handle, ols_handle, mean_line, med_line],
        loc="lower right",
        frameon=True,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=8.5,
    )

    _add_publication_chrome(
        fig,
        title="Customer Age Shows Zero Linear or Monotonic Association With Spend (r = 0.0430, p = 0.2930)",
        subtitle=(
            f"Scope: Dual-valid records with both age and purchase_amount "
            f"(n = {n_pair:,} [{n_pair / len(df) * 100:.2f}%]; {n_excluded:,} partial/missing records excluded)"
        ),
    )

    if save:
        save_publication_figure(fig, "e5", "bivariate_age_vs_spend")
    return fig


def plot_e5_feedback_and_geo_mismatch(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot E5 2-panel diagnostic: (a) spend by feedback & reachability; (b) city x country geo mismatch."""
    apply_publication_theme()
    n_total = len(df)

    fig, (ax_left, ax_right) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(16.0, 7.5),
        gridspec_kw={"width_ratios": [1.05, 1.15], "wspace": 0.34},
    )
    fig.subplots_adjust(left=0.10, right=0.98, top=0.81, bottom=0.15)

    # Panel (a): Purchase amount across Feedback Score (1..5, 10, Missing) + Reachable vs Unreachable
    spend_df = df[df["purchase_amount"].notna()].copy()
    spend_df["purchase_amount"] = spend_df["purchase_amount"].astype("float64")
    overall_med = float(spend_df["purchase_amount"].median())

    fb_map = pd.Series("Score Missing", index=spend_df.index, dtype="object")
    for score_int in (1, 2, 3, 4, 5):
        fb_map.loc[spend_df["feedback_score"] == float(score_int)] = f"Score {score_int}"
    fb_map.loc[spend_df["feedback_score"] == 10.0] = "Score 10 (Spike)"

    reach_ok = spend_df["has_valid_email"].astype(bool) | spend_df["has_valid_phone"].astype(bool)
    reach_map = pd.Series(
        np.where(reach_ok, "Reachable (>=1 Ch.)", "Unreachable (None)"),
        index=spend_df.index,
    )

    combined_rows = pd.concat(
        [
            pd.DataFrame({"group": fb_map, "purchase_amount": spend_df["purchase_amount"]}),
            pd.DataFrame({"group": reach_map, "purchase_amount": spend_df["purchase_amount"]}),
        ],
        ignore_index=True,
    )
    group_order = [
        "Score 1",
        "Score 2",
        "Score 3",
        "Score 4",
        "Score 5",
        "Score 10 (Spike)",
        "Score Missing",
        "Reachable (>=1 Ch.)",
        "Unreachable (None)",
    ]
    group_colors = [
        PALETTE_SECONDARY,
        PALETTE_SECONDARY,
        PALETTE_SECONDARY,
        PALETTE_SECONDARY,
        PALETTE_SECONDARY,
        PALETTE_ACCENT,
        PALETTE_MUTED,
        PALETTE_TEAL,
        PALETTE_MUTED,
    ]

    sns.boxplot(
        data=combined_rows,
        y="group",
        x="purchase_amount",
        order=group_order,
        hue="group",
        hue_order=group_order,
        palette=group_colors,
        legend=False,
        width=0.55,
        boxprops={"alpha": 0.74, "edgecolor": "#1F2937", "linewidth": 1.2},
        medianprops={"color": "#111827", "linewidth": 2.3},
        whiskerprops={"color": "#1F2937", "linewidth": 1.2},
        capprops={"color": "#1F2937", "linewidth": 1.2},
        ax=ax_left,
    )
    ax_left.axvline(overall_med, color=PALETTE_TEAL, linestyle="--", linewidth=1.5, alpha=0.85)
    ax_left.axhline(6.5, color="#64748B", linestyle="-", linewidth=1.4)

    y_tick_labels = []
    for idx, grp_name in enumerate(group_order):
        vals = combined_rows.loc[combined_rows["group"] == grp_name, "purchase_amount"]
        mean_g = float(vals.mean())
        med_g = float(vals.median())
        ax_left.scatter(
            [mean_g], [idx], color=PALETTE_ACCENT, marker="D", s=44, zorder=5, edgecolors="white", linewidths=0.7
        )
        ax_left.text(
            5120,
            idx,
            f"Mean ${mean_g:,.0f} | Med ${med_g:,.0f}",
            va="center",
            ha="left",
            fontsize=8.0,
            fontweight="bold",
            color="#1F2937",
        )
        y_tick_labels.append(f"{grp_name} (n={len(vals):,})")

    fb_known_groups = [
        combined_rows.loc[combined_rows["group"] == g, "purchase_amount"].to_numpy()
        for g in ["Score 1", "Score 2", "Score 3", "Score 4", "Score 5", "Score 10 (Spike)"]
    ]
    f_fb, p_fb = stats.f_oneway(*fb_known_groups)
    reach_groups = [
        combined_rows.loc[combined_rows["group"] == "Reachable (>=1 Ch.)", "purchase_amount"].to_numpy(),
        combined_rows.loc[combined_rows["group"] == "Unreachable (None)", "purchase_amount"].to_numpy(),
    ]
    f_rc, p_rc = stats.f_oneway(*reach_groups)
    unreach_spend_pct = float(reach_groups[1].sum() / spend_df["purchase_amount"].sum() * 100.0)

    ax_left.set_yticks(range(len(group_order)))
    ax_left.set_yticklabels(y_tick_labels, fontweight="bold", fontsize=8.7)
    ax_left.set_ylim(len(group_order) + 0.85, -0.65)
    ax_left.set_xlim(-100, 7150)
    ax_left.xaxis.set_major_formatter(_usd_formatter())
    ax_left.set_xlabel("Purchase Amount (USD $)")
    ax_left.set_ylabel("Feedback Rating & Reachability Segment")
    ax_left.set_title("(a) Spend vs. Feedback (p = 0.84) & Reachability (p = 0.32)", loc="left", pad=10)
    ax_left.text(
        0.985,
        0.018,
        f"Known Feedback ANOVA: F = {f_fb:.2f}, p = {p_fb:.2f} | Reachability: F = {f_rc:.2f}, p = {p_rc:.2f}\n"
        f"Unreachable accounts hold {unreach_spend_pct:.2f}% ($3.39M) of verified spend",
        transform=ax_left.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.0,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#FFF7ED", "edgecolor": PALETTE_ACCENT, "alpha": 0.95},
    )

    # Panel (b): City x Country Stacked Horizontal Percentage Bar Chart
    city_s = df["city"].astype(str)
    country_s = df["country"].astype(str)
    ct_counts = pd.crosstab(city_s, country_s).reindex(index=CITY_CATEGORIES, columns=COUNTRY_CATEGORIES, fill_value=0)
    ct_pct = ct_counts.div(ct_counts.sum(axis=1), axis=0) * 100.0

    dual_known_mask = (city_s != "Unknown") & (country_s != "Unknown")
    n_dual_known = int(dual_known_mask.sum())
    n_geo_mismatch = int(((city_s != "Unknown") & country_s.isin(NON_INDIAN_COUNTRIES)).sum())
    chi2_kn, p_chi2_kn, dof_kn, _ = stats.chi2_contingency(
        pd.crosstab(city_s[dual_known_mask], country_s[dual_known_mask])
    )

    stack_order = ["India", "USA", "Australia", "Canada", "UK", "Unknown"]
    stack_colors = {
        "India": PALETTE_TEAL,
        "USA": PALETTE_PRIMARY,
        "Australia": PALETTE_SECONDARY,
        "Canada": "#7570B3",
        "UK": PALETTE_ACCENT,
        "Unknown": PALETTE_MUTED,
    }

    y_idx = np.arange(len(CITY_CATEGORIES))
    left_cum = np.zeros(len(CITY_CATEGORIES))
    for cnt_name in stack_order:
        widths = ct_pct[cnt_name].to_numpy()
        seg_label = (
            f"{cnt_name} (Valid)"
            if cnt_name == "India"
            else (f"{cnt_name} (Mismatch)" if cnt_name != "Unknown" else "Unknown")
        )
        ax_right.barh(
            y_idx,
            widths,
            left=left_cum,
            height=0.62,
            color=stack_colors[cnt_name],
            edgecolor="white",
            linewidth=0.8,
            label=seg_label,
        )
        for row_i, w_val in enumerate(widths):
            if w_val >= 12.0:
                ax_right.text(
                    left_cum[row_i] + w_val / 2.0,
                    row_i,
                    f"{w_val:.1f}%",
                    ha="center",
                    va="center",
                    fontsize=7.6,
                    fontweight="bold",
                    color="white",
                )
        left_cum += widths

    city_labels_b = []
    for row_i, c_name in enumerate(CITY_CATEGORIES):
        n_c = int(ct_counts.loc[c_name].sum())
        city_labels_b.append(f"{c_name} (n={n_c:,})")
        if c_name != "Unknown":
            mis_n = int(ct_counts.loc[c_name, list(NON_INDIAN_COUNTRIES)].sum())
            mis_pct = mis_n / n_c * 100.0
            ax_right.text(
                101.5,
                row_i,
                f"{mis_n} mis. ({mis_pct:.1f}%)",
                va="center",
                ha="left",
                fontsize=8.0,
                fontweight="bold",
                color=PALETTE_ACCENT,
            )
        else:
            ax_right.text(
                101.5,
                row_i,
                "City Unknown",
                va="center",
                ha="left",
                fontsize=8.0,
                color=PALETTE_MUTED,
            )

    ax_right.set_yticks(y_idx)
    ax_right.set_yticklabels(city_labels_b, fontweight="bold", fontsize=8.8)
    ax_right.set_ylim(len(CITY_CATEGORIES) + 0.85, -0.65)
    ax_right.set_xlim(0, 128)
    ax_right.set_xticks([0, 20, 40, 60, 80, 100])
    ax_right.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax_right.set_xlabel("Share of City Records (%)")
    ax_right.set_ylabel("Customer City (8 Indian Metros + Unknown)")
    ax_right.set_title("(b) City × Country Geographic Contradiction (80.13% Dual-Known)", loc="left", pad=10)

    ax_right.legend(
        loc="upper center",
        bbox_to_anchor=(0.45, -0.12),
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="#CBD5E1",
        fontsize=8.1,
    )
    ax_right.text(
        0.99,
        0.018,
        f"Dual-Known Mismatch: {n_geo_mismatch:,} / {n_dual_known:,} ({n_geo_mismatch / n_dual_known * 100:.2f}%)\n"
        f"χ² = {chi2_kn:.2f} (dof = {dof_kn}, p = {p_chi2_kn:.2f} — Statistically Independent)",
        transform=ax_right.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.0,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#F8FAFC", "edgecolor": "#CBD5E1", "alpha": 0.95},
    )

    _add_publication_chrome(
        fig,
        title="Spend Is Invariant to Feedback & Reachability, While 80.13% of Dual-Known Locations Conflict",
        subtitle=(
            f"Scope: Panel (a) Valid spend n = {len(spend_df):,}; Panel (b) All N = {n_total:,} records "
            f"(5,888 geo mismatches across 7,348 dual-known rows; 6,655 total non-Indian country rows)"
        ),
        caption_y=-0.035,
    )

    if save:
        save_publication_figure(fig, "e5", "bivariate_feedback_and_geo_mismatch")
    return fig


def generate_essential_charts(df: pd.DataFrame | None = None) -> dict[str, Path]:
    """Generate and export all 8 Essential Level (E4 & E5) publication figures at 300 DPI."""
    if df is None:
        df = load_clean_customers("v1")

    builders = [
        ("e4_univariate_age_distribution", plot_e4_age_distribution),
        ("e4_univariate_purchase_distribution", plot_e4_purchase_distribution),
        ("e4_univariate_demographics_counts", plot_e4_demographics_counts),
        ("e4_univariate_feedback_reachability", plot_e4_feedback_and_reachability),
        ("e5_bivariate_spend_by_demographics", plot_e5_spend_by_demographics),
        ("e5_bivariate_spend_by_city_age", plot_e5_spend_by_city_and_age),
        ("e5_bivariate_age_vs_spend", plot_e5_age_vs_spend),
        ("e5_bivariate_feedback_and_geo_mismatch", plot_e5_feedback_and_geo_mismatch),
    ]

    exported: dict[str, Path] = {}
    for key, fn in builders:
        fig = fn(df, save=True)
        plt.close(fig)
        exported[key] = CHARTS_DIR / f"{key}.png"
    return exported


if __name__ == "__main__":
    import matplotlib

    matplotlib.use("Agg")
    generate_essential_charts()
