"""End-to-end reproducible data processing and enrichment pipeline (Task X1).

Orchestrates ingestion, sentinel remediation, schema casting, quality auditing,
feature engineering, auxiliary geographic enrichment, and summary table exports.

CLI Usage:
    python -m src.pipeline
    python -m src.pipeline --verbose
    python -m src.pipeline --output-dir custom_dir --raw-path custom_raw.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.analysis import (
    export_advanced_summaries,
    export_essential_summaries,
    export_m2_summaries,
    export_m3_summaries,
    export_m5_summaries,
    export_m6_summaries,
)
from src.cleaning import (
    clean_customers,
    export_a3_artifacts,
    export_m1_artifacts,
    load_raw_customers,
    validate_cleaned_customers,
)
from src.features import (
    engineer_features,
    enrich_with_external_metro_data,
    validate_enriched_customers,
)

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_RAW_PATH: Path = REPO_ROOT / "data" / "raw" / "messy_customer_data.csv"
DEFAULT_PROCESSED_DIR: Path = REPO_ROOT / "data" / "processed"
DEFAULT_SUMMARIES_DIR: Path = DEFAULT_PROCESSED_DIR / "summaries"


def run_pipeline(
    raw_path: Path | None = None,
    output_dir: Path | None = None,
    summary_dir: Path | None = None,
    export_summaries: bool = True,
    verbose: bool = True,
) -> dict[str, Path]:
    """Execute the full customer data cleaning, feature engineering and export pipeline.

    Parameters
    ----------
    raw_path : Path | None
        Path to raw customer CSV. Defaults to ``data/raw/messy_customer_data.csv``.
    output_dir : Path | None
        Directory where processed CSVs are saved. Defaults to ``data/processed/``.
    summary_dir : Path | None
        Directory where summary tables are saved. Defaults to ``data/processed/summaries/``.
    export_summaries : bool
        Whether to export all intermediate analytical summary tables.
    verbose : bool
        Whether to print step-by-step telemetry to stdout.

    Returns
    -------
    dict[str, Path]
        Dictionary mapping artifact identifiers to generated file paths.
    """
    start_time = time.perf_counter()
    raw_csv = raw_path if raw_path is not None else DEFAULT_RAW_PATH
    proc_dir = output_dir if output_dir is not None else DEFAULT_PROCESSED_DIR
    summ_dir = summary_dir if summary_dir is not None else DEFAULT_SUMMARIES_DIR

    proc_dir.mkdir(parents=True, exist_ok=True)
    summ_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, Path] = {}

    def log(msg: str) -> None:
        if verbose:
            print(f"[pipeline] {msg}")

    # Step 1: Raw Ingestion
    log(f"Step 1/6: Loading raw dataset from {raw_csv.name}...")
    df_raw = load_raw_customers(raw_csv)
    log(f"  Loaded {len(df_raw):,} raw records with {len(df_raw.columns)} columns.")

    # Step 2: Data Cleaning & Sentinel Remediation (customers_clean_v1.csv and v2)
    log("Step 2/6: Executing modular cleaning and sentinel remediation...")
    df_clean_v2 = clean_customers(df_raw)
    validate_cleaned_customers(df_clean_v2, expected_rows=len(df_raw))

    v2_path = proc_dir / "customers_clean_v2.csv"
    df_clean_v2.to_csv(v2_path, index=False)
    artifacts["customers_clean_v2"] = v2_path
    log(f"  Exported {v2_path.name} ({len(df_clean_v2):,} rows x {len(df_clean_v2.columns)} cols).")

    # Maintain backwards-compatible v1 dataset (first 15 columns)
    v1_cols = [
        "customer_id", "name", "gender", "age", "city", "signup_date", "last_purchase_date",
        "purchase_amount", "feedback_score", "email", "phone_number", "country",
        "has_valid_email", "has_valid_phone", "is_date_inverted",
    ]
    df_clean_v1 = df_clean_v2[v1_cols].copy()
    v1_path = proc_dir / "customers_clean_v1.csv"
    df_clean_v1.to_csv(v1_path, index=False)
    artifacts["customers_clean_v1"] = v1_path
    log(f"  Exported {v1_path.name} ({len(df_clean_v1):,} rows x {len(df_clean_v1.columns)} cols).")

    # Step 3: Feature Engineering (customers_enriched_v1.csv)
    log("Step 3/6: Deriving behavioral, temporal and tier features...")
    df_enriched_v1 = engineer_features(df_clean_v2)
    validate_enriched_customers(df_enriched_v1, expected_rows=len(df_raw), version="v1")

    enriched_v1_path = proc_dir / "customers_enriched_v1.csv"
    df_enriched_v1.to_csv(enriched_v1_path, index=False)
    artifacts["customers_enriched_v1"] = enriched_v1_path
    log(f"  Exported {enriched_v1_path.name} ({len(df_enriched_v1):,} rows x {len(df_enriched_v1.columns)} cols).")

    # Step 4: Auxiliary Geospatial & Macroeconomic Enrichment (customers_enriched_v2.csv)
    log("Step 4/6: Joining auxiliary Indian metropolitan catalog...")
    df_enriched_v2 = enrich_with_external_metro_data(df_enriched_v1)
    validate_enriched_customers(df_enriched_v2, expected_rows=len(df_raw), version="v2")

    enriched_v2_path = proc_dir / "customers_enriched_v2.csv"
    df_enriched_v2.to_csv(enriched_v2_path, index=False)
    artifacts["customers_enriched_v2"] = enriched_v2_path
    log(f"  Exported {enriched_v2_path.name} ({len(df_enriched_v2):,} rows x {len(df_enriched_v2.columns)} cols).")

    # Step 5: Analytical Summary Table Exports
    if export_summaries:
        log("Step 5/6: Exporting comprehensive analytical summary tables...")
        # M1 and A3 quality audits
        export_m1_artifacts(output_dir=proc_dir)
        export_a3_artifacts(output_dir=proc_dir)

        # Essential, Medium and Advanced summary tables
        export_essential_summaries(df_clean_v1, output_dir=summ_dir)
        export_m2_summaries(df_clean_v2, output_dir=summ_dir)
        export_m3_summaries(df_enriched_v1, output_dir=summ_dir)
        export_m5_summaries(df_enriched_v1, output_dir=summ_dir)
        export_m6_summaries(df_enriched_v1, output_dir=summ_dir)
        export_advanced_summaries(df_enriched_v2, output_dir=summ_dir)
        log(f"  Exported all summary tables to {summ_dir.name}/.")
    else:
        log("Step 5/6: Skipping summary exports (--skip-summaries).")

    # Step 6: Final Verification
    elapsed = time.perf_counter() - start_time
    log(f"Step 6/6: Pipeline finished successfully in {elapsed:.2f}s!")
    return artifacts


def main() -> int:
    """CLI entrypoint for executing the customer data processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Execute reproducible end-to-end customer cleaning and feature engineering pipeline."
    )
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=None,
        help="Optional override path for raw customer data CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override directory for processed datasets.",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=None,
        help="Optional override directory for summary tables.",
    )
    parser.add_argument(
        "--skip-summaries",
        action="store_true",
        help="Skip generation of auxiliary summary tables.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational stdout logs.",
    )
    args = parser.parse_args()

    try:
        run_pipeline(
            raw_path=args.raw_path,
            output_dir=args.output_dir,
            summary_dir=args.summary_dir,
            export_summaries=not args.skip_summaries,
            verbose=not args.quiet,
        )
        return 0
    except (RuntimeError, ValueError, FileNotFoundError, OSError, AssertionError) as exc:
        print(f"[pipeline ERROR] Execution failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
