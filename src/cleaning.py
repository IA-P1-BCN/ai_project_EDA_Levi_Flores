"""Deterministic data cleaning, sentinel remediation, and imputation rationale for Customer Messy Data.

Implements the canonical cleaning protocol from ``.agents/skills/data-cleaning/SKILL.md``
and ``specs/ontology.md`` (sections 2, 3.1, and 3.2), producing the 21-column ``v2`` cleaned
dataset alongside the ``M1`` methodological decision audit and variance-impact experiments.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
RAW_DATA_PATH: Path = REPO_ROOT / "data" / "raw" / "messy_customer_data.csv"
PROCESSED_DIR: Path = REPO_ROOT / "data" / "processed"
SUMMARIES_DIR: Path = PROCESSED_DIR / "summaries"

CLEAN_V2_FILENAME: str = "customers_clean_v2.csv"
M1_AUDIT_FILENAME: str = "m1_cleaning_decisions_audit.csv"
M1_IMPUTATION_IMPACT_FILENAME: str = "m1_imputation_variance_impact.csv"

EXPECTED_ROWS: int = 10_000

COLUMN_MAPPING: dict[str, str] = {
    "CustomerID": "customer_id",
    "Name": "name",
    "Gender": "gender",
    "Age": "age",
    "City": "city",
    "Signup_Date": "signup_date",
    "Last_purchase_date": "last_purchase_date",
    "purchase_amount": "purchase_amount",
    "feedback_score": "feedback_score",
    "email": "email",
    "Phone_number": "phone_number",
    "Country": "country",
}

CORE_COLUMNS: tuple[str, ...] = (
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
)

QUALITY_FLAG_COLUMNS: tuple[str, ...] = (
    "has_valid_email",
    "has_valid_phone",
    "is_date_inverted",
    "is_geo_mismatch",
    "is_age_missing",
    "is_purchase_missing",
    "is_score_10_spike",
    "feedback_score_1_to_5",
    "completeness_score",
)

V2_COLUMNS: tuple[str, ...] = (*CORE_COLUMNS, *QUALITY_FLAG_COLUMNS)

GENDER_CATEGORIES: list[str] = ["Male", "Female", "Unknown"]
CITY_CATEGORIES: list[str] = [
    "Hyderabad",
    "Mumbai",
    "Pune",
    "Bangalore",
    "Chennai",
    "Delhi",
    "Ahmedabad",
    "Kolkata",
    "Unknown",
]
COUNTRY_CATEGORIES: list[str] = ["USA", "Australia", "Canada", "UK", "India", "Unknown"]
NON_INDIAN_COUNTRIES: tuple[str, ...] = ("USA", "Australia", "Canada", "UK")

GENDER_MAP: dict[str, str] = {
    "m": "Male",
    "male": "Male",
    "f": "Female",
    "female": "Female",
    "": "Unknown",
    "unknown": "Unknown",
}

COUNTRY_MAP: dict[str, str] = {
    "usa": "USA",
    "australia": "Australia",
    "canada": "Canada",
    "uk": "UK",
    "india": "India",
    "": "Unknown",
    "unknown": "Unknown",
}

AGE_MIN: float = 18.0
AGE_MAX: float = 100.0
PURCHASE_MIN_EXCLUSIVE: float = 0.0
PURCHASE_MAX_INCLUSIVE: float = 10_000.0
VALID_FEEDBACK_VALUES: frozenset[float] = frozenset({1.0, 2.0, 3.0, 4.0, 5.0, 10.0})
DATE_MIN: date = date(2020, 1, 1)

CUSTOMER_ID_REGEX: re.Pattern[str] = re.compile(r"^C\d{5}$")
EMAIL_REGEX: re.Pattern[str] = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX: re.Pattern[str] = re.compile(r"^\d{10}$")


def _clean_str_series(series: pd.Series) -> pd.Series:
    """Convert any string, object, or categorical series into stripped strings with nulls mapped to ''."""
    obj = series.astype("object")
    return obj.where(obj.notna(), "").astype(str).str.strip()


def _to_categorical(series: pd.Series, canonical_order: list[str]) -> pd.Series:
    """Cast a non-null string series to unordered Categorical preserving canonical order."""
    present = [str(v) for v in series.dropna().unique()]
    extras = [v for v in present if v not in canonical_order]
    categories = [*canonical_order, *extras]
    return series.astype(pd.CategoricalDtype(categories=categories, ordered=False))


def _parse_customer_dates(series: pd.Series) -> pd.Series:
    """Parse DD/MM/YYYY or ISO YYYY-MM-DD strings into datetime64[us] within [2020-01-01, today]."""
    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = series.astype("datetime64[us]")
    else:
        cleaned = _clean_str_series(series).replace(
            {"not_a_date": np.nan, "missing": np.nan, "": np.nan, "NaT": np.nan, "nan": np.nan}
        )
        parsed_dmy = pd.to_datetime(cleaned, format="%d/%m/%Y", errors="coerce")
        needs_iso = cleaned.notna() & parsed_dmy.isna()
        if needs_iso.any():
            iso_parsed = pd.to_datetime(cleaned.where(needs_iso), format="%Y-%m-%d", errors="coerce")
            parsed_dmy = parsed_dmy.where(~needs_iso, iso_parsed)
        parsed = parsed_dmy.astype("datetime64[us]")

    min_ts = pd.Timestamp(DATE_MIN)
    max_ts = pd.Timestamp(date.today())
    return parsed.where((parsed >= min_ts) & (parsed <= max_ts), pd.NaT).astype("datetime64[us]")


def load_raw_customers(path: Path | None = None) -> pd.DataFrame:
    """Load ``data/raw/messy_customer_data.csv`` with ``keep_default_na=False`` for literal auditing.

    Preserves empty strings (``""``) as distinct from literal text sentinels such as ``"N/A"``,
    ``"not_a_date"``, ``"missing"``, ``"abc123"``, and ``"0"``.
    """
    csv_path = path if path is not None else RAW_DATA_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw customer dataset not found: {csv_path}")
    return pd.read_csv(csv_path, keep_default_na=False)


def validate_cleaned_customers(df: pd.DataFrame, *, expected_rows: int | None = EXPECTED_ROWS) -> None:
    """Assert post-cleaning schema, primary-key uniqueness, and ontology domain bounds."""
    if expected_rows is not None:
        assert len(df) == expected_rows, f"Expected {expected_rows:,} rows, got {len(df):,}"
    assert len(df) > 0, "Cleaned DataFrame must not be empty"
    assert list(df.columns) == list(V2_COLUMNS), f"Unexpected v2 schema columns: {list(df.columns)}"

    assert df["customer_id"].is_unique, "Primary key customer_id must have zero duplicates"
    assert df["customer_id"].str.match(CUSTOMER_ID_REGEX).all(), "Malformed customer_id values remain"
    assert (df["name"].str.len() > 0).all(), "Blank name values remain (expected 'Unknown')"

    assert set(df["gender"].unique()).issubset(set(GENDER_CATEGORIES)), "Unmapped gender labels remain"
    assert set(df["city"].unique()).issubset(set(CITY_CATEGORIES)), "Unexpected city labels remain"
    assert set(df["country"].unique()).issubset(set(COUNTRY_CATEGORIES)), "Unexpected country labels remain"

    valid_ages = df["age"].dropna()
    assert valid_ages.between(AGE_MIN, AGE_MAX).all(), "Out-of-range values remain in age"

    valid_amounts = df["purchase_amount"].dropna()
    assert ((valid_amounts > PURCHASE_MIN_EXCLUSIVE) & (valid_amounts <= PURCHASE_MAX_INCLUSIVE)).all(), (
        "Out-of-range values remain in purchase_amount"
    )

    valid_scores = df["feedback_score"].dropna()
    assert valid_scores.isin(VALID_FEEDBACK_VALUES).all(), "Invalid values remain in feedback_score"

    valid_scores_1_to_5 = df["feedback_score_1_to_5"].dropna()
    assert valid_scores_1_to_5.between(1.0, 5.0).all(), "Out-of-range values remain in feedback_score_1_to_5"

    valid_emails = df["email"].dropna()
    assert valid_emails.str.match(EMAIL_REGEX).all(), "Malformed email addresses remain"

    valid_phones = df["phone_number"].dropna()
    assert valid_phones.str.match(PHONE_REGEX).all(), "Malformed phone_number values remain"

    assert df["completeness_score"].notna().all(), "completeness_score must be non-null"
    assert df["completeness_score"].between(0.0, 1.0).all(), "completeness_score outside [0.0, 1.0]"


def clean_customers(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw or partially cleaned customer records into the 21-column ``v2`` schema.

    The transformation is pure, deterministic, and idempotent: calling
    ``clean_customers(clean_customers(df_raw))`` yields an identical DataFrame.
    """
    df = df_raw.copy()
    df = df.rename(columns=COLUMN_MAPPING)

    missing_cols = [col for col in CORE_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input DataFrame is missing required customer columns: {missing_cols}")

    # Verify 1-to-1 positional alignment on non-empty numeric/prefixed IDs when raw IDs exist
    raw_id_str = _clean_str_series(df["customer_id"])
    non_empty_mask = raw_id_str != ""
    if non_empty_mask.any():
        stripped_digits = raw_id_str.loc[non_empty_mask].str.lstrip("C").str.lstrip("0")
        expected_digits = pd.Series(range(1, len(df) + 1), index=df.index).loc[non_empty_mask].astype(str)
        if not (stripped_digits == expected_digits).all():
            raise ValueError("Non-empty CustomerID entries violate 1-based positional alignment")

    # 1. Reconstruct uniform 5-digit primary key (C00001..C10000)
    df["customer_id"] = pd.Series([f"C{i:05d}" for i in range(1, len(df) + 1)], index=df.index, dtype="str")

    # 2. Clean text & categorical attributes, assigning explicit 'Unknown' to blanks
    name_str = _clean_str_series(df["name"]).str.title()
    df["name"] = name_str.replace({"": "Unknown", "Nan": "Unknown", "None": "Unknown"}).astype("str")

    gender_str = _clean_str_series(df["gender"]).str.lower()
    gender_mapped = gender_str.map(GENDER_MAP)
    if gender_mapped.isna().any():
        unmapped = sorted(gender_str.loc[gender_mapped.isna()].unique().tolist())
        raise ValueError(f"Unmapped gender values encountered: {unmapped}")
    df["gender"] = _to_categorical(gender_mapped, GENDER_CATEGORIES)

    city_str = _clean_str_series(df["city"]).str.title()
    city_cleaned = city_str.replace({"": "Unknown", "Nan": "Unknown", "None": "Unknown"})
    df["city"] = _to_categorical(city_cleaned, CITY_CATEGORIES)

    country_str = _clean_str_series(df["country"]).str.lower()
    country_mapped = country_str.map(COUNTRY_MAP)
    if country_mapped.isna().any():
        unmapped_countries = sorted(country_str.loc[country_mapped.isna()].unique().tolist())
        raise ValueError(f"Unmapped country values encountered: {unmapped_countries}")
    df["country"] = _to_categorical(country_mapped, COUNTRY_CATEGORIES)

    # 3. Remediate numeric sentinels (-5, 200 in age; N/A, -999 in purchase_amount; -1 in feedback_score)
    if pd.api.types.is_numeric_dtype(df["age"]):
        age_num = df["age"].astype("float64")
    else:
        age_num = pd.to_numeric(_clean_str_series(df["age"]).replace({"": np.nan}), errors="coerce")
    df["age"] = age_num.where((age_num >= AGE_MIN) & (age_num <= AGE_MAX), np.nan).astype("float64")

    if pd.api.types.is_numeric_dtype(df["purchase_amount"]):
        amt_num = df["purchase_amount"].astype("float64")
    else:
        amt_clean = _clean_str_series(df["purchase_amount"]).replace({"N/A": np.nan, "-999": np.nan, "": np.nan})
        amt_num = pd.to_numeric(amt_clean, errors="coerce")
    df["purchase_amount"] = amt_num.where(
        (amt_num > PURCHASE_MIN_EXCLUSIVE) & (amt_num <= PURCHASE_MAX_INCLUSIVE), np.nan
    ).astype("float64")

    if pd.api.types.is_numeric_dtype(df["feedback_score"]):
        fb_num = df["feedback_score"].astype("float64")
    else:
        fb_clean = _clean_str_series(df["feedback_score"]).replace({"-1": np.nan, "": np.nan})
        fb_num = pd.to_numeric(fb_clean, errors="coerce")
    df["feedback_score"] = fb_num.where(fb_num.isin(VALID_FEEDBACK_VALUES), np.nan).astype("float64")

    # 4. Parse dates (%d/%m/%Y -> datetime64[us])
    df["signup_date"] = _parse_customer_dates(df["signup_date"])
    df["last_purchase_date"] = _parse_customer_dates(df["last_purchase_date"])

    # 5. Validate contact channels against ontology regex contracts
    email_str = _clean_str_series(df["email"])
    df["email"] = email_str.where(email_str.str.match(EMAIL_REGEX), np.nan).astype("str")

    phone_str = _clean_str_series(df["phone_number"])
    df["phone_number"] = phone_str.where(phone_str.str.match(PHONE_REGEX), np.nan).astype("str")

    # 6. Derive all 9 DataCleanerAgent-owned data-quality flags (specs/ontology.md section 3.2)
    df["has_valid_email"] = df["email"].notna().astype(bool)
    df["has_valid_phone"] = df["phone_number"].notna().astype(bool)
    df["is_date_inverted"] = (
        df["signup_date"].notna()
        & df["last_purchase_date"].notna()
        & (df["last_purchase_date"] < df["signup_date"])
    ).astype(bool)
    df["is_geo_mismatch"] = (
        (df["city"] != "Unknown") & df["country"].isin(NON_INDIAN_COUNTRIES)
    ).astype(bool)
    df["is_age_missing"] = df["age"].isna().astype(bool)
    df["is_purchase_missing"] = df["purchase_amount"].isna().astype(bool)
    df["is_score_10_spike"] = df["feedback_score"].eq(10.0).astype(bool)
    df["feedback_score_1_to_5"] = df["feedback_score"].where(df["feedback_score"] <= 5.0, np.nan).astype("float64")

    valid_core_attributes = (
        df["customer_id"].notna().astype(int)
        + (df["name"] != "Unknown").astype(int)
        + (df["gender"] != "Unknown").astype(int)
        + df["age"].notna().astype(int)
        + (df["city"] != "Unknown").astype(int)
        + df["signup_date"].notna().astype(int)
        + df["last_purchase_date"].notna().astype(int)
        + df["purchase_amount"].notna().astype(int)
        + df["feedback_score"].notna().astype(int)
        + df["email"].notna().astype(int)
        + df["phone_number"].notna().astype(int)
        + (df["country"] != "Unknown").astype(int)
    )
    df["completeness_score"] = (valid_core_attributes / 12.0).astype("float64").round(6)

    df = df.loc[:, list(V2_COLUMNS)]

    expected = EXPECTED_ROWS if len(df_raw) == EXPECTED_ROWS else len(df_raw)
    validate_cleaned_customers(df, expected_rows=expected)
    return df


def build_cleaning_decisions_audit(df_raw: pd.DataFrame, df_clean: pd.DataFrame) -> pd.DataFrame:
    """Build the 12-row ``M1`` methodological cleaning and imputation audit table.

    Quantifies literal blanks, domain sentinels/corrupted entries, valid coverage,
    remediation action, imputation choice, and statistical rationale per attribute.
    """
    total = len(df_raw)
    if total == 0 or len(df_clean) != total:
        raise ValueError("df_raw and df_clean must be non-empty and have matching row counts")

    valid_counts: dict[str, int] = {
        "CustomerID": int((_clean_str_series(df_raw["CustomerID"]) != "").sum()),
        "Name": int((df_clean["name"] != "Unknown").sum()),
        "Gender": int((df_clean["gender"] != "Unknown").sum()),
        "Age": int(df_clean["age"].notna().sum()),
        "City": int((df_clean["city"] != "Unknown").sum()),
        "Signup_Date": int(df_clean["signup_date"].notna().sum()),
        "Last_purchase_date": int(df_clean["last_purchase_date"].notna().sum()),
        "purchase_amount": int(df_clean["purchase_amount"].notna().sum()),
        "feedback_score": int(df_clean["feedback_score"].notna().sum()),
        "email": int(df_clean["email"].notna().sum()),
        "Phone_number": int(df_clean["phone_number"].notna().sum()),
        "Country": int((df_clean["country"] != "Unknown").sum()),
    }

    metadata: dict[str, tuple[str, str, str, str]] = {
        "CustomerID": (
            "str",
            "Reconstruct sequential C00001..C10000 primary key from 1-based row index",
            "Deterministic positional reconstruction (100% lossless)",
            (
                "0 full-row duplicates and 0 colliding IDs; all 7,621 non-blank entries (2,561 'C'-prefixed, "
                "5,060 bare digits) match row_idx + 1 exactly, enabling lossless PK recovery."
            ),
        ),
        "Name": (
            "str",
            "Strip whitespace, standardize to Title Case, map blanks to 'Unknown'",
            "Explicit 'Unknown' string token",
            (
                "Given names are non-unique nominal identifiers (10 distinct Indian first names); mode imputation "
                "would fabricate identity, whereas 'Unknown' preserves row retention."
            ),
        ),
        "Gender": (
            "category",
            "Trim whitespace, fold 6 lexical variants (M/male/Male, F/female/Female), map blanks to 'Unknown'",
            "Explicit 'Unknown' category level",
            (
                "24.55% missingness makes mode imputation ('Male') severely biased (+64.6% artificial surge in Male); "
                "explicit 'Unknown' keeps groupby(observed=True) exhaustive."
            ),
        ),
        "Age": (
            "float64",
            "Coerce sentinels (-5 [2,506], 200 [2,453]) and blanks to NaN; add is_age_missing flag",
            "NaN retention + boolean missingness indicator (no single-value imputation)",
            (
                "With 75.35% missingness (MCAR consistent), median/mean imputation collapses SD by ~50.3% "
                "(15.30 -> 7.60 yrs) and collapses IQR by 100% (27.00 -> 0.00 yrs)."
            ),
        ),
        "City": (
            "category",
            "Trim whitespace, Title-Case 8 Indian metros, map blanks to 'Unknown'",
            "Explicit 'Unknown' category level",
            (
                "Highest raw completeness (88.70%) and uniform spread across 8 Indian cities (~12.5% of known each); "
                "'Unknown' avoids inflating Hyderabad (the marginal mode)."
            ),
        ),
        "Signup_Date": (
            "datetime64[us]",
            "Replace 'not_a_date' (2,475) and blanks with NaT; parse strict DD/MM/YYYY format",
            "NaT retention",
            (
                "50.04% of timestamps are missing/corrupted; interpolating registration dates would fabricate "
                "acquisition cohorts and distort temporal trend analysis (M6)."
            ),
        ),
        "Last_purchase_date": (
            "datetime64[us]",
            "Replace 'missing' (3,366) and blanks with NaT; parse DD/MM/YYYY; add is_date_inverted flag",
            "NaT retention + is_date_inverted flag (829 inverted rows)",
            (
                "66.52% missingness plus 829/1,684 (49.23%) dual-date rows with last_purchase_date < signup_date; "
                "flagging preserves raw timestamps while protecting tenure_days (n=855)."
            ),
        ),
        "purchase_amount": (
            "float64",
            "Coerce sentinels ('N/A' [2,533], '-999' [2,501]) and blanks to NaN; add is_purchase_missing flag",
            "NaN retention + boolean missingness indicator (no single-value imputation)",
            (
                "With 75.34% missingness (MCAR consistent), median imputation shrinks SD by 50.35% ($1,442.83 -> "
                "$716.40), collapses IQR to $0.00, and fabricates $18.54M in unverified revenue."
            ),
        ),
        "feedback_score": (
            "float64",
            "Coerce '-1' (2,489) and blanks to NaN; add is_score_10_spike and feedback_score_1_to_5",
            "NaN retention + dual scale representation (full valid vs. 1-5 Likert)",
            (
                "49.51% missingness plus bimodal scale anomaly: 2,521 valid rows equal 10 (49.93% of valid); "
                "remapping 10 -> 5 would falsely inflate Promoters by +266.8% (945 -> 3,466)."
            ),
        ),
        "email": (
            "str",
            "Validate against RFC-style regex (^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$); set malformed (2,422) to NaN",
            "NaN retention + has_valid_email reachability flag",
            (
                "Contact addresses cannot be statistically imputed; 2,422 strings lacking '@' (e.g., user1mail.com) "
                "are non-routable and must be excluded from CRM reachability (25.12% valid)."
            ),
        ),
        "Phone_number": (
            "str",
            "Validate 10-digit mobile regex (^\\d{10}$); set 'abc123' (2,586) and '0' (2,460) to NaN",
            "NaN retention + has_valid_phone reachability flag",
            (
                "Phone numbers are unique contact identifiers; removing placeholders ('abc123', '0') isolates "
                "the 25.10% SMS-reachable cohort and prevents failed campaign dispatches."
            ),
        ),
        "Country": (
            "category",
            "Trim whitespace, standardize 5 country names, map blanks to 'Unknown'; add is_geo_mismatch flag",
            "Explicit 'Unknown' category + is_geo_mismatch flag (5,888 rows)",
            (
                "80.13% of dual-known geo rows pair an Indian city with USA/Australia/Canada/UK (chi2 p=0.8888); "
                "flagging preserves reported country for audit (A3) without overwriting raw fields."
            ),
        ),
    }

    records: list[dict[str, object]] = []
    for raw_col, clean_col in COLUMN_MAPPING.items():
        s_raw = _clean_str_series(df_raw[raw_col])
        blank_cnt = int((s_raw == "").sum())
        valid_cnt = valid_counts[raw_col]
        total_invalid = total - valid_cnt
        sentinel_cnt = total_invalid - blank_cnt
        target_dtype, action_taken, imputation_choice, rationale = metadata[raw_col]

        records.append(
            {
                "raw_column": raw_col,
                "clean_column": clean_col,
                "target_dtype": target_dtype,
                "blank_count": blank_cnt,
                "sentinel_count": sentinel_cnt,
                "total_invalid": total_invalid,
                "invalid_pct": round(total_invalid / total * 100.0, 2),
                "valid_count": valid_cnt,
                "valid_pct": round(valid_cnt / total * 100.0, 2),
                "action_taken": action_taken,
                "imputation_choice": imputation_choice,
                "methodological_rationale": rationale,
            }
        )

    return pd.DataFrame(records)


def compute_imputation_variance_impact(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Quantify variance/IQR distortion from single-value imputation and verify MCAR consistency.

    Compares ``NaN Retention (Chosen)``, ``Single Median Imputation (Rejected)``, and
    ``Single Mean Imputation (Rejected)`` on ``age`` and ``purchase_amount``, paired with
    two-sample Welch's t-test and Mann-Whitney U tests across missingness indicators.
    """
    total_rows = len(df_clean)
    if total_rows == 0:
        raise ValueError("df_clean must not be empty")

    is_age_miss = df_clean["age"].isna()
    is_pa_miss = df_clean["purchase_amount"].isna()

    pa_when_age_miss = df_clean.loc[is_age_miss, "purchase_amount"].dropna()
    pa_when_age_obs = df_clean.loc[~is_age_miss, "purchase_amount"].dropna()
    t_pa, p_t_pa = stats.ttest_ind(pa_when_age_miss, pa_when_age_obs, equal_var=False)
    u_pa, p_u_pa = stats.mannwhitneyu(pa_when_age_miss, pa_when_age_obs, alternative="two-sided")

    age_when_pa_miss = df_clean.loc[is_pa_miss, "age"].dropna()
    age_when_pa_obs = df_clean.loc[~is_pa_miss, "age"].dropna()
    t_age, p_t_age = stats.ttest_ind(age_when_pa_miss, age_when_pa_obs, equal_var=False)
    u_age, p_u_age = stats.mannwhitneyu(age_when_pa_miss, age_when_pa_obs, alternative="two-sided")

    mcar_specs: dict[str, dict[str, object]] = {
        "age": {
            "mcar_check_target": "purchase_amount by is_age_missing (True vs False)",
            "n_target_when_missing": len(pa_when_age_miss),
            "n_target_when_observed": len(pa_when_age_obs),
            "target_mean_when_missing": round(float(pa_when_age_miss.mean()), 4),
            "target_mean_when_observed": round(float(pa_when_age_obs.mean()), 4),
            "welch_t_stat": round(float(t_pa), 4),
            "welch_p_value": round(float(p_t_pa), 4),
            "mannwhitney_u_stat": round(float(u_pa), 2),
            "mannwhitney_p_value": round(float(p_u_pa), 4),
        },
        "purchase_amount": {
            "mcar_check_target": "age by is_purchase_missing (True vs False)",
            "n_target_when_missing": len(age_when_pa_miss),
            "n_target_when_observed": len(age_when_pa_obs),
            "target_mean_when_missing": round(float(age_when_pa_miss.mean()), 4),
            "target_mean_when_observed": round(float(age_when_pa_obs.mean()), 4),
            "welch_t_stat": round(float(t_age), 4),
            "welch_p_value": round(float(p_t_age), 4),
            "mannwhitney_u_stat": round(float(u_age), 2),
            "mannwhitney_p_value": round(float(p_u_age), 4),
        },
    }

    rows: list[dict[str, object]] = []
    for col in ("age", "purchase_amount"):
        s_valid = df_clean[col].dropna().astype("float64")
        missing_pct = round(float(df_clean[col].isna().mean() * 100.0), 2)
        base_std = float(s_valid.std(ddof=1))
        base_q1, _base_med, base_q3 = (float(v) for v in s_valid.quantile([0.25, 0.5, 0.75]))
        base_iqr = base_q3 - base_q1

        strategies: list[tuple[str, pd.Series]] = [
            ("NaN Retention (Chosen)", s_valid),
            ("Single Median Imputation (Rejected)", df_clean[col].fillna(float(s_valid.median()))),
            ("Single Mean Imputation (Rejected)", df_clean[col].fillna(float(s_valid.mean()))),
        ]

        mcar = mcar_specs[col]
        is_mcar = float(mcar["welch_p_value"]) > 0.05 and float(mcar["mannwhitney_p_value"]) > 0.05
        mcar_verdict = "MCAR consistent (p > 0.05)" if is_mcar else "Missingness shift detected (p <= 0.05)"

        for strategy_name, series in strategies:
            cur_std = float(series.std(ddof=1))
            q1, med, q3 = (float(v) for v in series.quantile([0.25, 0.5, 0.75]))
            cur_iqr = q3 - q1
            std_change_pct = 0.0 if strategy_name.startswith("NaN") else (cur_std - base_std) / base_std * 100.0
            iqr_change_pct = 0.0 if strategy_name.startswith("NaN") else (cur_iqr - base_iqr) / base_iqr * 100.0

            rows.append(
                {
                    "variable": col,
                    "missing_pct": missing_pct,
                    "strategy": strategy_name,
                    "n_evaluated": len(series),
                    "mean": round(float(series.mean()), 4),
                    "std": round(cur_std, 4),
                    "std_change_pct": round(std_change_pct, 2),
                    "q1": round(q1, 4),
                    "median": round(med, 4),
                    "q3": round(q3, 4),
                    "iqr": round(cur_iqr, 4),
                    "iqr_change_pct": round(iqr_change_pct, 2),
                    **mcar,
                    "mcar_conclusion": mcar_verdict,
                }
            )

    return pd.DataFrame(rows)


def export_m1_artifacts(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate and save ``customers_clean_v2.csv`` and the two ``M1`` summary CSVs."""
    target_processed_dir = output_dir if output_dir is not None else PROCESSED_DIR
    target_summaries_dir = target_processed_dir / "summaries"
    target_processed_dir.mkdir(parents=True, exist_ok=True)
    target_summaries_dir.mkdir(parents=True, exist_ok=True)

    df_raw = load_raw_customers()
    df_clean_v2 = clean_customers(df_raw)
    validate_cleaned_customers(df_clean_v2, expected_rows=EXPECTED_ROWS)

    audit_df = build_cleaning_decisions_audit(df_raw, df_clean_v2)
    impact_df = compute_imputation_variance_impact(df_clean_v2)

    v2_path = target_processed_dir / CLEAN_V2_FILENAME
    audit_path = target_summaries_dir / M1_AUDIT_FILENAME
    impact_path = target_summaries_dir / M1_IMPUTATION_IMPACT_FILENAME

    df_clean_v2.to_csv(v2_path, index=False)
    audit_df.to_csv(audit_path, index=False)
    impact_df.to_csv(impact_path, index=False)

    return {
        "customers_clean_v2": v2_path,
        "m1_cleaning_decisions_audit": audit_path,
        "m1_imputation_variance_impact": impact_path,
    }


if __name__ == "__main__":
    exported = export_m1_artifacts()
    for artifact_name, artifact_path in exported.items():
        print(f"Exported {artifact_name}: {artifact_path}")
