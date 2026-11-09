"""Unit test suite for the reproducible CLI pipeline (Task X1)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pipeline import run_pipeline


def test_run_pipeline_end_to_end(tmp_path: Path) -> None:
    """Test full execution of run_pipeline writing to temporary directories."""
    proc_dir = tmp_path / "processed"
    # Deliberately NOT <proc_dir>/summaries, so the --summary-dir override is exercised.
    summ_dir = tmp_path / "custom_summaries"

    artifacts = run_pipeline(
        output_dir=proc_dir,
        summary_dir=summ_dir,
        export_summaries=True,
        verbose=False,
    )

    assert "customers_clean_v1" in artifacts
    assert "customers_clean_v2" in artifacts
    assert "customers_enriched_v1" in artifacts
    assert "customers_enriched_v2" in artifacts

    # Check files exist on disk
    for path in artifacts.values():
        assert path.exists()
        assert path.stat().st_size > 0

    # Validate output schema
    df_clean_v2 = pd.read_csv(artifacts["customers_clean_v2"])
    assert len(df_clean_v2) == 10000
    assert df_clean_v2.shape[1] == 21

    df_enriched_v2 = pd.read_csv(artifacts["customers_enriched_v2"])
    assert len(df_enriched_v2) == 10000
    assert df_enriched_v2.shape[1] == 30

    # M1 and A3 audit tables must follow --summary-dir instead of <output_dir>/summaries.
    for name in (
        "m1_cleaning_decisions_audit.csv",
        "m1_imputation_variance_impact.csv",
        "a3_suspicious_data_audit.csv",
    ):
        assert (summ_dir / name).exists(), f"{name} missing from the requested summary directory"
    assert not (proc_dir / "summaries").exists()
