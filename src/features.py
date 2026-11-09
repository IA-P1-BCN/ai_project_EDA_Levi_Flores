"""Analytical feature engineering for Customer Messy Data EDA (Task M4).

Implements the exact six ``StatisticalAnalystAgent``-owned engineered features defined
in ``specs/ontology.md`` section 3.2 on top of ``customers_clean_v2.csv`` (21 columns),
producing the 27-column ``customers_enriched_v1.csv`` dataset and the ``M4`` profile table.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis import (
    AGE_GROUP_BINS,
    AGE_GROUP_CATEGORIES,
    AGE_GROUP_LABELS,
    BOOL_FLAG_COLUMNS,
    CITY_CATEGORIES,
    COUNTRY_CATEGORIES,
    GENDER_CATEGORIES,
    PROCESSED_DIR,
    REACHABILITY_TIER_CATEGORIES,
    load_clean_customers,
)

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
EXTERNAL_CITIES_PATH: Path = REPO_ROOT / "data" / "external" / "indian_cities_metadata.csv"
ENRICHED_V1_FILENAME: str = "customers_enriched_v1.csv"
ENRICHED_V2_FILENAME: str = "customers_enriched_v2.csv"
M4_SUMMARY_FILENAME: str = "m4_engineered_features_summary.csv"
EXPECTED_ROWS: int = 10_000

METRO_REGION_CATEGORIES: list[str] = ["West", "South", "North", "East", "Unknown"]
METRO_STATE_CATEGORIES: list[str] = [
    "Maharashtra",
    "Delhi (NCR)",
    "Karnataka",
    "Telangana",
    "Gujarat",
    "Tamil Nadu",
    "West Bengal",
    "Unknown",
]

A2_FEATURE_COLUMNS: tuple[str, ...] = ("metro_region", "metro_state", "metro_population_m")

SPEND_TIER_CATEGORIES: list[str] = [
    "Low (<$1,200)",
    "Medium ($1,200-$3,500)",
    "High (>$3,500)",
    "Missing",
]

FEEDBACK_TIER_CATEGORIES: list[str] = [
    "Detractor (1-2)",
    "Passive (3)",
    "Promoter (4-5)",
    "Scale-10 Spike (10)",
    "Missing",
]

V2_BASE_COLUMNS: tuple[str, ...] = (
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

ENGINEERED_COLUMNS: tuple[str, ...] = (
    "age_group",
    "spend_tier",
    "feedback_tier",
    "contact_reachability_tier",
    "customer_tenure_days",
    "log_purchase_amount",
)

ENRICHED_V1_COLUMNS: tuple[str, ...] = (*V2_BASE_COLUMNS, *ENGINEERED_COLUMNS)
ENRICHED_V2_COLUMNS: tuple[str, ...] = (*ENRICHED_V1_COLUMNS, *A2_FEATURE_COLUMNS)


def _r4(value: float) -> float:
    """Round float to 4 decimal places and normalize IEEE-754 negative zero (-0.0 -> 0.0)."""
    return round(float(value), 4) + 0.0


def _cast_categorical(series: pd.Series, categories: list[str], ordered: bool) -> pd.Series:
    """Cast a series to pandas Categorical with canonical category order."""
    present = [str(v) for v in series.dropna().unique()]
    extras = [v for v in present if v not in categories]
    all_cats = [*categories, *extras]
    return series.astype("str").where(series.notna(), np.nan).astype(
        pd.CategoricalDtype(categories=all_cats, ordered=ordered)
    )


def enrich_with_external_metro_data(
    df: pd.DataFrame,
    external_path: Path | str | None = None,
) -> pd.DataFrame:
    """Enrich customer DataFrame with auxiliary Indian metropolitan metadata (A2).

    Performs left join on ``city`` against ``indian_cities_metadata.csv``, adding
    ``metro_region``, ``metro_state``, and ``metro_population_m``. Missing and
    unmatched records map cleanly to 'Unknown' and np.nan population, preserving 100%
    of records without dropping or distorting customer observations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a ``city`` column.
    external_path : Path | str | None, optional
        Path to ``indian_cities_metadata.csv``. Defaults to ``EXTERNAL_CITIES_PATH``.

    Returns
    -------
    pd.DataFrame
        DataFrame augmented with the 3 A2 enriched columns.
    """
    path = Path(external_path) if external_path is not None else EXTERNAL_CITIES_PATH
    if not path.exists():
        raise FileNotFoundError(f"External metropolitan metadata not found: {path}")

    ext_df = pd.read_csv(path)
    required_cols = {"city", "metro_region", "metro_state", "metro_population_m"}
    if not required_cols.issubset(ext_df.columns):
        raise ValueError(f"External file missing required columns: {required_cols - set(ext_df.columns)}")

    merged = df.merge(
        ext_df[["city", "metro_region", "metro_state", "metro_population_m"]],
        on="city",
        how="left",
    )
    merged["metro_region"] = _cast_categorical(
        merged["metro_region"].fillna("Unknown"),
        METRO_REGION_CATEGORIES,
        ordered=True,
    )
    merged["metro_state"] = _cast_categorical(
        merged["metro_state"].fillna("Unknown"),
        METRO_STATE_CATEGORIES,
        ordered=False,
    )
    merged["metro_population_m"] = merged["metro_population_m"].astype("float64")
    return merged


def engineer_features(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Derive the 6 canonical analytical features on top of the 21-column ``v2`` dataset.

    Appends ``age_group``, ``spend_tier``, ``feedback_tier``, ``contact_reachability_tier``,
    ``customer_tenure_days``, and ``log_purchase_amount`` in exact ``specs/ontology.md`` §3.2
    order. Pure, deterministic, and idempotent.
    """
    missing_base = [col for col in V2_BASE_COLUMNS if col not in df_clean.columns]
    if missing_base:
        raise ValueError(f"Input DataFrame is missing required v2 columns: {missing_base}")

    df = df_clean.loc[:, list(V2_BASE_COLUMNS)].copy()

    # 1. age_group: ordered demographic cohort + 'Unknown'
    cut_age = pd.cut(df["age"].astype("float64"), bins=AGE_GROUP_BINS, labels=AGE_GROUP_LABELS, right=True)
    df["age_group"] = (
        cut_age.cat.add_categories(["Unknown"])
        .fillna("Unknown")
        .astype(pd.CategoricalDtype(categories=AGE_GROUP_CATEGORIES, ordered=True))
    )

    # 2. spend_tier: fixed business thresholds (<$1,200; $1,200-$3,500; >$3,500; Missing)
    amt = df["purchase_amount"].astype("float64")
    spend_labels = np.select(
        [
            amt.notna() & (amt < 1200.0),
            amt.notna() & (amt >= 1200.0) & (amt <= 3500.0),
            amt.notna() & (amt > 3500.0),
        ],
        [
            "Low (<$1,200)",
            "Medium ($1,200-$3,500)",
            "High (>$3,500)",
        ],
        default="Missing",
    )
    df["spend_tier"] = pd.Series(spend_labels, index=df.index).astype(
        pd.CategoricalDtype(categories=SPEND_TIER_CATEGORIES, ordered=True)
    )

    # 3. feedback_tier: Likert sentiment tiers (1-2, 3, 4-5) + Scale-10 Spike (10) + Missing
    fb = df["feedback_score"].astype("float64")
    fb_labels = np.select(
        [
            fb.isin([1.0, 2.0]),
            fb == 3.0,
            fb.isin([4.0, 5.0]),
            fb == 10.0,
        ],
        [
            "Detractor (1-2)",
            "Passive (3)",
            "Promoter (4-5)",
            "Scale-10 Spike (10)",
        ],
        default="Missing",
    )
    df["feedback_tier"] = pd.Series(fb_labels, index=df.index).astype(
        pd.CategoricalDtype(categories=FEEDBACK_TIER_CATEGORIES, ordered=True)
    )

    # 4. contact_reachability_tier: 4-channel operational reachability
    email_ok = df["has_valid_email"].astype(bool)
    phone_ok = df["has_valid_phone"].astype(bool)
    reach_labels = np.select(
        [
            email_ok & phone_ok,
            email_ok & ~phone_ok,
            ~email_ok & phone_ok,
        ],
        [
            "Omnichannel (Both)",
            "Email Only",
            "Phone Only",
        ],
        default="Unreachable (None)",
    )
    df["contact_reachability_tier"] = pd.Series(reach_labels, index=df.index).astype(
        pd.CategoricalDtype(categories=REACHABILITY_TIER_CATEGORIES, ordered=True)
    )

    # 5. customer_tenure_days: valid chronological duration in days
    valid_chrono = (
        df["signup_date"].notna()
        & df["last_purchase_date"].notna()
        & (~df["is_date_inverted"].astype(bool))
    )
    raw_days = (df["last_purchase_date"] - df["signup_date"]).dt.days.astype("float64")
    df["customer_tenure_days"] = raw_days.where(valid_chrono, np.nan).astype("float64")

    # 6. log_purchase_amount: deterministic log1p transform rounded to 6 decimals
    df["log_purchase_amount"] = np.log1p(amt).round(6).astype("float64")

    df = df.loc[:, list(ENRICHED_V1_COLUMNS)]
    expected = EXPECTED_ROWS if len(df_clean) == EXPECTED_ROWS else len(df_clean)
    validate_enriched_customers(df, expected_rows=expected)
    return df


def validate_enriched_customers(
    df: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_ROWS,
    version: str = "v1",
) -> None:
    """Assert enriched schema, ordered categorical completeness, and numeric invariants."""
    if expected_rows is not None:
        assert len(df) == expected_rows, f"Expected {expected_rows:,} rows, got {len(df):,}"
    assert len(df) > 0, "Enriched DataFrame must not be empty"

    expected_cols = list(
        ENRICHED_V2_COLUMNS if (version == "v2" or "metro_region" in df.columns) else ENRICHED_V1_COLUMNS
    )
    assert list(df.columns) == expected_cols, (
        f"Enriched columns mismatch expected schema contract: {list(df.columns)}"
    )

    tier_contracts: list[tuple[str, list[str]]] = [
        ("age_group", AGE_GROUP_CATEGORIES),
        ("spend_tier", SPEND_TIER_CATEGORIES),
        ("feedback_tier", FEEDBACK_TIER_CATEGORIES),
        ("contact_reachability_tier", REACHABILITY_TIER_CATEGORIES),
    ]
    if "metro_region" in df.columns:
        tier_contracts.append(("metro_region", METRO_REGION_CATEGORIES))

    for col, expected_cats in tier_contracts:
        assert df[col].notna().all(), f"Ordered categorical tier '{col}' must contain zero nulls"
        assert isinstance(df[col].dtype, pd.CategoricalDtype) and df[col].cat.ordered, (
            f"Column '{col}' must be an ordered pandas Categorical"
        )
        assert list(df[col].cat.categories) == expected_cats, (
            f"Categories for '{col}' mismatch ontology: {list(df[col].cat.categories)}"
        )

    if "metro_state" in df.columns:
        assert df["metro_state"].notna().all(), "metro_state must contain zero nulls"
        assert isinstance(df["metro_state"].dtype, pd.CategoricalDtype), (
            "Column 'metro_state' must be a pandas Categorical"
        )

    if "metro_population_m" in df.columns:
        known_pop = df.loc[df["city"] != "Unknown", "metro_population_m"]
        assert known_pop.notna().all() and (known_pop > 0).all(), (
            "Known cities must have valid positive metropolitan population numbers"
        )
        assert df.loc[df["city"] == "Unknown", "metro_population_m"].isna().all(), (
            "Unknown cities must have NaN metropolitan population numbers"
        )

    valid_tenure = df["customer_tenure_days"].dropna()
    assert (valid_tenure >= 0.0).all(), "customer_tenure_days contains negative durations"
    assert df.loc[df["is_date_inverted"], "customer_tenure_days"].isna().all(), (
        "Chronologically inverted records must have NaN customer_tenure_days"
    )

    valid_log = df["log_purchase_amount"].dropna()
    assert np.isfinite(valid_log).all() and (valid_log > 0.0).all(), (
        "Valid log_purchase_amount values must be finite and strictly positive"
    )
    assert (df["log_purchase_amount"].isna() == df["purchase_amount"].isna()).all(), (
        "log_purchase_amount missingness mask must match purchase_amount exactly"
    )


def load_enriched_customers(version: str = "v1", processed_dir: Path | None = None) -> pd.DataFrame:
    """Load ``data/processed/customers_enriched_{version}.csv`` restoring canonical dtypes."""
    base_dir = processed_dir if processed_dir is not None else PROCESSED_DIR
    csv_path = base_dir / f"customers_enriched_{version}.csv"
    if not csv_path.exists():
        if version == "v2":
            v1_df = load_enriched_customers("v1", processed_dir=base_dir)
            v2_df = enrich_with_external_metro_data(v1_df)
            validate_enriched_customers(v2_df, expected_rows=EXPECTED_ROWS, version="v2")
            v2_df.to_csv(csv_path, index=False)
            return v2_df
        raise FileNotFoundError(f"Enriched customer dataset not found: {csv_path}")

    dtype_map: dict[str, str] = {
        "customer_id": "str",
        "name": "str",
        "gender": "str",
        "age": "float64",
        "city": "str",
        "purchase_amount": "float64",
        "feedback_score": "float64",
        "email": "str",
        "phone_number": "str",
        "country": "str",
        "feedback_score_1_to_5": "float64",
        "completeness_score": "float64",
        "age_group": "str",
        "spend_tier": "str",
        "feedback_tier": "str",
        "contact_reachability_tier": "str",
        "customer_tenure_days": "float64",
        "log_purchase_amount": "float64",
    }
    if version == "v2":
        dtype_map["metro_region"] = "str"
        dtype_map["metro_state"] = "str"
        dtype_map["metro_population_m"] = "float64"

    df = pd.read_csv(csv_path, dtype=dtype_map, keep_default_na=True)

    for date_col in ("signup_date", "last_purchase_date"):
        df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce").astype("datetime64[us]")

    df["gender"] = _cast_categorical(df["gender"], GENDER_CATEGORIES, ordered=False)
    df["city"] = _cast_categorical(df["city"], CITY_CATEGORIES, ordered=False)
    df["country"] = _cast_categorical(df["country"], COUNTRY_CATEGORIES, ordered=False)

    for flag_col in BOOL_FLAG_COLUMNS:
        if flag_col in df.columns:
            df[flag_col] = df[flag_col].astype(bool)

    df["age_group"] = _cast_categorical(df["age_group"], AGE_GROUP_CATEGORIES, ordered=True)
    df["spend_tier"] = _cast_categorical(df["spend_tier"], SPEND_TIER_CATEGORIES, ordered=True)
    df["feedback_tier"] = _cast_categorical(df["feedback_tier"], FEEDBACK_TIER_CATEGORIES, ordered=True)
    df["contact_reachability_tier"] = _cast_categorical(
        df["contact_reachability_tier"], REACHABILITY_TIER_CATEGORIES, ordered=True
    )

    if "metro_region" in df.columns:
        df["metro_region"] = _cast_categorical(df["metro_region"], METRO_REGION_CATEGORIES, ordered=True)
    if "metro_state" in df.columns:
        df["metro_state"] = _cast_categorical(df["metro_state"], METRO_STATE_CATEGORIES, ordered=False)

    expected = EXPECTED_ROWS if len(df) == EXPECTED_ROWS else len(df)
    validate_enriched_customers(df, expected_rows=expected, version=version)
    return df


def summarize_engineered_features(df_enriched: pd.DataFrame) -> pd.DataFrame:
    """Build a unified M4 profile table across all 6 engineered features."""
    n_total = len(df_enriched)
    valid_spend_all = df_enriched["purchase_amount"].dropna().astype("float64")
    total_revenue = float(valid_spend_all.sum())
    raw_spend_skew = float(valid_spend_all.skew())

    rows: list[dict[str, object]] = []
    missing_tokens = {"Unknown", "Missing"}

    cat_features: list[tuple[str, str]] = [
        ("age_group", "Demographic lifecycle segmentation for Q1/Q2 cohort spend profiling"),
        ("spend_tier", "Fixed commercial value tiers isolating VIP (> $3,500) revenue concentration (Q2)"),
        ("feedback_tier", "NPS-style Likert grouping isolating the 2,521-row scale-10 survey spike (Q3)"),
        ("contact_reachability_tier", "Operational CRM dispatch routing across email and SMS channels (Q3)"),
    ]

    for feat_col, purpose in cat_features:
        known_mask = ~df_enriched[feat_col].astype(str).isin(missing_tokens)
        n_known_pool = int(known_mask.sum())

        for cat_label, grp in df_enriched.groupby(feat_col, observed=True):
            label_str = str(cat_label)
            n_rec = len(grp)
            pct_tot = (n_rec / n_total * 100.0) if n_total > 0 else np.nan
            pct_kn = (
                np.nan
                if (label_str in missing_tokens or n_known_pool == 0)
                else _r4(n_rec / n_known_pool * 100.0)
            )

            sp = grp["purchase_amount"].dropna().astype("float64")
            n_sp = len(sp)
            sum_sp = float(sp.sum()) if n_sp > 0 else 0.0
            share_sp = (sum_sp / total_revenue * 100.0) if total_revenue > 0 else np.nan

            rows.append(
                {
                    "feature_name": feat_col,
                    "feature_type": "ordered_category",
                    "level_or_scope": label_str,
                    "n_records": n_rec,
                    "pct_of_total": _r4(pct_tot),
                    "pct_of_known": pct_kn,
                    "valid_spend_n": n_sp,
                    "mean_spend_usd": _r4(float(sp.mean())) if n_sp > 0 else np.nan,
                    "median_spend_usd": _r4(float(sp.median())) if n_sp > 0 else np.nan,
                    "total_spend_usd": _r4(sum_sp),
                    "spend_share_pct": _r4(share_sp),
                    "cont_mean": np.nan,
                    "cont_std": np.nan,
                    "cont_min": np.nan,
                    "cont_q1": np.nan,
                    "cont_median": np.nan,
                    "cont_q3": np.nan,
                    "cont_max": np.nan,
                    "cont_iqr": np.nan,
                    "cont_skewness": np.nan,
                    "cont_kurtosis": np.nan,
                    "analytical_value": purpose,
                }
            )

    # Continuous engineered features: customer_tenure_days and log_purchase_amount
    tenure_s = df_enriched["customer_tenure_days"].dropna().astype("float64")
    tenure_spend = df_enriched.loc[df_enriched["customer_tenure_days"].notna(), "purchase_amount"].dropna()
    tq1, tmed, tq3 = (float(v) for v in tenure_s.quantile([0.25, 0.50, 0.75]))
    rows.append(
        {
            "feature_name": "customer_tenure_days",
            "feature_type": "continuous_float64",
            "level_or_scope": "Valid Chronological (last_purchase_date >= signup_date)",
            "n_records": len(tenure_s),
            "pct_of_total": _r4(len(tenure_s) / n_total * 100.0),
            "pct_of_known": 100.0,
            "valid_spend_n": len(tenure_spend),
            "mean_spend_usd": _r4(float(tenure_spend.mean())) if len(tenure_spend) > 0 else np.nan,
            "median_spend_usd": _r4(float(tenure_spend.median())) if len(tenure_spend) > 0 else np.nan,
            "total_spend_usd": _r4(float(tenure_spend.sum())),
            "spend_share_pct": _r4(float(tenure_spend.sum()) / total_revenue * 100.0),
            "cont_mean": _r4(float(tenure_s.mean())),
            "cont_std": _r4(float(tenure_s.std(ddof=1))),
            "cont_min": _r4(float(tenure_s.min())),
            "cont_q1": _r4(tq1),
            "cont_median": _r4(tmed),
            "cont_q3": _r4(tq3),
            "cont_max": _r4(float(tenure_s.max())),
            "cont_iqr": _r4(tq3 - tq1),
            "cont_skewness": _r4(float(tenure_s.skew())),
            "cont_kurtosis": _r4(float(tenure_s.kurt())),
            "analytical_value": (
                "Excludes 829 inverted date pairs to measure true active lifecycle duration in days (Q3/M6)."
            ),
        }
    )

    log_s = df_enriched["log_purchase_amount"].dropna().astype("float64")
    lq1, lmed, lq3 = (float(v) for v in log_s.quantile([0.25, 0.50, 0.75]))
    rows.append(
        {
            "feature_name": "log_purchase_amount",
            "feature_type": "continuous_float64",
            "level_or_scope": "np.log1p(purchase_amount) on Valid Orders",
            "n_records": len(log_s),
            "pct_of_total": _r4(len(log_s) / n_total * 100.0),
            "pct_of_known": 100.0,
            "valid_spend_n": len(valid_spend_all),
            "mean_spend_usd": _r4(float(valid_spend_all.mean())),
            "median_spend_usd": _r4(float(valid_spend_all.median())),
            "total_spend_usd": _r4(total_revenue),
            "spend_share_pct": 100.0,
            "cont_mean": _r4(float(log_s.mean())),
            "cont_std": _r4(float(log_s.std(ddof=1))),
            "cont_min": _r4(float(log_s.min())),
            "cont_q1": _r4(lq1),
            "cont_median": _r4(lmed),
            "cont_q3": _r4(lq3),
            "cont_max": _r4(float(log_s.max())),
            "cont_iqr": _r4(lq3 - lq1),
            "cont_skewness": _r4(float(log_s.skew())),
            "cont_kurtosis": _r4(float(log_s.kurt())),
            "analytical_value": (
                f"Compresses 484.8x dollar span ($10.31-$4,998.67, raw skew={raw_spend_skew:.4f}) "
                "into [2.43, 8.52] (SD=1.00) for Multiplicative/Elasticity modeling (A4)."
            ),
        }
    )

    return pd.DataFrame(rows)


def export_m4_features(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate and write ``customers_enriched_v1.csv`` and ``m4_engineered_features_summary.csv``."""
    target_processed_dir = output_dir if output_dir is not None else PROCESSED_DIR
    target_summaries_dir = target_processed_dir / "summaries"
    target_processed_dir.mkdir(parents=True, exist_ok=True)
    target_summaries_dir.mkdir(parents=True, exist_ok=True)

    df_v2 = load_clean_customers("v2")
    df_enriched = engineer_features(df_v2)
    summary_df = summarize_engineered_features(df_enriched)

    enriched_path = target_processed_dir / ENRICHED_V1_FILENAME
    summary_path = target_summaries_dir / M4_SUMMARY_FILENAME

    df_enriched.to_csv(enriched_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    return {
        "customers_enriched_v1": enriched_path,
        "m4_engineered_features_summary": summary_path,
    }


def export_a2_features(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate and write ``customers_enriched_v2.csv`` deterministically (A2)."""
    target_processed_dir = output_dir if output_dir is not None else PROCESSED_DIR
    target_processed_dir.mkdir(parents=True, exist_ok=True)

    df_v2 = load_clean_customers("v2")
    df_enriched_v1 = engineer_features(df_v2)
    df_enriched_v2 = enrich_with_external_metro_data(df_enriched_v1)
    validate_enriched_customers(df_enriched_v2, expected_rows=EXPECTED_ROWS, version="v2")

    enriched_v2_path = target_processed_dir / ENRICHED_V2_FILENAME
    df_enriched_v2.to_csv(enriched_v2_path, index=False)

    return {"customers_enriched_v2": enriched_v2_path}


if __name__ == "__main__":
    exported = {**export_m4_features(), **export_a2_features()}
    for name, path in exported.items():
        print(f"Exported {name}: {path}")
