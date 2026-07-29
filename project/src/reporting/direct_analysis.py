"""Analyse-Helfer für die Direkt-Verarbeitungs-Läufe (zweiter Ausführungsmodus).

Lädt die Result-JSONs aus data/results_direct/, dedupliziert auf den jüngsten
Lauf je (Provider, Task) und leitet aus den aufgezeichneten Metriken eine
*Diagnose* ab, die die vielen accuracy=0.000-Fälle trennt in:

- ``ok``               – zellweiser Abgleich möglich (Zeilenzahl + Schema passen)
- ``truncation``       – Ist deutlich kürzer als Soll -> Antwort am Token-Limit
                         abgeschnitten (der Output selbst passt nicht ins Budget)
- ``row_count_off``    – Zeilenzahl nur knapp daneben -> row_count_match scheitert,
                         der Score fällt hart auf 0 (Metrik-Strenge, kein Totalausfall)
- ``schema_mismatch``  – Spalten weichen ab
- ``content_error``    – Zeilenzahl+Schema passen prinzipiell, aber inhaltlich falsch
- ``api_error``        – transienter/technischer Fehlschlag

Die eigentlichen Ist-Tabellen (output.parquet) werden vom Runner seit dem
Persistenz-Patch mitgeschrieben; ``direct_output`` liest sie für Zell-Diffs.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import settings
from experiments.direct_runner import DIRECT_RESULTS, direct_run_dir

# Wiederverwendung der generischen Diff-Bausteine aus der Code-Gen-Analyse.
from reporting.analysis import (  # noqa: F401
    PROVIDER_LABEL, PROVIDER_ORDER, _CAT_ORDER, _DIFF_ORDER,
    aligned_accuracy, detect_key, diff_rows, diff_cells, ground_truth, heatmap,
)

_TRANSIENT = ("503", "502", "504", "500", "429", "529", "unavailable",
              "overloaded", "resourceexhausted", "deadlineexceeded",
              "rate limit", "timeout")

# Ab welchem Fehlbetrag gilt die Zeilenzahl noch als "nur knapp daneben"?
_ROW_OFF_ABS = 10          # absolute Toleranz
_ROW_OFF_FRAC = 0.05       # oder 5 % der Soll-Zeilen


def _diagnose(row) -> str:
    err = (row.error or "") if isinstance(row.error, str) else ""
    if row.comparable:
        return "ok"
    if any(m in err.lower() for m in _TRANSIENT) or row.correctness_missing:
        return "api_error"
    exp, act = row.row_expected, row.row_actual
    if exp is None or act is None:
        return "api_error"
    if not row.schema_match:
        return "schema_mismatch"
    # ab hier: Schema passt, nur die Zeilenzahl bricht den Vergleich
    deficit = exp - act
    tol = max(_ROW_OFF_ABS, int(_ROW_OFF_FRAC * exp))
    if deficit > tol:                 # Ist deutlich zu kurz -> abgeschnitten
        return "truncation"
    if abs(exp - act) <= tol:         # knapp daneben -> Metrik-Strenge
        return "row_count_off"
    return "content_error"            # zu viele Zeilen bei passendem Schema


DIAG_LABEL = {
    "ok": "auswertbar",
    "truncation": "Output abgeschnitten (Token-Limit)",
    "row_count_off": "Zeilenzahl knapp daneben (Metrik-Artefakt)",
    "schema_mismatch": "Schema weicht ab",
    "content_error": "inhaltlich abweichend",
    "api_error": "technischer Fehler",
}


def load_direct(seed: int = 1) -> pd.DataFrame:
    rows = []
    base = DIRECT_RESULTS / str(seed)
    for p in base.rglob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        c = d.get("correctness") or {}
        rows.append(dict(
            provider=d.get("provider"),
            model=d.get("model") or d.get("requested_model"),
            task_id=d.get("task_id"),
            category=d.get("task_category"),
            difficulty=d.get("task_difficulty"),
            timestamp=d.get("timestamp"),
            prompt_tokens=d.get("prompt_tokens"),
            completion_tokens=d.get("completion_tokens"),
            cost_usd=d.get("cost_usd"),
            latency_s=d.get("llm_latency_seconds"),
            n_rows_returned=d.get("n_rows_returned"),
            error=d.get("error"),
            correctness_missing=d.get("correctness") is None,
            accuracy=c.get("accuracy"),
            schema_match=bool(c.get("schema_match")),
            comparable=bool(c.get("comparable")),
            row_expected=c.get("row_count_expected"),
            row_actual=c.get("row_count_actual"),
            missing_columns=c.get("missing_columns"),
            extra_columns=c.get("extra_columns"),
        ))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("timestamp").drop_duplicates(
        ["provider", "task_id"], keep="last").reset_index(drop=True)
    df["diagnose"] = [_diagnose(r) for _, r in df.iterrows()]
    df["diagnose_label"] = df["diagnose"].map(DIAG_LABEL)
    df["label"] = df.provider.map(PROVIDER_LABEL).fillna(df.provider)
    df["_cat"] = df.category.map(_CAT_ORDER)
    df["_diff"] = df.difficulty.map(_DIFF_ORDER)
    eff, missing = _aligned_direct(df, seed)
    df["acc_effektiv"] = eff
    df["tabelle_fehlt"] = missing  # True: Ist-Tabelle nicht persistiert -> Neu-Lauf nötig
    return df.sort_values(["_cat", "_diff", "provider"]).reset_index(drop=True)


def _aligned_direct(df: pd.DataFrame, seed: int):
    """Abgeglichene Genauigkeit je Direkt-Lauf. Vergleichbare Läufe übernehmen die
    strenge Zahl; Schemafehler ergeben 0; bei stimmendem Schema, aber abweichender
    Zeilenzahl wird über die persistierte Ist-Tabelle abgeglichen. Fehlt die Tabelle
    (Lauf vor dem Persistenz-Patch), bleibt der Wert NaN und wird markiert."""
    gt_cache: dict[str, pd.DataFrame] = {}
    eff, missing = [], []
    for r in df.itertuples():
        if r.comparable:
            eff.append(r.accuracy); missing.append(False); continue
        if r.diagnose == "api_error":
            eff.append(float("nan")); missing.append(False); continue
        if not r.schema_match:
            eff.append(0.0); missing.append(False); continue
        tab = direct_output(r.provider, r.task_id, seed)
        if tab is None:
            eff.append(float("nan")); missing.append(True); continue
        exp = gt_cache.get(r.task_id)
        if exp is None:
            exp = ground_truth(r.task_id, seed); gt_cache[r.task_id] = exp
        eff.append(aligned_accuracy(tab, exp)); missing.append(False)
    return eff, missing


def direct_output(provider: str, task_id: str, seed: int = 1) -> pd.DataFrame | None:
    """Persistierte Ist-Tabelle eines Direkt-Laufs (None, wenn nicht vorhanden)."""
    d = direct_run_dir(seed, task_id, provider)
    pq, csv = d / "output.parquet", d / "output.csv"
    if pq.exists():
        return pd.read_parquet(pq)
    if csv.exists():
        return pd.read_csv(csv)
    return None


def summary_pivot(df: pd.DataFrame, value: str = "accuracy") -> pd.DataFrame:
    """Task x Provider-Pivot der gewünschten Kennzahl, in Kategorie/Schwere-Reihenfolge."""
    order = (df.drop_duplicates("task_id").sort_values(["_cat", "_diff"]).task_id)
    labels = [PROVIDER_LABEL[p] for p in PROVIDER_ORDER
              if PROVIDER_LABEL[p] in set(df.label)]
    piv = df.pivot_table(index="task_id", columns="label", values=value,
                         aggfunc="first")
    return piv.reindex(index=order, columns=labels)
