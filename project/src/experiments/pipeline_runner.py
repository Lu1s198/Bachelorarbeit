"""Verkettete End-to-End-Pipeline im Code-Generierungs-Modus.

Anders als die unabhängige Aufgaben-Matrix (jede Aufgabe bekommt die rohen,
dreckigen Daten) wird hier pro Modell eine zusammenhängende \ac{ETL}-Strecke
durchlaufen: Die Ausgabe jedes Schritts ist die Eingabe des nächsten. Dadurch
reparieren frühe Bereinigungsschritte die Daten, sodass spätere Schritte, die auf
den Rohdaten scheiterten (etwa die Datums-Sortierung der Schlüssel-Deduplizierung),
auf bereits normalisierten Daten arbeiten.

Kernmechanik:
- **Abhängigkeitsbewusster Kaskaden-Abbruch:** Ein Schritt läuft nur, wenn alle
  seine Eingabe-Schritte ein gültiges Ergebnis geliefert haben. Bricht ein Schritt
  (Code-Crash oder unvollständiges Schema), werden die davon abhängigen Schritte als
  ``blocked`` markiert -- genau das kaskadierende Verhalten einer realen Pipeline.
- **Schema-Prüfung nach jedem Schritt:** Fehlt eine erwartete Spalte, gilt der
  Schritt als Schema-Bruch (Folgeschritte scheitern sonst ohnehin).
- **Bewertung je Schritt:** abgeglichene Genauigkeit gegen eine *verkettete*
  Referenz, die dieselben Schritte auf den Referenzfunktionen komponiert.

Ergebnisse: data/results_pipeline/<seed>/<provider>/pipeline.json (+ je Schritt
Skript und Ausgabetabelle).
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from dataset import reference as ref
from experiments.code_execution import extract_code, run_generated_code
from experiments.runner import _generate_with_retry
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd
from reporting.analysis import aligned_accuracy

PIPELINE_RESULTS = settings.data_dir / "results_pipeline"

CUSTOMER_COLS = ["customer_id", "full_name", "email", "country", "registered_at"]
PRODUCT_COLS = ["product_id", "name", "category", "price_eur", "in_stock"]
ORDER_COLS = ["order_id", "customer_id", "product_id", "quantity",
              "unit_price_eur", "ordered_at", "total_eur", "order_year", "order_month"]
FINAL_COLS = ["country_code", "category", "total_revenue_eur", "order_count"]

SYSTEM = (
    "You are an experienced data engineer. Respond only with executable Python "
    "code. The execution environment uses Python 3.12 with pandas 3.0. "
    "Make sure the code works with that version. No explanations, no markdown code block, no text "
    "outside the code. Use only the pandas and numpy libraries and the Python "
    "standard library; do not import any other third-party packages (for example, "
    "do not use pycountry or similar packages that may not be installed) -- "
    "implement any required mappings inline. Before joins, ensure that the key columns are of the same type to avoid "
    "type mismatch errors."
)


@dataclass(frozen=True)
class Step:
    name: str
    label: str
    inputs: list[tuple[str, str]]   # (Rolle, Quelle) mit Quelle "raw:<datei>" | "step:<name>"
    instruction: str
    expected_cols: list[str]


PIPELINE: list[Step] = [
    Step("cleaning_easy", "1 · Bereinigung: Leerzeichen & fehlende Werte",
         [("input", "raw:customers_raw.csv")],
         "Entferne aus allen Textspalten führende und nachfolgende Leerzeichen und "
         "ersetze fehlende Werte in der Spalte `country` durch 'UNKNOWN'. Behalte "
         "alle Spalten unverändert bei. Beachte das verschiedene Versionen von Bibliotheken verschiedene Idiome haben", CUSTOMER_COLS),
    Step("cleaning_medium", "2 · Bereinigung: Datumsformate",
         [("input", "step:cleaning_easy")],
         "Normalisiere die Spalte `registered_at` auf das ISO-Format YYYY-MM-DD. Sie "
         "enthält gemischte Formate: ISO-Datum, deutsches Format TT.MM.JJJJ, "
         "US-Format 'Month DD YYYY' und Unix-Timestamps (Sekunden). Behalte alle "
         "Spalten.", CUSTOMER_COLS),
    Step("cleaning_hard", "3 · Bereinigung: Ländercodes (ISO)",
         [("input", "step:cleaning_medium")],
         "Vereinheitliche die Spalte `country` auf den zweistelligen "
         "ISO-3166-1-alpha-2-Code (z. B. 'DE'). Es können Abkürzungen jeglicher Art vorkommen.  " \
         "Ländernamen/Kürzel können sowohl deutsch, als auch englisch sein, " \
         "Werte, die sich nicht eindeutig "
         "zuordnen lassen, erhalten 'UNKNOWN'. Behalte alle Spalten.", CUSTOMER_COLS),
    Step("dedup_easy", "4 · Deduplizierung: exakte Duplikate",
         [("input", "step:cleaning_hard")],
         "Entferne exakte Duplikate (Zeilen, in denen alle Spaltenwerte identisch "
         "sind) und behalte jeweils das erste Vorkommen.", CUSTOMER_COLS),
    Step("dedup_medium", "5 · Deduplizierung: Schlüssel-Duplikate (E-Mail)",
         [("input", "step:dedup_easy")],
         "Entferne Zeilen mit mehrfach vorkommender `email`. Behalte bei gleicher "
         "E-Mail die Zeile mit dem jüngsten `registered_at`-Wert (die Werte liegen "
         "bereits im ISO-Format YYYY-MM-DD vor).", CUSTOMER_COLS),
    Step("dedup_hard", "6 · Deduplizierung: unscharfe Duplikate",
         [("input", "step:dedup_medium")],
         "Erkenne und entferne unscharfe Duplikate: dieselbe reale Person mit "
         "abweichender Schreibweise des Namens (Tippfehler, Groß-/Kleinschreibung, "
         "mit/ohne Mittelinitial) und/oder abweichender E-Mail-Schreibweise (Punkte vor "
         "dem @, Groß-/Kleinschreibung). Namen können Anreden/Titel enthalten, diese "
         "sind nicht Teil des Namens. Für Übereinstimmungen müssen Name und E-Mail auf " \
         "die selbe Person hindeuten" 
         "Behalte bei Übereinstimmungen die kleinste customer_id",
         CUSTOMER_COLS),
    Step("products", "7 · Produkte: Typkonvertierung",
         [("input", "raw:products_raw.csv")],
         "Konvertiere die Spalte `price_eur` (Text wie '19,99', '€19.99', "
         "'19.99 EUR') in einen Float mit Dezimalpunkt und die Spalte `in_stock` "
         "(Text wie 'ja'/'nein', 'true'/'false', '1'/'0') in einen Boolean.",
         PRODUCT_COLS),
    Step("orders", "8 · Bestellungen: abgeleitete Spalten",
         [("input", "raw:orders_raw.csv")],
         "Berechne die neue Spalte `total_eur = quantity * unit_price_eur`. "
         "Extrahiere aus `ordered_at` zusätzlich `order_year` (Integer) und "
         "`order_month` (Integer 1-12).", ORDER_COLS),
    Step("final", "9 · Join & Aggregation",
         [("customers", "step:dedup_hard"), ("products", "step:products"),
          ("orders", "step:orders")],
         "Verknüpfe die drei Eingabetabellen (Kunden, Produkte, Bestellungen) über "
         "ihre ID-Spalten (`customer_id`, `product_id`). Die Kundentabelle enthält "
         "in `country` bereits den ISO-Ländercode; nutze ihn als `country_code`. "
         "Aggregiere pro Land (`country_code`) und Produktkategorie (`category`) den "
         "Gesamtumsatz `total_revenue_eur = sum(quantity * unit_price_eur)` und die "
         "Anzahl Bestellungen `order_count`. Sortiere absteigend nach "
         "`total_revenue_eur`. Das Ergebnis enthält nur Zeilen mit gültigem country_code " \
         "und gültiger category; Bestellungen ohne passenden Kunden- oder Produktdatensatz bleiben unberücksichtigt.", FINAL_COLS),
]


def build_chain_reference(seed: int) -> dict[str, pd.DataFrame]:
    """Komponiert die Referenzfunktionen in Pipeline-Reihenfolge (verkettete Soll-Lösung)."""
    d = settings.synthetic_dir / str(seed)
    raw_customers = pd.read_csv(d / "customers_raw.csv")
    raw_products = pd.read_csv(d / "products_raw.csv")
    raw_orders = pd.read_csv(d / "orders_raw.csv")

    c1 = ref._cleaning_easy(raw_customers)
    c2 = ref._cleaning_medium(c1)
    c3 = ref._cleaning_hard(c2)
    c4 = ref._dedup_easy(c3)
    c5 = ref._dedup_medium(c4)
    c6 = ref._dedup_hard(c5)
    p1 = ref._transform_easy(raw_products)
    o1 = ref._transform_medium(raw_orders)
    c6r = c6.rename(columns={"country": "country_code"})
    final = ref._transform_hard(o1, c6r, p1)
    return {
        "cleaning_easy": c1, "cleaning_medium": c2, "cleaning_hard": c3,
        "dedup_easy": c4, "dedup_medium": c5, "dedup_hard": c6,
        "products": p1, "orders": o1, "final": final,
    }


def _resolve_inputs(step: Step, seed: int, available: dict[str, Path],
                    input_source: str = "self"):
    """Liefert (Rolle, Pfad)-Liste oder None, wenn eine Abhängigkeit blockiert ist.

    ``input_source="reference"`` entkoppelt die Kette: Jeder Schritt bekommt statt der
    eigenen Vorgänger-Ausgabe die *Soll*-Ausgabe des Vorgängers aus der Kettenreferenz.
    Damit ist jeder Schritt einzeln messbar -- auch nach einem Absturz --, die
    Obergrenze liegt für alle Modelle bei 1,0, und die Differenz zum verketteten Lauf
    beziffert genau die Kosten der Fehlerfortpflanzung. Die Referenz liefert nur saubere
    Eingabedaten, nicht die Lösung des jeweiligen Schritts."""
    resolved = []
    for role, src in step.inputs:
        if src.startswith("raw:"):
            resolved.append((role, settings.synthetic_dir / str(seed) / src[4:]))
        else:  # step:<name>
            dep = src.split(":", 1)[1]
            if input_source == "reference":
                p = _reference_dir(seed) / dep / "output.parquet"
                resolved.append((role, p))
            else:
                if dep not in available:
                    return None
                resolved.append((role, available[dep]))
    return resolved


def _column_types(path: Path) -> str:
    """Spalten und pandas-dtypes der Eingabedatei als Kurzbeschreibung.

    Wird je Schritt aus der tatsächlichen Eingabe abgeleitet -- entlang der Kette
    ändern sich die Typen (nach Schritt 7 ist ``price_eur`` ein Float, nach
    Schritt 8 kommen abgeleitete Spalten dazu), eine statische Angabe im
    Systemprompt wäre für die meisten Schritte falsch. Die Typangabe ist eine
    Eigenschaft der Daten, kein Lösungshinweis."""
    try:
        df = _read_table(path)
    except Exception:  # noqa: BLE001 - Beschreibung ist optional, nie laufentscheidend
        return ""
    return ", ".join(f"{c}: {t}" for c, t in df.dtypes.astype(str).items())


def _reference_dir(seed: int) -> Path:
    return PIPELINE_RESULTS / str(seed) / "_reference"


def materialize_reference(seed: int) -> Path:
    """Schreibt die Soll-Ausgaben der Kettenreferenz als Parquet, damit sie im
    isolierten Lauf als Eingabe dienen können."""
    d = _reference_dir(seed)
    for name, df in build_chain_reference(seed).items():
        (d / name).mkdir(parents=True, exist_ok=True)
        df.to_parquet(d / name / "output.parquet", index=False)
    return d


def _build_prompt(step: Step, resolved: list[tuple[str, Path]], out_path: Path) -> str:
    lines = ["Apply the following data transformation step to the input data and "
             "write the result as a Parquet file.", "", "Input file(s):"]
    for role, path in resolved:
        lines.append(f"  - {role}: {path.as_posix()}")
        types = _column_types(path)
        if types:
            lines.append(f"    columns as read by pandas: {types}")
    lines += ["", "Task:", step.instruction, "",
              f"The result must contain (at least) the columns: {', '.join(step.expected_cols)}.",
              f"Write the resulting table as a Parquet file to exactly: {out_path.as_posix()}",
              "The script must run without any further input and produce the output file."]
    return "\n".join(lines)


def _run_dir(seed: int, provider_name: str, suffix: str, rep: int) -> Path:
    """Ablageordner eines Laufs. Wiederholung 1 behaelt den schlichten Namen,
    damit bereits erhobene Laeufe unveraendert gueltig bleiben; ab der zweiten
    kommt ``_r<N>`` dazu, sodass sich Wiederholungen nicht ueberschreiben."""
    name = f"{provider_name}{suffix}" + (f"_r{rep}" if rep > 1 else "")
    return PIPELINE_RESULTS / str(seed) / name


def run_pipeline(provider_name: str, seed: int, attempts: int = 3,
                 model: str | None = None, best_of: int = 1,
                 input_source: str = "self", rep: int = 1) -> dict:
    """Durchläuft die verkettete Pipeline für ein Modell und protokolliert jeden Schritt.

    ``attempts`` steuert das Standardverhalten: Ein Schritt wird bis zu ``attempts``
    Mal erzeugt, aber beim ersten brauchbaren Ergebnis übernommen.

    ``best_of > 1`` schaltet auf **Oracle-Auswahl** um: Es werden immer genau
    ``best_of`` Kandidaten erzeugt und derjenige mit der höchsten abgeglichenen
    Genauigkeit gegen die Referenz übernommen. Das misst nicht mehr, was das Modell
    autonom liefert, sondern die *Obergrenze* bei perfekter Auswahl -- vergleichbar
    mit einer pass@k-Auswertung. Ergebnisse aus diesem Modus sind entsprechend zu
    kennzeichnen und nicht mit ``best_of=1``-Läufen in eine Tabelle zu mischen."""
    provider = get_provider(provider_name, model=model)
    chain_ref = build_chain_reference(seed)
    # Entkoppelter Lauf in eigenen Ordner, damit der normale Lauf erhalten bleibt.
    if input_source == "reference":
        materialize_reference(seed)
    suffix = "_isolated" if input_source == "reference" else ""
    base = _run_dir(seed, provider_name, suffix, rep)
    available: dict[str, Path] = {}
    steps: list[dict] = []

    for step in PIPELINE:
        rec = {"step": step.name, "label": step.label}
        resolved = _resolve_inputs(step, seed, available, input_source)
        if resolved is None:
            rec.update(status="blocked", schema_ok=False, accuracy=None,
                       attempts=0, error="Vorheriger Schritt fehlgeschlagen",
                       duration_s=0.0, llm_s=0.0, exec_s=0.0)
            steps.append(rec)
            print(f"   {step.label}: blockiert", flush=True)
            continue

        out_path = base / step.name / "output.parquet"
        script_path = base / step.name / "script.py"
        expected_df = chain_ref[step.name]
        status, schema_ok, accuracy, error = "code_error", False, None, None
        cost, ptok, ctok = 0.0, 0, 0
        # Zeitmessung je Schritt: Gesamtdauer (inkl. Wiederholungen und Backoff),
        # davon Antwortzeit des Modells und Laufzeit des erzeugten Skripts.
        t_step = time.perf_counter()
        llm_s, exec_s = 0.0, 0.0
        code = ""
        used = 0
        # Bei best_of > 1 werden immer alle Kandidaten erzeugt und am Ende der
        # beste übernommen; sonst bricht die Schleife beim ersten Erfolg ab.
        n_tries = max(attempts, best_of) if best_of > 1 else attempts
        best: dict | None = None          # bester Kandidat (Tabelle, Code, Genauigkeit)
        candidates: list[dict] = []
        for attempt in range(1, n_tries + 1):
            used = attempt
            try:
                prompt = _build_prompt(step, resolved, out_path)
                resp = _generate_with_retry(
                    provider, prompt, system=SYSTEM, temperature=0.0,
                    max_tokens=settings.max_output_tokens)
                ptok += resp.prompt_tokens or 0
                ctok += resp.completion_tokens or 0
                llm_s += resp.latency_seconds or 0.0
                cost += estimate_cost_usd(resp.model, resp.prompt_tokens,
                                          resp.completion_tokens) or 0.0
                code = extract_code(resp.text)
                execution = run_generated_code(code, script_path, out_path)
                exec_s += execution.duration_seconds or 0.0
                if not execution.success:
                    error = f"Code-Ausführung fehlgeschlagen: {execution.stderr[-400:]}"
                    candidates.append({"versuch": attempt, "status": "code_error"})
                    continue  # neuer Versuch
                actual = pd.read_parquet(out_path)
                missing = [c for c in expected_df.columns if c not in actual.columns]
                if missing:
                    schema_ok = False
                    error = f"Schema unvollständig, fehlende Spalten: {missing}"
                    candidates.append({"versuch": attempt, "status": "schema_break"})
                    continue  # neuer Versuch
                acc = aligned_accuracy(actual, expected_df)
                candidates.append({"versuch": attempt, "status": "ok",
                                   "accuracy": round(acc, 6)})
                if best is None or acc > best["accuracy"]:
                    best = {"accuracy": acc, "table": actual, "code": code,
                            "versuch": attempt}
                schema_ok = True
                accuracy = acc
                status, error = "ok", None
                if best_of <= 1:
                    break                 # Standardverhalten: erster Erfolg zählt
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                candidates.append({"versuch": attempt, "status": "exception"})
                continue

        if best is not None:
            # Gewinner-Tabelle und -Code festschreiben (der letzte Kandidat hat die
            # Datei ggf. überschrieben).
            best["table"].to_parquet(out_path, index=False)
            code, accuracy = best["code"], best["accuracy"]
            schema_ok, status, error = True, "ok", None
        if best_of > 1:
            rec["kandidaten"] = candidates
            rec["gewaehlter_versuch"] = best["versuch"] if best else None
            rec["auswahl"] = "oracle_best_of"

        duration = time.perf_counter() - t_step
        if not schema_ok and status != "ok":
            status = "schema_break" if error and "Schema" in error else "code_error"
        if status == "ok":
            available[step.name] = out_path
            extra = ""
            if best_of > 1:
                gut = [k for k in candidates if k["status"] == "ok"]
                extra = (f", {len(gut)}/{len(candidates)} lauffaehig, "
                         f"bester = Versuch {best['versuch']}")
            print(f"   {step.label}: ok (acc={accuracy:.3f}, Versuche={used}{extra}, "
                  f"{duration:.2f}s)", flush=True)
        else:
            print(f"   {step.label}: {status} nach {used} Versuch(en) "
                  f"({duration:.2f}s)", flush=True)

        rec.update(status=status, schema_ok=schema_ok,
                   accuracy=round(accuracy, 6) if accuracy is not None else None,
                   attempts=used, error=error, cost_usd=round(cost, 6),
                   duration_s=round(duration, 2), llm_s=round(llm_s, 2),
                   exec_s=round(exec_s, 2),
                   prompt_tokens=ptok, completion_tokens=ctok,
                   row_actual=(len(pd.read_parquet(out_path))
                               if out_path.exists() and status == "ok" else None),
                   row_expected=len(expected_df))
        _save_code(script_path.parent, code)
        steps.append(rec)
        # Nach jedem Schritt sichern: bricht der Lauf ab (Anbieterfehler, Abbruch
        # durch den Nutzer), bleiben die bereits gemessenen Schritte erhalten.
        _write_record(base, provider_name, provider.model_id, seed, attempts, steps,
                      best_of, input_source, rep)

    return _write_record(base, provider_name, provider.model_id, seed, attempts, steps,
                      best_of, input_source, rep)


def _write_record(base: Path, provider_name: str, model_id: str, seed: int,
                  attempts: int, steps: list[dict], best_of: int = 1,
                  input_source: str = "self", rep: int = 1) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name,
        "requested_model": model_id,
        "mode": "pipeline",
        "seed": seed,
        "repetition": rep,
        "attempts_per_step": attempts,
        "best_of": best_of,
        "input_source": input_source,
        "n_steps_completed": len(steps),
        "n_steps_ok": sum(s["status"] == "ok" for s in steps),
        "reached_end": any(s["step"] == "final" and s["status"] == "ok" for s in steps),
        "steps": steps,
    }
    base.mkdir(parents=True, exist_ok=True)
    (base / "pipeline.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return record


def _save_code(step_dir: Path, code: str) -> None:
    if code:
        step_dir.mkdir(parents=True, exist_ok=True)
        (step_dir / "generated_code.py").write_text(code, encoding="utf-8")


def run_all_pipelines(providers: list[str], seed: int | None = None,
                      attempts: int = 3, best_of: int = 1,
                      input_source: str = "self", rep: int = 1) -> list[dict]:
    seed = seed if seed is not None else settings.random_seed
    out = []
    for p in providers:
        modus = (f" | best-of-{best_of} (Oracle-Auswahl)" if best_of > 1 else "")
        modus += " | Eingaben aus der Baseline (Schritte entkoppelt)"             if input_source == "baseline" else ""
        print(f"-> Pipeline | {p}{modus}", flush=True)
        if p == "baseline":
            # Regelbasiert und damit deterministisch: Wiederholungen liefern
            # bitgenau dasselbe Ergebnis, deshalb immer nur ein Lauf.
            out.append(run_baseline_pipeline(seed, input_source=input_source))
        else:
            out.append(run_pipeline(p, seed, attempts=attempts, best_of=best_of,
                                    input_source=input_source, rep=rep))
    return out


# ---------------------------------------------------------------- Baseline

def _baseline_step(name: str, inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Regelbasierte Umsetzung eines Pipeline-Schritts.

    Für die formalisierbaren Schritte ist die Regel zugleich die korrekte Lösung
    (dieselben Routinen wie die Referenz); für die semantisch geprägten Schritte
    -- Länder-Vereinheitlichung und Fuzzy-Duplikate -- kommen die begrenzten
    Heuristiken der Vergleichsbasis zum Einsatz. Der Endschritt nutzt wie im
    Prompt beschrieben den bereits vereinheitlichten Ländercode aus Schritt 3,
    sodass dessen Fehler sich genauso fortpflanzen wie bei den Modellen."""
    from baseline import pipeline as bp

    i = inputs.get("input")
    match name:
        case "cleaning_easy":
            return ref._cleaning_easy(i)
        case "cleaning_medium":
            return ref._cleaning_medium(i)
        case "cleaning_hard":
            return bp._cleaning_hard(i)          # begrenzte Ländertabelle
        case "dedup_easy":
            return ref._dedup_easy(i)
        case "dedup_medium":
            return ref._dedup_medium(i)
        case "dedup_hard":
            return bp._dedup_hard(i)             # Heuristik statt Weltwissen
        case "products":
            return ref._transform_easy(i)
        case "orders":
            return ref._transform_medium(i)
        case "final":
            customers = inputs["customers"].rename(columns={"country": "country_code"})
            return ref._transform_hard(inputs["orders"], customers, inputs["products"])
        case _:
            raise KeyError(f"Unbekannter Schritt: {name}")


def _read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)


def run_baseline_pipeline(seed: int, input_source: str = "self") -> dict:
    """Dieselbe verkettete Strecke, regelbasiert statt LLM-generiert.

    Liefert einen Datensatz im gleichen Format wie ``run_pipeline``, sodass die
    Baseline in Heatmap und Verlaufsgrafik als zusätzliche Spalte erscheint. Es
    gibt keine Code-Erzeugung, daher immer genau ein Versuch und keine Kosten.

    ``input_source="reference"`` fuehrt sie -- wie die Modelle -- mit Soll-Eingaben
    aus. Der Aussagewert ist begrenzt und asymmetrisch: In den formalisierbaren
    Schritten verwendet die Baseline dieselben Routinen wie die Referenz, dort ist
    das Ergebnis definitionsgemaess 1,0 und kein Leistungsnachweis. Nicht trivial
    sind allein Schritt 3 und 6, wo die begrenzten Heuristiken der Vergleichsbasis
    greifen. Der Lauf ist dennoch sinnvoll, weil er belegt, dass auch die Regel
    ihren Endschritt mit sauberer Eingabe vollstaendig loest -- der in der Kette
    gemessene Verlust also auch bei ihr geerbt und nicht eigener Fehler ist."""
    chain_ref = build_chain_reference(seed)
    suffix = "_isolated" if input_source == "reference" else ""
    base = PIPELINE_RESULTS / str(seed) / f"baseline{suffix}"
    available: dict[str, Path] = {}
    steps: list[dict] = []

    for step in PIPELINE:
        rec = {"step": step.name, "label": step.label}
        resolved = _resolve_inputs(step, seed, available, input_source)
        if resolved is None:
            rec.update(status="blocked", schema_ok=False, accuracy=None,
                       attempts=0, error="Vorheriger Schritt fehlgeschlagen",
                       cost_usd=0.0, prompt_tokens=0, completion_tokens=0,
                       duration_s=0.0, llm_s=0.0, exec_s=0.0)
            steps.append(rec)
            print(f"   {step.label}: blockiert", flush=True)
            continue

        out_path = base / step.name / "output.parquet"
        expected_df = chain_ref[step.name]
        status, schema_ok, accuracy, error = "code_error", False, None, None
        t_step = time.perf_counter()
        try:
            result = _baseline_step(step.name, {r: _read_table(p) for r, p in resolved})
            missing = [c for c in expected_df.columns if c not in result.columns]
            if missing:
                error = f"Schema unvollständig, fehlende Spalten: {missing}"
                status = "schema_break"
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                result.to_parquet(out_path, index=False)
                schema_ok = True
                accuracy = aligned_accuracy(result, expected_df)
                status = "ok"
                available[step.name] = out_path
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"

        duration = time.perf_counter() - t_step
        if status == "ok":
            print(f"   {step.label}: ok (acc={accuracy:.3f}, Versuche=1, "
                  f"{duration:.2f}s)", flush=True)
        else:
            print(f"   {step.label}: {status} ({error}) ({duration:.2f}s)", flush=True)

        rec.update(status=status, schema_ok=schema_ok,
                   accuracy=round(accuracy, 6) if accuracy is not None else None,
                   attempts=1, error=error, cost_usd=0.0,
                   duration_s=round(duration, 2), llm_s=0.0,
                   exec_s=round(duration, 2),
                   prompt_tokens=0, completion_tokens=0,
                   row_actual=(len(pd.read_parquet(out_path))
                               if status == "ok" else None),
                   row_expected=len(expected_df))
        steps.append(rec)
        _write_record(base, "baseline", "rule_based", seed, 1, steps)

    return _write_record(base, "baseline", "rule_based", seed, 1, steps)
