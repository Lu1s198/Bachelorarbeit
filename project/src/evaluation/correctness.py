"""Korrektheits-Evaluation: Vergleicht Output des KI-Codes mit Ground Truth.

Kernkriterien:
- Schema-Match (Spaltennamen, Datentypen)
- Zeilenanzahl
- Wertegleichheit (zellweise)
- Behandlung von NaN/None
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class CorrectnessResult:
    schema_match: bool
    row_count_match: bool
    values_match: bool
    accuracy: float          # Anteil korrekter Zellen
    missing_columns: list[str]
    extra_columns: list[str]
    notes: str = ""


def evaluate_correctness(actual: pd.DataFrame, expected: pd.DataFrame) -> CorrectnessResult:
    """Vergleicht zwei DataFrames und liefert Korrektheits-Metriken."""
    actual_cols = set(actual.columns)
    expected_cols = set(expected.columns)
    missing = sorted(expected_cols - actual_cols)
    extra = sorted(actual_cols - expected_cols)
    schema_match = not missing and not extra

    row_count_match = len(actual) == len(expected)

    accuracy = 0.0
    values_match = False
    if schema_match and row_count_match:
        # Spalten in gleiche Reihenfolge bringen
        aligned = actual[expected.columns]
        total_cells = expected.size
        if total_cells > 0:
            matching = (aligned.fillna("__NA__") == expected.fillna("__NA__")).sum().sum()
            accuracy = float(matching) / total_cells
            values_match = accuracy == 1.0

    return CorrectnessResult(
        schema_match=schema_match,
        row_count_match=row_count_match,
        values_match=values_match,
        accuracy=accuracy,
        missing_columns=missing,
        extra_columns=extra,
    )
