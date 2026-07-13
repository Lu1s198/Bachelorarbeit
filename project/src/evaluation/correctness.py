"""Evaluation der Ergebnisse gegen die Ground Truth (Kapitel 4.5).

Operationalisiert die vier Kriterien:
- Genauigkeit  (accuracy):      Anteil zellweise korrekter Werte
- Vollständigkeit (completeness): erwartete Spalten vorhanden + Datensatzanzahl
- Konsistenz   (consistency):   Übereinstimmung der Datentypen mit dem Sollschema
- (Effizienz wird im Runner erhoben: Zeit, Tokens, Kosten)

Der Vergleich ist bewusst reihenfolge-unabhängig: LLM-erzeugter Code liefert
korrekte Ergebnisse häufig in abweichender Zeilenreihenfolge. Vor dem
zellweisen Abgleich werden beide Tabellen nach allen Spalten sortiert.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


@dataclass
class CorrectnessResult:
    schema_match: bool
    row_count_match: bool
    values_match: bool
    accuracy: float                 # Genauigkeit: Anteil korrekter Zellen [0, 1]
    completeness: float             # Vollständigkeit: Spalten + Zeilen [0, 1]
    consistency: float              # Konsistenz: Anteil dtyp-konformer Spalten [0, 1]
    row_count_expected: int
    row_count_actual: int
    missing_columns: list[str]
    extra_columns: list[str]
    comparable: bool                # True, wenn ein zellweiser Abgleich möglich war
    notes: str = ""


def _sorted(df: pd.DataFrame) -> pd.DataFrame:
    """Reihenfolge-unabhängig machen: nach allen Spalten (als Text) sortieren."""
    cols = list(df.columns)
    return df.sort_values(by=cols, key=lambda s: s.astype(str)).reset_index(drop=True)


def evaluate_correctness(actual: pd.DataFrame, expected: pd.DataFrame) -> CorrectnessResult:
    """Vergleicht Ergebnis- und Soll-DataFrame und liefert die Kriterien."""
    actual_cols = set(actual.columns)
    expected_cols = set(expected.columns)
    missing = sorted(expected_cols - actual_cols)
    extra = sorted(actual_cols - expected_cols)
    schema_match = not missing and not extra

    row_count_match = len(actual) == len(expected)

    # Vollständigkeit: Anteil vorhandener Soll-Spalten * Verhältnis der Zeilenzahl.
    col_ratio = 1.0 - len(missing) / len(expected_cols) if expected_cols else 0.0
    if len(expected) == 0:
        row_ratio = 1.0 if len(actual) == 0 else 0.0
    else:
        row_ratio = min(len(actual), len(expected)) / max(len(actual), len(expected), 1)
    completeness = col_ratio * row_ratio

    accuracy = 0.0
    consistency = 0.0
    values_match = False
    comparable = schema_match and row_count_match and len(expected) > 0

    if comparable:
        a = _sorted(actual[list(expected.columns)])
        e = _sorted(expected)

        total_cells = e.size
        matching = 0
        cols_type_ok = 0
        for col in e.columns:
            ec, ac = e[col], a[col]
            if is_numeric_dtype(ec) and is_numeric_dtype(ac):
                eq = np.isclose(
                    ac.astype(float).to_numpy(),
                    ec.astype(float).to_numpy(),
                    rtol=1e-05,
                    atol=1e-02,
                    equal_nan=True,
                )
                cols_type_ok += 1
            else:
                eq = ac.fillna("__NA__").astype(str).to_numpy() == ec.fillna(
                    "__NA__"
                ).astype(str).to_numpy()
                # Konsistenz: nicht-numerische Spalte gilt als typkonform,
                # wenn die Soll-Spalte ebenfalls nicht-numerisch ist.
                cols_type_ok += int(not is_numeric_dtype(ec))
            matching += int(eq.sum())

        accuracy = matching / total_cells if total_cells else 0.0
        consistency = cols_type_ok / len(e.columns) if len(e.columns) else 0.0
        values_match = accuracy == 1.0

    return CorrectnessResult(
        schema_match=schema_match,
        row_count_match=row_count_match,
        values_match=values_match,
        accuracy=accuracy,
        completeness=completeness,
        consistency=consistency,
        row_count_expected=len(expected),
        row_count_actual=len(actual),
        missing_columns=missing,
        extra_columns=extra,
        comparable=comparable,
    )
