"""Regression tests for the reference cleaning solutions."""

from pathlib import Path

import pandas as pd

from dataset.reference import _cleaning_hard, _cleaning_medium


def _assert_no_edge_whitespace(df: pd.DataFrame) -> None:
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            mask = df[col].astype(str).str.contains(r"^\s|\s$", regex=True)
            assert not mask.any(), f"column {col} still contains edge whitespace"


def test_medium_reference_trims_customer_text_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    raw_customers = pd.read_csv(root / "data" / "synthetic" / "1" / "customers_raw.csv")

    cleaned = _cleaning_medium(raw_customers)

    _assert_no_edge_whitespace(cleaned)


def test_hard_reference_trims_customer_text_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    raw_customers = pd.read_csv(root / "data" / "synthetic" / "1" / "customers_raw.csv")

    cleaned = _cleaning_hard(raw_customers)

    _assert_no_edge_whitespace(cleaned)