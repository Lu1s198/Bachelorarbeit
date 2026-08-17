"""Zusammengesetzte Aufgabe mit expliziter Schrittanweisung (Kapitel 8).

Die Aufgabe ``transform_hard_join_and_aggregate`` der Faktormatrix verlangt
Bereinigung, Verknuepfung und Aggregation in einem Zug, benennt die noetige
Bereinigung aber nur vage ("bereinige dabei die Daten so weit wie noetig").
Sie wurde von keinem Modell geloest -- offen bleibt dabei, ob die Modelle die
Komposition mehrerer Schritte nicht beherrschen oder ob sie lediglich die
unausgesprochene Anforderung nicht erraten haben. Beides ist ein Befund, aber
ein voellig anderer.

Dieses Modul trennt die beiden Erklaerungen. Es stellt dieselbe Aufgabe mit
**explizit aufgezaehlten Teilschritten** und misst gegen eine Soll-Loesung, die
aus den Eingabedaten tatsaechlich erreichbar ist: Laender, die in den Rohdaten
fehlen, erscheinen als ``UNKNOWN`` und nicht mit dem nur dem Generator bekannten
wahren Wert. Zusaetzlich wird die Aufgabe in **beiden Ausfuehrungsmodi** und
unter **allen drei Prompting-Strategien** gestellt, sodass der Modusvergleich
nicht laenger einen optimierten gegen einen festen Prompt stellt.

Ergebnisse: data/results_composite/<seed>/<modus>/<provider>_<prompt>/
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from dataset import reference as ref
from experiments.code_execution import extract_code, run_generated_code
from experiments.direct_runner import _embed_data, _extract_table
from experiments.runner import _generate_with_retry
from llm.factory import get_provider
from llm.pricing import estimate_cost_usd
from llm.prompt import load_prompt
from reporting.analysis import aligned_accuracy

COMPOSITE_RESULTS = settings.data_dir / "results_composite"

CODEGEN_PROMPTS = ["v1_zero_shot", "v2_few_shot", "v3_chain_of_thought"]
DIRECT_PROMPTS = ["d1_zero_shot", "d2_few_shot", "d3_chain_of_thought"]

TARGET_COLS = ["country_code", "category", "total_revenue_eur", "order_count"]

# Die Teilschritte werden einzeln benannt. Entscheidend ist Schritt 2: Die
# Vereinheitlichung der Laenderangaben war in der urspruenglichen Aufgabe nur
# implizit ueber das Zielschema angedeutet und wurde von zwei der drei Modelle
# uebergangen.
TASK_DESCRIPTION = (
    "Erzeuge aus den drei Rohtabellen `customers_raw.csv`, `products_raw.csv` "
    "und `orders_raw.csv` eine Umsatzauswertung. Fuehre dazu die folgenden "
    "Schritte in dieser Reihenfolge aus:\n"
    "1. Entferne in `customers_raw.csv` fuehrende und nachfolgende Leerzeichen "
    "aus allen Textspalten.\n"
    "2. Vereinheitliche die Spalte `country` in `customers_raw.csv` auf den "
    "zweistelligen ISO-3166-1-alpha-2-Code und lege sie als `country_code` ab. "
    "Die Rohwerte liegen in unterschiedlichen Sprachen, als Abkuerzungen und mit "
    "Tippfehlern vor (z. B. 'Deutschland', 'Germany', 'GER', 'Deutshcland' -> "
    "'DE'). Werte, die sich nicht eindeutig zuordnen lassen, sowie fehlende "
    "Werte erhalten 'UNKNOWN'.\n"
    "3. Entferne aus `customers_raw.csv` Datensaetze mit mehrfach vorkommender "
    "`customer_id` und behalte jeweils das erste Vorkommen.\n"
    "4. Konvertiere in `products_raw.csv` die Spalte `price_eur` (Text wie "
    "'19,99', '19.99 EUR') in einen Float und `in_stock` in einen Boolean.\n"
    "5. Verknuepfe `orders_raw.csv` mit `customers_raw.csv` ueber `customer_id` "
    "und mit `products_raw.csv` ueber `product_id`. Alle Bestellzeilen aus "
    "`orders_raw.csv` bleiben dabei erhalten.\n"
    "6. Aggregiere pro Land (`country_code`) und Produktkategorie (`category`) "
    "den Gesamtumsatz `total_revenue_eur = sum(quantity * unit_price_eur)`, auf "
    "zwei Nachkommastellen gerundet, sowie die Anzahl Bestellungen "
    "`order_count`. Die Spalten `quantity` und `unit_price_eur` stammen beide "
    "aus `orders_raw.csv`; der Preis aus `products_raw.csv` wird fuer die "
    "Umsatzberechnung nicht verwendet. Sortiere absteigend nach "
    "`total_revenue_eur`."
)

TARGET_SCHEMA = (
    "country_code: string (2-letter ISO code or 'UNKNOWN'), category: string, "
    "total_revenue_eur: float (rounded to 2 decimals), order_count: int "
    "(one row per country/category combination, sorted descending by "
    "total_revenue_eur)"
)

INPUT_FILES = ["customers_raw.csv", "products_raw.csv", "orders_raw.csv"]


def build_reference(seed: int) -> pd.DataFrame:
    """Soll-Loesung, die den sechs Schritten woertlich folgt.

    Anders als die Soll-Loesung der Faktormatrix greift sie **nicht** auf die
    dem Generator bekannten wahren Laenderwerte zurueck. Kunden ohne Landangabe
    in den Rohdaten bilden hier eine ``UNKNOWN``-Gruppe -- das Ergebnis ist damit
    aus den Eingabedaten allein erreichbar."""
    d = settings.synthetic_dir / str(seed)
    raw_c = pd.read_csv(d / "customers_raw.csv")
    raw_p = pd.read_csv(d / "products_raw.csv")
    raw_o = pd.read_csv(d / "orders_raw.csv")

    c = ref._cleaning_hard(raw_c)                       # Schritt 1 und 2
    c = c.drop_duplicates(subset="customer_id", keep="first")   # Schritt 3
    p = ref._transform_easy(raw_p)                      # Schritt 4
    c = c.rename(columns={"country": "country_code"})
    return ref._transform_hard(raw_o, c, p)             # Schritt 5 und 6


def _run_dir(seed: int, mode: str, provider: str, prompt_id: str,
             rep: int) -> Path:
    name = f"{provider}_{prompt_id}" + (f"_r{rep}" if rep > 1 else "")
    return COMPOSITE_RESULTS / str(seed) / mode / name


def run_composite(provider_name: str, prompt_id: str, seed: int, mode: str,
                  attempts: int = 3, model: str | None = None, rep: int = 1,
                  max_tokens: int | None = None) -> dict:
    """Fuehrt die zusammengesetzte Aufgabe in einem Modus und einer Strategie aus."""
    expected = build_reference(seed)
    base = _run_dir(seed, mode, provider_name, prompt_id, rep)
    out_path = base / "output.parquet"
    script_path = base / "script.py"
    prompt = load_prompt(prompt_id)

    # Im Direkt-Modus zehrt das standardmaessige Reasoning am Ausgabebudget,
    # bevor die Tabelle beginnt; die Ergebnistabelle ist hier klein (66 Zeilen),
    # ein Denkprozess also weder noetig noch bezahlbar.
    provider = get_provider(provider_name, model=model,
                            disable_thinking=(mode == "direct"))

    if mode == "direct":
        user = prompt.render(
            task_description=TASK_DESCRIPTION,
            target_schema=TARGET_SCHEMA,
            data=_embed_data_composite(seed))
        budget = max_tokens or 32000
    else:
        user = prompt.render(
            task_description=TASK_DESCRIPTION,
            input_dir=(settings.synthetic_dir / str(seed)).as_posix(),
            output_path=out_path.as_posix(),
            target_schema=TARGET_SCHEMA)
        budget = max_tokens or settings.max_output_tokens

    rec: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider_name, "prompt_id": prompt_id,
        "prompt_strategy": prompt.strategy, "mode": mode, "seed": seed,
        "repetition": rep, "task": "composite_explicit",
    }

    status, accuracy, error = "code_error", None, None
    cost, ptok, ctok, llm_s = 0.0, 0, 0, 0.0
    code, used = "", 0
    t0 = time.perf_counter()

    for versuch in range(1, attempts + 1):
        used = versuch
        try:
            resp = _generate_with_retry(provider, user, system=prompt.system,
                                        temperature=0.0, max_tokens=budget)
            ptok += resp.prompt_tokens or 0
            ctok += resp.completion_tokens or 0
            llm_s += resp.latency_seconds or 0.0
            cost += estimate_cost_usd(resp.model, resp.prompt_tokens,
                                      resp.completion_tokens) or 0.0

            if mode == "direct":
                ergebnis = _extract_table(resp.text)
                if ergebnis is None:
                    error = "keine auswertbare Tabelle in der Antwort"
                    continue
                base.mkdir(parents=True, exist_ok=True)
                ergebnis.to_parquet(out_path, index=False)
            else:
                code = extract_code(resp.text)
                ausf = run_generated_code(code, script_path, out_path)
                if not ausf.success or not out_path.exists():
                    error = (ausf.stderr or "keine Ausgabedatei").strip()[-400:]
                    continue
                ergebnis = pd.read_parquet(out_path)

            fehlend = [c for c in TARGET_COLS if c not in ergebnis.columns]
            if fehlend:
                error, status = f"fehlende Spalten: {fehlend}", "schema_break"
                continue
            accuracy = aligned_accuracy(ergebnis[TARGET_COLS], expected[TARGET_COLS])
            status, error = "ok", None
            break
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"

    n_laender = None
    if status == "ok":
        n_laender = int(pd.read_parquet(out_path).country_code.nunique())

    rec.update(status=status,
               accuracy=round(accuracy, 6) if accuracy is not None else None,
               attempts=used, error=error, cost_usd=round(cost, 6),
               prompt_tokens=ptok, completion_tokens=ctok,
               duration_s=round(time.perf_counter() - t0, 2),
               llm_s=round(llm_s, 2), generated_code=code or None,
               row_actual=(len(pd.read_parquet(out_path)) if status == "ok" else None),
               row_expected=len(expected),
               # Zahl der Gruppierungsschluessel: 11 = Laender vereinheitlicht,
               # deutlich mehr = die Bereinigung wurde uebergangen.
               n_country_codes=n_laender)
    base.mkdir(parents=True, exist_ok=True)
    (base / "record.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return rec


def _embed_data_composite(seed: int) -> str:
    """Alle drei Rohtabellen als Text fuer den Direkt-Modus."""
    d = settings.synthetic_dir / str(seed)
    teile = []
    for f in INPUT_FILES:
        teile.append(f"--- FILE: {f} ---\n{(d / f).read_text(encoding='utf-8')}")
    return "\n\n".join(teile)


def run_all_composite(providers: list[str], seed: int, modes: list[str],
                      attempts: int = 3, rep: int = 1,
                      max_tokens: int | None = None) -> list[dict]:
    ergebnisse = []
    for mode in modes:
        prompts = DIRECT_PROMPTS if mode == "direct" else CODEGEN_PROMPTS
        print(f"\n=== Modus: {mode} ===", flush=True)
        for prov in providers:
            for pid in prompts:
                r = run_composite(prov, pid, seed, mode, attempts=attempts,
                                  rep=rep, max_tokens=max_tokens)
                wert = (f"acc={r['accuracy']:.3f}" if r["accuracy"] is not None
                        else r["status"])
                lander = (f", {r['n_country_codes']} Laender"
                          if r["n_country_codes"] else "")
                print(f"   {prov:10} {pid:22} {wert}{lander}  "
                      f"({r['attempts']} Versuch(e), {r['duration_s']:.1f}s, "
                      f"${r['cost_usd']:.4f})", flush=True)
                ergebnisse.append(r)
    return ergebnisse


def load_composite(seed: int) -> pd.DataFrame:
    wurzel = COMPOSITE_RESULTS / str(seed)
    if not wurzel.is_dir():
        return pd.DataFrame()
    zeilen = []
    for p in sorted(wurzel.glob("*/*/record.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        d["acc_eff"] = d["accuracy"] if d["status"] == "ok" else 0.0
        zeilen.append(d)
    return pd.DataFrame(zeilen)
