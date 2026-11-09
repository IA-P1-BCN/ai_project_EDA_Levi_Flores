"""Unit test suite for the executive interactive dashboard (Task X2, X3).

Verifies dataset loading, interactive filtering logic, anomaly toggles, and executive
KPI metric calculation.
"""

from __future__ import annotations

import pandas as pd
import pytest

from app.dashboard import (
    apply_filters,
    compute_kpi_summary,
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
