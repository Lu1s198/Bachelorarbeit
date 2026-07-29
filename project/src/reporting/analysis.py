"""Analyse-Helfer für die Auswertungs-Notebooks (Kapitel 6).

Lädt die Result-JSONs (LLM + regelbasierte Baseline), dedupliziert auf den
neuesten Lauf je Konfiguration, klassifiziert Fehler und stellt Bausteine für
Vergleiche, Heatmaps und konkrete Zell-/Zeilen-Diffs bereit.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from baseline import run_baseline_task
from config import settings
from dataset.scenarios import ALL_TASKS, get_task

PROVIDER_LABEL = {
    "anthropic": "Claude", "openai": "GPT", "google": "Gemini",
    "ollama": "Llama", "baseline": "Baseline",
}
PROVIDER_ORDER = ["anthropic", "openai", "google", "ollama", "baseline"]

_CAT_ORDER = {"cleaning": 0, "deduplication": 1, "transformation": 2}
_DIFF_ORDER = {"easy": 0, "medium": 1, "hard": 2}
_TRANSIENT = ("503", "502", "504", "500", "429", "529", "unavailable",
              "overloaded", "resourceexhausted", "deadlineexceeded",
              "rate limit", "timeout")


# ---------------------------------------------------------------- Laden

def _classify(comparable: bool, error, exec_success) -> str:
    if comparable:
        return "ok"
    err = error.lower() if isinstance(error, str) else ""
    if any(m in err for m in _TRANSIENT):
        return "api_error"
    if exec_success is False:
        return "code_error"
    return "wrong_output"


def load_runs(seed: int = 1, include_baseline: bool = True,
              aligned: bool = True) -> pd.DataFrame:
    rows = []
    for p in (settings.results_dir / str(seed)).rglob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        c = d.get("correctness") or {}
        rows.append(dict(
            provider=d.get("provider"),
            model=d.get("model") or d.get("requested_model"),
            prompt_id=d.get("prompt_id"), task_id=d.get("task_id"),
            category=d.get("task_category"), difficulty=d.get("task_difficulty"),
            repetition=d.get("repetition"), timestamp=d.get("timestamp"),
            prompt_tokens=d.get("prompt_tokens"), completion_tokens=d.get("completion_tokens"),
            cost_usd=d.get("cost_usd"), latency_s=d.get("llm_latency_seconds"),
            exec_success=d.get("exec_success"), error=d.get("error"),
            accuracy=c.get("accuracy"), completeness=c.get("completeness"),
            consistency=c.get("consistency"), comparable=bool(c.get("comparable")),
            schema_match=bool(c.get("schema_match")),
            row_expected=c.get("row_count_expected"), row_actual=c.get("row_count_actual"),
        ))
    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").drop_duplicates(
        ["provider", "prompt_id", "task_id", "repetition"], keep="last")
    if not include_baseline:
        df = df[df.provider != "baseline"]
    df["status"] = [_classify(a, b, c) for a, b, c in
                    zip(df.comparable, df.error, df.exec_success)]
    # Strenge effektive Genauigkeit (bisheriges Verhalten): nicht vergleichbare
    # Läufe zählen als 0, API-Fehler als NaN.
    df["acc_streng"] = np.where(
        df.comparable, df.accuracy,
        np.where(df.status == "api_error", np.nan, 0.0))
    # Abgeglichene Genauigkeit: bei stimmendem Schema wird auch bei abweichender
    # Zeilenzahl der Anteil korrekt reproduzierter Werte gemessen (kein harter
    # Absturz auf 0, wenn z.B. 519 von 520 Zeilen korrekt sind).
    df["acc_aligned"] = _aligned_column(df, seed) if aligned else df["acc_streng"]
    df["eff_accuracy"] = df["acc_aligned"]
    df["produced"] = df.status == "ok"
    df["valid"] = df.status != "api_error"
    df["label"] = df.provider.map(PROVIDER_LABEL).fillna(df.provider)
    df["_cat"] = df.category.map(_CAT_ORDER)
    df["_diff"] = df.difficulty.map(_DIFF_ORDER)
    return df


def _aligned_column(df: pd.DataFrame, seed: int) -> list:
    """Berechnet die abgeglichene Genauigkeit je Lauf (lädt Ist-Tabellen nur für
    nicht direkt vergleichbare Läufe; vergleichbare übernehmen die strenge Zahl)."""
    gt_cache: dict[str, pd.DataFrame] = {}
    base_cache: dict[str, pd.DataFrame] = {}
    out = []
    for r in df.itertuples():
        if r.comparable:
            out.append(r.accuracy)
            continue
        if r.status == "api_error":
            out.append(np.nan)
            continue
        exp = gt_cache.get(r.task_id)
        if exp is None:
            exp = ground_truth(r.task_id, seed)
            gt_cache[r.task_id] = exp
        if r.provider == "baseline":
            tab = base_cache.get(r.task_id)
            if tab is None:
                tab = baseline_output(r.task_id, seed)
                base_cache[r.task_id] = tab
        else:
            tab = llm_output(r.provider, r.prompt_id, r.task_id, int(r.repetition), seed)
        out.append(aligned_accuracy(tab, exp))
    return out


def tasks_of(df: pd.DataFrame, category: str) -> list[str]:
    sub = df[df.category == category]
    return list(sub.sort_values("_diff").drop_duplicates("task_id").task_id)


def ordered_labels(df: pd.DataFrame) -> list[str]:
    present = set(df.label)
    return [PROVIDER_LABEL[p] for p in PROVIDER_ORDER
            if PROVIDER_LABEL[p] in present]


# ---------------------------------------------------------------- Daten je Lauf

def ground_truth(task_id: str, seed: int = 1) -> pd.DataFrame:
    return pd.read_parquet(settings.ground_truth_dir / str(seed) / get_task(task_id).expected_output)


def baseline_output(task_id: str, seed: int = 1) -> pd.DataFrame:
    return run_baseline_task(task_id, seed=seed)


def llm_output(provider: str, prompt_id: str, task_id: str, rep: int,
               seed: int = 1) -> pd.DataFrame | None:
    run_id = f"{provider}_{prompt_id}_{task_id}_r{rep}"
    p = settings.results_dir / str(seed) / task_id / run_id / "output.parquet"
    return pd.read_parquet(p) if p.exists() else None


# ---------------------------------------------------------------- Diffs

KEY_CANDIDATES = ["customer_id", "product_id", "order_id"]


def detect_key(expected: pd.DataFrame):
    for k in KEY_CANDIDATES:
        if k in expected.columns:
            return k
    if {"country_code", "category"}.issubset(expected.columns):
        return ["country_code", "category"]
    return None


def diff_rows(actual, expected, key=None):
    """Übersehene (Soll, fehlt im Ist) und überzählige (Ist, nicht im Soll) Zeilen."""
    if actual is None:
        return None, None
    key = key or detect_key(expected)
    keys = [key] if isinstance(key, str) else list(key)
    if not set(keys).issubset(actual.columns):
        return None, None
    e, a = expected.copy(), actual.copy()
    for k in keys:  # Typangleich: manche LLM-Outputs liefern IDs als String
        e[k] = e[k].astype(str)
        a[k] = a[k].astype(str)
    m = e[keys].merge(a[keys], on=keys, how="outer", indicator=True)
    missed = e.merge(m[m["_merge"] == "left_only"][keys], on=keys)
    extra = a.merge(m[m["_merge"] == "right_only"][keys], on=keys)
    return missed, extra


def diff_cells(actual, expected, key=None) -> pd.DataFrame:
    """Zellen, in denen Ist vom Soll abweicht. Duplikat-Schlüssel werden über
    einen Vorkommens-Index (occ) 1:1 zugeordnet (setzt gleiche Zeilenreihenfolge
    voraus, wie sie Cleaning-Aufgaben erhalten)."""
    if actual is None:
        return pd.DataFrame()
    key = key or detect_key(expected)
    keys = [key] if isinstance(key, str) else list(key)
    if not set(keys).issubset(actual.columns):
        return pd.DataFrame([{"hinweis": "Schlüsselspalte fehlt im Ist – Schema passt nicht"}])
    e, a = expected.copy(), actual.copy()
    for k in keys:  # Typangleich (int/str) für den Schlüssel
        e[k] = e[k].astype(str)
        a[k] = a[k].astype(str)
    e["_occ"] = e.groupby(keys).cumcount()
    a["_occ"] = a.groupby(keys).cumcount()
    merged = e.merge(a, on=keys + ["_occ"], how="inner", suffixes=("_soll", "_ist"))
    recs = []
    for col in [c for c in expected.columns if c not in keys]:
        s, i = merged[f"{col}_soll"], merged[f"{col}_ist"]
        if is_numeric_dtype(s) and is_numeric_dtype(i):
            neq = ~np.isclose(s.astype(float), i.astype(float),
                              rtol=1e-5, atol=1e-2, equal_nan=True)
        else:
            neq = s.fillna("∅").astype(str) != i.fillna("∅").astype(str)
        for _, row in merged.loc[neq].iterrows():
            kv = row[keys[0]] if len(keys) == 1 else tuple(row[k] for k in keys)
            recs.append({"schluessel": kv, "spalte": col,
                         "soll": row[f"{col}_soll"], "ist": row[f"{col}_ist"]})
    return pd.DataFrame(recs)


# ---------------------------------------------------------------- Abgeglichene Genauigkeit

def _cellwise_eq(soll: pd.Series, ist: pd.Series) -> np.ndarray:
    """Boolesche Gleichheit je Zelle: numerisch toleriert kleine Abweichungen,
    sonst String-Vergleich (fehlende Werte einheitlich behandelt)."""
    if is_numeric_dtype(soll) and is_numeric_dtype(ist):
        return np.isclose(soll.astype(float).to_numpy(), ist.astype(float).to_numpy(),
                          rtol=1e-5, atol=1e-2, equal_nan=True)
    return (soll.fillna("∅").astype(str).to_numpy()
            == ist.fillna("∅").astype(str).to_numpy())


def _unique_key(expected: pd.DataFrame, actual: pd.DataFrame):
    """Wählt einen im Soll eindeutigen Schlüssel, der auch im Ist vorhanden ist.
    Nötig, weil manche Tabellen mehrere ID-Spalten führen (z.B. orders mit
    customer_id UND order_id), aber nur eine davon zeilenweise eindeutig ist."""
    for k in ("order_id", "product_id", "customer_id"):
        if k in expected.columns and k in actual.columns and expected[k].is_unique:
            return k
    kk = ["country_code", "category"]
    if set(kk).issubset(expected.columns) and set(kk).issubset(actual.columns) \
            and not expected.duplicated(kk).any():
        return kk
    return None


def aligned_accuracy(actual, expected, key=None) -> float:
    """Schema-getreue, zeilenzahl-tolerante Genauigkeit.

    Im Unterschied zur strengen Bewertung (die exakt gleiche Zeilenzahl verlangt und
    andernfalls 0 liefert) gleicht diese Kennzahl Ist und Soll über einen eindeutigen
    Schlüssel ab und misst den Anteil korrekt reproduzierter Werte. Fehlende und
    überzählige Zeilen zählen über den Nenner ``max(Soll, Ist)`` gegen das Ergebnis,
    sodass ein knapp danebenliegendes Resultat (etwa 519 statt 520 korrekten Zeilen)
    einen Wert nahe 1 statt 0 erhält. Voraussetzung ist ein übereinstimmendes Schema:
    fehlt eine Soll-Spalte im Ist, ist der Wert 0.
    """
    if actual is None or len(expected) == 0:
        return 0.0
    exp_cols = list(expected.columns)
    if not set(exp_cols).issubset(actual.columns):
        return 0.0  # Schema passt nicht -> kein sinnvoller Abgleich
    e, a = expected.copy(), actual[exp_cols].copy()
    key = key or _unique_key(e, a)

    if key is None:  # kein eindeutiger Schlüssel -> positionsbasiert nach Sortierung
        es = e.sort_values(by=exp_cols, key=lambda s: s.astype(str)).reset_index(drop=True)
        as_ = a.sort_values(by=exp_cols, key=lambda s: s.astype(str)).reset_index(drop=True)
        n = min(len(es), len(as_))
        correct = sum(int(_cellwise_eq(es[c].iloc[:n], as_[c].iloc[:n]).sum())
                      for c in exp_cols)
        denom = max(len(e), len(a)) * len(exp_cols)
        return correct / denom if denom else 0.0

    keys = [key] if isinstance(key, str) else list(key)
    for k in keys:
        e[k] = e[k].astype(str)
        a[k] = a[k].astype(str)
    e["_occ"] = e.groupby(keys).cumcount()
    a["_occ"] = a.groupby(keys).cumcount()
    merged = e.merge(a, on=keys + ["_occ"], how="inner", suffixes=("_soll", "_ist"))
    noncols = [c for c in exp_cols if c not in keys]
    correct = sum(int(_cellwise_eq(merged[f"{c}_soll"], merged[f"{c}_ist"]).sum())
                  for c in noncols)
    denom = max(len(expected), len(actual)) * len(noncols)
    return correct / denom if denom else 0.0


# ---------------------------------------------------------------- Plot

def heatmap(pivot: pd.DataFrame, ax=None, title: str = "",
            vmin: float = 0.0, vmax: float = 1.0, cmap: str = "RdYlGn",
            pct: bool = True):
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots(
            figsize=(1.15 * len(pivot.columns) + 3, 0.55 * len(pivot.index) + 1.6))
    vals = pivot.values.astype(float)
    im = ax.imshow(vals, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns], rotation=30, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(i) for i in pivot.index])
    for r in range(vals.shape[0]):
        for c in range(vals.shape[1]):
            v = vals[r, c]
            if not np.isnan(v):
                ax.text(c, r, f"{v * 100:.0f}" if pct else f"{v:.2f}",
                        ha="center", va="center", fontsize=9)
    ax.set_title(title)
    return ax
