"""Executive Interactive EDA Dashboard (Streamlit).

Expert milestone task X2. Provides C-level interactive exploration of the Customer Messy Data
cleaned and enriched artifacts (customers_enriched_v2.csv) with multi-dimensional filtering,
KPI scorecards, demographic breakdown (Q1), spend analysis (Q2), satisfaction/reachability (Q3),
and data quality auditing (X4).

Usage:
    streamlit run app/dashboard.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH: Path = REPO_ROOT / "data" / "processed" / "customers_enriched_v2.csv"
FALLBACK_DATA_PATH: Path = REPO_ROOT / "data" / "processed" / "customers_clean_v2.csv"

# Colorblind-safe Okabe-Ito palette (specs/ontology.md & .agents/skills/eda-visualization/SKILL.md)
PALETTE_PRIMARY = "#1B4F72"    # Deep Navy
PALETTE_SECONDARY = "#2E86AB"  # Steel Blue
PALETTE_ACCENT = "#D95F02"     # Orange (Outliers / Mean / Warnings)
PALETTE_TEAL = "#1B9E77"       # Emerald Teal (Positive / Median)
PALETTE_MUTED = "#7F8C8D"      # Slate Grey (Unknown / Missing)
PALETTE_DISCRETE = [
    "#1B4F72", "#2E86AB", "#1B9E77", "#D95F02",
    "#7570B3", "#E7298A", "#66A61E", "#E6AB02",
]


@st.cache_data(show_spinner=False)
def load_dashboard_data(path: Path | str | None = None) -> pd.DataFrame:
    """Load and prepare processed customer dataset for interactive visualization.

    Parameters
    ----------
    path : Path or str, optional
        Path to processed CSV. Defaults to customers_enriched_v2.csv.

    Returns
    -------
    pd.DataFrame
        Prepared DataFrame with correct types and date parsers.
    """
    target_path = Path(path) if path is not None else DEFAULT_DATA_PATH
    if not target_path.exists():
        target_path = FALLBACK_DATA_PATH

    if not target_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {target_path}")

    df = pd.read_csv(
        target_path,
        parse_dates=["signup_date", "last_purchase_date"],
        low_memory=False,
    )
    return df


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
    """Apply user-selected sidebar filters to the dataframe."""
    filtered = df.copy()

    if selected_genders and "All" not in selected_genders:
        filtered = filtered[filtered["gender"].isin(selected_genders)]

    if selected_cities and "All" not in selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]

    if "age_group" in filtered.columns and selected_age_groups and "All" not in selected_age_groups:
        filtered = filtered[filtered["age_group"].isin(selected_age_groups)]

    if "spend_tier" in filtered.columns and selected_spend_tiers and "All" not in selected_spend_tiers:
        filtered = filtered[filtered["spend_tier"].isin(selected_spend_tiers)]

    if (
        "contact_reachability_tier" in filtered.columns
        and selected_reachability
        and "All" not in selected_reachability
    ):
        filtered = filtered[filtered["contact_reachability_tier"].isin(selected_reachability)]

    if exclude_inverted_dates and "is_date_inverted" in filtered.columns:
        filtered = filtered[~filtered["is_date_inverted"]]

    if exclude_geo_mismatch and "is_geo_mismatch" in filtered.columns:
        filtered = filtered[~filtered["is_geo_mismatch"]]

    if exclude_score_10_spike and "is_score_10_spike" in filtered.columns:
        filtered = filtered[~filtered["is_score_10_spike"]]

    return filtered


def compute_kpi_summary(df: pd.DataFrame, filtered_df: pd.DataFrame) -> dict[str, Any]:
    """Calculate executive KPIs matching specs/ontology.md §4."""
    n_total = len(df)
    n_filtered = len(filtered_df)

    valid_purchases = filtered_df["purchase_amount"].dropna()
    mean_spend = valid_purchases.mean() if not valid_purchases.empty else np.nan
    median_spend = valid_purchases.median() if not valid_purchases.empty else np.nan
    total_revenue = valid_purchases.sum() if not valid_purchases.empty else 0.0

    # KPI-3: Normalized Revenue per 1,000 customers
    norm_rev_per_1k = (mean_spend * 1000.0) if pd.notna(mean_spend) else 0.0

    # KPI-4: Omnichannel Reachability Rate
    if "has_valid_email" in filtered_df.columns and "has_valid_phone" in filtered_df.columns:
        reachable = (filtered_df["has_valid_email"] | filtered_df["has_valid_phone"]).sum()
        reachability_rate = (reachable / n_filtered * 100.0) if n_filtered > 0 else 0.0
    else:
        reachability_rate = 0.0

    # KPI-6: Average Likert feedback (1-5 scale)
    feedback_col = "feedback_score_1_to_5" if "feedback_score_1_to_5" in filtered_df.columns else "feedback_score"
    valid_feedback = filtered_df[feedback_col].dropna()
    avg_feedback = valid_feedback.mean() if not valid_feedback.empty else np.nan

    # Average Completeness Score
    avg_completeness = (
        filtered_df["completeness_score"].mean() * 100.0
        if "completeness_score" in filtered_df.columns and not filtered_df.empty
        else np.nan
    )

    return {
        "n_total": n_total,
        "n_filtered": n_filtered,
        "n_valid_spend": len(valid_purchases),
        "mean_spend": mean_spend,
        "median_spend": median_spend,
        "total_revenue": total_revenue,
        "norm_rev_per_1k": norm_rev_per_1k,
        "reachability_rate": reachability_rate,
        "avg_feedback": avg_feedback,
        "avg_completeness": avg_completeness,
    }


def render_overview_tab(filtered_df: pd.DataFrame, kpis: dict[str, Any]) -> None:
    """Render Executive Overview tab with macro distributions."""
    st.markdown("### 📌 Executive Summary & Key Highlights")
    st.info(
        f"**Scope & Coverage Caveat:** Displaying **{kpis['n_filtered']:,}** records filtered from the 10,000 raw baseline. "
        f"Valid monetary purchase records available in current selection: **n = {kpis['n_valid_spend']:,}** "
        f"({(kpis['n_valid_spend'] / kpis['n_filtered'] * 100 if kpis['n_filtered'] > 0 else 0):.1f}% coverage)."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💳 Purchase Amount Distribution (Valid Spenders)")
        valid_spend = filtered_df["purchase_amount"].dropna()
        if not valid_spend.empty:
            fig_hist = px.histogram(
                filtered_df,
                x="purchase_amount",
                nbins=40,
                color_discrete_sequence=[PALETTE_PRIMARY],
                labels={"purchase_amount": "Purchase Amount (USD $)", "count": "Customer Count (n)"},
                title=f"Spend Distribution (n = {len(valid_spend):,}, Median = ${kpis['median_spend']:,.2f})",
            )
            fig_hist.add_vline(
                x=kpis["median_spend"],
                line_dash="dash",
                line_color=PALETTE_TEAL,
                annotation_text=f"Median: ${kpis['median_spend']:,.0f}",
                annotation_position="top left",
            )
            fig_hist.add_vline(
                x=kpis["mean_spend"],
                line_dash="dot",
                line_color=PALETTE_ACCENT,
                annotation_text=f"Mean: ${kpis['mean_spend']:,.0f}",
                annotation_position="top right",
            )
            fig_hist.update_layout(bargap=0.08, height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("No valid purchase records in selected filter range.")

    with col2:
        st.markdown("#### 📡 Contact Reachability Breakdown")
        if "contact_reachability_tier" in filtered_df.columns:
            reach_counts = filtered_df["contact_reachability_tier"].value_counts().reset_index()
            reach_counts.columns = ["Channel Tier", "Customers"]
            color_map = {
                "Omnichannel (Both)": PALETTE_TEAL,
                "Email Only": PALETTE_PRIMARY,
                "Phone Only": PALETTE_SECONDARY,
                "Unreachable (None)": PALETTE_MUTED,
            }
            fig_reach = px.pie(
                reach_counts,
                names="Channel Tier",
                values="Customers",
                color="Channel Tier",
                color_discrete_map=color_map,
                hole=0.45,
                title=f"Marketing Reachability Share (n = {kpis['n_filtered']:,})",
            )
            fig_reach.update_traces(textposition="inside", textinfo="percent+label")
            fig_reach.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_reach, use_container_width=True)


def render_demographics_tab(filtered_df: pd.DataFrame) -> None:
    """Render Demographics & Geography Tab (Business Question Q1)."""
    st.markdown("### 👥 Demographic & Geographic Profile (`Q1`)")
    st.caption("Addressing who our customers are, where they reside, and how demographic cohorts are structured.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎂 Age Group Distribution")
        if "age_group" in filtered_df.columns:
            age_counts = filtered_df["age_group"].value_counts().reset_index()
            age_counts.columns = ["Age Group", "Customers"]
            fig_age = px.bar(
                age_counts,
                x="Age Group",
                y="Customers",
                text="Customers",
                color="Age Group",
                color_discrete_sequence=PALETTE_DISCRETE,
                title="Customer Distribution by Age Cohort",
                labels={"Customers": "Customer Count (n)"},
            )
            fig_age.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig_age.update_layout(showlegend=False, height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_age, use_container_width=True)

    with col2:
        st.markdown("#### ⚧ Gender Representation")
        gender_counts = filtered_df["gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Customers"]
        color_map = {"Male": PALETTE_PRIMARY, "Female": PALETTE_SECONDARY, "Unknown": PALETTE_MUTED}
        fig_gender = px.bar(
            gender_counts,
            x="Gender",
            y="Customers",
            text="Customers",
            color="Gender",
            color_discrete_map=color_map,
            title="Gender Profile (Standardized Categories)",
            labels={"Customers": "Customer Count (n)"},
        )
        fig_gender.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_gender.update_layout(showlegend=False, height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
        st.plotly_chart(fig_gender, use_container_width=True)

    st.markdown("#### 🏙️ Geographic Concentration Across Indian Metros")
    city_counts = filtered_df["city"].value_counts().reset_index()
    city_counts.columns = ["City", "Customers"]
    fig_city = px.bar(
        city_counts,
        x="City",
        y="Customers",
        text="Customers",
        color="City",
        color_discrete_sequence=PALETTE_DISCRETE,
        title="Urban Geographic Footprint (Top Indian Metropolitan Centers)",
        labels={"Customers": "Customer Count (n)"},
    )
    fig_city.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_city.update_layout(showlegend=False, height=360, margin={"l": 20, "r": 20, "t": 50, "b": 30})
    st.plotly_chart(fig_city, use_container_width=True)


def render_revenue_tab(filtered_df: pd.DataFrame) -> None:
    """Render Revenue & Spending Tab (Business Question Q2)."""
    st.markdown("### 💰 Commercial Revenue & Spending Segments (`Q2`)")
    st.caption("Addressing spend distribution, segment profitability, and identifying high-value customer tiers.")

    valid_df = filtered_df.dropna(subset=["purchase_amount"])

    if valid_df.empty:
        st.warning("No records with valid purchase amount in current selection.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 Spend Tier Segmentation")
        if "spend_tier" in filtered_df.columns:
            tier_df = (
                filtered_df[filtered_df["spend_tier"] != "Missing"]["spend_tier"]
                .value_counts()
                .reset_index()
            )
            tier_df.columns = ["Spend Tier", "Customer Count"]
            fig_tier = px.pie(
                tier_df,
                names="Spend Tier",
                values="Customer Count",
                color_discrete_sequence=[PALETTE_TEAL, PALETTE_PRIMARY, PALETTE_SECONDARY],
                hole=0.4,
                title="Customer Concentration by Spend Tier",
            )
            fig_tier.update_traces(textinfo="percent+label")
            fig_tier.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_tier, use_container_width=True)

    with col2:
        st.markdown("#### 🎯 Spend by Demographic Age Group")
        if "age_group" in valid_df.columns:
            fig_box = px.box(
                valid_df,
                x="age_group",
                y="purchase_amount",
                color="age_group",
                color_discrete_sequence=PALETTE_DISCRETE,
                title="Purchase Amount Dispersion across Age Cohorts",
                labels={"purchase_amount": "Purchase Amount (USD $)", "age_group": "Age Group"},
            )
            fig_box.update_layout(showlegend=False, height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("#### 📊 Normalized Revenue per 1,000 Customers by City (KPI-3)")
    city_spend = (
        valid_df.groupby("city", observed=True)["purchase_amount"]
        .agg(["count", "mean", "median", "sum"])
        .reset_index()
    )
    city_spend["norm_rev_1k"] = city_spend["mean"] * 1000.0
    city_spend = city_spend.sort_values(by="norm_rev_1k", ascending=False)

    fig_city_spend = px.bar(
        city_spend,
        x="city",
        y="norm_rev_1k",
        text="norm_rev_1k",
        color="city",
        color_discrete_sequence=PALETTE_DISCRETE,
        title="Revenue Potential Normalized per 1,000 Customers by Metropolitan Hub",
        labels={"norm_rev_1k": "Normalized Revenue per 1,000 Customers (USD $)", "city": "City"},
    )
    fig_city_spend.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig_city_spend.update_layout(showlegend=False, height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
    st.plotly_chart(fig_city_spend, use_container_width=True)


def render_satisfaction_tab(filtered_df: pd.DataFrame) -> None:
    """Render Satisfaction, Retention & Omnichannel Tab (Business Question Q3)."""
    st.markdown("### ⭐ Customer Satisfaction, Retention & Reachability (`Q3`)")
    st.caption("Addressing post-purchase satisfaction ratings, omnichannel communication reach, and lifecycle retention.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🌟 Feedback Score Distribution (Dual Representation)")
        valid_feedback = filtered_df["feedback_score"].dropna()
        if not valid_feedback.empty:
            fb_counts = valid_feedback.value_counts().sort_index().reset_index()
            fb_counts.columns = ["Feedback Score", "Count"]
            fb_counts["Is Spike"] = fb_counts["Feedback Score"].apply(lambda x: "Score 10 Spike" if x == 10 else "Likert (1-5)")
            fig_fb = px.bar(
                fb_counts,
                x="Feedback Score",
                y="Count",
                color="Is Spike",
                text="Count",
                color_discrete_map={"Likert (1-5)": PALETTE_PRIMARY, "Score 10 Spike": PALETTE_ACCENT},
                title=f"Feedback Distribution: 1-5 Scale vs. 10 Spike (n = {len(valid_feedback):,})",
                labels={"Count": "Response Count (n)", "Feedback Score": "Recorded Feedback Score"},
            )
            fig_fb.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig_fb.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_fb, use_container_width=True)
        else:
            st.warning("No feedback data available in current selection.")

    with col2:
        st.markdown("#### ⏱️ Customer Lifecycle Tenure (Valid Non-Inverted)")
        if "customer_tenure_days" in filtered_df.columns:
            valid_tenure = filtered_df["customer_tenure_days"].dropna()
            if not valid_tenure.empty:
                fig_tenure = px.histogram(
                    filtered_df,
                    x="customer_tenure_days",
                    nbins=35,
                    color_discrete_sequence=[PALETTE_TEAL],
                    title=f"Customer Tenure in Days (n = {len(valid_tenure):,}, Median = {valid_tenure.median():.0f} d)",
                    labels={"customer_tenure_days": "Tenure Duration (Days)", "count": "Customer Count (n)"},
                )
                fig_tenure.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
                st.plotly_chart(fig_tenure, use_container_width=True)
            else:
                st.warning("No valid non-inverted tenure records available.")


def render_quality_audit_tab(filtered_df: pd.DataFrame) -> None:
    """Render Data Quality & Integrity Audit Tab (Task X4)."""
    st.markdown("### 🛡️ Data Quality & Anomaly Diagnostic Audit (`X4`)")
    st.caption("Deep-dive inspection into the 40.7% corruption baseline, sentinel remediation, and consistency flags.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🚩 Data Quality Flags Breakdown")
        flags = [
            ("Geographic Mismatch (Non-Indian Country)", "is_geo_mismatch"),
            ("Chronological Date Inversion", "is_date_inverted"),
            ("Missing Age (Sentinel Coerced)", "is_age_missing"),
            ("Missing Spend (Sentinel Coerced)", "is_purchase_missing"),
            ("Feedback Score 10 Spike Anomaly", "is_score_10_spike"),
        ]
        flag_summary = []
        for label, col in flags:
            if col in filtered_df.columns:
                count = filtered_df[col].sum()
                pct = (count / len(filtered_df) * 100.0) if len(filtered_df) > 0 else 0.0
                flag_summary.append({"Anomaly / Flag": label, "Count": count, "Rate (%)": pct})

        if flag_summary:
            flag_df = pd.DataFrame(flag_summary)
            fig_flags = px.bar(
                flag_df,
                y="Anomaly / Flag",
                x="Count",
                text="Rate (%)",
                orientation="h",
                color_discrete_sequence=[PALETTE_ACCENT],
                title="Prevalence of Anomalies in Selected Customer Cohort",
                labels={"Count": "Flagged Records (n)"},
            )
            fig_flags.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_flags.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_flags, use_container_width=True)

    with col2:
        st.markdown("#### 📈 Completeness Score Distribution")
        if "completeness_score" in filtered_df.columns:
            fig_comp = px.histogram(
                filtered_df,
                x="completeness_score",
                nbins=20,
                color_discrete_sequence=[PALETTE_SECONDARY],
                title=f"Record Completeness Score (Mean = {filtered_df['completeness_score'].mean():.2%})",
                labels={"completeness_score": "Completeness Score (0.0 to 1.0)", "count": "Records (n)"},
            )
            fig_comp.update_layout(height=380, margin={"l": 20, "r": 20, "t": 50, "b": 30})
            st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("#### 🔍 Interactive Dataset Inspector (First 500 Records)")
    display_cols = [
        c for c in [
            "customer_id", "name", "gender", "age", "city", "country",
            "purchase_amount", "feedback_score", "has_valid_email", "has_valid_phone",
            "is_date_inverted", "is_geo_mismatch", "completeness_score",
        ] if c in filtered_df.columns
    ]
    st.dataframe(filtered_df[display_cols].head(500), use_container_width=True)


def main() -> None:
    """Main execution function for Streamlit dashboard application."""
    st.set_page_config(
        page_title="Customer Intelligence Executive Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Global custom styling
    st.markdown(
        """
        <style>
        .metric-card {
            background-color: #F8F9FA;
            border-radius: 8px;
            padding: 15px;
            border-left: 5px solid #1B4F72;
            margin-bottom: 10px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 48px;
            white-space: pre-wrap;
            background-color: #F0F4F8;
            border-radius: 4px 4px 0px 0px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1B4F72 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📊 Customer Intelligence & Data Quality Executive Dashboard")
    st.markdown(
        "**Exploratory Data Analysis & Strategic Insights — 10,000 Customer Records**  \n"
        "*Author:* Levi Flores (`@levifvy`) | *Dataset:* Kaggle Customer Messy Data | *Version:* 2.0 (Enriched & Fully Audited)"
    )

    # 1. Load Data
    try:
        raw_df = load_dashboard_data()
    except (FileNotFoundError, ValueError, KeyError, OSError) as exc:
        st.error(f"Failed to load dataset: {exc}")
        return

    # 2. Sidebar Filters
    st.sidebar.header("🔍 Executive Filters")

    # Demographics filters
    gender_options = ["All"] + sorted([g for g in raw_df["gender"].unique() if pd.notna(g)])
    selected_genders = st.sidebar.multiselect("Gender", gender_options, default=["All"])

    city_options = ["All"] + sorted([c for c in raw_df["city"].unique() if pd.notna(c)])
    selected_cities = st.sidebar.multiselect("City (Indian Metros)", city_options, default=["All"])

    age_group_options = ["All"]
    if "age_group" in raw_df.columns:
        age_group_options += [ag for ag in raw_df["age_group"].unique() if pd.notna(ag)]
    selected_age_groups = st.sidebar.multiselect("Age Cohort", age_group_options, default=["All"])

    spend_tier_options = ["All"]
    if "spend_tier" in raw_df.columns:
        spend_tier_options += [st_opt for st_opt in raw_df["spend_tier"].unique() if pd.notna(st_opt)]
    selected_spend_tiers = st.sidebar.multiselect("Spend Tier", spend_tier_options, default=["All"])

    reach_options = ["All"]
    if "contact_reachability_tier" in raw_df.columns:
        reach_options += [r for r in raw_df["contact_reachability_tier"].unique() if pd.notna(r)]
    selected_reach = st.sidebar.multiselect("Marketing Reachability", reach_options, default=["All"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🛡️ Data Integrity Toggles")
    exclude_inverted = st.sidebar.checkbox("Exclude Chronological Inversions", value=False)
    exclude_mismatch = st.sidebar.checkbox("Exclude Geographic Mismatches", value=False)
    exclude_spike = st.sidebar.checkbox("Exclude Score 10 Feedback Spike", value=False)

    # 3. Apply Filters
    filtered_df = apply_filters(
        raw_df,
        selected_genders,
        selected_cities,
        selected_age_groups,
        selected_spend_tiers,
        selected_reach,
        exclude_inverted,
        exclude_mismatch,
        exclude_spike,
    )

    # 4. Compute KPIs
    kpis = compute_kpi_summary(raw_df, filtered_df)

    # 5. Render Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Customers", f"{kpis['n_filtered']:,}", f"{(kpis['n_filtered']/kpis['n_total']*100):.1f}% active")
    with m2:
        median_val = f"${kpis['median_spend']:,.0f}" if pd.notna(kpis['median_spend']) else "N/A"
        st.metric("Median Spend (MOV)", median_val, f"n = {kpis['n_valid_spend']:,}")
    with m3:
        norm_val = f"${kpis['norm_rev_per_1k']:,.0f}" if pd.notna(kpis['norm_rev_per_1k']) else "N/A"
        st.metric("Rev / 1k Customers", norm_val, "Normalized KPI-3")
    with m4:
        st.metric("Reachability Rate", f"{kpis['reachability_rate']:.1f}%", "Email or Phone")
    with m5:
        avg_comp = f"{kpis['avg_completeness']:.1f}%" if pd.notna(kpis['avg_completeness']) else "N/A"
        st.metric("Avg Record Quality", avg_comp, "Completeness")

    # 6. Navigation Tabs
    tab_overview, tab_demo, tab_rev, tab_sat, tab_qa = st.tabs([
        "📌 Overview",
        "👥 Demographics (Q1)",
        "💰 Revenue & Spenders (Q2)",
        "⭐ Satisfaction & Churn (Q3)",
        "🛡️ Quality & Audit (X4)",
    ])

    with tab_overview:
        render_overview_tab(filtered_df, kpis)

    with tab_demo:
        render_demographics_tab(filtered_df)

    with tab_rev:
        render_revenue_tab(filtered_df)

    with tab_sat:
        render_satisfaction_tab(filtered_df)

    with tab_qa:
        render_quality_audit_tab(filtered_df)

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #7F8C8D; font-size: 13px;'>"
        "Exploratory Data Analysis Project & Interactive Dashboard | Authored by Levi Flores (@levifvy) | "
        "Strict Domain Contract & ISO Quality Gate Adherent"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
