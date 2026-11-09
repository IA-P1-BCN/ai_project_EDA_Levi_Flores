"""Unit test suite for customer cleaning functions (Task X3, TDD).

Covers sentinel remediation, schema casting, date parsing, inversion flags,
contact channel validation, quality metrics derivation, and idempotency.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.cleaning import (
    clean_customers,
    clean_demographic_attributes,
    derive_quality_flags,
    parse_dates_and_inversions,
    reconstruct_customer_ids,
    remediate_numeric_sentinels,
    standardize_column_names,
    validate_cleaned_customers,
    validate_contact_channels,
)


class TestColumnStandardization:
    """Tests for standardize_column_names."""

    def test_renames_all_raw_columns(self, sample_raw_records: pd.DataFrame) -> None:
        standardized = standardize_column_names(sample_raw_records)
        expected_cols = [
            "customer_id",
            "name",
            "gender",
            "age",
            "city",
            "signup_date",
            "last_purchase_date",
            "purchase_amount",
            "feedback_score",
            "email",
            "phone_number",
            "country",
        ]
        assert list(standardized.columns) == expected_cols

    def test_idempotent_on_snake_case_columns(self, clean_baseline_record: pd.DataFrame) -> None:
        first_pass = standardize_column_names(clean_baseline_record)
        second_pass = standardize_column_names(first_pass)
        assert list(first_pass.columns) == list(second_pass.columns)


class TestCustomerIdReconstruction:
    """Tests for reconstruct_customer_ids."""

    def test_reconstructs_sequential_ids(self, sample_raw_records: pd.DataFrame) -> None:
        standardized = standardize_column_names(sample_raw_records)
        reconstructed = reconstruct_customer_ids(standardized)
        expected_ids = ["C00001", "C00002", "C00003", "C00004", "C00005"]
        assert list(reconstructed["customer_id"]) == expected_ids

    def test_handles_empty_dataframe(self) -> None:
        empty_df = pd.DataFrame(columns=["customer_id"])
        result = reconstruct_customer_ids(empty_df)
        assert len(result) == 0

    def test_raises_error_on_positional_mismatch(self) -> None:
        mismatched_df = pd.DataFrame({"customer_id": ["C99999"]})
        with pytest.raises(ValueError, match="positional alignment"):
            reconstruct_customer_ids(mismatched_df)


class TestDemographicCleaning:
    """Tests for clean_demographic_attributes."""

    def test_cleans_name_formatting(self, sample_raw_records: pd.DataFrame) -> None:
        df = reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        cleaned = clean_demographic_attributes(df)
        assert cleaned["name"].iloc[0] == "John Doe"
        assert cleaned["name"].iloc[1] == "Jane Smith"
        assert cleaned["name"].iloc[2] == "Unknown"
        assert cleaned["name"].iloc[3] == "Unknown"
        assert cleaned["name"].iloc[4] == "Alice Brown"

    def test_standardizes_gender_taxonomy(self, sample_raw_records: pd.DataFrame) -> None:
        df = reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        cleaned = clean_demographic_attributes(df)
        assert cleaned["gender"].iloc[0] == "Male"
        assert cleaned["gender"].iloc[1] == "Female"
        assert cleaned["gender"].iloc[2] == "Female"
        assert cleaned["gender"].iloc[3] == "Unknown"
        assert cleaned["gender"].iloc[4] == "Female"

    def test_replaces_empty_city_and_country_with_unknown(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        df = reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        cleaned = clean_demographic_attributes(df)
        assert cleaned["city"].iloc[0] == "Mumbai"
        assert cleaned["city"].iloc[2] == "Unknown"
        assert cleaned["city"].iloc[3] == "Unknown"
        assert cleaned["country"].iloc[3] == "Unknown"

    def test_raises_error_on_unmapped_gender(self) -> None:
        invalid_gender_df = pd.DataFrame(
            {
                "customer_id": ["C00001"],
                "name": ["Alex"],
                "gender": ["Alien"],
                "city": ["Mumbai"],
                "country": ["India"],
            }
        )
        with pytest.raises(ValueError, match="Unmapped gender"):
            clean_demographic_attributes(invalid_gender_df)


class TestNumericSentinelRemediation:
    """Tests for remediate_numeric_sentinels."""

    def test_remediates_age_sentinels(self, sample_raw_records: pd.DataFrame) -> None:
        df = clean_demographic_attributes(
            reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        )
        remediated = remediate_numeric_sentinels(df)

        # -5 and 200 must become NaN
        assert pd.isna(remediated["age"].iloc[0])
        assert pd.isna(remediated["age"].iloc[1])
        # 34 is valid
        assert remediated["age"].iloc[2] == 34.0
        # 105 (>100) must become NaN
        assert pd.isna(remediated["age"].iloc[3])
        # blank becomes NaN
        assert pd.isna(remediated["age"].iloc[4])

    def test_remediates_purchase_amount_sentinels(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        df = clean_demographic_attributes(
            reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        )
        remediated = remediate_numeric_sentinels(df)

        # -999 and N/A must become NaN
        assert pd.isna(remediated["purchase_amount"].iloc[0])
        assert pd.isna(remediated["purchase_amount"].iloc[1])
        # 1500.50 is valid
        assert remediated["purchase_amount"].iloc[2] == 1500.50
        # 0 must become NaN (orders must be positive)
        assert pd.isna(remediated["purchase_amount"].iloc[3])
        # blank becomes NaN
        assert pd.isna(remediated["purchase_amount"].iloc[4])

    def test_remediates_feedback_score_sentinels(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        df = clean_demographic_attributes(
            reconstruct_customer_ids(standardize_column_names(sample_raw_records))
        )
        remediated = remediate_numeric_sentinels(df)

        # -1 becomes NaN
        assert pd.isna(remediated["feedback_score"].iloc[0])
        # 10 is preserved as raw feedback score
        assert remediated["feedback_score"].iloc[1] == 10.0
        # 4 and 5 are valid
        assert remediated["feedback_score"].iloc[2] == 4.0
        assert remediated["feedback_score"].iloc[3] == 5.0
        assert pd.isna(remediated["feedback_score"].iloc[4])


class TestDateParsingAndInversions:
    """Tests for parse_dates_and_inversions."""

    def test_parses_dates_and_replaces_sentinels(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        df = remediate_numeric_sentinels(
            clean_demographic_attributes(
                reconstruct_customer_ids(standardize_column_names(sample_raw_records))
            )
        )
        parsed = parse_dates_and_inversions(df)

        # Record 0: valid dates parsed
        assert pd.notna(parsed["signup_date"].iloc[0])
        assert pd.notna(parsed["last_purchase_date"].iloc[0])

        # Record 1: not_a_date and missing -> NaT
        assert pd.isna(parsed["signup_date"].iloc[1])
        assert pd.isna(parsed["last_purchase_date"].iloc[1])


class TestContactChannelsValidation:
    """Tests for validate_contact_channels."""

    def test_validates_email_and_phone_regex(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        df = parse_dates_and_inversions(
            remediate_numeric_sentinels(
                clean_demographic_attributes(
                    reconstruct_customer_ids(standardize_column_names(sample_raw_records))
                )
            )
        )
        validated = validate_contact_channels(df)

        # Record 0: valid email, valid phone
        assert validated["email"].iloc[0] == "john@example.com"
        assert validated["phone_number"].iloc[0] == "9876543210"

        # Record 1: invalid email, invalid phone ('abc123')
        assert validated["email"].iloc[1] == "" or pd.isna(validated["email"].iloc[1])
        assert validated["phone_number"].iloc[1] == "" or pd.isna(validated["phone_number"].iloc[1])


class TestQualityFlagsDerivation:
    """Tests for derive_quality_flags."""

    def test_derives_all_ontology_flags(self, sample_raw_records: pd.DataFrame) -> None:
        df = validate_contact_channels(
            parse_dates_and_inversions(
                remediate_numeric_sentinels(
                    clean_demographic_attributes(
                        reconstruct_customer_ids(standardize_column_names(sample_raw_records))
                    )
                )
            )
        )
        flagged = derive_quality_flags(df)

        # Check column presence
        expected_flags = [
            "has_valid_email",
            "has_valid_phone",
            "is_date_inverted",
            "is_geo_mismatch",
            "is_age_missing",
            "is_purchase_missing",
            "is_score_10_spike",
            "feedback_score_1_to_5",
            "completeness_score",
        ]
        for f in expected_flags:
            assert f in flagged.columns

        # Record 0: signup=2022-01-01, last_purchase=2021-01-15 -> INVERTED
        assert bool(flagged["is_date_inverted"].iloc[0]) is True

        # Record 0: Mumbai paired with USA -> is_geo_mismatch == True
        assert bool(flagged["is_geo_mismatch"].iloc[0]) is True

        # Record 1: feedback_score = 10 -> is_score_10_spike == True, feedback_score_1_to_5 is NaN
        assert bool(flagged["is_score_10_spike"].iloc[1]) is True
        assert pd.isna(flagged["feedback_score_1_to_5"].iloc[1])

        # Record 2: feedback_score = 4 -> is_score_10_spike == False, feedback_score_1_to_5 == 4.0
        assert bool(flagged["is_score_10_spike"].iloc[2]) is False
        assert flagged["feedback_score_1_to_5"].iloc[2] == 4.0

        # Completeness score must be bounded in [0.0, 1.0]
        assert flagged["completeness_score"].between(0.0, 1.0).all()


class TestEndToEndAndIdempotency:
    """Tests for end-to-end clean_customers pipeline and idempotency."""

    def test_clean_customers_produces_valid_contract(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        cleaned = clean_customers(sample_raw_records)
        assert cleaned.shape[0] == 5
        assert cleaned.shape[1] == 21

        # Check no raw text sentinels exist
        sentinels = {"N/A", "-999", "not_a_date", "missing", "abc123"}
        for col in cleaned.columns:
            for s in sentinels:
                assert not (cleaned[col].astype(str) == s).any()

    def test_clean_customers_is_idempotent(
        self, sample_raw_records: pd.DataFrame
    ) -> None:
        pass1 = clean_customers(sample_raw_records)
        pass2 = clean_customers(pass1)
        pd.testing.assert_frame_equal(pass1, pass2)

    def test_validate_cleaned_customers_contract_enforcement(
        self, clean_baseline_record: pd.DataFrame
    ) -> None:
        cleaned = clean_customers(clean_baseline_record)
        # Should pass with no exception
        validate_cleaned_customers(cleaned, expected_rows=1)

        # Tampering with invalid sentinel must raise AssertionError
        tampered = cleaned.copy()
        tampered["age"] = -5.0
        with pytest.raises((ValueError, AssertionError)):
            validate_cleaned_customers(tampered, expected_rows=1)
