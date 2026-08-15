"""Verkettete Pipeline im Direkt-Modus (In-Context-Verarbeitung).

Gegenstueck zu ``pipeline_runner`` (Code-Generierung): Dieselben neun Schritte,
dieselbe Kettenreferenz und dieselbe Bewertung -- aber das Modell erzeugt keinen
Code, sondern bekommt die Eingabetabelle als CSV ins Prompt und liefert die
Ergebnistabelle unmittelbar zurueck.

Warum das eine eigene Untersuchung wert ist: In der Einzelaufgaben-Matrix war der
Direkt-Modus den semantisch gepraegten Aufgaben deutlich ueberlegen (unscharfe
Duplikate 96,5 % gegenueber 69,0 % bei der Code-Generierung), weil das Modell sein
Wissen auf jeden einzelnen Wert anwenden kann, statt es in eine verallgemeinernde
Vorschrift giessen zu muessen. Ob dieser Vorteil eine ganze Kette uebersteht --
in der jeder Schritt die vollstaendige Tabelle fehlerfrei durchreichen muss --
ist damit noch nicht beantwortet.

**Datenmenge**: Der Modus ist durch das *Ausgabefenster* begrenzt, nicht durch das
Kontextfenster: Jeder Schritt muss die komplette Ergebnistabelle zurueckschreiben.
Beim vollen Datensatz braeuchte allein der Bestellschritt rund 48.000
Ausgabe-Token und wird abgeschnitten. Fuer diesen Lauf ist daher ein halbierter
Datensatz vorgesehen (``scripts/make_half_dataset.py``, Seed 101), bei dem die
groesste Einzelausgabe bei rund 24.000 Token liegt.

Ergebnisse: data/results_pipeline/<seed>/<provider>_direct[_isolated]/
"""

from __future__ import annotations

import json
import re
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from experiments.direct_runner import _extract_table, _is_transient
from experiments.pipeline_runner import (
    PIPELINE, PIPELINE_RESULTS, Step, _reference_dir, _run_dir,
    build_chain_reference, materialize_reference,
)
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd
from reporting.analysis import aligned_accuracy

DEFAULT_MAX_TOKENS = 32000
# Ab diesem Anteil des Ausgabebudgets gilt es als aufgebraucht.
BUDGET_MARGIN = 0.98


def _fence_geschlossen(text: str) -> bool:
    """True, wenn die Antwort einen vollstaendig geschlossenen ```-Block enthaelt.

    Das ist das verlaessliche Kennzeichen einer *inhaltlich* vollstaendigen
    Tabelle. Ein aufgebrauchtes Token-Budget allein genuegt nicht: Reasoning-
    Modelle verbrauchen einen Grossteil des Budgets fuer verborgene Denk-Token,
    die in ``completion_tokens`` mitgezaehlt werden -- die gelieferte Tabelle kann
    dabei trotzdem vollstaendig sein.
    """
    return bool(re.search(r"```(?:csv)?\s*\n.*?```", text or "", re.DOTALL))

SYSTEM = (
    "You are a precise data-processing engine. You receive one or more input "
    "tables and a single transformation step. Apply the step directly to the data "
    "and return ONLY the resulting table as CSV (comma-separated, with a header "
    "row), wrapped in a single ```csv code block. Output every result row -- the "
    "table is the input of the next processing step, so a truncated or summarised "
    "answer makes the whole chain fail. No explanations, no prose, no row index "
    "column."
)


def _as_csv(path: Path) -> str:
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype=str)
    return df.to_csv(index=False)


def _build_prompt(step: Step, resolved: list[tuple[str, Path]]) -> str:
    teile = ["Task:", step.instruction, ""]
    teile.append("The result table must contain exactly these columns:")
    teile.append(", ".join(step.expected_cols))
    teile.append("")
    for rolle, pfad in resolved:
        teile.append(f"--- INPUT TABLE: {rolle} ---")
        teile.append(_as_csv(pfad))
    teile.append(
        "Return the COMPLETE resulting table as CSV inside one ```csv code block. "
        "Include ALL result rows, no index column, no commentary.")
    return "\n".join(teile)


def _resolve_inputs(step: Step, seed: int, available: dict[str, Path],
                    input_source: str) -> list[tuple[str, Path]] | None:
    """Wie im Code-Gen-Lauf: ``reference`` haengt jeden Schritt an die Soll-Ausgabe
    seines Vorgaengers, sodass die eigene Schrittleistung ohne Fehlerfortpflanzung
    messbar wird."""
    resolved = []
    for rolle, src in step.inputs:
        if src.startswith("raw:"):
            resolved.append((rolle, settings.synthetic_dir / str(seed) / src[4:]))
        else:
            dep = src.split(":", 1)[1]
            if input_source == "reference":
                resolved.append((rolle, _reference_dir(seed) / dep / "output.parquet"))
            elif dep in available:
                resolved.append((rolle, available[dep]))
            else:
                return None
    return resolved


def run_pipeline_direct(provider_name: str, seed: int, attempts: int = 3,
                        model: str | None = None, input_source: str = "self",
                        max_tokens: int = DEFAULT_MAX_TOKENS, rep: int = 1) -> dict:
    """Durchlaeuft die Kette im Direkt-Modus und protokolliert jeden Schritt."""
    provider = get_provider(provider_name, model=model, disable_thinking=True)
    chain_ref = build_chain_reference(seed)
    if input_source == "reference":
        materialize_reference(seed)
    suffix = "_isolated" if input_source == "reference" else ""
    base = _run_dir(seed, f"{provider_name}_direct", suffix, rep)
    available: dict[str, Path] = {}
    steps: list[dict] = []

    print(f"-> Pipeline (direkt) | {provider_name}", flush=True)
    for step in PIPELINE:
        rec = {"step": step.name, "label": step.label}
        resolved = _resolve_inputs(step, seed, available, input_source)
        if resolved is None:
            rec.update(status="blocked", schema_ok=False, accuracy=None, attempts=0,
                       error="Vorheriger Schritt fehlgeschlagen", duration_s=0.0,
                       llm_s=0.0, exec_s=0.0, row_actual=None, truncated=False,
                       cost_usd=0.0, prompt_tokens=0, completion_tokens=0)
            steps.append(rec)
            print(f"   {step.label}: blockiert", flush=True)
            _write_record(base, provider_name, provider.model_id, seed, steps,
                          input_source, max_tokens, rep)
            continue

        step_dir = base / step.name
        step_dir.mkdir(parents=True, exist_ok=True)
        erwartet = chain_ref[step.name]
        prompt = _build_prompt(step, resolved)

        status, schema_ok, accuracy, error = "wrong_output", False, None, None
        cost, ptok, ctok, rows, truncated = 0.0, 0, 0, None, False
        budget_erschoepft, denk_tokens, finish_reason = False, None, None
        t_step = time.perf_counter()
        llm_s = 0.0
        tabelle = None

        for versuch in range(1, attempts + 1):
            try:
                t0 = time.perf_counter()
                resp = provider.generate(prompt, system=SYSTEM, temperature=0.0,
                                         max_tokens=max_tokens)
                llm_s += time.perf_counter() - t0
                ptok, ctok = resp.prompt_tokens, resp.completion_tokens
                # Bei unbekanntem Modell liefert die Preisschaetzung None -- das
                # darf den Lauf nicht abbrechen, die Kosten sind Nebenmessgroesse.
                cost += estimate_cost_usd(resp.model, ptok, ctok) or 0.0
                # Budget aufgebraucht ist NICHT dasselbe wie abgeschnittene
                # Tabelle: Reasoning-Modelle verbuchen ihre Denk-Token ebenfalls
                # als completion_tokens. Massgeblich ist, ob der ```-Block
                # geschlossen wurde bzw. was der Anbieter als Abbruchgrund meldet.
                roh = getattr(resp, "raw_response", None) or {}
                denk_tokens = roh.get("thinking_tokens")
                finish_reason = roh.get("finish_reason")
                budget_erschoepft = bool(ctok and ctok >= max_tokens * BUDGET_MARGIN)
                truncated = bool(
                    (budget_erschoepft or "MAX_TOKENS" in str(finish_reason or ""))
                    and not _fence_geschlossen(resp.text))

                tabelle = _extract_table(resp.text)
                (step_dir / "response.txt").write_text(resp.text or "", encoding="utf-8")
                if tabelle is None:
                    error = "leere oder unparsebare Antwort"
                    if versuch < attempts:
                        time.sleep(2 * versuch)
                        continue
                    status = "code_error"
                    break

                rows = len(tabelle)
                fehlend = [c for c in step.expected_cols if c not in tabelle.columns]
                if fehlend:
                    error = f"Spalten fehlen: {', '.join(fehlend)}"
                    if versuch < attempts:
                        time.sleep(1)
                        continue
                    status = "wrong_output"
                    break

                # Nur die Zielspalten uebernehmen; Zusatzspalten wuerden sich sonst
                # durch die Kette schleppen und spaetere Schritte verwirren.
                tabelle = tabelle[step.expected_cols]
                schema_ok = True
                accuracy = aligned_accuracy(tabelle, erwartet)
                status = "ok"
                error = "Antwort vermutlich abgeschnitten" if truncated else None
                break

            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                rec["traceback"] = traceback.format_exc()
                if versuch < attempts and _is_transient(exc):
                    time.sleep(2 * versuch)
                    continue
                status = "code_error"
                break

        dauer = time.perf_counter() - t_step
        if status == "ok" and tabelle is not None:
            out_path = step_dir / "output.parquet"
            tabelle.to_parquet(out_path, index=False)
            available[step.name] = out_path

        # Feldnamen bewusst identisch zum Code-Gen-Lauf, damit reporting.
        # pipeline_analysis.load_pipeline beide Modi ohne Sonderfall liest.
        rec.update(status=status, schema_ok=schema_ok, accuracy=accuracy,
                   attempts=versuch, error=error, duration_s=round(dauer, 2),
                   llm_s=round(llm_s, 2), exec_s=0.0, truncated=truncated,
                   row_actual=rows, row_expected=len(erwartet),
                   budget_erschoepft=budget_erschoepft, denk_tokens=denk_tokens,
                   finish_reason=str(finish_reason) if finish_reason else None,
                   cost_usd=round(cost, 6), prompt_tokens=ptok,
                   completion_tokens=ctok, model=provider.model_id)
        steps.append(rec)

        if status == "ok":
            if truncated:
                hinweis = "  [Tabelle abgeschnitten]"
            elif budget_erschoepft:
                hinweis = (f"  [Budget aufgebraucht, Tabelle aber vollstaendig"
                           f"{f'; {denk_tokens} Denk-Token' if denk_tokens else ''}]")
            else:
                hinweis = ""
            print(f"   {step.label}: ok (acc={accuracy:.3f}, Zeilen={rows}, "
                  f"Versuche={versuch}, {dauer:.2f}s){hinweis}", flush=True)
        else:
            print(f"   {step.label}: {status} nach {versuch} Versuch(en) "
                  f"({dauer:.2f}s) -- {error}", flush=True)

        _write_record(base, provider_name, provider.model_id, seed, steps,
                      input_source, max_tokens, rep)

    n_ok = sum(1 for s in steps if s["status"] == "ok")
    return {"provider": provider_name, "mode": "direct", "seed": seed,
            "n_steps_ok": n_ok, "reached_end": steps[-1]["status"] == "ok",
            "steps": steps}


def _write_record(base: Path, provider_name: str, model_id: str, seed: int,
                  steps: list[dict], input_source: str, max_tokens: int,
                  rep: int = 1) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name,
        "mode": "direct",
        "model": model_id,
        "seed": seed,
        "repetition": rep,
        "input_source": input_source,
        "max_output_tokens": max_tokens,
        "n_steps_completed": len(steps),
        "n_steps_ok": sum(1 for s in steps if s["status"] == "ok"),
        "steps": steps,
    }
    path = base / "pipeline.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    return path


def run_all_pipelines_direct(providers: list[str], seed: int | None = None,
                             attempts: int = 3, input_source: str = "self",
                             max_tokens: int = DEFAULT_MAX_TOKENS,
                             rep: int = 1) -> list[dict]:
    seed = seed if seed is not None else settings.random_seed
    ergebnisse = []
    for p in providers:
        ergebnisse.append(run_pipeline_direct(p, seed, attempts=attempts,
                                              input_source=input_source,
                                              max_tokens=max_tokens, rep=rep))
    return ergebnisse
