"""Experiment-Runner über die Matrix Modell x Prompt-Strategie x Aufgabe.

Für jede Konfiguration wird das Modell mehrfach zur Code-Erzeugung aufgefordert
(Wiederholungen für die Reproduzierbarkeitsdimension FF3), der Code ausgeführt
und das Ergebnis gegen die Ground Truth bewertet. Jedes Ergebnis wird als
eigenes, unveränderliches JSON abgelegt.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from dataset.scenarios import Task, get_task
from evaluation import evaluate_correctness
from experiments.code_execution import extract_code, run_generated_code
from llm.base import LLMProvider, LLMResponse
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd
from llm.prompt import load_prompt

# Marker für transiente (wiederholbare) Anbieterfehler -- providerübergreifend
# an Status-Code bzw. Fehlertext erkannt (503/429 usw. bei Gemini, Anthropic,
# OpenAI; Verbindungsfehler bei Ollama).
_TRANSIENT_MARKERS = (
    "503", "502", "504", "500", "429", "529", "unavailable", "overloaded",
    "rate limit", "ratelimit", "resourceexhausted", "deadlineexceeded",
    "timeout", "timed out", "temporarily", "connection", "econnreset",
)


def _is_transient(exc: Exception) -> bool:
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if code in (429, 500, 502, 503, 504, 529):
        return True
    msg = str(exc).lower()
    return any(m in msg for m in _TRANSIENT_MARKERS)


def _generate_with_retry(
    provider: LLMProvider, prompt: str, *, attempts: int = 3,
    base_delay: float = 2.0, **kwargs,
) -> LLMResponse:
    """Ruft provider.generate() mit exponentiellem Backoff bei transienten Fehlern."""
    for attempt in range(1, attempts + 1):
        try:
            return provider.generate(prompt, **kwargs)
        except Exception as exc:  # noqa: BLE001 - bewusst breit; Klassifikation folgt
            if attempt < attempts and _is_transient(exc):
                delay = base_delay * 2 ** (attempt - 1)
                # Statuscode und Meldung mitloggen: ohne sie laesst sich hinterher
                # nicht mehr unterscheiden, ob es Ueberlastung, Rate-Limit oder ein
                # Netzproblem war (der Ausnahmetyp allein sagt bei generischen
                # APIStatusError nichts aus).
                code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                msg = " ".join(str(exc).split())[:200]
                print(f"   transienter Fehler ({type(exc).__name__}"
                      f"{f', HTTP {code}' if code else ''}): {msg}\n"
                      f"      Retry {attempt}/{attempts - 1} in {delay:.0f}s ...",
                      flush=True)
                time.sleep(delay)
                continue
            raise


def _ground_truth_path(task: Task, seed: int) -> Path:
    return settings.ground_truth_dir / str(seed) / task.expected_output


def run_single(
    provider_name: str,
    prompt_id: str,
    task_id: str,
    repetition: int,
    seed: int,
    temperature: float | None,
    model: str | None = None,
) -> dict:
    """Führt genau eine Konfiguration (eine Wiederholung) durch und loggt sie."""
    task = get_task(task_id)
    prompt = load_prompt(prompt_id)
    provider = get_provider(provider_name, model=model)

    input_dir = settings.synthetic_dir / str(seed)
    run_id = f"{provider_name}_{prompt_id}_{task_id}_r{repetition}"
    work_dir = settings.results_dir / str(seed) / task_id / run_id
    script_path = work_dir / "script.py"
    output_path = work_dir / "output.parquet"

    # target_schema wird nur von schema-basierten Strategien (z.B. v4) im Template genutzt.
    user_prompt = prompt.render(
        task_description=task.description,
        input_dir=input_dir.as_posix(),
        output_path=output_path.as_posix(),
        target_schema=task.target_schema,
    )

    record: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name,
        "requested_model": provider.model_id,
        "prompt_id": prompt_id,
        "prompt_strategy": prompt.strategy,
        "task_id": task_id,
        "task_category": task.category,
        "task_difficulty": task.difficulty,
        "seed": seed,
        "repetition": repetition,
        "temperature": temperature,
    }

    try:
        response = _generate_with_retry(
            provider, user_prompt, system=prompt.system, temperature=temperature,
            max_tokens=settings.max_output_tokens,
        )
        code = extract_code(response.text)
        execution = run_generated_code(code, script_path, output_path)

        record.update({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost_usd": estimate_cost_usd(
                response.model, response.prompt_tokens, response.completion_tokens
            ),
            "llm_latency_seconds": response.latency_seconds,
            "exec_duration_seconds": execution.duration_seconds,
            "exec_success": execution.success,
            "exec_return_code": execution.return_code,
            "exec_stderr": execution.stderr,
            "generated_code": code,
        })

        if execution.success:
            actual = pd.read_parquet(output_path)
            expected = pd.read_parquet(_ground_truth_path(task, seed))
            record["correctness"] = asdict(evaluate_correctness(actual, expected))
        else:
            record["correctness"] = None
        record["error"] = None
    except Exception as exc:  # noqa: BLE001 - Fehler soll den Lauf nicht abbrechen
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()

    _write_record(record, seed, task_id, run_id)
    return record


def _write_record(record: dict, seed: int, task_id: str, run_id: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    out_dir = settings.results_dir / str(seed) / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}_{stamp}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def run_experiments(
    providers: list[str],
    prompt_ids: list[str],
    task_ids: list[str],
    seed: int | None = None,
    repetitions: int | None = None,
    temperature: float | None = None,
    models: dict[str, str] | None = None,
) -> list[dict]:
    """Iteriert die vollständige Matrix und liefert alle Ergebnis-Records."""
    seed = seed if seed is not None else settings.random_seed
    repetitions = repetitions if repetitions is not None else settings.n_repetitions
    temperature = temperature if temperature is not None else settings.temperature
    models = models or {}

    results: list[dict] = []
    for provider_name in providers:
        for prompt_id in prompt_ids:
            for task_id in task_ids:
                for rep in range(1, repetitions + 1):
                    print(f"-> {provider_name} | {prompt_id} | {task_id} | r{rep}", flush=True)
                    rec = run_single(
                        provider_name, prompt_id, task_id, rep, seed, temperature,
                        model=models.get(provider_name),
                    )
                    acc = (rec.get("correctness") or {}).get("accuracy")
                    status = rec.get("error") or (
                        f"accuracy={acc:.3f}" if acc is not None else "kein Ergebnis"
                    )
                    print(f"   {status}", flush=True)
                    results.append(rec)
    return results
