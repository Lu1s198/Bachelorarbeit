"""Prompting-Strategien auf gedrittelter Strecke (Kapitel 8).

Die Einzelaufgaben-Matrix stellt jede der neun Aufgaben fuer sich auf die
Rohdaten. Fuer die schweren Stufen bedeutet das, dass eine Aufgabe alle
vorgelagerten Maengel mitbehandeln muss: ``transform_hard`` verlangt Bereinigung,
Verknuepfung und Aggregation in einem Zug und wurde deshalb von keinem Modell
und in keiner Strategie geloest. Ein Vergleich der Prompting-Strategien auf einer
Aufgabe, die alle gleichermassen auf 0 setzt, unterscheidet sie nicht -- die
Messung ist dort blind.

Dieses Modul bildet den Mittelweg zwischen Einzelaufgabe und Neunerkette: Die
neun Schritte werden zu drei Gruppen zu je drei Schritten zusammengefasst, und
jede Gruppe erhaelt die *Soll*-Ausgabe ihrer Vorgaengergruppe als Eingabe. Damit
bleibt die Komposition mehrerer Verarbeitungsschritte als Anforderung erhalten --
genau die Eigenschaft, an der sich Strategien wie Chain-of-Thought bewaehren
sollten --, ohne dass Fehler aus einer frueheren Gruppe das Ergebnis
ueberdecken. Die Obergrenze liegt fuer jede Gruppe bei 1,0.

Ergebnisse: data/results_group/<seed>/<gruppe>/<provider>_<prompt>/
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from experiments.code_execution import extract_code, run_generated_code
from experiments.pipeline_runner import (
    CUSTOMER_COLS, FINAL_COLS, PIPELINE, _column_types, _read_table,
    _reference_dir, build_chain_reference, materialize_reference,
)
from experiments.runner import _generate_with_retry
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd
from llm.prompt import load_prompt
from reporting.analysis import aligned_accuracy

GROUP_RESULTS = settings.data_dir / "results_group"


@dataclass(frozen=True)
class Group:
    name: str
    label: str
    steps: list[str]                    # Schritte der Pipeline, in Reihenfolge
    inputs: list[tuple[str, str]]       # (Rolle, "raw:<datei>" | "step:<name>")
    expected_cols: list[str]
    target: str                         # Schritt, gegen dessen Soll bewertet wird


GROUPS: list[Group] = [
    Group("cleaning", "Gruppe 1 · Bereinigung (Schritte 1-3)",
          ["cleaning_easy", "cleaning_medium", "cleaning_hard"],
          [("input", "raw:customers_raw.csv")],
          CUSTOMER_COLS, "cleaning_hard"),
    Group("dedup", "Gruppe 2 · Deduplizierung (Schritte 4-6)",
          ["dedup_easy", "dedup_medium", "dedup_hard"],
          [("input", "step:cleaning_hard")],
          CUSTOMER_COLS, "dedup_hard"),
    Group("transform", "Gruppe 3 · Transformation (Schritte 7-9)",
          ["products", "orders", "final"],
          [("products", "raw:products_raw.csv"), ("orders", "raw:orders_raw.csv"),
           ("customers", "step:dedup_hard")],
          FINAL_COLS, "final"),
]

_STEP = {s.name: s for s in PIPELINE}


def _resolve(group: Group, seed: int) -> list[tuple[str, Path]]:
    """Eingabepfade einer Gruppe. Schritt-Abhaengigkeiten kommen immer aus der
    materialisierten Kettenreferenz -- die Gruppen sind gegeneinander entkoppelt."""
    out = []
    for role, src in group.inputs:
        if src.startswith("raw:"):
            out.append((role, settings.synthetic_dir / str(seed) / src[4:]))
        else:
            dep = src.split(":", 1)[1]
            out.append((role, _reference_dir(seed) / dep / "output.parquet"))
    return out


def _task_description(group: Group, resolved: list[tuple[str, Path]]) -> str:
    """Aufgabentext einer Gruppe: die Anweisungen ihrer drei Schritte, nummeriert.

    Die Schrittanweisungen werden woertlich uebernommen, damit die Gruppe
    inhaltlich exakt dasselbe verlangt wie die drei Einzelschritte der Kette und
    der Vergleich beider Betrachtungsweisen zulaessig bleibt."""
    zeilen = [f"Perform the following {len(group.steps)} transformation steps in "
              f"order on the input data:", ""]
    for i, name in enumerate(group.steps, 1):
        zeilen.append(f"{i}. {_STEP[name].instruction}")
        zeilen.append("")
    zeilen += ["Input file(s):"]
    for role, path in resolved:
        zeilen.append(f"  - {role}: {path.as_posix()}")
        typen = _column_types(path)
        if typen:
            zeilen.append(f"    columns as read by pandas: {typen}")
    zeilen += ["",
               "Only the result of the last step is written out. It must contain "
               f"(at least) the columns: {', '.join(group.expected_cols)}."]
    return "\n".join(zeilen)


def run_group(provider_name: str, prompt_id: str, group: Group, seed: int,
              attempts: int = 3, model: str | None = None,
              repetition: int = 1) -> dict:
    """Fuehrt eine Gruppe mit einer Prompt-Strategie aus und bewertet sie."""
    provider = get_provider(provider_name, model=model)
    chain_ref = build_chain_reference(seed)
    expected_df = chain_ref[group.target]

    lauf = f"{provider_name}_{prompt_id}" + (f"_r{repetition}" if repetition > 1 else "")
    base = GROUP_RESULTS / str(seed) / group.name / lauf
    out_path = base / "output.parquet"
    script_path = base / "script.py"

    resolved = _resolve(group, seed)
    prompt = load_prompt(prompt_id)
    user_prompt = prompt.render(
        task_description=_task_description(group, resolved),
        input_dir=(settings.synthetic_dir / str(seed)).as_posix(),
        output_path=out_path.as_posix(),
        target_schema=", ".join(group.expected_cols),
    )

    rec: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name, "prompt_id": prompt_id,
        "prompt_strategy": prompt.strategy, "group": group.name,
        "group_label": group.label, "steps": group.steps, "seed": seed,
        "repetition": repetition,
    }

    status, accuracy, error = "code_error", None, None
    cost, ptok, ctok, llm_s, exec_s = 0.0, 0, 0, 0.0, 0.0
    code, used = "", 0
    t0 = time.perf_counter()

    for versuch in range(1, attempts + 1):
        used = versuch
        try:
            resp = _generate_with_retry(
                provider, user_prompt, system=prompt.system, temperature=0.0,
                max_tokens=settings.max_output_tokens)
            ptok += resp.prompt_tokens or 0
            ctok += resp.completion_tokens or 0
            llm_s += resp.latency_seconds or 0.0
            cost += estimate_cost_usd(resp.model, resp.prompt_tokens,
                                      resp.completion_tokens) or 0.0
            code = extract_code(resp.text)
            ausf = run_generated_code(code, script_path, out_path)
            exec_s += ausf.duration_seconds or 0.0
            if not ausf.success or not out_path.exists():
                error = (ausf.stderr or "keine Ausgabedatei").strip()[-400:]
                continue
            ergebnis = pd.read_parquet(out_path)
            fehlend = [c for c in expected_df.columns if c not in ergebnis.columns]
            if fehlend:
                error = f"Schema unvollständig, fehlende Spalten: {fehlend}"
                status = "schema_break"
                continue
            accuracy = aligned_accuracy(ergebnis, expected_df)
            status, error = "ok", None
            break
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc(limit=1)

    dauer = time.perf_counter() - t0
    rec.update(status=status, accuracy=round(accuracy, 6) if accuracy is not None else None,
               attempts=used, error=error, cost_usd=round(cost, 6),
               prompt_tokens=ptok, completion_tokens=ctok,
               duration_s=round(dauer, 2), llm_s=round(llm_s, 2),
               exec_s=round(exec_s, 2), generated_code=code,
               row_actual=(len(pd.read_parquet(out_path)) if status == "ok" else None),
               row_expected=len(expected_df))
    base.mkdir(parents=True, exist_ok=True)
    (base / "record.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return rec


def run_all_groups(providers: list[str], prompt_ids: list[str], seed: int,
                   attempts: int = 3, repetition: int = 1,
                   groups: list[str] | None = None) -> list[dict]:
    """Kreuzt Modelle x Strategien x Gruppen. Die Kettenreferenz wird einmal
    materialisiert, da die Gruppen 2 und 3 ihre Eingaben daraus beziehen."""
    materialize_reference(seed)
    gewaehlt = [g for g in GROUPS if groups is None or g.name in groups]
    ergebnisse = []
    for group in gewaehlt:
        print(f"\n=== {group.label} ===", flush=True)
        for prov in providers:
            for pid in prompt_ids:
                r = run_group(prov, pid, group, seed, attempts=attempts,
                              repetition=repetition)
                wert = f"acc={r['accuracy']:.3f}" if r["accuracy"] is not None \
                    else str(r["status"])
                print(f"   {prov:10} {pid:20} {wert}  "
                      f"({r['attempts']} Versuch(e), {r['duration_s']:.1f}s, "
                      f"${r['cost_usd']:.4f})", flush=True)
                ergebnisse.append(r)
    return ergebnisse


def load_groups(seed: int) -> pd.DataFrame:
    """Alle Gruppenlaeufe eines Seeds als DataFrame."""
    zeilen = []
    wurzel = GROUP_RESULTS / str(seed)
    if not wurzel.is_dir():
        return pd.DataFrame()
    for p in sorted(wurzel.glob("*/*/record.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        d["acc_eff"] = d["accuracy"] if d["status"] == "ok" else 0.0
        zeilen.append(d)
    return pd.DataFrame(zeilen)
