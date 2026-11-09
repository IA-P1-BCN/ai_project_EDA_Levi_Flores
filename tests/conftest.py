"""Shared test fixtures for the customer EDA test suite."""

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_records() -> pd.DataFrame:
    """Return a minimal synthetic DataFrame with all known raw corruption patterns.

    Uses positionally aligned IDs for existing non-empty slots (C00002, C00005)
    matching the project contract in reconstruct_customer_ids.
    """
    return pd.DataFrame(
        {
            "CustomerID": ["", "C00002", None, "   ", "C00005"],
            "Name": ["john doe", "  JANE SMITH  ", "", None, "ALICE BROWN"],
            "Gender": ["m", "Female", "FEMALE", "", "f"],
            "Age": ["-5", "200", "34", "105", ""],
            "City": ["mumbai", "Bangalore", "", "   ", "delhi"],
            "Signup_Date": ["01/01/2022", "not_a_date", "15/06/2021", "", "20/03/2023"],
            "Last_purchase_date": ["15/01/2021", "missing", "20/06/2021", "", "10/01/2023"],
            "purchase_amount": ["-999", "N/A", "1500.50", "0", ""],
            "feedback_score": ["-1", "10", "4", "5", ""],
            "email": ["john@example.com", "not_an_email", "jane.doe@company.org", "", "test@domain"],
            "Phone_number": ["9876543210", "abc123", "0", "1234567890", ""],
            "Country": ["USA", "India", "UK", "", "Canada"],
        }
    )


@pytest.fixture
def clean_baseline_record() -> pd.DataFrame:
    """Return a single pristine customer record matching the expected schema."""
    return pd.DataFrame(
        {
            "CustomerID": ["C00001"],
            "Name": ["Priya Sharma"],
            "Gender": ["Female"],
            "Age": ["28"],
            "City": ["Mumbai"],
            "Signup_Date": ["10/01/2022"],
            "Last_purchase_date": ["15/08/2022"],
            "purchase_amount": ["1250.00"],
            "feedback_score": ["4"],
            "email": ["priya.sharma@example.in"],
            "Phone_number": ["9876543210"],
            "Country": ["India"],
        }
    )
