"""Tests für die Korrektheits-Evaluation."""

import pandas as pd

from ba_ki_etl.evaluation import evaluate_correctness


def test_perfect_match() -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    result = evaluate_correctness(df.copy(), df)
    assert result.schema_match
    assert result.row_count_match
    assert result.values_match
    assert result.accuracy == 1.0


def test_missing_column() -> None:
    actual = pd.DataFrame({"a": [1, 2]})
    expected = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    result = evaluate_correctness(actual, expected)
    assert not result.schema_match
    assert result.missing_columns == ["b"]


def test_partial_accuracy() -> None:
    actual = pd.DataFrame({"a": [1, 2], "b": ["x", "WRONG"]})
    expected = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    result = evaluate_correctness(actual, expected)
    assert result.schema_match
    assert not result.values_match
    assert result.accuracy == 0.75  # 3 von 4 Zellen
