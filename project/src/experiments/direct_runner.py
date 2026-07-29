"""Direkte In-Context-Verarbeitung als zweiter Ausführungsmodus.

Statt Python-Code generieren zu lassen (siehe experiments/runner.py), bekommt das
LLM hier die Rohdaten direkt ins Prompt eingebettet und liefert die transformierte
Ergebnistabelle unmittelbar als CSV zurück. Kein Zwischenschritt über generierten,
ausgeführten Code.

Design-Entscheidungen (bewusst anders als die Code-Gen-Matrix):
- **Nur ein Lauf** je (Modell x Aufgabe) -- Token sparen, da die eingebetteten
  Daten die Aufrufe teuer machen. Der max_output_tokens wird dafür angehoben.
- **Retry nur bei technischem Fehlschlag**: transiente API-Fehler oder eine
  leere/unparsebare Antwort werden bis zu `attempts`-mal wiederholt. Ein
  inhaltlich falsches, aber wohlgeformtes Ergebnis wird NICHT wiederholt (das
  ist ein gültiger Messwert).

Ergebnisse: data/results_direct/<seed>/<task>/...json  (mode="direct").
"""

from __future__ import annotations

import io
import json
import re
import time
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from dataset.scenarios import ALL_TASKS, Task, get_task
from evaluation import evaluate_correctness
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd

DIRECT_RESULTS = settings.data_dir / "results_direct"
DEFAULT_MAX_TOKENS = 32000

SYSTEM = (
    "You are a precise data-processing engine. You receive one or more input "
    "tables and a data transformation task. Apply the task directly to the data "
    "and return ONLY the resulting table as CSV (comma-separated, with a header "
    "row), wrapped in a single ```csv code block. Output every result row. "
    "No explanations, no prose, no row index column."
)

USER_TEMPLATE = (
    "Task:\n{task_description}\n\n"
    "The result table must have exactly these columns:\n{target_schema}\n\n"
    "Input data (CSV):\n{data}\n\n"
    "Return the COMPLETE resulting table as CSV inside one ```csv code block. "
    "Include ALL result rows, no index column, no commentary."
)

_TRANSIENT = ("503", "502", "504", "500", "429", "529", "unavailable",
              "overloaded", "resourceexhausted", "deadlineexceeded",
              "rate limit", "timeout")


def _is_transient(exc: Exception) -> bool:
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if code in (429, 500, 502, 503, 504, 529):
        return True
    return any(m in str(exc).lower() for m in _TRANSIENT)


def _embed_data(task: Task, seed: int) -> str:
    d = settings.synthetic_dir / str(seed)
    parts = []
    for fname in task.input_files:
        text = (d / fname).read_text(encoding="utf-8")
        parts.append(f"--- FILE: {fname} ---\n{text}")
    return "\n\n".join(parts)


def _extract_table(text: str) -> pd.DataFrame | None:
    """Zieht die CSV-Tabelle aus der Antwort und parst sie. None bei leer/kaputt.

    Robust gegen abgeschnittene Antworten: Ist der ```-Block nicht geschlossen
    (Truncation am Token-Limit), wird alles ab der Eröffnung genommen; eine
    unvollständige letzte Zeile wird beim Parsen übersprungen.
    """
    if not text:
        return None
    m = re.search(r"```(?:csv)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        raw = m.group(1)
    else:  # unclosed fence -> alles ab der Eröffnung; sonst der ganze Text
        m2 = re.search(r"```(?:csv)?\s*\n(.*)$", text, re.DOTALL)
        raw = m2.group(1) if m2 else text
    raw = raw.strip()
    if not raw:
        return None
    try:
        df = pd.read_csv(io.StringIO(raw), on_bad_lines="skip")
    except Exception:
        return None
    return df if df.shape[0] and df.shape[1] else None


def _resp_fields(resp) -> dict:
    return {
        "model": resp.model,
        "prompt_tokens": resp.prompt_tokens,
        "completion_tokens": resp.completion_tokens,
        "cost_usd": estimate_cost_usd(resp.model, resp.prompt_tokens, resp.completion_tokens),
        "llm_latency_seconds": resp.latency_seconds,
    }


def run_direct_task(
    provider_name: str, task_id: str, seed: int,
    max_tokens: int = DEFAULT_MAX_TOKENS, attempts: int = 3,
    model: str | None = None,
) -> dict:
    """Ein Direkt-Lauf; Retry nur bei Exception/leerer Antwort."""
    task = get_task(task_id)
    # Thinking abschalten: bei der mechanischen Bulk-Transformation verbraucht das
    # (bei aktuellen Modellen standardmäßige) Reasoning sonst das Output-Budget.
    provider = get_provider(provider_name, model=model, disable_thinking=True)
    user = USER_TEMPLATE.format(
        task_description=task.description,
        target_schema=task.target_schema or "(wie in der Aufgabe beschrieben)",
        data=_embed_data(task, seed),
    )

    record: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name,
        "mode": "direct",
        "requested_model": provider.model_id,
        "prompt_id": "direct_v1",
        "prompt_strategy": "direct",
        "task_id": task_id,
        "task_category": task.category,
        "task_difficulty": task.difficulty,
        "seed": seed,
        "repetition": 1,
        "temperature": 0.0,
        "error": None,
    }

    for attempt in range(1, attempts + 1):
        try:
            resp = provider.generate(user, system=SYSTEM, temperature=0.0, max_tokens=max_tokens)
            actual = _extract_table(resp.text)
            record.update(_resp_fields(resp))

            if actual is None:  # leere/unparsebare Antwort -> ist ein Fehlschlag
                record["error"] = "leere oder unparsebare Antwort"
                record["correctness"] = None
                record["n_rows_returned"] = 0
                if attempt < attempts:
                    time.sleep(2 * attempt)
                    continue
                break

            expected = pd.read_parquet(
                settings.ground_truth_dir / str(seed) / task.expected_output)
            record["correctness"] = asdict(evaluate_correctness(actual, expected))
            record["n_rows_returned"] = len(actual)
            record["error"] = None
            # Ist-Tabelle + Rohantwort persistieren, damit die Auswertungs-
            # Notebooks zell-/zeilenweise diffen können, ohne neu zu erzeugen.
            _persist_output(actual, resp.text, seed, task_id, provider_name)
            break

        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["traceback"] = traceback.format_exc()
            record["correctness"] = None
            if attempt < attempts and _is_transient(exc):
                time.sleep(2 * attempt)
                continue
            break

    _write_record(record, seed, task_id, provider_name)
    return record


def direct_run_dir(seed: int, task_id: str, provider_name: str) -> Path:
    """Stabiler Ordner je (Provider, Task) – Neu-Läufe überschreiben die
    Ist-Tabelle, sodass die Auswertung stets den jüngsten Lauf sieht."""
    return DIRECT_RESULTS / str(seed) / task_id / f"{provider_name}_direct"


def _persist_output(actual: pd.DataFrame, raw_text: str, seed: int,
                    task_id: str, provider_name: str) -> None:
    d = direct_run_dir(seed, task_id, provider_name)
    d.mkdir(parents=True, exist_ok=True)
    try:
        actual.to_parquet(d / "output.parquet")
    except Exception:  # exotische Spaltentypen -> wenigstens als CSV sichern
        actual.to_csv(d / "output.csv", index=False)
    (d / "response.txt").write_text(raw_text or "", encoding="utf-8")


def _write_record(record: dict, seed: int, task_id: str, provider_name: str) -> Path:
    out_dir = DIRECT_RESULTS / str(seed) / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    path = out_dir / f"{provider_name}_direct_{task_id}_{stamp}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def run_direct_experiments(
    providers: list[str], task_ids: list[str], seed: int | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS, attempts: int = 3,
    models: dict[str, str] | None = None,
) -> list[dict]:
    seed = seed if seed is not None else settings.random_seed
    models = models or {}
    results = []
    for provider_name in providers:
        for task_id in task_ids:
            print(f"-> {provider_name} | direct | {task_id}", flush=True)
            rec = run_direct_task(
                provider_name, task_id, seed, max_tokens, attempts,
                model=models.get(provider_name))
            acc = (rec.get("correctness") or {}).get("accuracy")
            status = rec.get("error") or (
                f"accuracy={acc:.3f}, {rec.get('n_rows_returned')} Zeilen"
                if acc is not None else "kein Ergebnis")
            print(f"   {status}", flush=True)
            results.append(rec)
    return results
