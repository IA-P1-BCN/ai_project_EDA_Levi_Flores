"""Unit test suite for analysis, feature engineering, and metrics normalization (Task X3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import (
    compute_a1_normalized_metrics_comparison,
    compute_a4_transformation_statistics,
    compute_a5_segment_profiles,
)
from src.cleaning import clean_customers
from src.features import (
    engineer_features,
    enrich_with_external_metro_data,
    validate_enriched_customers,
)


@pytest.fixture
def clean_df_for_features(clean_baseline_record: pd.DataFrame) -> pd.DataFrame:
    """Return a single cleaned record augmented to test feature engineering."""
    cleaned = clean_customers(clean_baseline_record)
    return cleaned


class TestFeatureEngineering:
    """Tests for feature engineering transformations."""

    def test_engineers_all_ontology_features(
        self, clean_df_for_features: pd.DataFrame
    ) -> None:
        enriched = engineer_features(clean_df_for_features)
        validate_enriched_customers(enriched, expected_rows=1, version="v1")

        expected_features = [
            "age_group",
            "spend_tier",
            "feedback_tier",
            "contact_reachability_tier",
            "customer_tenure_days",
            "log_purchase_amount",
        ]
        for feat in expected_features:
            assert feat in enriched.columns

        # Record 0 has age=28 -> Young Adult
        assert str(enriched["age_group"].iloc[0]) == "18-29 (Young Adult)"
        # spend=1250.00 -> Medium ($1,200-$3,500)
        assert str(enriched["spend_tier"].iloc[0]) == "Medium ($1,200-$3,500)"
        # feedback=4 -> Promoter (4-5)
        assert str(enriched["feedback_tier"].iloc[0]) == "Promoter (4-5)"
        # email & phone both valid -> Omnichannel (Both)
        assert str(enriched["contact_reachability_tier"].iloc[0]) == "Omnichannel (Both)"
        # log_purchase_amount == ln(1 + 1250)
        np.testing.assert_allclose(
            enriched["log_purchase_amount"].iloc[0],
            np.log1p(1250.00),
            rtol=1e-5,
        )

    def test_tenure_is_nan_when_date_inverted(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        cleaned = clean_customers(sample_raw_records)
        enriched = engineer_features(cleaned)

        # Record 0 has inverted dates -> customer_tenure_days must be NaN
        assert bool(cleaned["is_date_inverted"].iloc[0]) is True
        assert pd.isna(enriched["customer_tenure_days"].iloc[0])


class TestAuxiliaryMetropolitanEnrichment:
    """Tests for external metadata enrichment."""

    def test_enriches_with_external_metro_catalog(
        self, clean_df_for_features: pd.DataFrame
    ) -> None:
        enriched_v1 = engineer_features(clean_df_for_features)
        enriched_v2 = enrich_with_external_metro_data(enriched_v1)
        validate_enriched_customers(enriched_v2, expected_rows=1, version="v2")

        assert "metro_region" in enriched_v2.columns
        assert "metro_state" in enriched_v2.columns
        assert "metro_population_m" in enriched_v2.columns

        # Mumbai is in West region, Maharashtra, ~20.96M population
        assert str(enriched_v2["metro_region"].iloc[0]) == "West"
        assert str(enriched_v2["metro_state"].iloc[0]) == "Maharashtra"
        assert enriched_v2["metro_population_m"].iloc[0] > 15.0


class TestAnalyticalAggregationsAndMetrics:
    """Tests for KPI-3 and segment summary functions."""

    def test_compute_a1_normalized_metrics_comparison(
        self, clean_df_for_features: pd.DataFrame
    ) -> None:
        enriched_v2 = enrich_with_external_metro_data(
            engineer_features(clean_df_for_features)
        )
        a1_df = compute_a1_normalized_metrics_comparison(enriched_v2)
        assert len(a1_df) > 0
        assert "revenue_per_1k_registered_usd" in a1_df.columns
        assert "headcount_bias_factor" in a1_df.columns

    def test_compute_a4_transformation_statistics(
        self, clean_df_for_features: pd.DataFrame
    ) -> None:
        enriched_v2 = enrich_with_external_metro_data(
            engineer_features(clean_df_for_features)
        )
        a4_df = compute_a4_transformation_statistics(enriched_v2)
        assert len(a4_df) > 0
        assert "skewness" in a4_df.columns
        assert "kurtosis" in a4_df.columns

    def test_compute_a5_segment_profiles(
        self, clean_df_for_features: pd.DataFrame
    ) -> None:
        enriched_v2 = enrich_with_external_metro_data(
            engineer_features(clean_df_for_features)
        )
        a5_df = compute_a5_segment_profiles(enriched_v2)
        assert len(a5_df) > 0
        assert "customer_count" in a5_df.columns
        assert "total_revenue_usd" in a5_df.columns
