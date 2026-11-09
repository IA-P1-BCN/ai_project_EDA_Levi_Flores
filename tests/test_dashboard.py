"""Unit test suite for the executive interactive dashboard (Task X2, X3).

Verifies dataset loading, interactive filtering logic, anomaly toggles, and executive
KPI metric calculation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.dashboard import (
    apply_filters,
    build_coverage_table,
    build_flag_summary,
    compute_group_spend,
    compute_kpi_summary,
    describe_active_filters,
    format_money,
    kruskal_pvalue,
    load_dashboard_data,
)


@pytest.fixture
def sample_dashboard_df() -> pd.DataFrame:
    """Fixture providing a synthetic DataFrame mimicking customers_enriched_v2.csv."""
    return pd.DataFrame(
        {
            "customer_id": ["C00001", "C00002", "C00003", "C00004"],
            "name": ["Rahul", "Sneha", "Kiran", "Unknown"],
            "gender": ["Male", "Female", "Male", "Unknown"],
            "age": [25.0, 42.0, 65.0, None],
            "city": ["Bangalore", "Mumbai", "Delhi", "Unknown"],
            "country": ["India", "USA", "India", "Unknown"],
            "signup_date": pd.to_datetime(["2021-01-01", "2022-05-10", "2023-08-15", "2024-02-01"]),
            "last_purchase_date": pd.to_datetime(["2021-06-01", "2021-01-01", "2023-10-20", "2024-03-01"]),
            "purchase_amount": [1500.0, 3200.0, None, 4500.0],
            "feedback_score": [4.0, 10.0, 2.0, None],
            "feedback_score_1_to_5": [4.0, None, 2.0, None],
            "has_valid_email": [True, True, False, False],
            "has_valid_phone": [True, False, False, False],
            "is_date_inverted": [False, True, False, False],
            "is_geo_mismatch": [False, True, False, False],
            "is_score_10_spike": [False, True, False, False],
            "completeness_score": [1.0, 0.8, 0.6, 0.5],
            "age_group": ["18-29 (Young Adult)", "30-44 (Early Career)", "60+ (Senior)", "Unknown"],
            "spend_tier": ["Medium ($1,200-$3,500)", "Medium ($1,200-$3,500)", "Missing", "High (>$3,500)"],
            "contact_reachability_tier": ["Omnichannel (Both)", "Email Only", "Unreachable (None)", "Unreachable (None)"],
        }
    )


class TestDashboardDataLoader:
    """Tests for load_dashboard_data."""

    def test_loads_production_dataset(self) -> None:
        df = load_dashboard_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10000
        assert "customer_id" in df.columns
        assert "purchase_amount" in df.columns


class TestDashboardFilterLogic:
    """Tests for apply_filters."""

    def test_filter_by_gender(self, sample_dashboard_df: pd.DataFrame) -> None:
        filtered = apply_filters(
            sample_dashboard_df,
            selected_genders=["Male"],
            selected_cities=["All"],
            selected_age_groups=["All"],
            selected_spend_tiers=["All"],
            selected_reachability=["All"],
            exclude_inverted_dates=False,
            exclude_geo_mismatch=False,
            exclude_score_10_spike=False,
        )
        assert len(filtered) == 2
        assert set(filtered["gender"].unique()) == {"Male"}

    def test_filter_by_city(self, sample_dashboard_df: pd.DataFrame) -> None:
        filtered = apply_filters(
            sample_dashboard_df,
            selected_genders=["All"],
            selected_cities=["Bangalore"],
            selected_age_groups=["All"],
            selected_spend_tiers=["All"],
            selected_reachability=["All"],
            exclude_inverted_dates=False,
            exclude_geo_mismatch=False,
            exclude_score_10_spike=False,
        )
        assert len(filtered) == 1
        assert filtered.iloc[0]["city"] == "Bangalore"

    def test_filter_exclude_anomalies(self, sample_dashboard_df: pd.DataFrame) -> None:
        filtered = apply_filters(
            sample_dashboard_df,
            selected_genders=["All"],
            selected_cities=["All"],
            selected_age_groups=["All"],
            selected_spend_tiers=["All"],
            selected_reachability=["All"],
            exclude_inverted_dates=True,
            exclude_geo_mismatch=True,
            exclude_score_10_spike=True,
        )
        # Record 2 has date inverted, geo mismatch, and score 10 spike
        assert len(filtered) == 3
        assert "C00002" not in filtered["customer_id"].values


class TestDashboardKpis:
    """Tests for compute_kpi_summary."""

    def test_computes_accurate_summary_metrics(self, sample_dashboard_df: pd.DataFrame) -> None:
        kpis = compute_kpi_summary(sample_dashboard_df, sample_dashboard_df)
        assert kpis["n_total"] == 4
        assert kpis["n_filtered"] == 4
        assert kpis["n_valid_spend"] == 3
        # Spends: 1500, 3200, 4500 -> median is 3200
        assert kpis["median_spend"] == 3200.0
        assert kpis["mean_spend"] == pytest.approx(3066.666, rel=1e-2)
        # Reachable: record 1 (both), record 2 (email) -> 2 out of 4 = 50%
        assert kpis["reachability_rate"] == 50.0


class TestDashboardHelpers:
    """Tests for the pure helpers behind the redesigned dashboard views."""

    def test_empty_selection_means_no_filter(self, sample_dashboard_df: pd.DataFrame) -> None:
        filtered = apply_filters(sample_dashboard_df, [], [], [], [], [], False, False, False)
        assert len(filtered) == len(sample_dashboard_df)

    def test_kpis_split_reachability_and_ratings(self, sample_dashboard_df: pd.DataFrame) -> None:
        kpis = compute_kpi_summary(sample_dashboard_df, sample_dashboard_df)
        assert kpis["reachable_n"] == 2
        assert kpis["omnichannel_n"] == 1
        assert kpis["unreachable_n"] == 2
        # Unreachable rows: C00003 (no spend) and C00004 (4,500) -> 4,500 of 9,200 revenue.
        assert kpis["unreachable_revenue"] == pytest.approx(4500.0)
        assert kpis["unreachable_revenue_share"] == pytest.approx(4500.0 / 9200.0 * 100.0)
        # Genuine 1-5 ratings are 4 and 2; the off-scale 10 is counted separately.
        assert kpis["avg_feedback"] == pytest.approx(3.0)
        assert kpis["n_likert"] == 2
        assert kpis["n_spike"] == 1

    def test_kpis_on_empty_selection(self, sample_dashboard_df: pd.DataFrame) -> None:
        kpis = compute_kpi_summary(sample_dashboard_df, sample_dashboard_df.iloc[0:0])
        assert kpis["n_filtered"] == 0
        assert kpis["total_revenue"] == 0.0
        assert kpis["reachability_rate"] == 0.0

    def test_group_spend_keeps_requested_order(self, sample_dashboard_df: pd.DataFrame) -> None:
        table = compute_group_spend(sample_dashboard_df, "gender", ["Female", "Male", "Unknown"])
        assert list(table["segment"]) == ["Female", "Male", "Unknown"]
        male = table.set_index("segment").loc["Male"]
        assert male["customers"] == 2
        assert male["buyers"] == 1
        assert male["rev_per_1k"] == pytest.approx(1_500_000.0)
        assert table["revenue_share"].sum() == pytest.approx(100.0)

    def test_flag_summary_counts_each_flag(self, sample_dashboard_df: pd.DataFrame) -> None:
        summary = build_flag_summary(sample_dashboard_df).set_index("flag")
        assert summary.loc["Purchase before signup", "records"] == 1
        assert summary.loc["Purchase before signup", "rate"] == pytest.approx(25.0)

    def test_coverage_treats_unknown_as_invalid(self, sample_dashboard_df: pd.DataFrame) -> None:
        coverage = build_coverage_table(sample_dashboard_df).set_index("attribute")
        assert coverage.loc["City", "valid"] == 3
        assert coverage.loc["Purchase amount", "valid"] == 3
        assert coverage.loc["Age", "coverage"] == pytest.approx(75.0)

    def test_kruskal_needs_two_groups(self, sample_dashboard_df: pd.DataFrame) -> None:
        assert np.isnan(kruskal_pvalue(sample_dashboard_df, "city"))

    def test_production_dataset_types(self) -> None:
        df = load_dashboard_data()
        assert df["phone_number"].dropna().str.fullmatch(r"\d{10}").all()
        assert df["has_valid_email"].dtype == bool
        kpis = compute_kpi_summary(df, df)
        # Empirical KPI-4 baseline recorded in specs/ontology.md §4.
        assert kpis["reachable_n"] == 4388
        assert kpis["omnichannel_n"] == 634

    def test_money_and_filter_labels(self) -> None:
        assert format_money(6_043_218.46, compact=True) == "$6.04M"
        assert format_money(2460.36) == "$2,460"
        assert format_money(float("nan")) == "N/A"
        labels = describe_active_filters({"Gender": ["Male"], "City": []}, {"Off-scale feedback": True})
        assert labels == ["Gender: Male", "Excluding off-scale feedback"]


class TestDashboardApp:
    """Smoke tests that run the full Streamlit script headlessly."""

    APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "dashboard.py")

    def _run(self, **state: object) -> AppTest:
        app = AppTest.from_file(self.APP_PATH, default_timeout=60)
        for key, value in state.items():
            app.session_state[key] = value
        return app.run()

    def test_default_view_renders_every_tab(self) -> None:
        app = self._run()
        assert not app.exception
        assert len(app.tabs) == 6

    def test_filtered_view_renders(self) -> None:
        app = self._run(f_gender=["Female"], f_city=["Pune"], x_spike=True, x_mismatch=True)
        assert not app.exception
        assert not app.warning

    def test_empty_selection_shows_warning_instead_of_failing(self) -> None:
        app = self._run(f_tier=["Missing"], f_reach=["Omnichannel (Both)"], f_age=["60+ (Senior)"], f_city=["Delhi"],
                        f_gender=["Unknown"], x_inverted=True)
        assert not app.exception
