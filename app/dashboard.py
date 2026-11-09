"""Customer Intelligence executive dashboard (Streamlit, task X2).

Lets a non-technical executive explore the cleaned and enriched customer base
(``data/processed/customers_enriched_v2.csv``) without code: segment filters,
data-quality exclusions, KPI scorecards, one tab per business question
(Q1 demographics & geography, Q2 revenue, Q3 satisfaction & reachability),
a data-quality audit (X4) and a methodology page.

All metrics follow the KPI definitions in ``specs/ontology.md`` §4.

Usage:
    streamlit run app/dashboard.py
"""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH: Path = REPO_ROOT / "data" / "processed" / "customers_enriched_v2.csv"
FALLBACK_DATA_PATH: Path = REPO_ROOT / "data" / "processed" / "customers_clean_v2.csv"
RAW_BASELINE_ROWS: int = 10_000

# --------------------------------------------------------------------------------------
# Visual identity. Single-series marks use the project navy; categorical identities use
# the colorblind-safe Okabe-Ito hues in a fixed order; ordered categories use one
# sequential blue ramp; 'Unknown' / 'Missing' / 'Unreachable' are always muted grey.
# Mean / median reference colors match src/visualization.py.
# --------------------------------------------------------------------------------------
NAVY = "#1B4F72"
INK = "#1F2933"
INK_MUTED = "#5F6B7A"
GRID = "#E4E8EE"
MUTED = "#A3ADB8"
MEAN_COLOR = "#D95F02"
MEDIAN_COLOR = "#1B9E77"
WARNING_COLOR = "#D95F02"

OKABE_BLUE = "#0072B2"
OKABE_ORANGE = "#E69F00"
OKABE_GREEN = "#009E73"
OKABE_VERMILLION = "#D55E00"

SEQUENTIAL_BLUES = ["#C6DBEF", "#6BAED6", "#2171B5", "#08306B"]

AGE_GROUP_ORDER = ["18-29 (Young Adult)", "30-44 (Early Career)", "45-59 (Mid-Senior)", "60+ (Senior)", "Unknown"]
SPEND_TIER_ORDER = ["Low (<$1,200)", "Medium ($1,200-$3,500)", "High (>$3,500)", "Missing"]
REACHABILITY_ORDER = ["Omnichannel (Both)", "Email Only", "Phone Only", "Unreachable (None)"]
FEEDBACK_TIER_ORDER = ["Detractor (1-2)", "Passive (3)", "Promoter (4-5)", "Scale-10 Spike (10)", "Missing"]
GENDER_ORDER = ["Female", "Male", "Unknown"]

AGE_GROUP_COLORS = dict(zip(AGE_GROUP_ORDER, [*SEQUENTIAL_BLUES, MUTED]))
SPEND_TIER_COLORS = dict(zip(SPEND_TIER_ORDER, [SEQUENTIAL_BLUES[0], SEQUENTIAL_BLUES[2], SEQUENTIAL_BLUES[3], MUTED]))
REACHABILITY_COLORS = {
    "Omnichannel (Both)": OKABE_GREEN,
    "Email Only": OKABE_BLUE,
    "Phone Only": OKABE_ORANGE,
    "Unreachable (None)": MUTED,
}
FEEDBACK_SCORE_COLORS = {
    "Detractor (1-2)": OKABE_VERMILLION,
    "Passive (3)": "#BAC2CC",
    "Promoter (4-5)": OKABE_BLUE,
    "Scale-10 Spike (10)": OKABE_ORANGE,
}
GENDER_COLORS = {"Female": OKABE_ORANGE, "Male": OKABE_BLUE, "Unknown": MUTED}

# (short label, flag column, what the flag means)
QUALITY_FLAGS: list[tuple[str, str, str]] = [
    ("City/country mismatch", "is_geo_mismatch", "Indian city paired with USA, UK, Canada or Australia"),
    ("Age missing", "is_age_missing", "Blank, -5 or 200 in the raw Age column"),
    ("Spend missing", "is_purchase_missing", "Blank, -999 or N/A in the raw purchase_amount column"),
    ("Off-scale rating (10)", "is_score_10_spike", "Feedback score of 10 on a 1-5 survey scale"),
    ("Purchase before signup", "is_date_inverted", "Last purchase dated before the signup date"),
]

# Raw attribute -> rule that marks a cleaned value as valid (KPI-1 coverage).
COVERAGE_RULES: list[tuple[str, str, str]] = [
    ("City", "city", "known"),
    ("Name", "name", "known"),
    ("Country", "country", "known"),
    ("Gender", "gender", "known"),
    ("Feedback score", "feedback_score", "notna"),
    ("Signup date", "signup_date", "notna"),
    ("Last purchase date", "last_purchase_date", "notna"),
    ("Email", "email", "notna"),
    ("Phone number", "phone_number", "notna"),
    ("Purchase amount", "purchase_amount", "notna"),
    ("Age", "age", "notna"),
]

BOOLEAN_FLAGS = [
    "has_valid_email",
    "has_valid_phone",
    "is_date_inverted",
    "is_geo_mismatch",
    "is_age_missing",
    "is_purchase_missing",
    "is_score_10_spike",
]

PLOTLY_CONFIG: dict[str, Any] = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


# ======================================================================================
# Data access and pure helpers (unit-tested in tests/test_dashboard.py)
# ======================================================================================
@st.cache_data(show_spinner="Loading customer data...")
def load_dashboard_data(path: Path | str | None = None) -> pd.DataFrame:
    """Load the processed customer dataset with the dtypes the dashboard relies on.

    Parameters
    ----------
    path : Path or str, optional
        Processed CSV to load. Defaults to ``customers_enriched_v2.csv`` and falls back to
        ``customers_clean_v2.csv`` when the enriched file has not been generated yet.

    Returns
    -------
    pd.DataFrame
        Customer table with parsed dates, string phone numbers and boolean quality flags.
    """
    target_path = Path(path) if path is not None else DEFAULT_DATA_PATH
    if not target_path.exists():
        target_path = FALLBACK_DATA_PATH
    if not target_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {target_path}. Run `python -m src.pipeline` first."
        )

    df = pd.read_csv(
        target_path,
        parse_dates=["signup_date", "last_purchase_date"],
        # Phone numbers are identifiers, not quantities: keep them as text.
        dtype={"phone_number": "string", "customer_id": "string"},
        low_memory=False,
    )
    for flag in BOOLEAN_FLAGS:
        if flag in df.columns:
            df[flag] = df[flag].fillna(False).astype(bool)
    return df


def _is_unfiltered(selection: list[str] | None) -> bool:
    """An empty selection or one containing 'All' means 'do not filter this dimension'."""
    return not selection or "All" in selection


def apply_filters(
    df: pd.DataFrame,
    selected_genders: list[str],
    selected_cities: list[str],
    selected_age_groups: list[str],
    selected_spend_tiers: list[str],
    selected_reachability: list[str],
    exclude_inverted_dates: bool,
    exclude_geo_mismatch: bool,
    exclude_score_10_spike: bool,
) -> pd.DataFrame:
    """Return the rows matching the sidebar selections.

    Each categorical selection is ignored when it is empty or contains ``"All"``. The three
    exclusion toggles drop rows carrying the matching data-quality flag.
    """
    mask = pd.Series(True, index=df.index)
    categorical = [
        ("gender", selected_genders),
        ("city", selected_cities),
        ("age_group", selected_age_groups),
        ("spend_tier", selected_spend_tiers),
        ("contact_reachability_tier", selected_reachability),
    ]
    for column, selection in categorical:
        if column in df.columns and not _is_unfiltered(selection):
            mask &= df[column].isin(selection)

    exclusions = [
        ("is_date_inverted", exclude_inverted_dates),
        ("is_geo_mismatch", exclude_geo_mismatch),
        ("is_score_10_spike", exclude_score_10_spike),
    ]
    for flag, active in exclusions:
        if active and flag in df.columns:
            mask &= ~df[flag].astype(bool)

    return df.loc[mask].copy()


def compute_kpi_summary(df: pd.DataFrame, filtered_df: pd.DataFrame) -> dict[str, Any]:
    """Compute the executive KPIs (``specs/ontology.md`` §4) for the filtered selection."""
    n_total = len(df)
    n_filtered = len(filtered_df)

    spend = filtered_df["purchase_amount"].dropna()
    has_spend = not spend.empty
    mean_spend = float(spend.mean()) if has_spend else np.nan
    median_spend = float(spend.median()) if has_spend else np.nan
    total_revenue = float(spend.sum()) if has_spend else 0.0
    iqr_spend = float(spend.quantile(0.75) - spend.quantile(0.25)) if has_spend else np.nan

    # KPI-3: sum(spend) / n_valid_spend x 1,000 == mean order value x 1,000.
    norm_rev_per_1k = mean_spend * 1000.0 if has_spend else np.nan

    # KPI-4: reachable through at least one valid channel.
    if {"has_valid_email", "has_valid_phone"}.issubset(filtered_df.columns):
        email = filtered_df["has_valid_email"].astype(bool)
        phone = filtered_df["has_valid_phone"].astype(bool)
        reachable_mask = email | phone
        reachable_n = int(reachable_mask.sum())
        omnichannel_n = int((email & phone).sum())
        unreachable_revenue = float(filtered_df.loc[~reachable_mask, "purchase_amount"].sum())
    else:
        reachable_n = omnichannel_n = 0
        unreachable_revenue = 0.0
    reachability_rate = reachable_n / n_filtered * 100.0 if n_filtered else 0.0

    # KPI-6: genuine 1-5 ratings only; the off-scale 10 is reported separately.
    feedback_col = "feedback_score_1_to_5" if "feedback_score_1_to_5" in filtered_df.columns else "feedback_score"
    likert = filtered_df[feedback_col].dropna()
    likert = likert[likert <= 5]
    n_spike = int((filtered_df["feedback_score"] == 10).sum()) if "feedback_score" in filtered_df.columns else 0

    avg_completeness = (
        float(filtered_df["completeness_score"].mean() * 100.0)
        if "completeness_score" in filtered_df.columns and n_filtered
        else np.nan
    )

    return {
        "n_total": n_total,
        "n_filtered": n_filtered,
        "n_valid_spend": len(spend),
        "spend_coverage": len(spend) / n_filtered * 100.0 if n_filtered else 0.0,
        "mean_spend": mean_spend,
        "median_spend": median_spend,
        "iqr_spend": iqr_spend,
        "total_revenue": total_revenue,
        "norm_rev_per_1k": norm_rev_per_1k,
        "reachable_n": reachable_n,
        "omnichannel_n": omnichannel_n,
        "unreachable_n": n_filtered - reachable_n,
        "unreachable_revenue": unreachable_revenue,
        "unreachable_revenue_share": unreachable_revenue / total_revenue * 100.0 if total_revenue else 0.0,
        "reachability_rate": reachability_rate,
        "avg_feedback": float(likert.mean()) if not likert.empty else np.nan,
        "n_likert": len(likert),
        "n_spike": n_spike,
        "avg_completeness": avg_completeness,
    }


def compute_group_spend(df: pd.DataFrame, column: str, order: list[str] | None = None) -> pd.DataFrame:
    """Spend profile per category: customers, buyers, mean, median, revenue and KPI-3.

    Categories in ``order`` keep that order; any other observed category follows it.
    """
    grouped = df.groupby(column, observed=True)
    table = pd.DataFrame(
        {
            "customers": grouped.size(),
            "buyers": grouped["purchase_amount"].count(),
            "mean_spend": grouped["purchase_amount"].mean(),
            "median_spend": grouped["purchase_amount"].median(),
            "revenue": grouped["purchase_amount"].sum(),
        }
    )
    table["rev_per_1k"] = table["mean_spend"] * 1000.0
    total_revenue = table["revenue"].sum()
    table["revenue_share"] = table["revenue"] / total_revenue * 100.0 if total_revenue else 0.0
    table["customer_share"] = table["customers"] / table["customers"].sum() * 100.0
    if order is not None:
        ordered = [c for c in order if c in table.index] + [c for c in table.index if c not in order]
        table = table.loc[ordered]
    return table.reset_index().rename(columns={column: "segment"})


def kruskal_pvalue(df: pd.DataFrame, column: str, exclude: tuple[str, ...] = ("Unknown", "Missing")) -> float:
    """Kruskal-Wallis p-value for purchase amount across the groups of ``column``.

    Returns ``nan`` when fewer than two groups have at least two valid purchases.
    """
    if column not in df.columns:
        return float("nan")
    samples = [
        group["purchase_amount"].dropna().to_numpy()
        for name, group in df.groupby(column, observed=True)
        if name not in exclude
    ]
    samples = [s for s in samples if len(s) >= 2]
    if len(samples) < 2:
        return float("nan")
    return float(stats.kruskal(*samples).pvalue)


def build_flag_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Count and rate of every data-quality flag present in ``df``, largest first."""
    rows = [
        {"flag": label, "detail": detail, "records": int(df[column].astype(bool).sum())}
        for label, column, detail in QUALITY_FLAGS
        if column in df.columns
    ]
    summary = pd.DataFrame(rows, columns=["flag", "detail", "records"])
    summary["rate"] = summary["records"] / len(df) * 100.0 if len(df) else 0.0
    return summary.sort_values("records", ascending=True, ignore_index=True)


def build_coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    """KPI-1 valid-attribute coverage for each raw attribute, lowest coverage first."""
    rows = []
    for label, column, rule in COVERAGE_RULES:
        if column not in df.columns:
            continue
        values = df[column]
        valid = values.notna() & (values != "Unknown") if rule == "known" else values.notna()
        rows.append({"attribute": label, "valid": int(valid.sum())})
    table = pd.DataFrame(rows, columns=["attribute", "valid"])
    table["coverage"] = table["valid"] / len(df) * 100.0 if len(df) else 0.0
    return table.sort_values("coverage", ascending=False, ignore_index=True)


def format_money(value: float, compact: bool = False) -> str:
    """Format a USD amount (``$2,460`` or, when ``compact``, ``$6.04M`` / ``$412K``)."""
    if value is None or pd.isna(value):
        return "N/A"
    if compact:
        magnitude = abs(value)
        if magnitude >= 1e6:
            return f"${value / 1e6:,.2f}M"
        if magnitude >= 1e3:
            return f"${value / 1e3:,.0f}K"
    return f"${value:,.0f}"


def format_pvalue(p: float) -> str:
    """Readable p-value for chart subtitles."""
    if pd.isna(p):
        return "p = n/a"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def describe_active_filters(selections: dict[str, list[str]], exclusions: dict[str, bool]) -> list[str]:
    """Human-readable labels for the filters currently narrowing the data."""
    labels = [f"{name}: {', '.join(values)}" for name, values in selections.items() if not _is_unfiltered(values)]
    labels += [f"Excluding {name.lower()}" for name, active in exclusions.items() if active]
    return labels


# ======================================================================================
# Presentation helpers
# ======================================================================================
def style_figure(fig: go.Figure, title: str, subtitle: str = "", height: int = 380) -> go.Figure:
    """Apply the shared executive chart style: headline title, n/scope subtitle, quiet axes."""
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px;color:{INK_MUTED}'>{subtitle}</span>"
    fig.update_layout(
        title={"text": title_text, "x": 0, "xanchor": "left", "y": 0.97, "yanchor": "top", "pad": {"l": 14},
               "font": {"size": 15, "color": INK}},
        height=height,
        margin={"l": 16, "r": 24, "t": 84, "b": 16, "pad": 4},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif", "size": 12, "color": INK},
        hoverlabel={"bgcolor": "#FFFFFF", "bordercolor": GRID, "font": {"color": INK, "size": 12}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "xanchor": "right", "x": 1,
                "font": {"size": 11}, "bgcolor": "rgba(0,0,0,0)"},
        bargap=0.28,
        barcornerradius=4,
    )
    fig.update_xaxes(automargin=True, showgrid=False, linecolor=GRID, ticks="", title_font={"size": 12, "color": INK_MUTED},
                     zeroline=False)
    fig.update_yaxes(automargin=True, gridcolor=GRID, linecolor=GRID, ticks="", title_font={"size": 12, "color": INK_MUTED},
                     zeroline=False)
    # Vertical bars with outside labels need head-room so labels do not collide with the title.
    vertical_bars = [t for t in fig.data if t.type == "bar" and t.orientation != "h" and t.textposition == "outside"]
    if vertical_bars:
        top = max((float(v) for t in vertical_bars for v in t.y), default=0.0)
        if top > 0:
            fig.update_yaxes(range=[0, top * 1.22])
    return fig


def wrap_label(label: str) -> str:
    """Break 'Group (Detail)' axis labels onto two lines so they never need rotating."""
    return label.replace(" (", "<br>(", 1)


def gender_title(counts: pd.Series) -> str:
    """Finding-style title for the gender chart."""
    known = counts.drop("Unknown", errors="ignore")
    if len(known) < 2:
        return "Gender profile of the selection"
    gap = abs(known.iloc[0] - known.iloc[1]) / known.sum() * 100
    return "Women and men are almost equally represented" if gap < 5 else f"{known.idxmax()} customers are the majority"


def city_title(counts: pd.Series) -> str:
    """Finding-style title for the city chart."""
    known = counts.drop("Unknown", errors="ignore")
    if known.empty:
        return "Customers by city"
    top_share = known.max() / counts.sum() * 100
    if top_share < 20:
        return "No single metro dominates the customer base"
    return f"{known.idxmax()} holds {top_share:.0f}% of the selection"


def region_title(counts: pd.Series) -> str:
    """Finding-style title for the metro-region chart."""
    known = counts.drop("Unknown", errors="ignore").sort_values(ascending=False)
    if len(known) < 2:
        return "Customers by metro region"
    share = known.iloc[:2].sum() / counts.sum() * 100
    return f"{known.index[0]} and {known.index[1]} hold {share:.0f}% of customers"


def show_chart(fig: go.Figure) -> None:
    """Render a Plotly figure with the shared toolbar configuration."""
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOTLY_CONFIG)


def section_header(title: str, caption: str) -> None:
    """Tab heading with a one-line description of the question it answers."""
    st.markdown(
        f"<div class='section-head'><h3>{html.escape(title)}</h3><p>{html.escape(caption)}</p></div>",
        unsafe_allow_html=True,
    )


def insight_box(points: list[str], title: str = "Key findings") -> None:
    """Callout listing the dynamic findings of a tab (values already formatted, HTML-safe)."""
    items = "".join(f"<li>{p}</li>" for p in points)
    st.markdown(
        f"<div class='insight'><div class='insight-title'>{html.escape(title)}</div><ul>{items}</ul></div>",
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    """Small muted footnote under a chart."""
    st.markdown(f"<div class='chart-note'>{text}</div>", unsafe_allow_html=True)


def kpi_cards(cards: list[tuple[str, str, str]]) -> None:
    """Render a responsive row of KPI cards: (label, value, footnote)."""
    body = "".join(
        "<div class='kpi'>"
        f"<div class='kpi-label'>{html.escape(label)}</div>"
        f"<div class='kpi-value'>{html.escape(value)}</div>"
        f"<div class='kpi-foot'>{html.escape(foot)}</div>"
        "</div>"
        for label, value, foot in cards
    )
    st.markdown(f"<div class='kpi-grid'>{body}</div>", unsafe_allow_html=True)


def horizontal_bar(
    labels: list[str],
    values: list[float],
    colors: list[str] | str,
    text: list[str],
    hover: list[str],
    x_title: str,
    headroom: float = 1.32,
) -> go.Figure:
    """Horizontal bar chart with direct labels; the first label is drawn at the top."""
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker={"color": colors},
            text=text,
            textposition="outside",
            cliponaxis=False,
            customdata=hover,
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(labels)), showgrid=False)
    # Leave head-room on the right so the outside labels are never clipped.
    top = max((float(v) for v in values if pd.notna(v)), default=0.0)
    fig.update_xaxes(title_text=x_title, showgrid=True, gridcolor=GRID, range=[0, top * headroom if top > 0 else 1])
    return fig


def inject_css() -> None:
    """Global styles for header, KPI cards, callouts and tabs."""
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 2.2rem; padding-bottom: 2rem; max-width: 1440px; }}
        .app-header {{ background: linear-gradient(120deg, {NAVY} 0%, #2E6A97 100%); color: #FFFFFF;
            border-radius: 12px; padding: 22px 28px; margin-bottom: 18px; display: flex;
            justify-content: space-between; align-items: flex-end; gap: 24px; flex-wrap: wrap; }}
        .app-header h1 {{ color: #FFFFFF; font-size: 1.7rem; font-weight: 700; margin: 0; padding: 0; }}
        .app-header p {{ margin: 6px 0 0 0; color: #D6E4F0; font-size: 0.92rem; }}
        .app-meta {{ text-align: right; font-size: 0.8rem; color: #D6E4F0; line-height: 1.5; }}
        .app-meta b {{ color: #FFFFFF; }}
        .chips {{ margin: -4px 0 14px 0; font-size: 0.8rem; color: {INK_MUTED}; }}
        .chip {{ display: inline-block; background: #E3ECF5; color: {NAVY}; border-radius: 999px;
            padding: 2px 10px; margin: 2px 6px 2px 0; font-weight: 600; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 12px; margin-bottom: 18px; }}
        @media (max-width: 1200px) {{ .kpi-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
        @media (max-width: 640px) {{ .kpi-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
        .kpi {{ background: #FFFFFF; border: 1px solid {GRID}; border-top: 3px solid {NAVY};
            border-radius: 10px; padding: 14px 16px; }}
        .kpi-label {{ font-size: 0.74rem; text-transform: uppercase; letter-spacing: .04em;
            color: {INK_MUTED}; font-weight: 600; }}
        .kpi-value {{ font-size: 1.55rem; font-weight: 700; color: {INK}; margin: 4px 0 2px 0;
            font-variant-numeric: tabular-nums; }}
        .kpi-foot {{ font-size: 0.76rem; color: {INK_MUTED}; }}
        .section-head h3 {{ margin: 6px 0 0 0; font-size: 1.25rem; color: {INK}; }}
        .section-head p {{ margin: 2px 0 12px 0; color: {INK_MUTED}; font-size: 0.9rem; }}
        .insight {{ background: #FFFFFF; border: 1px solid {GRID}; border-left: 4px solid {MEDIAN_COLOR};
            border-radius: 8px; padding: 12px 18px; margin: 4px 0 16px 0; }}
        .insight-title {{ font-weight: 700; color: {INK}; font-size: 0.9rem; margin-bottom: 4px; }}
        .insight ul {{ margin: 0; padding-left: 18px; }}
        .insight li {{ font-size: 0.9rem; color: {INK}; margin: 3px 0; }}
        .chart-note {{ font-size: 0.78rem; color: {INK_MUTED}; margin: -6px 0 14px 4px; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {GRID}; }}
        .stTabs [data-baseweb="tab"] {{ height: 44px; padding: 0 16px; border-radius: 8px 8px 0 0;
            font-weight: 600; }}
        .stTabs [aria-selected="true"] {{ background: #FFFFFF; color: {NAVY}; }}
        [data-testid="stPlotlyChart"] {{ background: #FFFFFF; border: 1px solid {GRID};
            border-radius: 10px; overflow: hidden; }}
        .footer {{ text-align: center; color: {INK_MUTED}; font-size: 0.78rem; margin-top: 18px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ======================================================================================
# Tabs
# ======================================================================================
def render_overview_tab(filtered_df: pd.DataFrame, kpis: dict[str, Any]) -> None:
    """Overview: headline findings, spend distribution and reachability."""
    section_header(
        "Executive overview",
        "The three numbers leadership needs first: how much verified revenue, whom we can reach, how satisfied they are.",
    )
    points = [
        (f"<b>{format_money(kpis['total_revenue'], compact=True)}</b> of verified revenue comes from "
        f"<b>{kpis['n_valid_spend']:,}</b> orders with a valid amount ({kpis['spend_coverage']:.1f}% of the "
        f"{kpis['n_filtered']:,} customers in scope); the median order is <b>{format_money(kpis['median_spend'])}</b>."),
        (f"<b>{kpis['unreachable_n']:,}</b> customers ({100 - kpis['reachability_rate']:.1f}%) have neither a valid email "
        f"nor a valid phone; they hold <b>{format_money(kpis['unreachable_revenue'], compact=True)}</b> "
        f"({kpis['unreachable_revenue_share']:.1f}%) of verified revenue."),
    ]
    if kpis["n_likert"]:
        points.append(
            f"Genuine 1–5 ratings average <b>{kpis['avg_feedback']:.2f}</b> (n = {kpis['n_likert']:,}); "
            f"{kpis['n_spike']:,} ratings sit on an off-scale <b>10</b> and are excluded from that average."
        )
    insight_box(points)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        spend = filtered_df["purchase_amount"].dropna()
        if spend.empty:
            st.info("No valid purchase amounts in the current selection.")
        else:
            edges = np.arange(0, max(5000.0, float(spend.max())) + 250, 250)
            counts, _ = np.histogram(spend, bins=edges)
            fig = go.Figure(
                go.Histogram(
                    x=spend,
                    xbins={"start": 0, "end": float(edges[-1]), "size": 250},
                    marker={"color": NAVY, "line": {"color": "#FFFFFF", "width": 1}},
                    name="Customers",
                    showlegend=False,
                    hovertemplate="$%{x}<br>%{y:,} customers<extra></extra>",
                )
            )
            y_top = float(counts.max()) * 1.08
            for label, value, color, dash in [
                ("Median", kpis["median_spend"], MEDIAN_COLOR, "dash"),
                ("Mean", kpis["mean_spend"], MEAN_COLOR, "dot"),
            ]:
                fig.add_trace(
                    go.Scatter(
                        x=[value, value], y=[0, y_top], mode="lines",
                        line={"color": color, "width": 2, "dash": dash},
                        name=f"{label} {format_money(value)}",
                        hovertemplate=f"{label}: {format_money(value)}<extra></extra>",
                    )
                )
            style_figure(
                fig,
                f"Order values range from {format_money(spend.min())} to {format_money(spend.max())}",
                f"n = {len(spend):,} valid orders · bins of $250 · median {format_money(kpis['median_spend'])}",
            )
            fig.update_xaxes(title_text="Purchase amount (USD)", tickprefix="$", tickformat=",")
            fig.update_yaxes(title_text="Customers (n)")
            show_chart(fig)

    with col2:
        if "contact_reachability_tier" in filtered_df.columns:
            counts = filtered_df["contact_reachability_tier"].value_counts()
            revenue = filtered_df.groupby("contact_reachability_tier")["purchase_amount"].sum()
            tiers = [t for t in REACHABILITY_ORDER if t in counts.index]
            n = len(filtered_df)
            fig = horizontal_bar(
                labels=tiers,
                values=[int(counts[t]) for t in tiers],
                colors=[REACHABILITY_COLORS[t] for t in tiers],
                text=[f"{counts[t]:,} · {counts[t] / n * 100:.1f}%" for t in tiers],
                hover=[
                    f"<b>{t}</b><br>{counts[t]:,} customers ({counts[t] / n * 100:.1f}%)"
                    f"<br>Verified revenue: {format_money(revenue.get(t, 0.0), compact=True)}"
                    for t in tiers
                ],
                x_title="Customers (n)",
            )
            style_figure(
                fig,
                f"{100 - kpis['reachability_rate']:.0f}% of customers cannot be contacted",
                f"n = {n:,} customers · valid email and/or 10-digit phone",
            )
            show_chart(fig)


def render_demographics_tab(filtered_df: pd.DataFrame) -> None:
    """Q1: who the customers are and where they live."""
    section_header(
        "Q1 · Demographics & geography",
        "Who our customers are, how old they are and which metropolitan areas they come from.",
    )
    n = len(filtered_df)
    age = filtered_df["age"].dropna() if "age" in filtered_df.columns else pd.Series(dtype=float)
    gender_known = filtered_df[filtered_df["gender"] != "Unknown"]["gender"].value_counts()
    city_known = filtered_df[filtered_df["city"] != "Unknown"]["city"].value_counts()

    points = []
    if not age.empty:
        points.append(
            f"Median age is <b>{age.median():.0f} years</b> (mean {age.mean():.1f}, n = {len(age):,}); "
            f"age is unknown for {n - len(age):,} customers ({(n - len(age)) / n * 100:.1f}%)."
        )
    if len(gender_known) >= 2:
        shares = ", ".join(f"{g} {c / gender_known.sum() * 100:.1f}%" for g, c in gender_known.items())
        points.append(f"Among customers with a recorded gender (n = {gender_known.sum():,}): {shares}.")
    if not city_known.empty:
        points.append(
            f"Customers are spread evenly across {len(city_known)} Indian metros: from "
            f"{city_known.min():,} ({city_known.idxmin()}) to {city_known.max():,} ({city_known.idxmax()})."
        )
    if points:
        insight_box(points)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if "age_group" in filtered_df.columns:
            counts = filtered_df["age_group"].value_counts()
            groups = [g for g in AGE_GROUP_ORDER if g in counts.index and g != "Unknown"]
            if groups:
                known = int(sum(counts[g] for g in groups))
                fig = go.Figure(
                    go.Bar(
                        x=[wrap_label(g) for g in groups],
                        y=[int(counts[g]) for g in groups],
                        marker={"color": [AGE_GROUP_COLORS[g] for g in groups]},
                        text=[f"{counts[g]:,}<br>{counts[g] / known * 100:.1f}%" for g in groups],
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate="<b>%{x}</b><br>%{y:,} customers<extra></extra>",
                    )
                )
                style_figure(
                    fig,
                    f"{max(groups, key=lambda g: counts[g]).split(' (')[0]} is the largest known age cohort",
                    f"n = {known:,} customers with a valid age · {counts.get('Unknown', 0):,} unknown not shown",
                )
                fig.update_yaxes(title_text="Customers (n)", rangemode="tozero")
                show_chart(fig)
    with col2:
        counts = filtered_df["gender"].value_counts()
        genders = [g for g in GENDER_ORDER if g in counts.index]
        fig = go.Figure(
            go.Bar(
                x=genders,
                y=[int(counts[g]) for g in genders],
                marker={"color": [GENDER_COLORS[g] for g in genders]},
                text=[f"{counts[g]:,}<br>{counts[g] / n * 100:.1f}%" for g in genders],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>%{y:,} customers<extra></extra>",
            )
        )
        style_figure(
            fig,
            gender_title(counts),
            f"n = {n:,} customers · six raw spellings standardised to Female / Male / Unknown",
        )
        fig.update_yaxes(title_text="Customers (n)", rangemode="tozero")
        show_chart(fig)

    col3, col4 = st.columns([3, 2], gap="medium")
    with col3:
        counts = filtered_df["city"].value_counts()
        cities = [c for c in counts.index if c != "Unknown"] + (["Unknown"] if "Unknown" in counts.index else [])
        fig = horizontal_bar(
            labels=cities,
            values=[int(counts[c]) for c in cities],
            colors=[MUTED if c == "Unknown" else NAVY for c in cities],
            text=[f"{counts[c]:,} · {counts[c] / n * 100:.1f}%" for c in cities],
            hover=[f"<b>{c}</b><br>{counts[c]:,} customers" for c in cities],
            x_title="Customers (n)",
        )
        style_figure(
            fig,
            city_title(counts),
            f"n = {n:,} customers · all known cities are in India",
            height=420,
        )
        show_chart(fig)
    with col4:
        if "metro_region" in filtered_df.columns:
            counts = filtered_df["metro_region"].value_counts()
            regions = [r for r in counts.index if r != "Unknown"] + (["Unknown"] if "Unknown" in counts.index else [])
            fig = horizontal_bar(
                labels=regions,
                values=[int(counts[r]) for r in regions],
                colors=[MUTED if r == "Unknown" else SEQUENTIAL_BLUES[2] for r in regions],
                text=[f"{counts[r]:,} · {counts[r] / n * 100:.1f}%" for r in regions],
                hover=[f"<b>{r}</b><br>{counts[r]:,} customers" for r in regions],
                x_title="Customers (n)",
            )
            style_figure(
                fig,
                region_title(counts),
                "Region from the external Indian metro catalog (A2)",
                height=420,
            )
            show_chart(fig)
    if "is_geo_mismatch" in filtered_df.columns and filtered_df["is_geo_mismatch"].any():
        mismatch = int(filtered_df["is_geo_mismatch"].sum())
        note(
            f"Country is not analysed: {mismatch:,} records ({mismatch / n * 100:.1f}%) pair an Indian city with "
            "USA, UK, Canada or Australia, so the city is used as the reliable location field."
        )


def render_revenue_tab(filtered_df: pd.DataFrame, kpis: dict[str, Any]) -> None:
    """Q2: how spend is distributed and which segments carry the value."""
    section_header(
        "Q2 · Revenue & high-value segments",
        "How much customers spend, which tiers concentrate value and whether demographics change spend.",
    )
    valid = filtered_df.dropna(subset=["purchase_amount"])
    if valid.empty:
        st.info("No valid purchase amounts in the current selection.")
        return

    p_city = kruskal_pvalue(valid, "city")
    p_age = kruskal_pvalue(valid, "age_group")
    p_gender = kruskal_pvalue(valid, "gender")
    tiers = compute_group_spend(valid, "spend_tier", SPEND_TIER_ORDER) if "spend_tier" in valid.columns else None

    points = [
        (f"Revenue per 1,000 buyers (KPI-3) is <b>{format_money(kpis['norm_rev_per_1k'], compact=True)}</b> "
        f"(mean order {format_money(kpis['mean_spend'])}, interquartile range {format_money(kpis['iqr_spend'])}).")
    ]
    if tiers is not None and "High (>$3,500)" in set(tiers["segment"]):
        high = tiers.set_index("segment").loc["High (>$3,500)"]
        points.append(
            f"<b>{int(high['customers']):,}</b> high-value customers (orders above $3,500, "
            f"{high['customer_share']:.1f}% of buyers) generate <b>{high['revenue_share']:.1f}%</b> of verified revenue."
        )
    points.append(
        "Spend does not differ significantly by city "
        f"({format_pvalue(p_city)}), age group ({format_pvalue(p_age)}) or gender ({format_pvalue(p_gender)}); "
        "Kruskal–Wallis tests, observational data — no causal claim."
    )
    insight_box(points)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if tiers is not None:
            tiers = tiers[tiers["segment"] != "Missing"]
            labels = list(tiers["segment"])
            fig = horizontal_bar(
                labels=labels,
                values=list(tiers["customers"]),
                colors=[SPEND_TIER_COLORS[t] for t in labels],
                text=[
                    f"{int(r.customers):,} · {format_money(r.revenue, compact=True)} ({r.revenue_share:.0f}%)"
                    for r in tiers.itertuples()
                ],
                hover=[
                    f"<b>{r.segment}</b><br>{int(r.customers):,} buyers ({r.customer_share:.1f}%)"
                    f"<br>Revenue {format_money(r.revenue, compact=True)} ({r.revenue_share:.1f}%)"
                    f"<br>Median order {format_money(r.median_spend)}"
                    for r in tiers.itertuples()
                ],
                x_title="Buyers (n)",
                headroom=1.6,
            )
            style_figure(
                fig,
                f"{tiers.loc[tiers['revenue'].idxmax(), 'segment'].split(' (')[0]} spenders generate the largest revenue share",
                f"n = {len(valid):,} buyers · label: buyers · revenue (share of revenue)",
            )
            show_chart(fig)
    with col2:
        if "age_group" in valid.columns:
            groups = [g for g in AGE_GROUP_ORDER if g in set(valid["age_group"]) and g != "Unknown"]
            fig = go.Figure()
            for g in groups:
                values = valid.loc[valid["age_group"] == g, "purchase_amount"]
                fig.add_trace(
                    go.Box(
                        y=values, name=wrap_label(g), marker={"color": AGE_GROUP_COLORS[g]},
                        line={"width": 1.5}, boxmean=True, boxpoints=False, showlegend=False,
                        hovertemplate=f"<b>{g}</b><br>%{{y:$,.0f}}<extra></extra>",
                    )
                )
            n_age = int(valid["age"].notna().sum()) if "age" in valid.columns else 0
            style_figure(
                fig,
                "Order value barely differs across age cohorts" if not p_age < 0.05 else "Order value differs across age cohorts",
                f"n = {n_age:,} buyers with a valid age · box = IQR, dashed = mean · {format_pvalue(p_age)}",
            )
            fig.update_yaxes(title_text="Purchase amount (USD)", tickprefix="$", tickformat=",", rangemode="tozero")
            show_chart(fig)

    city = compute_group_spend(valid, "city")
    city = pd.concat(
        [city[city["segment"] != "Unknown"].sort_values("rev_per_1k", ascending=False), city[city["segment"] == "Unknown"]]
    )
    labels = list(city["segment"])
    fig = horizontal_bar(
        labels=labels,
        values=list(city["rev_per_1k"] / 1e6),
        colors=[MUTED if c == "Unknown" else NAVY for c in labels],
        text=[format_money(v, compact=True) for v in city["rev_per_1k"]],
        hover=[
            f"<b>{r.segment}</b><br>Revenue per 1,000 buyers: {format_money(r.rev_per_1k, compact=True)}"
            f"<br>Buyers: {int(r.buyers):,} · median order {format_money(r.median_spend)}"
            for r in city.itertuples()
        ],
        x_title="Revenue per 1,000 buyers (USD millions)",
    )
    fig.add_vline(
        x=kpis["norm_rev_per_1k"] / 1e6, line={"color": MEAN_COLOR, "dash": "dot", "width": 2},
        annotation_text=f"All buyers {format_money(kpis['norm_rev_per_1k'], compact=True)}",
        annotation_position="top", annotation_font={"color": MEAN_COLOR, "size": 11},
    )
    style_figure(
        fig,
        "Revenue per 1,000 buyers is flat across metros (KPI-3)" if not p_city < 0.05
        else "Revenue per 1,000 buyers differs across metros (KPI-3)",
        f"Normalised for city size · n = {len(valid):,} buyers · Kruskal–Wallis {format_pvalue(p_city)}",
        height=430,
    )
    fig.update_xaxes(tickprefix="$", ticksuffix="M", tickformat=",.1f")
    show_chart(fig)

    with st.expander("Segment table — spend by city, age group and gender"):
        dimension = st.radio(
            "Segment by", ["city", "age_group", "gender", "metro_region"], horizontal=True,
            format_func=lambda c: c.replace("_", " ").title(), key="segment_dimension",
        )
        if dimension in valid.columns:
            order = {"age_group": AGE_GROUP_ORDER, "gender": GENDER_ORDER}.get(dimension)
            table = compute_group_spend(valid, dimension, order)
            st.dataframe(
                table[["segment", "buyers", "mean_spend", "median_spend", "revenue", "revenue_share", "rev_per_1k"]],
                hide_index=True,
                width="stretch",
                column_config={
                    "segment": st.column_config.TextColumn("Segment"),
                    "buyers": st.column_config.NumberColumn("Buyers (n)", format="%d"),
                    "mean_spend": st.column_config.NumberColumn("Mean order", format="$%.0f"),
                    "median_spend": st.column_config.NumberColumn("Median order", format="$%.0f"),
                    "revenue": st.column_config.NumberColumn("Revenue", format="$%.0f"),
                    "revenue_share": st.column_config.NumberColumn("Revenue share", format="%.1f%%"),
                    "rev_per_1k": st.column_config.NumberColumn("Revenue / 1,000 buyers", format="$%.0f"),
                },
            )


def render_satisfaction_tab(filtered_df: pd.DataFrame, kpis: dict[str, Any]) -> None:
    """Q3: satisfaction, contactability and customer tenure."""
    section_header(
        "Q3 · Satisfaction, reachability & tenure",
        "How satisfied customers are, whether we can contact them and how long they stay active.",
    )
    tenure = (
        filtered_df["customer_tenure_days"].dropna()
        if "customer_tenure_days" in filtered_df.columns
        else pd.Series(dtype=float)
    )

    points = []
    if kpis["n_likert"]:
        likert = filtered_df["feedback_score"].dropna()
        likert = likert[likert <= 5]
        detractors = (likert <= 2).sum() / len(likert) * 100
        promoters = (likert >= 4).sum() / len(likert) * 100
        points.append(
            f"On the genuine 1–5 scale the average is <b>{kpis['avg_feedback']:.2f}</b>: "
            f"{detractors:.1f}% detractors (1–2) vs {promoters:.1f}% promoters (4–5), n = {len(likert):,}."
        )
    if kpis["n_spike"]:
        points.append(
            f"<b>{kpis['n_spike']:,}</b> ratings are an off-scale <b>10</b> on a 1–5 survey — most likely a survey "
            "configuration error to confirm with the survey owner, not genuine delight."
        )
    points.append(
        f"Only <b>{kpis['omnichannel_n']:,}</b> customers ({kpis['omnichannel_n'] / max(kpis['n_filtered'], 1) * 100:.1f}%) "
        f"can be reached on both channels; unreachable customers hold "
        f"<b>{format_money(kpis['unreachable_revenue'], compact=True)}</b> of verified revenue."
    )
    if not tenure.empty:
        points.append(
            f"Median tenure is <b>{tenure.median():.0f} days</b>, but only {len(tenure):,} customers "
            f"({len(tenure) / kpis['n_filtered'] * 100:.1f}%) have two valid, correctly ordered dates."
        )
    insight_box(points)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        scores = filtered_df["feedback_score"].dropna()
        if scores.empty:
            st.info("No feedback scores in the current selection.")
        else:
            counts = scores.value_counts()
            order = [s for s in [1.0, 2.0, 3.0, 4.0, 5.0, 10.0] if s in counts.index]

            def tier(score: float) -> str:
                if score == 10:
                    return "Scale-10 Spike (10)"
                return "Detractor (1-2)" if score <= 2 else "Passive (3)" if score == 3 else "Promoter (4-5)"

            fig = go.Figure()
            for name, color in FEEDBACK_SCORE_COLORS.items():
                xs = [s for s in order if tier(s) == name]
                if not xs:
                    continue
                fig.add_trace(
                    go.Bar(
                        x=[f"{s:.0f}" for s in xs],
                        y=[int(counts[s]) for s in xs],
                        name=name,
                        marker={"color": color},
                        text=[f"{counts[s]:,}" for s in xs],
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate=f"Score %{{x}} · {name}<br>%{{y:,}} ratings<extra></extra>",
                    )
                )
            style_figure(
                fig,
                f"{counts.get(10.0, 0) / len(scores) * 100:.0f}% of ratings are an off-scale 10",
                f"n = {len(scores):,} valid ratings · the 1–5 survey scale should not contain a 10",
            )
            fig.update_xaxes(title_text="Feedback score", type="category",
                             categoryorder="array", categoryarray=[f"{s:.0f}" for s in order])
            fig.update_yaxes(title_text="Ratings (n)", rangemode="tozero")
            fig.update_layout(legend={"y": 1.02})
            show_chart(fig)

    with col2:
        if "contact_reachability_tier" in filtered_df.columns:
            reach = compute_group_spend(filtered_df, "contact_reachability_tier", REACHABILITY_ORDER)
            labels = list(reach["segment"])
            fig = horizontal_bar(
                labels=labels,
                values=list(reach["revenue"] / 1e6),
                colors=[REACHABILITY_COLORS.get(t, MUTED) for t in labels],
                text=[f"{format_money(r.revenue, compact=True)} · {r.revenue_share:.1f}%" for r in reach.itertuples()],
                hover=[
                    f"<b>{r.segment}</b><br>Revenue {format_money(r.revenue, compact=True)} ({r.revenue_share:.1f}%)"
                    f"<br>{int(r.customers):,} customers · {int(r.buyers):,} with a valid order"
                    for r in reach.itertuples()
                ],
                x_title="Verified revenue (USD millions)",
                headroom=1.45,
            )
            style_figure(
                fig,
                f"{reach.set_index('segment')['revenue_share'].get('Unreachable (None)', 0.0):.0f}% of revenue sits with "
                "customers we cannot contact",
                f"n = {kpis['n_valid_spend']:,} valid orders · revenue by contact channel",
            )
            fig.update_xaxes(tickprefix="$", ticksuffix="M", tickformat=",.1f")
            show_chart(fig)

    if not tenure.empty:
        edges = np.arange(0, float(tenure.max()) + 60, 60)
        counts, _ = np.histogram(tenure, bins=edges)
        fig = go.Figure(
            go.Histogram(
                x=tenure,
                xbins={"start": 0, "end": float(edges[-1]), "size": 60},
                marker={"color": OKABE_GREEN, "line": {"color": "#FFFFFF", "width": 1}},
                showlegend=False,
                hovertemplate="%{x} days<br>%{y:,} customers<extra></extra>",
            )
        )
        median_tenure = float(tenure.median())
        fig.add_trace(
            go.Scatter(
                x=[median_tenure, median_tenure], y=[0, float(counts.max()) * 1.08], mode="lines",
                line={"color": INK, "width": 2, "dash": "dash"}, name=f"Median {median_tenure:.0f} days",
                hovertemplate=f"Median: {median_tenure:.0f} days<extra></extra>",
            )
        )
        style_figure(
            fig,
            f"Median time from signup to last purchase is {median_tenure:.0f} days",
            f"n = {len(tenure):,} customers with valid, correctly ordered dates · bins of 60 days",
            height=340,
        )
        fig.update_xaxes(title_text="Days from signup to last purchase")
        fig.update_yaxes(title_text="Customers (n)")
        show_chart(fig)
        note(
            "Tenure is right-censored: recent signups have had less time to buy again, so shorter tenure in newer "
            "cohorts is not evidence of faster churn. Records with the last purchase before signup are excluded."
        )


def render_quality_audit_tab(filtered_df: pd.DataFrame, kpis: dict[str, Any]) -> None:
    """X4: how complete and trustworthy each field is, plus a record inspector."""
    section_header(
        "Data quality audit",
        "How much of each field survived cleaning, which consistency flags fire and how complete each record is.",
    )
    coverage = build_coverage_table(filtered_df)
    flags = build_flag_summary(filtered_df)

    lowest = coverage.iloc[-1] if not coverage.empty else None
    points = [
        f"An average record has <b>{kpis['avg_completeness']:.1f}%</b> of its 12 raw attributes valid.",
    ]
    if lowest is not None:
        points.append(
            f"The weakest field is <b>{lowest['attribute'].lower()}</b>: only {lowest['coverage']:.1f}% "
            f"({int(lowest['valid']):,}) of values are valid after removing blanks and placeholder codes."
        )
    points.append(
        "Missing values are kept as missing (not filled with an average), so every statistic is computed on "
        "verified values only and reports its own n."
    )
    insight_box(points)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        labels = list(coverage["attribute"])
        fig = horizontal_bar(
            labels=labels,
            values=list(coverage["coverage"]),
            colors=[NAVY if v >= 50 else WARNING_COLOR for v in coverage["coverage"]],
            text=[f"{v:.1f}%" for v in coverage["coverage"]],
            hover=[f"<b>{r.attribute}</b><br>{int(r.valid):,} valid values ({r.coverage:.1f}%)"
                   for r in coverage.itertuples()],
            x_title="Valid values (% of records)",
        )
        fig.add_vline(x=50, line={"color": INK_MUTED, "dash": "dot", "width": 1})
        style_figure(
            fig,
            f"Only {coverage.iloc[-1]['coverage']:.0f}% of records hold a valid {coverage.iloc[-1]['attribute'].lower()}",
            f"KPI-1 coverage · n = {len(filtered_df):,} records · orange = below 50%",
            height=430,
        )
        fig.update_xaxes(range=[0, 118], ticksuffix="%")
        show_chart(fig)
    with col2:
        labels = list(flags["flag"])[::-1]
        ordered = flags.iloc[::-1]
        fig = horizontal_bar(
            labels=labels,
            values=list(ordered["records"]),
            colors=WARNING_COLOR,
            text=[f"{int(r.records):,} · {r.rate:.1f}%" for r in ordered.itertuples()],
            hover=[f"<b>{r.flag}</b><br>{r.detail}<br>{int(r.records):,} records ({r.rate:.1f}%)"
                   for r in ordered.itertuples()],
            x_title="Flagged records (n)",
            headroom=1.5,
        )
        style_figure(
            fig,
            f"'{flags.iloc[-1]['flag']}' is the most frequent quality flag" if not flags.empty else "Quality flags",
            f"n = {len(filtered_df):,} records · a record can carry several flags",
            height=430,
        )
        show_chart(fig)

    if "completeness_score" in filtered_df.columns:
        valid_attrs = (filtered_df["completeness_score"] * 12).round().astype(int)
        counts = valid_attrs.value_counts().sort_index()
        fig = go.Figure(
            go.Bar(
                x=list(counts.index),
                y=list(counts.values),
                marker={"color": SEQUENTIAL_BLUES[2]},
                text=[f"{v:,}" for v in counts.values],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x} of 12 attributes valid<br>%{y:,} records<extra></extra>",
            )
        )
        style_figure(
            fig,
            f"The typical record has {counts.idxmax()} of 12 attributes valid (mean {kpis['avg_completeness']:.1f}%)",
            f"Record completeness score · n = {len(filtered_df):,} records",
            height=320,
        )
        fig.update_xaxes(title_text="Valid attributes per record (of 12)", dtick=1)
        fig.update_yaxes(title_text="Records (n)", rangemode="tozero")
        show_chart(fig)

    st.markdown("#### Record inspector")
    display_cols = [
        c for c in [
            "customer_id", "name", "gender", "age", "city", "country", "purchase_amount", "spend_tier",
            "feedback_score", "contact_reachability_tier", "is_date_inverted", "is_geo_mismatch",
            "completeness_score",
        ] if c in filtered_df.columns
    ]
    st.caption(f"Showing the first 500 of {len(filtered_df):,} records in scope. Download the full selection below.")
    st.dataframe(
        filtered_df[display_cols].head(500),
        hide_index=True,
        width="stretch",
        height=360,
        column_config={
            "customer_id": st.column_config.TextColumn("Customer ID"),
            "name": st.column_config.TextColumn("Name"),
            "gender": st.column_config.TextColumn("Gender"),
            "age": st.column_config.NumberColumn("Age", format="%.0f"),
            "city": st.column_config.TextColumn("City"),
            "country": st.column_config.TextColumn("Country (raw)"),
            "purchase_amount": st.column_config.NumberColumn("Purchase (USD)", format="$%.2f"),
            "spend_tier": st.column_config.TextColumn("Spend tier"),
            "feedback_score": st.column_config.NumberColumn("Feedback", format="%.0f"),
            "contact_reachability_tier": st.column_config.TextColumn("Reachability"),
            "is_date_inverted": st.column_config.CheckboxColumn("Date inverted"),
            "is_geo_mismatch": st.column_config.CheckboxColumn("Geo mismatch"),
            "completeness_score": st.column_config.ProgressColumn(
                "Completeness", min_value=0.0, max_value=1.0, format="%.2f"
            ),
        },
    )
    st.download_button(
        "Download selection (CSV)",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="customers_filtered_selection.csv",
        mime="text/csv",
        icon=":material/download:",
    )


def render_methodology_tab() -> None:
    """Definitions, data caveats and sources, so every number on the page is traceable."""
    section_header("Methodology & definitions", "How each metric is calculated and what the data can and cannot support.")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(
            """
**Key metrics** (`specs/ontology.md` §4)

| Metric | Definition |
|---|---|
| Verified revenue | Sum of valid purchase amounts (sentinels `-999` / `N/A` and blanks excluded) |
| Median order value | Median of valid purchase amounts (KPI-2) |
| Revenue per 1,000 buyers | Mean valid order × 1,000 — removes segment-size bias (KPI-3) |
| Reachability rate | Customers with a valid email **or** a valid 10-digit phone (KPI-4) |
| Satisfaction (1–5) | Mean of genuine 1–5 ratings; the off-scale `10` is excluded (KPI-6) |
| Completeness | Share of the 12 raw attributes holding a valid value, per record |
"""
        )
    with col2:
        st.markdown(
            """
**Caveats**

- Every chart reports its own *n*: most fields are valid for only part of the 10,000 records.
- Missing values are **not** imputed; filling age or spend with the median would halve their spread.
- Group comparisons use Kruskal–Wallis tests on observational data — they show association, never causation.
- *Country* contradicts *city* for most records, so location analysis uses the city.
- Tenure is right-censored and covers only customers with two valid, correctly ordered dates.

**Sources**: Kaggle *Customer Messy Data* (10,000 × 12) · cleaned by `python -m src.pipeline` ·
full narrative in `reports/executive_report.md` and `reports/data_quality_report.md`.
"""
        )


# ======================================================================================
# Page assembly
# ======================================================================================
FILTER_KEYS = ["f_gender", "f_city", "f_age", "f_tier", "f_reach"]
TOGGLE_KEYS = ["x_inverted", "x_mismatch", "x_spike"]


def reset_filters() -> None:
    """Callback for the sidebar reset button."""
    for key in FILTER_KEYS:
        st.session_state[key] = []
    for key in TOGGLE_KEYS:
        st.session_state[key] = False


def _ordered_options(df: pd.DataFrame, column: str, order: list[str] | None = None) -> list[str]:
    if column not in df.columns:
        return []
    present = [v for v in df[column].dropna().unique()]
    if order is None:
        return sorted(present)
    return [v for v in order if v in present] + sorted(v for v in present if v not in order)


def main() -> None:
    """Streamlit entry point."""
    st.set_page_config(
        page_title="Customer Intelligence Dashboard",
        page_icon=":material/insights:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    try:
        raw_df = load_dashboard_data()
    except (FileNotFoundError, ValueError, KeyError, OSError) as exc:
        st.error(f"Failed to load the dataset: {exc}")
        return

    data_path = DEFAULT_DATA_PATH if DEFAULT_DATA_PATH.exists() else FALLBACK_DATA_PATH
    refreshed = datetime.fromtimestamp(data_path.stat().st_mtime).strftime("%d %b %Y, %H:%M")

    # ---- Sidebar -------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### Filters")
        st.caption("Leave a filter empty to include every value.")
        st.markdown("**Customer segment**")
        genders = st.multiselect("Gender", _ordered_options(raw_df, "gender", GENDER_ORDER),
                                 key="f_gender", placeholder="All genders")
        cities = st.multiselect("City", _ordered_options(raw_df, "city"), key="f_city", placeholder="All cities")
        ages = st.multiselect("Age group", _ordered_options(raw_df, "age_group", AGE_GROUP_ORDER),
                              key="f_age", placeholder="All age groups")
        tiers = st.multiselect("Spend tier", _ordered_options(raw_df, "spend_tier", SPEND_TIER_ORDER),
                               key="f_tier", placeholder="All spend tiers")
        reach = st.multiselect("Contact reachability",
                               _ordered_options(raw_df, "contact_reachability_tier", REACHABILITY_ORDER),
                               key="f_reach", placeholder="All channels")
        st.divider()
        st.markdown("**Data-quality exclusions**")
        x_inverted = st.toggle("Exclude purchase-before-signup dates", key="x_inverted",
                               help="Drops records whose last purchase is dated before signup (is_date_inverted).")
        x_mismatch = st.toggle("Exclude city/country mismatches", key="x_mismatch",
                               help="Drops records pairing an Indian city with a non-Indian country (is_geo_mismatch).")
        x_spike = st.toggle("Exclude off-scale feedback (10)", key="x_spike",
                            help="Drops records whose feedback score is the off-scale 10 (is_score_10_spike).")
        st.button("Reset all filters", on_click=reset_filters, width="stretch", icon=":material/restart_alt:")

    filtered_df = apply_filters(raw_df, genders, cities, ages, tiers, reach, x_inverted, x_mismatch, x_spike)
    kpis = compute_kpi_summary(raw_df, filtered_df)

    with st.sidebar:
        st.divider()
        share = kpis["n_filtered"] / max(kpis["n_total"], 1)
        st.progress(share, text=f"{kpis['n_filtered']:,} of {kpis['n_total']:,} records in scope ({share:.0%})")

    # ---- Header ---------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="app-header">
          <div>
            <h1>Customer Intelligence Dashboard</h1>
            <p>Exploratory analysis of {kpis['n_total']:,} customer records · Kaggle <i>Customer Messy Data</i></p>
          </div>
          <div class="app-meta">
            Data: <b>{html.escape(data_path.name)}</b><br>
            Refreshed: <b>{refreshed}</b><br>
            Author: <b>Levi Flores</b>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    active = describe_active_filters(
        {"Gender": genders, "City": cities, "Age group": ages, "Spend tier": tiers, "Reachability": reach},
        {"Purchase-before-signup dates": x_inverted, "City/country mismatches": x_mismatch,
         "Off-scale feedback": x_spike},
    )
    chips = "".join(f"<span class='chip'>{html.escape(a)}</span>" for a in active) or "<span>None — full customer base</span>"
    st.markdown(f"<div class='chips'>Active filters: {chips}</div>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("No customers match the current filters. Widen the selection or use **Reset all filters**.")
        return

    # ---- KPI scorecard --------------------------------------------------------------
    kpi_cards([
        ("Customers in scope", f"{kpis['n_filtered']:,}", f"{kpis['n_filtered'] / kpis['n_total'] * 100:.1f}% of the base"),
        ("Verified revenue", format_money(kpis["total_revenue"], compact=True),
         f"{kpis['n_valid_spend']:,} valid orders ({kpis['spend_coverage']:.1f}%)"),
        ("Median order value", format_money(kpis["median_spend"]), f"Mean {format_money(kpis['mean_spend'])}"),
        ("Revenue / 1,000 buyers", format_money(kpis["norm_rev_per_1k"], compact=True), "KPI-3 · size-normalised"),
        ("Reachable customers", f"{kpis['reachability_rate']:.1f}%", f"{kpis['reachable_n']:,} by email or phone"),
        ("Satisfaction (1–5)", f"{kpis['avg_feedback']:.2f}" if pd.notna(kpis["avg_feedback"]) else "N/A",
         f"n = {kpis['n_likert']:,} genuine ratings"),
    ])

    tabs = st.tabs([
        ":material/dashboard: Overview",
        ":material/groups: Q1 · Demographics",
        ":material/payments: Q2 · Revenue",
        ":material/sentiment_satisfied: Q3 · Satisfaction & reach",
        ":material/fact_check: Data quality",
        ":material/menu_book: Methodology",
    ])
    with tabs[0]:
        render_overview_tab(filtered_df, kpis)
    with tabs[1]:
        render_demographics_tab(filtered_df)
    with tabs[2]:
        render_revenue_tab(filtered_df, kpis)
    with tabs[3]:
        render_satisfaction_tab(filtered_df, kpis)
    with tabs[4]:
        render_quality_audit_tab(filtered_df, kpis)
    with tabs[5]:
        render_methodology_tab()

    st.markdown(
        "<div class='footer'>Customer Messy Data EDA · Levi Flores (@levifvy) · "
        "Metrics defined in specs/ontology.md · Observational data: associations, not causes</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
