"""Quantitative univariate, bivariate, KPI, outlier, and aggregation functions (E4-E6, M2, M3).

Provides pure, deterministic statistical functions operating on cleaned and enriched customer
datasets (``data/processed/customers_*.csv``) in strict compliance with ``specs/ontology.md``
and ``.agents/skills/statistical-analysis/SKILL.md``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
PROCESSED_DIR: Path = REPO_ROOT / "data" / "processed"
SUMMARIES_DIR: Path = PROCESSED_DIR / "summaries"

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

AGE_GROUP_BINS: list[int] = [17, 29, 44, 59, 100]
AGE_GROUP_LABELS: list[str] = [
    "18-29 (Young Adult)",
    "30-44 (Early Career)",
    "45-59 (Mid-Senior)",
    "60+ (Senior)",
]
AGE_GROUP_CATEGORIES: list[str] = [*AGE_GROUP_LABELS, "Unknown"]

FEEDBACK_DISCRETE_CATEGORIES: list[str] = ["1", "2", "3", "4", "5", "10", "Missing"]
REACHABILITY_TIER_CATEGORIES: list[str] = [
    "Omnichannel (Both)",
    "Email Only",
    "Phone Only",
    "Unreachable (None)",
]
REACHABILITY_BINARY_CATEGORIES: list[str] = [
    "Reachable (>=1 channel)",
    "Unreachable (None)",
]

BOOL_FLAG_COLUMNS: tuple[str, ...] = (
    "has_valid_email",
    "has_valid_phone",
    "is_date_inverted",
    "is_geo_mismatch",
    "is_age_missing",
    "is_purchase_missing",
    "is_score_10_spike",
)


def _to_categorical(series: pd.Series, canonical_order: list[str], ordered: bool = False) -> pd.Series:
    """Cast a series to pandas Categorical preserving canonical order plus any extra values."""
    present = [str(v) for v in series.dropna().unique()]
    extras = [v for v in present if v not in canonical_order]
    categories = [*canonical_order, *extras]
    return series.astype("str").where(series.notna(), np.nan).astype(
        pd.CategoricalDtype(categories=categories, ordered=ordered)
    )


def load_clean_customers(version: str = "v1") -> pd.DataFrame:
    """Load ``data/processed/customers_clean_{version}.csv`` with canonical dtypes.

    Parses ``signup_date`` and ``last_purchase_date`` as ``datetime64[us]``, casts
    ``gender``, ``city``, and ``country`` to ``category``, ensures boolean indicator
    flags are ``bool``, and preserves ``NaN`` on missing strings and numerics.
    """
    csv_path = PROCESSED_DIR / f"customers_clean_{version}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Cleaned customer dataset not found: {csv_path}")

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
    }
    df = pd.read_csv(csv_path, dtype=dtype_map, keep_default_na=True)

    for date_col in ("signup_date", "last_purchase_date"):
        df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d", errors="coerce").astype("datetime64[us]")

    df["gender"] = _to_categorical(df["gender"], GENDER_CATEGORIES, ordered=False)
    df["city"] = _to_categorical(df["city"], CITY_CATEGORIES, ordered=False)
    df["country"] = _to_categorical(df["country"], COUNTRY_CATEGORIES, ordered=False)

    for flag_col in BOOL_FLAG_COLUMNS:
        if flag_col in df.columns:
            df[flag_col] = df[flag_col].astype(bool)

    for float_col in ("feedback_score_1_to_5", "completeness_score"):
        if float_col in df.columns:
            df[float_col] = pd.to_numeric(df[float_col], errors="coerce").astype("float64")

    return df


def _derive_completeness_score(df: pd.DataFrame) -> pd.Series:
    """Return record-level valid attribute proportion across the 12 core columns."""
    if "completeness_score" in df.columns:
        return df["completeness_score"].astype("float64")
    valid_count = (
        df["customer_id"].notna().astype(int)
        + (df["name"].astype(str) != "Unknown").astype(int)
        + (df["gender"].astype(str) != "Unknown").astype(int)
        + df["age"].notna().astype(int)
        + (df["city"].astype(str) != "Unknown").astype(int)
        + df["signup_date"].notna().astype(int)
        + df["last_purchase_date"].notna().astype(int)
        + df["purchase_amount"].notna().astype(int)
        + df["feedback_score"].notna().astype(int)
        + df["email"].notna().astype(int)
        + df["phone_number"].notna().astype(int)
        + (df["country"].astype(str) != "Unknown").astype(int)
    )
    return (valid_count / 12.0).astype("float64").round(6)


def _derive_is_date_inverted(df: pd.DataFrame) -> pd.Series:
    """Return boolean series flagging ``last_purchase_date < signup_date``."""
    if "is_date_inverted" in df.columns:
        return df["is_date_inverted"].astype(bool)
    return (
        df["signup_date"].notna()
        & df["last_purchase_date"].notna()
        & (df["last_purchase_date"] < df["signup_date"])
    )


def _derive_tenure_days(df: pd.DataFrame) -> pd.Series:
    """Compute chronologically valid customer tenure in days per ontology section 3.2."""
    if "customer_tenure_days" in df.columns:
        return df["customer_tenure_days"].astype("float64")
    is_inverted = _derive_is_date_inverted(df)
    raw_days = (df["last_purchase_date"] - df["signup_date"]).dt.days.astype("float64")
    return raw_days.where(~is_inverted, np.nan)


def _derive_feedback_1_to_5(df: pd.DataFrame) -> pd.Series:
    """Return ``feedback_score`` restricted to the standard 1-5 Likert scale (10 -> NaN)."""
    if "feedback_score_1_to_5" in df.columns:
        return df["feedback_score_1_to_5"].astype("float64")
    return df["feedback_score"].where(df["feedback_score"] <= 5.0, np.nan)


def _derive_age_group(df: pd.DataFrame) -> pd.Series:
    """Bin ``age`` into canonical ontology cohorts with ``'Unknown'`` for missing values."""
    if "age_group" in df.columns:
        return _to_categorical(df["age_group"], AGE_GROUP_CATEGORIES, ordered=True)
    cut_series = pd.cut(df["age"], bins=AGE_GROUP_BINS, labels=AGE_GROUP_LABELS, right=True)
    with_unknown = cut_series.cat.add_categories(["Unknown"]).fillna("Unknown")
    return with_unknown.astype(pd.CategoricalDtype(categories=AGE_GROUP_CATEGORIES, ordered=True))


def _derive_feedback_discrete(df: pd.DataFrame) -> pd.Series:
    """Map numeric ``feedback_score`` to ordered discrete labels ``1..5, 10, Missing``."""
    mapped = pd.Series("Missing", index=df.index, dtype="object")
    valid_mask = df["feedback_score"].notna()
    mapped.loc[valid_mask] = df.loc[valid_mask, "feedback_score"].astype(int).astype(str)
    return mapped.astype(pd.CategoricalDtype(categories=FEEDBACK_DISCRETE_CATEGORIES, ordered=True))


def _derive_reachability_tier(df: pd.DataFrame) -> pd.Series:
    """Derive 4-level ``contact_reachability_tier`` per ontology section 3.2."""
    if "contact_reachability_tier" in df.columns:
        return _to_categorical(df["contact_reachability_tier"], REACHABILITY_TIER_CATEGORIES, ordered=True)
    email_ok = df["has_valid_email"].astype(bool)
    phone_ok = df["has_valid_phone"].astype(bool)
    labels = np.select(
        [email_ok & phone_ok, email_ok & ~phone_ok, ~email_ok & phone_ok],
        ["Omnichannel (Both)", "Email Only", "Phone Only"],
        default="Unreachable (None)",
    )
    return pd.Series(labels, index=df.index).astype(
        pd.CategoricalDtype(categories=REACHABILITY_TIER_CATEGORIES, ordered=True)
    )


def _derive_reachability_binary(df: pd.DataFrame) -> pd.Series:
    """Derive binary contact reachability (``Reachable (>=1 channel)`` vs ``Unreachable (None)``)."""
    reachable = df["has_valid_email"].astype(bool) | df["has_valid_phone"].astype(bool)
    labels = np.where(reachable, "Reachable (>=1 channel)", "Unreachable (None)")
    return pd.Series(labels, index=df.index).astype(
        pd.CategoricalDtype(categories=REACHABILITY_BINARY_CATEGORIES, ordered=True)
    )


def compute_univariate_numeric_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute parametric and non-parametric univariate statistics for E4 numeric features.

    Evaluates ``age``, ``purchase_amount``, ``feedback_score`` (all valid 1-5 and 10),
    ``feedback_score_1_to_5`` (restricted to <= 5), and chronologically valid ``tenure_days``.
    Note: ``kurtosis`` reports Fisher excess kurtosis via ``pd.Series.kurt()``.
    """
    n_total = len(df)
    series_map: list[tuple[str, pd.Series]] = [
        ("age", df["age"].astype("float64")),
        ("purchase_amount", df["purchase_amount"].astype("float64")),
        ("feedback_score", df["feedback_score"].astype("float64")),
        ("feedback_score_1_to_5", _derive_feedback_1_to_5(df)),
        ("tenure_days", _derive_tenure_days(df)),
    ]

    rows: list[dict[str, object]] = []
    for var_name, series in series_map:
        valid = series.dropna()
        n_valid = len(valid)
        n_missing = n_total - n_valid
        coverage_pct = (n_valid / n_total * 100.0) if n_total > 0 else np.nan

        if n_valid == 0:
            rows.append(
                {
                    "variable": var_name,
                    "n_total": n_total,
                    "n_valid": 0,
                    "n_missing": n_missing,
                    "coverage_pct": round(coverage_pct, 4),
                    "mean": np.nan,
                    "std": np.nan,
                    "min": np.nan,
                    "q1": np.nan,
                    "median": np.nan,
                    "q3": np.nan,
                    "max": np.nan,
                    "iqr": np.nan,
                    "skewness": np.nan,
                    "kurtosis": np.nan,
                }
            )
            continue

        q1_val = float(valid.quantile(0.25))
        med_val = float(valid.quantile(0.50))
        q3_val = float(valid.quantile(0.75))
        rows.append(
            {
                "variable": var_name,
                "n_total": n_total,
                "n_valid": n_valid,
                "n_missing": n_missing,
                "coverage_pct": round(coverage_pct, 4),
                "mean": round(float(valid.mean()), 4),
                "std": round(float(valid.std(ddof=1)), 4) if n_valid > 1 else np.nan,
                "min": round(float(valid.min()), 4),
                "q1": round(q1_val, 4),
                "median": round(med_val, 4),
                "q3": round(q3_val, 4),
                "max": round(float(valid.max()), 4),
                "iqr": round(q3_val - q1_val, 4),
                "skewness": round(float(valid.skew()), 4) if n_valid > 2 else np.nan,
                "kurtosis": round(float(valid.kurt()), 4) if n_valid > 3 else np.nan,
            }
        )

    return pd.DataFrame(rows)


def compute_univariate_categorical_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute E4 frequency counts, total share (%), and known-record share (%) across categoricals.

    Covers ``gender``, ``city``, ``country``, discrete ``feedback_score`` (``1..5, 10, Missing``),
    and 4-tier ``contact_reachability`` (``Omnichannel (Both)``, ``Email Only``, ``Phone Only``,
    ``Unreachable (None)``). ``pct_known`` excludes ``'Unknown'`` and ``'Missing'`` from the
    denominator and sets their ``pct_known`` entry to ``NaN``.
    """
    n_total = len(df)
    missing_labels = {"Unknown", "Missing"}

    cat_specs: list[tuple[str, pd.Series, bool]] = [
        ("gender", _to_categorical(df["gender"], GENDER_CATEGORIES), True),
        ("city", _to_categorical(df["city"], CITY_CATEGORIES), True),
        ("country", _to_categorical(df["country"], COUNTRY_CATEGORIES), True),
        ("feedback_score", _derive_feedback_discrete(df), False),
        ("contact_reachability", _derive_reachability_tier(df), False),
    ]

    rows: list[dict[str, object]] = []
    for var_name, cat_series, sort_known_desc in cat_specs:
        counts = cat_series.value_counts(dropna=False, sort=False)
        known_categories = [str(k) for k in counts.index if str(k) not in missing_labels]
        missing_categories = [str(k) for k in counts.index if str(k) in missing_labels]

        if sort_known_desc:
            known_categories = sorted(known_categories, key=lambda k: (-int(counts[k]), k))

        ordered_keys = [*known_categories, *missing_categories]
        n_known_total = sum(int(counts[k]) for k in known_categories)

        for label in ordered_keys:
            cnt = int(counts[label])
            pct_tot = round(cnt / n_total * 100.0, 4) if n_total > 0 else np.nan
            if label in missing_labels or n_known_total == 0:
                pct_kn = np.nan
            else:
                pct_kn = round(cnt / n_known_total * 100.0, 4)
            rows.append(
                {
                    "variable": var_name,
                    "category": label,
                    "n": cnt,
                    "pct_total": pct_tot,
                    "pct_known": pct_kn,
                }
            )

    return pd.DataFrame(rows)


def compute_bivariate_segment_spend(df: pd.DataFrame) -> pd.DataFrame:
    """Compute E5 group-level ``purchase_amount`` statistics across demographic and channel segments.

    Evaluates ``gender``, ``country``, ``city``, ``age_group``, ``feedback_score``, binary
    ``contact_reachability``, and 4-level ``contact_reachability_tier`` using explicit
    ``observed=True`` on categorical ``groupby``.
    """
    work = pd.DataFrame({"purchase_amount": df["purchase_amount"].astype("float64")}, index=df.index)
    dimensions: list[tuple[str, pd.Series]] = [
        ("gender", _to_categorical(df["gender"], GENDER_CATEGORIES, ordered=True)),
        ("country", _to_categorical(df["country"], COUNTRY_CATEGORIES, ordered=True)),
        ("city", _to_categorical(df["city"], CITY_CATEGORIES, ordered=True)),
        ("age_group", _derive_age_group(df)),
        ("feedback_score", _derive_feedback_discrete(df)),
        ("contact_reachability", _derive_reachability_binary(df)),
        ("contact_reachability_tier", _derive_reachability_tier(df)),
    ]

    rows: list[dict[str, object]] = []
    for dim_name, seg_series in dimensions:
        temp = work.assign(_segment=seg_series)
        for seg_label, grp in temp.groupby("_segment", observed=True):
            n_seg = len(grp)
            valid_spend = grp["purchase_amount"].dropna()
            n_valid = len(valid_spend)
            cov_pct = round(n_valid / n_seg * 100.0, 4) if n_seg > 0 else np.nan

            if n_valid == 0:
                rows.append(
                    {
                        "dimension": dim_name,
                        "segment": str(seg_label),
                        "n_segment": n_seg,
                        "n_valid_spend": 0,
                        "spend_coverage_pct": cov_pct,
                        "mean_spend": np.nan,
                        "std_spend": np.nan,
                        "median_spend": np.nan,
                        "q1_spend": np.nan,
                        "q3_spend": np.nan,
                        "iqr_spend": np.nan,
                        "total_spend": 0.0,
                        "revenue_per_1k_valid": np.nan,
                    }
                )
                continue

            q1_val = float(valid_spend.quantile(0.25))
            med_val = float(valid_spend.quantile(0.50))
            q3_val = float(valid_spend.quantile(0.75))
            tot_val = float(valid_spend.sum())
            rev_per_1k = tot_val / n_valid * 1000.0

            rows.append(
                {
                    "dimension": dim_name,
                    "segment": str(seg_label),
                    "n_segment": n_seg,
                    "n_valid_spend": n_valid,
                    "spend_coverage_pct": cov_pct,
                    "mean_spend": round(float(valid_spend.mean()), 4),
                    "std_spend": round(float(valid_spend.std(ddof=1)), 4) if n_valid > 1 else np.nan,
                    "median_spend": round(med_val, 4),
                    "q1_spend": round(q1_val, 4),
                    "q3_spend": round(q3_val, 4),
                    "iqr_spend": round(q3_val - q1_val, 4),
                    "total_spend": round(tot_val, 4),
                    "revenue_per_1k_valid": round(rev_per_1k, 4),
                }
            )

    return pd.DataFrame(rows)


def _anova_kruskal_row(
    var_x: str,
    scope: str,
    seg_series: pd.Series,
    spend_series: pd.Series,
    exclude_labels: set[str] | None = None,
) -> dict[str, object]:
    """Run one-way ANOVA and Kruskal-Wallis across non-empty spend groups."""
    mask = spend_series.notna() & seg_series.notna()
    if exclude_labels:
        mask = mask & (~seg_series.astype(str).isin(exclude_labels))

    sub = pd.DataFrame({"seg": seg_series[mask], "spend": spend_series[mask]})
    groups = [grp["spend"].to_numpy() for _, grp in sub.groupby("seg", observed=True) if len(grp) >= 2]
    n_obs = sum(len(g) for g in groups)
    n_groups = len(groups)

    if n_groups >= 2:
        f_res = stats.f_oneway(*groups)
        k_res = stats.kruskal(*groups)
        f_stat, p_anova = round(float(f_res.statistic), 4), round(float(f_res.pvalue), 4)
        h_stat, p_kruskal = round(float(k_res.statistic), 4), round(float(k_res.pvalue), 4)
        sig = bool((f_res.pvalue < 0.05) or (k_res.pvalue < 0.05))
    else:
        f_stat = p_anova = h_stat = p_kruskal = np.nan
        sig = False

    return {
        "test_family": "continuous_vs_categorical",
        "variable_x": var_x,
        "variable_y": "purchase_amount",
        "scope": scope,
        "n_obs": n_obs,
        "n_groups": n_groups,
        "dof": n_groups - 1 if n_groups >= 2 else np.nan,
        "f_stat": f_stat,
        "p_anova": p_anova,
        "h_stat": h_stat,
        "p_kruskal": p_kruskal,
        "pearson_r": np.nan,
        "p_pearson": np.nan,
        "spearman_rho": np.nan,
        "p_spearman": np.nan,
        "chi2_stat": np.nan,
        "p_chi2": np.nan,
        "n_geo_mismatch": np.nan,
        "significant_at_0_05": sig,
    }


def run_bivariate_hypothesis_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Execute formal E5 parametric and non-parametric bivariate hypothesis tests.

    Covers:
      1. Continuous x Categorical: One-way ANOVA (``f_stat``, ``p_anova``) and Kruskal-Wallis
         (``h_stat``, ``p_kruskal``) for ``purchase_amount`` across ``gender``, ``country``,
         ``city``, ``age_group``, ``feedback_score``, and contact reachability (both including
         and excluding ``'Unknown'``/``'Missing'``).
      2. Continuous x Continuous: Pairwise ``n_obs``, Pearson ``r`` and Spearman ``rho`` with
         two-sided p-values for ``age``, ``feedback_score_1_to_5``, ``feedback_score`` (all),
         and valid ``tenure_days`` against ``purchase_amount``.
      3. Categorical x Categorical: Chi-square test of independence on ``city`` x ``country``
         (all categories and known-only) plus exact ``is_geo_mismatch`` audit count.
    """
    spend = df["purchase_amount"].astype("float64")
    rows: list[dict[str, object]] = []

    # 1. Continuous x Categorical
    cat_pairs: list[tuple[str, pd.Series, bool]] = [
        ("gender", _to_categorical(df["gender"], GENDER_CATEGORIES), True),
        ("country", _to_categorical(df["country"], COUNTRY_CATEGORIES), True),
        ("city", _to_categorical(df["city"], CITY_CATEGORIES), True),
        ("age_group", _derive_age_group(df), True),
        ("feedback_score", _derive_feedback_discrete(df), True),
        ("contact_reachability", _derive_reachability_binary(df), False),
        ("contact_reachability_tier", _derive_reachability_tier(df), False),
    ]
    for var_x, seg_s, has_unknown in cat_pairs:
        rows.append(_anova_kruskal_row(var_x, "all_segments", seg_s, spend))
        if has_unknown:
            rows.append(
                _anova_kruskal_row(var_x, "known_only", seg_s, spend, exclude_labels={"Unknown", "Missing"})
            )
        if var_x == "feedback_score":
            rows.append(
                _anova_kruskal_row(
                    var_x,
                    "likert_1_to_5_only",
                    seg_s,
                    spend,
                    exclude_labels={"10", "Missing"},
                )
            )

    # 2. Continuous x Continuous
    cont_specs: list[tuple[str, pd.Series]] = [
        ("age", df["age"].astype("float64")),
        ("feedback_score_1_to_5", _derive_feedback_1_to_5(df)),
        ("feedback_score", df["feedback_score"].astype("float64")),
        ("tenure_days", _derive_tenure_days(df)),
    ]
    for var_x, x_series in cont_specs:
        valid_pair = pd.DataFrame({"x": x_series, "y": spend}).dropna()
        n_pair = len(valid_pair)
        if n_pair >= 3:
            r_res = stats.pearsonr(valid_pair["x"], valid_pair["y"])
            s_res = stats.spearmanr(valid_pair["x"], valid_pair["y"])
            r_val, p_r = round(float(r_res.statistic), 4), round(float(r_res.pvalue), 4)
            rho_val, p_rho = round(float(s_res.statistic), 4), round(float(s_res.pvalue), 4)
            sig = bool((r_res.pvalue < 0.05) or (s_res.pvalue < 0.05))
        else:
            r_val = p_r = rho_val = p_rho = np.nan
            sig = False

        rows.append(
            {
                "test_family": "continuous_vs_continuous",
                "variable_x": var_x,
                "variable_y": "purchase_amount",
                "scope": "pairwise_valid",
                "n_obs": n_pair,
                "n_groups": np.nan,
                "dof": n_pair - 2 if n_pair >= 3 else np.nan,
                "f_stat": np.nan,
                "p_anova": np.nan,
                "h_stat": np.nan,
                "p_kruskal": np.nan,
                "pearson_r": r_val,
                "p_pearson": p_r,
                "spearman_rho": rho_val,
                "p_spearman": p_rho,
                "chi2_stat": np.nan,
                "p_chi2": np.nan,
                "n_geo_mismatch": np.nan,
                "significant_at_0_05": sig,
            }
        )

    # 3. Categorical x Categorical (city vs country + geographic mismatch audit)
    city_str = df["city"].astype(str)
    country_str = df["country"].astype(str)
    geo_mismatch_mask = (city_str != "Unknown") & country_str.isin(NON_INDIAN_COUNTRIES)
    n_geo_mismatch = int(geo_mismatch_mask.sum())

    for scope, sub_mask in [
        ("all_segments", pd.Series(True, index=df.index)),
        ("known_only", (city_str != "Unknown") & (country_str != "Unknown")),
    ]:
        ct = pd.crosstab(city_str[sub_mask], country_str[sub_mask])
        n_ct = int(ct.to_numpy().sum())
        if ct.shape[0] >= 2 and ct.shape[1] >= 2:
            chi2_val, p_val, dof_val, _ = stats.chi2_contingency(ct)
            chi2_r, p_r, dof_r = round(float(chi2_val), 4), round(float(p_val), 4), int(dof_val)
            sig = bool(p_val < 0.05)
        else:
            chi2_r = p_r = dof_r = np.nan
            sig = False

        rows.append(
            {
                "test_family": "categorical_vs_categorical",
                "variable_x": "city",
                "variable_y": "country",
                "scope": scope,
                "n_obs": n_ct,
                "n_groups": ct.shape[0] * ct.shape[1],
                "dof": dof_r,
                "f_stat": np.nan,
                "p_anova": np.nan,
                "h_stat": np.nan,
                "p_kruskal": np.nan,
                "pearson_r": np.nan,
                "p_pearson": np.nan,
                "spearman_rho": np.nan,
                "p_spearman": np.nan,
                "chi2_stat": chi2_r,
                "p_chi2": p_r,
                "n_geo_mismatch": n_geo_mismatch,
                "significant_at_0_05": sig,
            }
        )

    result = pd.DataFrame(rows)
    for int_col in ("n_obs", "n_groups", "dof", "n_geo_mismatch"):
        result[int_col] = result[int_col].astype("Int64")
    return result


def compute_city_country_crosstab(df: pd.DataFrame) -> pd.DataFrame:
    """Compute E5 cross-tabulation of ``city`` x ``country`` counts, row shares, and geo mismatches."""
    city_cat = _to_categorical(df["city"], CITY_CATEGORIES, ordered=True)
    country_cat = _to_categorical(df["country"], COUNTRY_CATEGORIES, ordered=True)

    counts_ct = pd.crosstab(city_cat, country_cat, dropna=False)
    counts_ct = counts_ct.reindex(index=CITY_CATEGORIES, columns=COUNTRY_CATEGORIES, fill_value=0)

    rows: list[dict[str, object]] = []
    for city_name in CITY_CATEGORIES:
        row_counts = counts_ct.loc[city_name]
        n_tot = int(row_counts.sum())
        is_indian_city = city_name != "Unknown"
        mismatch_n = int(sum(int(row_counts[c]) for c in NON_INDIAN_COUNTRIES)) if is_indian_city else 0

        record: dict[str, object] = {"city": city_name, "n_total": n_tot}
        for country_name in COUNTRY_CATEGORIES:
            col_slug = country_name.lower()
            record[f"{col_slug}_n"] = int(row_counts[country_name])
        for country_name in COUNTRY_CATEGORIES:
            col_slug = country_name.lower()
            cnt = int(row_counts[country_name])
            record[f"{col_slug}_row_pct"] = round(cnt / n_tot * 100.0, 4) if n_tot > 0 else np.nan

        record["geo_mismatch_n"] = mismatch_n
        record["geo_mismatch_row_pct"] = round(mismatch_n / n_tot * 100.0, 4) if n_tot > 0 else np.nan
        rows.append(record)

    return pd.DataFrame(rows)


def compute_research_question_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Synthesize canonical KPI-1 through KPI-6 mapped to Q1, Q2, and Q3 (ontology section 4)."""
    n_total = len(df)
    city_str = df["city"].astype(str)
    country_str = df["country"].astype(str)
    gender_str = df["gender"].astype(str)

    # KPI-1: Coverage & Geographic Consistency (Q1)
    n_age = int(df["age"].notna().sum())
    n_spend = int(df["purchase_amount"].notna().sum())
    n_fb = int(df["feedback_score"].notna().sum())
    n_city_known = int((city_str != "Unknown").sum())
    n_country_known = int((country_str != "Unknown").sum())
    n_gender_known = int((gender_str != "Unknown").sum())
    n_male = int((gender_str == "Male").sum())
    n_female = int((gender_str == "Female").sum())
    n_non_indian = int(country_str.isin(NON_INDIAN_COUNTRIES).sum())
    n_dual_geo = int(((city_str != "Unknown") & (country_str != "Unknown")).sum())
    n_geo_mismatch = int(((city_str != "Unknown") & country_str.isin(NON_INDIAN_COUNTRIES)).sum())

    # KPI-2 & KPI-3: Revenue Distribution & Normalized Segment Revenue (Q2)
    valid_spend = df["purchase_amount"].dropna()
    mean_spend = float(valid_spend.mean())
    std_spend = float(valid_spend.std(ddof=1))
    med_spend = float(valid_spend.median())
    iqr_spend = float(valid_spend.quantile(0.75) - valid_spend.quantile(0.25))
    total_spend = float(valid_spend.sum())
    overall_rev_1k = total_spend / n_spend * 1000.0 if n_spend > 0 else np.nan

    seg_df = compute_bivariate_segment_spend(df)
    known_seg_df = seg_df[
        seg_df["dimension"].isin(["gender", "country", "city", "age_group"])
        & (~seg_df["segment"].isin(["Unknown", "Missing"]))
    ]
    top_seg = known_seg_df.sort_values("revenue_per_1k_valid", ascending=False).iloc[0]
    low_seg = known_seg_df.sort_values("revenue_per_1k_valid", ascending=True).iloc[0]

    # KPI-4: Omnichannel Reachability Rate (Q3)
    email_ok = df["has_valid_email"].astype(bool)
    phone_ok = df["has_valid_phone"].astype(bool)
    n_email = int(email_ok.sum())
    n_phone = int(phone_ok.sum())
    n_reachable = int((email_ok | phone_ok).sum())
    n_both = int((email_ok & phone_ok).sum())
    n_unreachable = n_total - n_reachable

    # KPI-5: Chronological Integrity & Valid Tenure (Q3)
    both_dates_mask = df["signup_date"].notna() & df["last_purchase_date"].notna()
    n_both_dates = int(both_dates_mask.sum())
    is_inv = _derive_is_date_inverted(df)
    n_inverted = int((both_dates_mask & is_inv).sum())
    n_chrono_valid = n_both_dates - n_inverted
    tenure_valid = _derive_tenure_days(df).dropna()
    tenure_iqr = float(tenure_valid.quantile(0.75) - tenure_valid.quantile(0.25))

    # KPI-6: Net Satisfaction Distribution 1-5 vs 10 (Q3)
    fb_valid = df["feedback_score"].dropna()
    fb_1_5 = _derive_feedback_1_to_5(df).dropna()
    n_fb_1_5 = len(fb_1_5)
    n_detractors = int(fb_1_5.isin([1.0, 2.0]).sum())
    n_passives = int((fb_1_5 == 3.0).sum())
    n_promoters = int(fb_1_5.isin([4.0, 5.0]).sum())
    n_spike_10 = int((fb_valid == 10.0).sum())

    rows: list[dict[str, object]] = [
        {
            "kpi_id": "KPI-1",
            "business_question": "Q1",
            "kpi_name": "Valid Attribute Coverage Rate (%)",
            "indicator": "Age Valid Coverage",
            "n_numerator": n_age,
            "n_denominator": n_total,
            "primary_value": round(n_age / n_total * 100.0, 4),
            "unit": "pct",
            "secondary_value": round(float(df["age"].mean()), 4),
            "secondary_metric": "mean_age_years",
            "notes": f"Median age={df['age'].median():.2f}y, SD={df['age'].std(ddof=1):.2f}y (range 18-70)",
        },
        {
            "kpi_id": "KPI-1",
            "business_question": "Q1",
            "kpi_name": "Valid Attribute Coverage Rate (%)",
            "indicator": "Demographics & Location Coverage (Gender / City / Country)",
            "n_numerator": n_city_known,
            "n_denominator": n_total,
            "primary_value": round(n_city_known / n_total * 100.0, 4),
            "unit": "pct",
            "secondary_value": round(n_country_known / n_total * 100.0, 4),
            "secondary_metric": "country_coverage_pct",
            "notes": (
                f"Gender known={n_gender_known} ({n_gender_known / n_total * 100:.2f}%); "
                f"Male={n_male} ({n_male / n_gender_known * 100:.2f}% known), "
                f"Female={n_female} ({n_female / n_gender_known * 100:.2f}% known)"
            ),
        },
        {
            "kpi_id": "KPI-1",
            "business_question": "Q1",
            "kpi_name": "Valid Attribute Coverage Rate (%)",
            "indicator": "Geographic Mismatch Rate (Indian City paired with Non-Indian Country)",
            "n_numerator": n_geo_mismatch,
            "n_denominator": n_dual_geo,
            "primary_value": round(n_geo_mismatch / n_dual_geo * 100.0, 4),
            "unit": "pct_of_dual_known",
            "secondary_value": round(n_geo_mismatch / n_total * 100.0, 4),
            "secondary_metric": "pct_of_all_records",
            "notes": (
                f"8 Indian cities paired independently with USA/Australia/Canada/UK "
                f"({n_non_indian} total non-Indian rows)"
            ),
        },
        {
            "kpi_id": "KPI-2",
            "business_question": "Q2",
            "kpi_name": "Mean & Median Order Value (AOV / MOV)",
            "indicator": "Overall Valid Transaction Spend",
            "n_numerator": n_spend,
            "n_denominator": n_total,
            "primary_value": round(mean_spend, 4),
            "unit": "USD",
            "secondary_value": round(med_spend, 4),
            "secondary_metric": "median_spend_usd",
            "notes": (
                f"SD=${std_spend:,.2f}, IQR=${iqr_spend:,.2f}, "
                f"Total=${total_spend:,.2f} across {n_spend:,} valid orders ({n_spend / n_total * 100:.2f}%)"
            ),
        },
        {
            "kpi_id": "KPI-3",
            "business_question": "Q2",
            "kpi_name": "Normalized Segment Revenue per 1,000 Customers",
            "indicator": "Overall Baseline Revenue per 1,000 Valid Customers",
            "n_numerator": n_spend,
            "n_denominator": 1000,
            "primary_value": round(overall_rev_1k, 4),
            "unit": "USD_per_1k_valid",
            "secondary_value": round(float(top_seg["revenue_per_1k_valid"]), 4),
            "secondary_metric": f"top_known_segment_{top_seg['dimension']}_{top_seg['segment']}",
            "notes": (
                f"Highest known={top_seg['dimension']}:{top_seg['segment']} "
                f"(${top_seg['revenue_per_1k_valid']:,.2f}/1k); "
                f"Lowest known={low_seg['dimension']}:{low_seg['segment']} "
                f"(${low_seg['revenue_per_1k_valid']:,.2f}/1k); all ANOVA/Kruskal p > 0.05"
            ),
        },
        {
            "kpi_id": "KPI-4",
            "business_question": "Q3",
            "kpi_name": "Omnichannel Reachability Rate (%)",
            "indicator": "Reachable Customers (>=1 Valid Contact Channel)",
            "n_numerator": n_reachable,
            "n_denominator": n_total,
            "primary_value": round(n_reachable / n_total * 100.0, 4),
            "unit": "pct",
            "secondary_value": round(n_both / n_total * 100.0, 4),
            "secondary_metric": "omnichannel_both_pct",
            "notes": (
                f"Email valid={n_email} ({n_email / n_total * 100:.2f}%), "
                f"Phone valid={n_phone} ({n_phone / n_total * 100:.2f}%), "
                f"Both={n_both} ({n_both / n_total * 100:.2f}%), "
                f"Unreachable={n_unreachable} ({n_unreachable / n_total * 100:.2f}%)"
            ),
        },
        {
            "kpi_id": "KPI-5",
            "business_question": "Q3",
            "kpi_name": "Chronological Integrity Rate (%)",
            "indicator": "Valid Chronological Lifecycle Pairs (last_purchase_date >= signup_date)",
            "n_numerator": n_chrono_valid,
            "n_denominator": n_both_dates,
            "primary_value": round(n_chrono_valid / n_both_dates * 100.0, 4),
            "unit": "pct_of_dual_dates",
            "secondary_value": round(float(tenure_valid.median()), 4),
            "secondary_metric": "median_valid_tenure_days",
            "notes": (
                f"{n_inverted} inverted pairs ({n_inverted / n_both_dates * 100:.2f}%) excluded; "
                f"valid tenure mean={tenure_valid.mean():.2f}d, "
                f"SD={tenure_valid.std(ddof=1):.2f}d, IQR={tenure_iqr:.2f}d"
            ),
        },
        {
            "kpi_id": "KPI-6",
            "business_question": "Q3",
            "kpi_name": "Net Satisfaction Distribution (1-5 vs. 10)",
            "indicator": "Standard Likert Scale (1-5) Mean vs. Scale-10 Anomaly Share",
            "n_numerator": n_fb_1_5,
            "n_denominator": n_fb,
            "primary_value": round(float(fb_1_5.mean()), 4),
            "unit": "rating_1_to_5",
            "secondary_value": round(n_spike_10 / n_fb * 100.0, 4),
            "secondary_metric": "scale_10_spike_pct_of_valid",
            "notes": (
                f"Valid ratings={n_fb}: Detractors(1-2)={n_detractors} ({n_detractors / n_fb * 100:.2f}%), "
                f"Passives(3)={n_passives} ({n_passives / n_fb * 100:.2f}%), "
                f"Promoters(4-5)={n_promoters} ({n_promoters / n_fb * 100:.2f}%), "
                f"Scale-10 Spike={n_spike_10} ({n_spike_10 / n_fb * 100:.2f}%)"
            ),
        },
    ]

    return pd.DataFrame(rows)


def _r4(value: float) -> float:
    """Round float to 4 decimal places and normalize IEEE-754 negative zero (-0.0 -> 0.0)."""
    return round(float(value), 4) + 0.0


def compute_iqr_outlier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Execute formal M2 Tukey IQR (1.5x and 3.0x) outlier audit across continuous and rating columns.

    Separates Layer 1 ingestion sentinels (remediated to NaN in E3/M1) from Layer 2 statistical
    domain outliers across ``age``, ``purchase_amount``, ``customer_tenure_days``,
    ``feedback_score``, ``feedback_score_1_to_5``, and ``completeness_score``.
    """
    n_total = len(df)
    specs: list[tuple[str, pd.Series, str, str, str]] = [
        (
            "age",
            df["age"].astype("float64"),
            "-5 (2,506 rows) and 200 (2,453 rows) -> NaN (4,959 sentinels + 2,576 blanks)",
            "Retain all valid observations unclipped",
            (
                "0 Tukey (1.5xIQR) or extreme (3.0xIQR) outliers across [18, 70] yrs; "
                "platykurtic adult spread makes capping destructive."
            ),
        ),
        (
            "purchase_amount",
            df["purchase_amount"].astype("float64"),
            "-999 (2,501 rows) and 'N/A' (2,533 rows) -> NaN (5,034 sentinels + 2,500 blanks)",
            "Retain all valid observations unclipped",
            (
                "0 Tukey (1.5xIQR) or extreme (3.0xIQR) outliers across $10.31-$4,998.67; "
                "upper tail represents genuine high-value orders."
            ),
        ),
        (
            "customer_tenure_days",
            _derive_tenure_days(df),
            "not_a_date (2,475), missing (3,366), and 829 inverted date pairs -> NaN",
            "Retain valid chronological durations unclipped",
            (
                "0 Tukey (1.5xIQR) or extreme (3.0xIQR) outliers across 0-1,925 days (~5.27 yrs); "
                "mild right skew (0.52) is natural lifecycle duration."
            ),
        ),
        (
            "feedback_score",
            df["feedback_score"].astype("float64"),
            "-1 (2,489 rows) -> NaN (+ 2,462 blanks); 2,521 off-scale 10s flagged via is_score_10_spike",
            "Isolate 10-spike via is_score_10_spike + analyze clean Likert via feedback_score_1_to_5",
            (
                "0 formal Tukey outliers on raw valid [-7.50, 20.50] due to quartile masking "
                "(49.93% at 10 shifts Q3 to 10.0), but 10 exceeds clean Likert upper fence (7.00)."
            ),
        ),
        (
            "feedback_score_1_to_5",
            _derive_feedback_1_to_5(df),
            "-1 (2,489 rows) and off-scale 10 (2,521 rows) -> NaN (+ 2,462 blanks)",
            "Retain all clean 1-5 Likert ratings unclipped",
            (
                "0 Tukey (1.5xIQR: [-1.00, 7.00]) or extreme [-4.00, 10.00] outliers; "
                "establishes true Likert upper fence (7.00) proving score 10 is a scale anomaly."
            ),
        ),
        (
            "completeness_score",
            _derive_completeness_score(df),
            "Derived row-quality ratio across 12 attributes after sentinel remediation",
            "Retain all 10,000 account scores unclipped (audit low tail in A3/X4)",
            (
                "9 accounts (0.09%) with 2/12 valid fields (0.1667) fall below lower Tukey fence "
                "(0.2500), 0 extreme outliers; retaining preserves exact N=10,000 KPI denominators."
            ),
        ),
    ]

    rows: list[dict[str, object]] = []
    for var_name, series, sentinels_info, rule, justification in specs:
        valid = series.dropna()
        n_valid = len(valid)
        missing_pct = ((n_total - n_valid) / n_total * 100.0) if n_total > 0 else np.nan

        if n_valid == 0:
            rows.append(
                {
                    "variable": var_name,
                    "n_valid": 0,
                    "missing_pct": round(missing_pct, 4),
                    "mean": np.nan,
                    "std": np.nan,
                    "min": np.nan,
                    "p01": np.nan,
                    "q1": np.nan,
                    "median": np.nan,
                    "q3": np.nan,
                    "p99": np.nan,
                    "max": np.nan,
                    "iqr": np.nan,
                    "tukey_lower_fence": np.nan,
                    "tukey_upper_fence": np.nan,
                    "n_below_lower": 0,
                    "n_above_upper": 0,
                    "n_tukey_outliers": 0,
                    "outlier_pct_of_valid": np.nan,
                    "extreme_lower_fence": np.nan,
                    "extreme_upper_fence": np.nan,
                    "n_extreme_outliers": 0,
                    "sentinels_removed_in_cleaning": sentinels_info,
                    "treatment_rule": rule,
                    "treatment_justification": justification,
                }
            )
            continue

        p01_v, q1_v, med_v, q3_v, p99_v = (float(v) for v in valid.quantile([0.01, 0.25, 0.50, 0.75, 0.99]))
        iqr_v = q3_v - q1_v
        low_fence = q1_v - 1.5 * iqr_v
        high_fence = q3_v + 1.5 * iqr_v
        ext_low = q1_v - 3.0 * iqr_v
        ext_high = q3_v + 3.0 * iqr_v

        n_below = int((valid < low_fence).sum())
        n_above = int((valid > high_fence).sum())
        n_out = n_below + n_above
        n_ext = int(((valid < ext_low) | (valid > ext_high)).sum())

        rows.append(
            {
                "variable": var_name,
                "n_valid": n_valid,
                "missing_pct": _r4(missing_pct),
                "mean": _r4(float(valid.mean())),
                "std": _r4(float(valid.std(ddof=1))) if n_valid > 1 else np.nan,
                "min": _r4(float(valid.min())),
                "p01": _r4(p01_v),
                "q1": _r4(q1_v),
                "median": _r4(med_v),
                "q3": _r4(q3_v),
                "p99": _r4(p99_v),
                "max": _r4(float(valid.max())),
                "iqr": _r4(iqr_v),
                "tukey_lower_fence": _r4(low_fence),
                "tukey_upper_fence": _r4(high_fence),
                "n_below_lower": n_below,
                "n_above_upper": n_above,
                "n_tukey_outliers": n_out,
                "outlier_pct_of_valid": _r4(n_out / n_valid * 100.0),
                "extreme_lower_fence": _r4(ext_low),
                "extreme_upper_fence": _r4(ext_high),
                "n_extreme_outliers": n_ext,
                "sentinels_removed_in_cleaning": sentinels_info,
                "treatment_rule": rule,
                "treatment_justification": justification,
            }
        )

    return pd.DataFrame(rows)


def _summarize_regime(
    var_name: str,
    regime: str,
    decision: str,
    series: pd.Series,
    n_modified: int,
    n_base_valid: int,
    base_std: float,
    base_iqr: float,
    rationale: str,
) -> dict[str, object]:
    """Build a single row comparing central tendency and dispersion under an M2 treatment regime."""
    n_eval = len(series)
    cur_std = float(series.std(ddof=1)) if n_eval > 1 else 0.0
    q1_v, med_v, q3_v = (float(v) for v in series.quantile([0.25, 0.50, 0.75]))
    cur_iqr = q3_v - q1_v
    std_chg = ((cur_std - base_std) / base_std * 100.0) if base_std > 0 else 0.0
    iqr_chg = ((cur_iqr - base_iqr) / base_iqr * 100.0) if base_iqr > 0 else 0.0
    pct_aff = (n_modified / n_base_valid * 100.0) if n_base_valid > 0 else 0.0

    return {
        "variable": var_name,
        "regime": regime,
        "decision": decision,
        "n_evaluated": n_eval,
        "n_modified_or_dropped": n_modified,
        "pct_valid_affected": _r4(pct_aff),
        "mean": _r4(float(series.mean())),
        "std": _r4(cur_std),
        "std_change_pct": _r4(std_chg),
        "median": _r4(med_v),
        "q1": _r4(q1_v),
        "q3": _r4(q3_v),
        "iqr": _r4(cur_iqr),
        "iqr_change_pct": _r4(iqr_chg),
        "min": _r4(float(series.min())),
        "max": _r4(float(series.max())),
        "rationale": rationale,
    }


def evaluate_outlier_treatment(df: pd.DataFrame) -> pd.DataFrame:
    """Compare central tendency and dispersion across M2 candidate outlier treatment regimes.

    Evaluates ``Retain Valid Unclipped (Chosen)``, ``Winsorize [P01, P99] (Sensitivity Check - Rejected)``,
    and ``Naive Median-Imputed + Tukey IQR (Anti-Pattern - Rejected)`` across ``age``,
    ``purchase_amount``, and ``customer_tenure_days``, plus the four scale/capping regimes
    for ``feedback_score``.
    """
    rows: list[dict[str, object]] = []

    cont_vars: list[tuple[str, pd.Series]] = [
        ("age", df["age"].astype("float64")),
        ("purchase_amount", df["purchase_amount"].astype("float64")),
        ("customer_tenure_days", _derive_tenure_days(df)),
    ]
    for var_name, full_series in cont_vars:
        valid = full_series.dropna()
        n_valid = len(valid)
        base_std = float(valid.std(ddof=1))
        bq1, bmed, bq3 = (float(v) for v in valid.quantile([0.25, 0.50, 0.75]))
        base_iqr = bq3 - bq1

        # 1. Retain Valid Unclipped (Chosen)
        rows.append(
            _summarize_regime(
                var_name,
                "Retain Valid Unclipped (Chosen)",
                "Chosen",
                valid,
                0,
                n_valid,
                base_std,
                base_iqr,
                "0 Tukey outliers; preserves 100% of genuine signal and exact parametric/non-parametric spread.",
            )
        )

        # 2. Winsorize [P01, P99] (Sensitivity Check - Rejected)
        p01_v, p99_v = (float(v) for v in valid.quantile([0.01, 0.99]))
        winsorized = valid.clip(lower=p01_v, upper=p99_v)
        n_clipped = int(((valid < p01_v) | (valid > p99_v)).sum())
        rows.append(
            _summarize_regime(
                var_name,
                "Winsorize [P01, P99] (Sensitivity Check - Rejected)",
                "Rejected",
                winsorized,
                n_clipped,
                n_valid,
                base_std,
                base_iqr,
                "Negligible mean/SD shift (<0.3%) confirms robustness, but arbitrarily censors genuine 1%/99% tails.",
            )
        )

        # 3. Naive Median-Imputed + Tukey IQR (Anti-Pattern - Rejected)
        imputed = full_series.fillna(bmed)
        iq1, iq3 = (float(v) for v in imputed.quantile([0.25, 0.75]))
        iiqr = iq3 - iq1
        ilow, ihigh = iq1 - 1.5 * iiqr, iq3 + 1.5 * iiqr
        kept_imputed = imputed[(imputed >= ilow) & (imputed <= ihigh)]
        n_false_dropped = int(((valid < ilow) | (valid > ihigh)).sum())
        rows.append(
            _summarize_regime(
                var_name,
                "Naive Median-Imputed + Tukey IQR (Anti-Pattern - Rejected)",
                "Rejected",
                kept_imputed,
                n_false_dropped,
                n_valid,
                base_std,
                base_iqr,
                (
                    f"Median imputation collapses IQR to 0.00 and falsely drops {n_false_dropped:,}/{n_valid:,} "
                    f"({n_false_dropped / n_valid * 100:.2f}%) genuine records as 'outliers', leaving SD=0.00."
                ),
            )
        )

    # 4. Feedback score treatment regimes
    fb_all = df["feedback_score"].dropna().astype("float64")
    fb_likert_full = _derive_feedback_1_to_5(df)
    fb_likert = fb_likert_full.dropna()
    n_likert = len(fb_likert)
    fb_base_std = float(fb_likert.std(ddof=1))
    fq1, fmed, fq3 = (float(v) for v in fb_likert.quantile([0.25, 0.50, 0.75]))
    fb_base_iqr = fq3 - fq1
    n_spike_10 = int((fb_all == 10.0).sum())

    rows.append(
        _summarize_regime(
            "feedback_score",
            "Dual Scale: Clean Likert 1-5 + is_score_10_spike (Chosen)",
            "Chosen",
            fb_likert,
            n_spike_10,
            len(fb_all),
            fb_base_std,
            fb_base_iqr,
            "Isolates 2,521 off-scale 10s into is_score_10_spike while preserving unbiased 1-5 Likert statistics.",
        )
    )
    rows.append(
        _summarize_regime(
            "feedback_score",
            "Unfiltered 1-10 Scale (Distorted Mean)",
            "Rejected (for Likert mean)",
            fb_all,
            0,
            len(fb_all),
            fb_base_std,
            fb_base_iqr,
            "Mixing 1-5 (n=2,528) and 10 (n=2,521) inflates mean to 6.48 (+118.55%) and masks 10 via Q3=10.0.",
        )
    )
    rows.append(
        _summarize_regime(
            "feedback_score",
            "Cap/Winsorize 10 -> 5 (Rejected - False Promoter Surge)",
            "Rejected",
            fb_all.clip(upper=5.0),
            n_spike_10,
            len(fb_all),
            fb_base_std,
            fb_base_iqr,
            "Remapping 10 -> 5 shifts median 3.0 -> 5.0 and inflates Promoters (4-5) by +266.77% (945 -> 3,466).",
        )
    )

    fb_imp = fb_likert_full.fillna(fmed)
    fiq1, fiq3 = (float(v) for v in fb_imp.quantile([0.25, 0.75]))
    fiiqr = fiq3 - fiq1
    filow, fihigh = fiq1 - 1.5 * fiiqr, fiq3 + 1.5 * fiiqr
    fb_kept_imp = fb_imp[(fb_imp >= filow) & (fb_imp <= fihigh)]
    fb_false_dropped = int(((fb_likert < filow) | (fb_likert > fihigh)).sum())
    rows.append(
        _summarize_regime(
            "feedback_score",
            "Naive Median-Imputed + Tukey IQR (Anti-Pattern - Rejected)",
            "Rejected",
            fb_kept_imp,
            fb_false_dropped,
            n_likert,
            fb_base_std,
            fb_base_iqr,
            (
                f"Imputing 74.72% missing Likert scores to 3.0 collapses IQR to 0.00 and drops "
                f"{fb_false_dropped:,}/{n_likert:,} ({fb_false_dropped / n_likert * 100:.2f}%) genuine 1/2/4/5 ratings."
            ),
        )
    )

    return pd.DataFrame(rows)


def build_m3_demographic_spend_groupby(df_enriched: pd.DataFrame) -> pd.DataFrame:
    """Summarize multi-dimensional gender x age_group KPIs using groupby(..., observed=True).agg(...)."""
    n_total = len(df_enriched)
    work = pd.DataFrame(
        {
            "customer_id": df_enriched["customer_id"],
            "gender": _to_categorical(df_enriched["gender"], GENDER_CATEGORIES, ordered=True),
            "age_group": _derive_age_group(df_enriched),
            "purchase_amount": df_enriched["purchase_amount"].astype("float64"),
            "_is_reachable": (
                df_enriched["has_valid_email"].astype(bool) | df_enriched["has_valid_phone"].astype(bool)
            ).astype("float64"),
            "completeness_score": _derive_completeness_score(df_enriched),
        },
        index=df_enriched.index,
    )

    grouped = (
        work.groupby(["gender", "age_group"], observed=True)
        .agg(
            account_count=("customer_id", "count"),
            valid_spend_n=("purchase_amount", "count"),
            total_spend_usd=("purchase_amount", "sum"),
            mean_spend_usd=("purchase_amount", "mean"),
            std_spend_usd=("purchase_amount", "std"),
            median_spend_usd=("purchase_amount", "median"),
            q1_spend=("purchase_amount", lambda s: s.quantile(0.25)),
            q3_spend=("purchase_amount", lambda s: s.quantile(0.75)),
            reachable_rate=("_is_reachable", "mean"),
            mean_completeness_score=("completeness_score", "mean"),
        )
        .reset_index()
    )

    grouped["gender"] = grouped["gender"].astype(str)
    grouped["age_group"] = grouped["age_group"].astype(str)
    grouped["account_share_pct"] = (grouped["account_count"] / n_total * 100.0).round(4) + 0.0
    grouped["spend_coverage_pct"] = (
        np.where(
            grouped["account_count"] > 0,
            grouped["valid_spend_n"] / grouped["account_count"] * 100.0,
            np.nan,
        )
        .round(4)
        + 0.0
    )
    grouped["iqr_spend_usd"] = (grouped["q3_spend"] - grouped["q1_spend"]).round(4) + 0.0
    grouped["rev_per_1k_valid_customers_usd"] = (
        np.where(
            grouped["valid_spend_n"] > 0,
            grouped["total_spend_usd"] / grouped["valid_spend_n"] * 1000.0,
            np.nan,
        )
        .round(4)
        + 0.0
    )
    grouped["reachable_pct"] = (grouped["reachable_rate"] * 100.0).round(4) + 0.0

    for col in (
        "total_spend_usd",
        "mean_spend_usd",
        "std_spend_usd",
        "median_spend_usd",
        "mean_completeness_score",
    ):
        grouped[col] = grouped[col].round(4) + 0.0

    ordered_cols = [
        "gender",
        "age_group",
        "account_count",
        "account_share_pct",
        "valid_spend_n",
        "spend_coverage_pct",
        "total_spend_usd",
        "mean_spend_usd",
        "std_spend_usd",
        "median_spend_usd",
        "iqr_spend_usd",
        "rev_per_1k_valid_customers_usd",
        "reachable_pct",
        "mean_completeness_score",
    ]
    return grouped.loc[:, ordered_cols]


def build_m3_country_age_pivot(df_enriched: pd.DataFrame) -> pd.DataFrame:
    """Build M3 country x age_group spend matrix via pd.pivot_table(..., observed=True, margins=True)."""
    work = pd.DataFrame(
        {
            "country": _to_categorical(df_enriched["country"], COUNTRY_CATEGORIES, ordered=True),
            "age_group": _derive_age_group(df_enriched),
            "purchase_amount": df_enriched["purchase_amount"].astype("float64"),
        },
        index=df_enriched.index,
    )

    piv = pd.pivot_table(
        work,
        index="country",
        columns="age_group",
        values="purchase_amount",
        aggfunc=["count", "mean", "median", "sum"],
        observed=True,
        margins=True,
        margins_name="All",
    )

    age_slug_map: dict[str, str] = {
        "18-29 (Young Adult)": "age_18_29",
        "30-44 (Early Career)": "age_30_44",
        "45-59 (Mid-Senior)": "age_45_59",
        "60+ (Senior)": "age_60_plus",
        "Unknown": "age_unknown",
        "All": "all_ages",
    }
    func_prefix_map: dict[str, str] = {
        "count": "n",
        "mean": "mean",
        "median": "median",
        "sum": "sum",
    }

    flat = pd.DataFrame({"country": [str(idx) for idx in piv.index]})
    for agg_name, prefix in func_prefix_map.items():
        sub = piv[agg_name]
        for raw_col in [*AGE_GROUP_CATEGORIES, "All"]:
            if raw_col not in sub.columns:
                continue
            col_name = f"{prefix}_{age_slug_map[raw_col]}"
            if agg_name == "count":
                flat[col_name] = sub[raw_col].fillna(0).astype(int).to_numpy()
            else:
                flat[col_name] = (sub[raw_col].astype("float64").round(4) + 0.0).to_numpy()

    return flat


def build_m3_reachability_spend_tier_pivot(df_enriched: pd.DataFrame) -> pd.DataFrame:
    """Cross contact_reachability_tier x spend_tier via pivot_table & groupby(..., observed=True)."""
    if "spend_tier" not in df_enriched.columns or "feedback_tier" not in df_enriched.columns:
        raise ValueError("df_enriched must include 'spend_tier' and 'feedback_tier' from src.features")

    n_total = len(df_enriched)
    total_rev = float(df_enriched["purchase_amount"].dropna().sum())

    work = pd.DataFrame(
        {
            "customer_id": df_enriched["customer_id"],
            "contact_reachability_tier": _derive_reachability_tier(df_enriched),
            "spend_tier": df_enriched["spend_tier"],
            "purchase_amount": df_enriched["purchase_amount"].astype("float64"),
            "_fb_valid": (df_enriched["feedback_tier"].astype(str) != "Missing").astype(int),
            "_fb_promoter": (df_enriched["feedback_tier"].astype(str) == "Promoter (4-5)").astype(int),
            "_fb_detractor": (df_enriched["feedback_tier"].astype(str) == "Detractor (1-2)").astype(int),
            "_fb_spike10": (df_enriched["feedback_tier"].astype(str) == "Scale-10 Spike (10)").astype(int),
        },
        index=df_enriched.index,
    )

    count_piv = pd.pivot_table(
        work,
        index="contact_reachability_tier",
        columns="spend_tier",
        values="customer_id",
        aggfunc="count",
        observed=True,
        margins=True,
        margins_name="All",
    )
    rev_piv = pd.pivot_table(
        work,
        index="contact_reachability_tier",
        columns="spend_tier",
        values="purchase_amount",
        aggfunc="sum",
        observed=True,
        margins=True,
        margins_name="All",
    )

    grp_stats = (
        work.groupby(["contact_reachability_tier", "spend_tier"], observed=True)
        .agg(
            account_count=("customer_id", "count"),
            mean_spend_usd=("purchase_amount", "mean"),
            median_spend_usd=("purchase_amount", "median"),
            valid_feedback_n=("_fb_valid", "sum"),
            promoter_n=("_fb_promoter", "sum"),
            detractor_n=("_fb_detractor", "sum"),
            spike10_n=("_fb_spike10", "sum"),
        )
        .reset_index()
    )

    rows: list[dict[str, object]] = []
    for _, r in grp_stats.iterrows():
        reach_lbl = str(r["contact_reachability_tier"])
        spend_lbl = str(r["spend_tier"])
        acc_n = int(count_piv.loc[reach_lbl, spend_lbl])
        reach_tot = int(count_piv.loc[reach_lbl, "All"])
        spend_tot = int(count_piv.loc["All", spend_lbl])
        cell_rev = float(rev_piv.loc[reach_lbl, spend_lbl]) if spend_lbl != "Missing" else 0.0
        fb_n = int(r["valid_feedback_n"])

        rows.append(
            {
                "contact_reachability_tier": reach_lbl,
                "spend_tier": spend_lbl,
                "account_count": acc_n,
                "pct_of_reachability_tier": _r4(acc_n / reach_tot * 100.0) if reach_tot > 0 else np.nan,
                "pct_of_spend_tier": _r4(acc_n / spend_tot * 100.0) if spend_tot > 0 else np.nan,
                "pct_of_total_accounts": _r4(acc_n / n_total * 100.0) if n_total > 0 else np.nan,
                "verified_revenue_usd": _r4(cell_rev),
                "pct_of_total_revenue": _r4(cell_rev / total_rev * 100.0) if total_rev > 0 else np.nan,
                "mean_spend_usd": _r4(float(r["mean_spend_usd"])) if pd.notna(r["mean_spend_usd"]) else np.nan,
                "median_spend_usd": (
                    _r4(float(r["median_spend_usd"])) if pd.notna(r["median_spend_usd"]) else np.nan
                ),
                "valid_feedback_n": fb_n,
                "promoter_4_5_pct_of_valid_fb": _r4(int(r["promoter_n"]) / fb_n * 100.0) if fb_n > 0 else np.nan,
                "detractor_1_2_pct_of_valid_fb": (
                    _r4(int(r["detractor_n"]) / fb_n * 100.0) if fb_n > 0 else np.nan
                ),
                "scale_10_spike_pct_of_valid_fb": (
                    _r4(int(r["spike10_n"]) / fb_n * 100.0) if fb_n > 0 else np.nan
                ),
            }
        )

    return pd.DataFrame(rows)


def export_m3_summaries(
    df_enriched: pd.DataFrame | None = None,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Generate and write all three M3 multi-dimensional aggregation CSV tables."""
    if df_enriched is None:
        from src.features import engineer_features, load_enriched_customers

        enriched_csv = PROCESSED_DIR / "customers_enriched_v1.csv"
        df_enriched = (
            load_enriched_customers("v1")
            if enriched_csv.exists()
            else engineer_features(load_clean_customers("v2"))
        )

    target_dir = SUMMARIES_DIR if output_dir is None else output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, pd.DataFrame] = {
        "m3_groupby_demographic_spend.csv": build_m3_demographic_spend_groupby(df_enriched),
        "m3_pivot_country_age_spend.csv": build_m3_country_age_pivot(df_enriched),
        "m3_pivot_reachability_spend_tier.csv": build_m3_reachability_spend_tier_pivot(df_enriched),
    }

    written: dict[str, Path] = {}
    for filename, table in artifacts.items():
        out_path = target_dir / filename
        table.to_csv(out_path, index=False)
        written[filename] = out_path
    return written


def export_m2_summaries(
    df: pd.DataFrame | None = None,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Generate and write the two M2 outlier summary CSV tables deterministically."""
    clean_df = load_clean_customers("v2") if df is None else df
    target_dir = SUMMARIES_DIR if output_dir is None else output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, pd.DataFrame] = {
        "m2_iqr_outlier_summary.csv": compute_iqr_outlier_summary(clean_df),
        "m2_outlier_treatment_comparison.csv": evaluate_outlier_treatment(clean_df),
    }

    written: dict[str, Path] = {}
    for filename, table in artifacts.items():
        out_path = target_dir / filename
        table.to_csv(out_path, index=False)
        written[filename] = out_path
    return written


def export_essential_summaries(
    df: pd.DataFrame | None = None,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Generate and write all six E4-E6 summary CSV tables deterministically."""
    clean_df = load_clean_customers("v1") if df is None else df
    target_dir = SUMMARIES_DIR if output_dir is None else output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, pd.DataFrame] = {
        "e4_univariate_numeric_stats.csv": compute_univariate_numeric_stats(clean_df),
        "e4_univariate_categorical_counts.csv": compute_univariate_categorical_counts(clean_df),
        "e5_bivariate_spend_by_segment.csv": compute_bivariate_segment_spend(clean_df),
        "e5_bivariate_hypothesis_tests.csv": run_bivariate_hypothesis_tests(clean_df),
        "e5_city_country_crosstab.csv": compute_city_country_crosstab(clean_df),
        "e6_research_questions_kpis.csv": compute_research_question_kpis(clean_df),
    }

    written: dict[str, Path] = {}
    for filename, table in artifacts.items():
        out_path = target_dir / filename
        table.to_csv(out_path, index=False)
        written[filename] = out_path
    return written


if __name__ == "__main__":
    exported_e = export_essential_summaries()
    exported_m2 = export_m2_summaries()
    exported_m3 = export_m3_summaries()
    for name, path in {**exported_e, **exported_m2, **exported_m3}.items():
        print(f"Exported {name} -> {path}")
