"""Wertet die Ergebnis-JSONs eines Experiment-Laufs aus (Kapitel 4.5 / 6).

Liest alle Result-JSONs unter data/results/<seed>/, dedupliziert auf den
jeweils neuesten Lauf je Konfiguration (Provider x Prompt x Task x Wiederholung)
und aggregiert die vier Kriterien plus Effizienz:

- Genauigkeit (accuracy)      -- zellweiser Anteil korrekter Werte
- Vollständigkeit / Konsistenz
- Erfolgsquote                -- Anteil lauffähiger, bewertbarer Läufe
- Reproduzierbarkeit (FF3)    -- Streuung der Genauigkeit über Wiederholungen
- Kosten / Tokens / Latenz

Aufruf:
    python scripts/analyze_results.py                 # Seed 1
    python scripts/analyze_results.py --seed 99
    python scripts/analyze_results.py --csv           # zusätzlich CSVs schreiben
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from config import settings  # noqa: E402
from reporting.analysis import (  # noqa: E402
    aligned_accuracy, ground_truth, llm_output,
)

# Feste Reihenfolge für die Ausgabe (leicht -> schwer je Kategorie).
_CATEGORY_ORDER = {"cleaning": 0, "dedup": 1, "transform": 2}
_DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}

# Marker für transiente API-Fehler (kein Modellversagen -> nachlaufen).
_TRANSIENT = ("503", "UNAVAILABLE", "ResourceExhausted", "429",
              "ServerError", "DeadlineExceeded", "Overloaded", "500")


def _classify(row: dict) -> str:
    """ok | api_error (transient) | code_error (Crash) | wrong_output (falsche Tabelle)."""
    if row["comparable"]:
        return "ok"
    err = row["error"] if isinstance(row["error"], str) else ""
    if any(marker in err for marker in _TRANSIENT):
        return "api_error"
    if row["exec_success"] is False:
        return "code_error"
    return "wrong_output"


_GT_CACHE: dict[tuple, pd.DataFrame] = {}


def _aligned_for_row(r, seed: int) -> float:
    """Abgeglichene Genauigkeit eines Laufs: vergleichbare Läufe übernehmen die
    strenge Zahl, nicht vergleichbare werden schema-getreu über den Schlüssel
    gegen das Soll gerechnet (lädt dafür die Ist-Tabelle)."""
    if r["status"] == "ok":
        return r["accuracy"]
    if r["status"] == "api_error":
        return float("nan")
    key = (seed, r["task_id"])
    exp = _GT_CACHE.get(key)
    if exp is None:
        exp = ground_truth(r["task_id"], seed)
        _GT_CACHE[key] = exp
    tab = llm_output(r["provider"], r["prompt_id"], r["task_id"], int(r["repetition"]), seed)
    return aligned_accuracy(tab, exp)


def _load_records(seed: int) -> pd.DataFrame:
    """Lädt alle JSONs und behält je Konfiguration nur den neuesten Lauf."""
    root = settings.results_dir / str(seed)
    rows: list[dict] = []
    for path in root.rglob("*.json"):
        d = json.loads(path.read_text(encoding="utf-8"))
        corr = d.get("correctness") or {}
        rows.append({
            "provider": d.get("provider"),
            "model": d.get("model") or d.get("requested_model"),
            "prompt_id": d.get("prompt_id"),
            "prompt_strategy": d.get("prompt_strategy"),
            "task_id": d.get("task_id"),
            "category": d.get("task_category"),
            "difficulty": d.get("task_difficulty"),
            "repetition": d.get("repetition"),
            "timestamp": d.get("timestamp"),
            "prompt_tokens": d.get("prompt_tokens"),
            "completion_tokens": d.get("completion_tokens"),
            "cost_usd": d.get("cost_usd"),
            "latency_s": d.get("llm_latency_seconds"),
            "exec_success": bool(d.get("exec_success")),
            "error": d.get("error"),
            "accuracy": corr.get("accuracy"),
            "completeness": corr.get("completeness"),
            "consistency": corr.get("consistency"),
            "comparable": bool(corr.get("comparable")),
            "schema_match": bool(corr.get("schema_match")),
        })
    if not rows:
        sys.exit(f"Keine Ergebnisse unter {root} gefunden.")

    df = pd.DataFrame(rows)
    # Regelbasierte Baseline getrennt betrachten -> hier nur LLM-Läufe.
    df = df[~df["model"].fillna("").str.startswith("rule_based")].copy()
    # Deduplizieren: pro (Provider,Prompt,Task,Wdh.) den neuesten Zeitstempel.
    df = df.sort_values("timestamp").drop_duplicates(
        subset=["provider", "prompt_id", "task_id", "repetition"], keep="last"
    )

    df["status"] = df.apply(_classify, axis=1)
    # Strenge effektive Genauigkeit: echte Fehler = 0, API-Fehler = NaN.
    df["acc_streng"] = df.apply(
        lambda r: r["accuracy"] if r["status"] == "ok"
        else (float("nan") if r["status"] == "api_error" else 0.0),
        axis=1,
    )
    # Abgeglichene Genauigkeit: bei stimmendem Schema wird auch bei abweichender
    # Zeilenzahl der Anteil korrekt reproduzierter Werte gemessen (statt hart 0).
    df["eff_accuracy"] = df.apply(lambda r: _aligned_for_row(r, seed), axis=1)
    df["acc_aligned"] = df["eff_accuracy"]
    df["valid"] = df["status"] != "api_error"      # gültige Messung?
    df["produced"] = df["status"] == "ok"          # bewertbares Ergebnis geliefert?
    df["_cat"] = df["category"].map(_CATEGORY_ORDER)
    df["_diff"] = df["difficulty"].map(_DIFFICULTY_ORDER)
    return df


def _fmt_pct(x: float) -> str:
    return f"{x * 100:5.1f}%"


def analyze(seed: int, write_csv: bool) -> None:
    df = _load_records(seed)
    n = len(df)

    print("=" * 68)
    print(f"AUSWERTUNG  Seed {seed}   |   {n} Läufe   |   "
          f"Modell(e): {', '.join(sorted(df['model'].dropna().unique()))}")
    print("=" * 68)

    # ---- Gesamtüberblick (nur gültige Messungen, API-Fehler ausgeschlossen) ----
    valid = df[df["valid"]]
    n_valid = len(valid)
    success_rate = valid["produced"].mean()
    eff_acc = valid["eff_accuracy"].mean()
    cond_acc = valid.loc[valid["produced"], "accuracy"].mean()
    n_api = int((~df["valid"]).sum())
    print(f"\n# GESAMT   ({n_valid} gültige Läufe; {n_api} API-Fehler ausgeschlossen)")
    print(f"  Erfolgsquote (lauffähig & bewertbar): {_fmt_pct(success_rate)} "
          f"({int(valid['produced'].sum())}/{n_valid})")
    print(f"  Genauigkeit effektiv (abgeglichen)  : {_fmt_pct(eff_acc)}")
    print(f"  Genauigkeit nur bewertbare Läufe    : {_fmt_pct(cond_acc)}")
    print(f"  Kosten gesamt                       : ${df['cost_usd'].sum():.4f}")
    print(f"  Tokens  in / out                    : "
          f"{int(df['prompt_tokens'].sum()):,} / {int(df['completion_tokens'].sum()):,}")
    print(f"  Latenz Ø / max                      : "
          f"{df['latency_s'].mean():.1f}s / {df['latency_s'].max():.1f}s")

    # ---- Nach Aufgabe (mit Streuung über Wiederholungen = FF3) ----
    print("\n# JE AUFGABE  (acc = abgeglichene Genauigkeit, ±Std über Wiederholungen)")
    g = (valid.sort_values(["_cat", "_diff"])
              .groupby(["category", "difficulty", "task_id"], sort=False))
    print(f"  {'Aufgabe':40} {'Erfolg':>7} {'acc Ø':>7} {'±Std':>6} {'$Ø':>8}")
    for (cat, diff, task), sub in g:
        print(f"  {task:40} {_fmt_pct(sub['produced'].mean()):>7} "
              f"{_fmt_pct(sub['eff_accuracy'].mean()):>7} "
              f"{sub['eff_accuracy'].std(ddof=0) * 100:5.1f}% "
              f"${sub['cost_usd'].mean():7.4f}")

    # ---- Nach Prompt-Strategie ----
    print("\n# JE PROMPT-STRATEGIE")
    ps = valid.groupby("prompt_id").agg(
        erfolg=("produced", "mean"),
        acc=("eff_accuracy", "mean"),
        kosten=("cost_usd", "sum"),
    ).sort_values("acc", ascending=False)
    print(f"  {'Prompt':18} {'Erfolg':>7} {'acc Ø':>7} {'$ ges':>8}")
    for pid, r in ps.iterrows():
        print(f"  {pid:18} {_fmt_pct(r['erfolg']):>7} {_fmt_pct(r['acc']):>7} "
              f"${r['kosten']:7.4f}")

    # ---- Echte Fehler (Modellschwäche) ----
    real_fail = valid[~valid["produced"]]
    if len(real_fail):
        print(f"\n# ECHTE FEHLER = MODELLSCHWÄCHE ({len(real_fail)})")
        for _, r in real_fail.sort_values(["task_id", "prompt_id"]).iterrows():
            grund = {"code_error": "Code crasht",
                     "wrong_output": "falsches Schema/Zeilenzahl"}[r["status"]]
            print(f"  {r['prompt_id']:18} {r['task_id']:40} r{r['repetition']}  ({grund})")

    # ---- API-Fehler = nachlaufen ----
    api_fail = df[df["status"] == "api_error"]
    if len(api_fail):
        print(f"\n# API-FEHLER -> NACHLAUFEN ({len(api_fail)}; NICHT gegen das Modell gewertet)")
        for _, r in api_fail.iterrows():
            print(f"  {r['prompt_id']:18} {r['task_id']:40} r{r['repetition']}")
        tasks = sorted(api_fail["task_id"].unique())
        print("\n  Betroffene Tasks erneut laufen lassen:")
        print("    python scripts/run_experiments.py --providers google \\")
        print(f"      --tasks {' '.join(tasks)}")

    if write_csv:
        out = settings.results_dir / str(seed) / "analysis"
        out.mkdir(parents=True, exist_ok=True)
        df.drop(columns=["_cat", "_diff"]).to_csv(out / "runs.csv", index=False)
        print(f"\nCSV geschrieben: {out / 'runs.csv'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--csv", action="store_true", help="Detail-CSV schreiben")
    args = parser.parse_args()
    analyze(args.seed, args.csv)
