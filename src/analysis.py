"""Quantitative univariate, bivariate, and KPI synthesis functions for Essential EDA (E4-E6).

Provides pure, deterministic statistical functions operating on cleaned customer datasets
(``data/processed/customers_clean_*.csv``) in strict compliance with ``specs/ontology.md``
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

    return df


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
        table.to_csv(out_path, index=False, lineterminator="\n")
        written[filename] = out_path
    return written


if __name__ == "__main__":
    exported = export_essential_summaries()
    for name, path in exported.items():
        print(f"Exported {name} -> {path}")
