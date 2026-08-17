"""Sammelt saemtliche Kennzahlen fuer Kapitel 7 und 8 aus Seed 2 / 102.

Die Auswertung der Arbeit stuetzt sich ausschliesslich auf diesen Datensatz:
Er war waehrend der Entwicklung unbekannt, wurde ohne nachtraegliche Anpassung
von Prompts oder Auswertungslogik durchlaufen und liegt auf jeder
Untersuchungsebene mit mehreren Wiederholungen vor.

Aufruf:  python scripts/kennzahlen_seed2.py  > kennzahlen.txt
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from config import settings  # noqa: E402
from experiments.composite_runner import load_composite  # noqa: E402
from experiments.group_runner import load_groups  # noqa: E402
from experiments.pipeline_runner import PIPELINE  # noqa: E402
from reporting.analysis import load_runs  # noqa: E402
from reporting.pipeline_analysis import load_pipeline_reps, mean_over_reps  # noqa: E402

pd.set_option("display.width", 200)
SEED, SEED_HALB = 2, 102
CLOUD = ["anthropic", "openai", "google"]


def kopf(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def unter(t: str) -> None:
    print(f"\n--- {t}")


# ------------------------------------------------------------------ Matrix

kopf("1  FAKTORMATRIX (Code-Generierung), Seed 2")

runs = load_runs(seed=SEED, include_baseline=False)
base = load_runs(seed=SEED, include_baseline=True)
base = base[base.provider == "baseline"]

print(f"Laeufe gesamt: {len(runs)}   Modelle: {sorted(runs.provider.unique())}")
print(f"Strategien: {sorted(runs.prompt_id.unique())}   "
      f"Wiederholungen: {sorted(runs.repetition.unique())}")
print(f"\nmittlere Genauigkeit : {runs.eff_accuracy.mean():.3f}")
print(f"Erfolgsquote         : {runs.produced.mean() * 100:.1f} %")
print(f"Ausgang              : {runs.status.value_counts().to_dict()}")
print(f"Kosten gesamt        : {runs.cost_usd.sum():.2f} USD")
print(f"Token                : {runs.prompt_tokens.sum():,.0f} ein / "
      f"{runs.completion_tokens.sum():,.0f} aus")
print(f"Antwortzeit im Mittel: {runs.latency_s.mean():.1f} s")

unter("je Aufgabe (alle Modelle / Strategien / Wiederholungen)")
t = runs.groupby(["_cat", "_diff", "task_id"], as_index=False).agg(
    acc=("eff_accuracy", "mean"), erfolg=("produced", "mean"))
bt = base.groupby("task_id").eff_accuracy.mean().rename("baseline")
t = t.merge(bt, on="task_id", how="left").sort_values(["_cat", "_diff"])
print(t.assign(acc=(t.acc * 100).round(1), erfolg=(t.erfolg * 100).round(1),
               baseline=(t.baseline * 100).round(1))
      [["task_id", "acc", "erfolg", "baseline"]].to_string(index=False))

unter("je Aufgabe, nur Cloud-Modelle")
c = runs[runs.provider.isin(CLOUD)]
t2 = c.groupby(["_cat", "_diff", "task_id"], as_index=False).agg(
    acc=("eff_accuracy", "mean"), erfolg=("produced", "mean"),
    best=("eff_accuracy", "max")).sort_values(["_cat", "_diff"])
print(t2.assign(acc=(t2.acc * 100).round(1), erfolg=(t2.erfolg * 100).round(1),
                best=(t2.best * 100).round(1))
      [["task_id", "acc", "erfolg", "best"]].to_string(index=False))

unter("je Modell")
m = runs.groupby(["label"], as_index=False).agg(
    n=("eff_accuracy", "size"), acc=("eff_accuracy", "mean"),
    erfolg=("produced", "mean"), kosten=("cost_usd", "sum"),
    latenz=("latency_s", "mean"))
print(m.round(3).to_string(index=False))
print("\nAusgang je Modell:")
print(pd.crosstab(runs.label, runs.status).to_string())

unter("je Modell x Aufgabe (bestes Ergebnis ueber Strategien/Wiederholungen)")
print((runs.pivot_table(index="task_id", columns="label", values="eff_accuracy",
                        aggfunc="max") * 100).round(1).to_string())

unter("je Strategie -- alle Modelle vs. nur Cloud")
for name, teil in [("alle", runs), ("cloud", c)]:
    s = teil.groupby("prompt_id", as_index=False).agg(
        acc=("eff_accuracy", "mean"), erfolg=("produced", "mean"),
        ptok=("prompt_tokens", "mean"))
    print(f"\n[{name}]")
    print(s.assign(acc=(s.acc * 100).round(1), erfolg=(s.erfolg * 100).round(1),
                   ptok=s.ptok.round(0)).to_string(index=False))

unter("je Strategie x Aufgabe, nur Cloud")
print((c.pivot_table(index="task_id", columns="prompt_id",
                     values="eff_accuracy", aggfunc="mean") * 100)
      .round(1).to_string())

unter("je Strategie x Kategorie")
for name, teil in [("alle", runs), ("cloud", c)]:
    print(f"\n[{name}]")
    print((teil.pivot_table(index="category", columns="prompt_id",
                            values="eff_accuracy", aggfunc="mean") * 100)
          .round(1).to_string())

unter("lokales Modell im Detail")
lo = runs[runs.provider == "ollama"]
if len(lo):
    print(f"n={len(lo)}  acc={lo.eff_accuracy.mean():.3f}  "
          f"erfolg={lo.produced.mean() * 100:.1f} %")
    print(lo.groupby("prompt_id").agg(
        acc=("eff_accuracy", "mean"), erfolg=("produced", "mean")).round(3).to_string())
    print(f"Ausgang: {lo.status.value_counts().to_dict()}")
    print(f"Latenz  : {lo.latency_s.mean():.1f} s")

unter("Reproduzierbarkeit ueber die 2 Wiederholungen")
g = runs.groupby(["provider", "prompt_id", "task_id"]).eff_accuracy
std = g.std()
identisch = g.apply(lambda s: s.nunique() == 1)
print(f"mittlere Standardabweichung: {std.mean():.3f}")
print(f"identische Wiederholungen  : {identisch.mean() * 100:.1f} %")
print("\nje Aufgabe:")
print(runs.groupby(["provider", "prompt_id", "task_id"]).eff_accuracy.std()
      .groupby("task_id").mean().round(3).sort_values(ascending=False).to_string())
print("\nje Modell:")
print(runs.groupby(["provider", "prompt_id", "task_id"]).eff_accuracy.std()
      .groupby("provider").mean().round(3).to_string())

unter("Baseline je Aufgabe")
print((base.groupby("task_id").eff_accuracy.mean() * 100).round(1).to_string())


# ------------------------------------------------------------------ Pipeline

kopf("2  VERKETTETE PIPELINE (Code-Generierung), Seed 2")

KURZ = {s.name: f"{i + 1} {s.label.split(': ')[-1]}" for i, s in enumerate(PIPELINE)}

for iso in (False, True):
    unter(f"{'isoliert' if iso else 'verkettet'}")
    mv = mean_over_reps(SEED, isolated=iso)
    if not len(mv):
        print("keine Daten")
        continue
    lang = load_pipeline_reps(SEED, isolated=iso)
    print(f"Wiederholungen je Modell: "
          f"{lang.groupby('label').rep.nunique().to_dict()}")
    p = mv.pivot_table(index="order", columns="label", values="accuracy")
    p.index = [KURZ[s.name] for s in PIPELINE if
               (mv.order == [i for i, x in enumerate(PIPELINE) if x is s][0]).any()]
    print((p * 100).round(1).to_string())
    print("\nGesamtmittel je Modell:")
    print((mv.groupby("label").accuracy.mean() * 100).round(1).to_string())
    print("\nAufwand je vollstaendiger Strecke:")
    auf = mv.groupby("label").agg(usd=("cost_usd", "sum"), sek=("duration_s", "sum"),
                                  ptok=("prompt_tokens", "sum"),
                                  ctok=("completion_tokens", "sum"))
    print(auf.round(3).to_string())

unter("Streuung ueber die Wiederholungen (verkettet vs. isoliert)")
for iso in (False, True):
    lang = load_pipeline_reps(SEED, isolated=iso)
    if not len(lang):
        continue
    lang = lang.copy()
    lang["acc_eff"] = np.where(lang.status == "ok", lang.accuracy, 0.0)
    ges = lang.groupby(["label", "rep"]).acc_eff.mean().unstack()
    end = lang[lang.order == len(PIPELINE) - 1].pivot_table(
        index="label", columns="rep", values="acc_eff")
    print(f"\n[{'isoliert' if iso else 'verkettet'}] Gesamtwert je Wiederholung (%)")
    print((ges * 100).round(1).to_string())
    print(f"  Standardabweichung: {(ges.std(axis=1) * 100).round(2).to_dict()}")
    print("Endschritt je Wiederholung (%)")
    print((end * 100).round(1).to_string())

unter("Fehlerfortpflanzung: Verlust Kette gegenueber isoliert")
a = mean_over_reps(SEED, isolated=False).set_index(["label", "order"]).accuracy
b = mean_over_reps(SEED, isolated=True).set_index(["label", "order"]).accuracy
d = (b - a).dropna()
print("Endschritt:")
print((d.xs(len(PIPELINE) - 1, level="order") * 100).round(1).to_string())
print("\nueber alle Schritte gemittelt:")
print((d.groupby("label").mean() * 100).round(1).to_string())


# ------------------------------------------------------------------ Direkt

kopf("3  DIREKTVERARBEITUNG")

unter("Pipeline im Direkt-Modus, Seed 102")
for iso in (False, True):
    mv = mean_over_reps(SEED_HALB, isolated=iso, mode="direct")
    if not len(mv):
        print(f"[{'isoliert' if iso else 'verkettet'}] keine Daten")
        continue
    print(f"\n[{'isoliert' if iso else 'verkettet'}]")
    p = mv.pivot_table(index="order", columns="label", values="accuracy")
    print((p * 100).round(1).to_string())
    print("Gesamtmittel:", (mv.groupby("label").accuracy.mean() * 100).round(1).to_dict())
    auf = mv.groupby("label").agg(usd=("cost_usd", "sum"), sek=("duration_s", "sum"),
                                  ptok=("prompt_tokens", "sum"),
                                  ctok=("completion_tokens", "sum"))
    print(auf.round(2).to_string())

unter("Direkte Einzelaufgaben, Seed 2 (results_direct)")
zeilen = []
for p in sorted((settings.data_dir / "results_direct" / str(SEED)).rglob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    c = d.get("correctness") or {}
    zeilen.append(dict(
        provider=d.get("provider"), task_id=d.get("task_id"),
        accuracy=c.get("accuracy"), comparable=bool(c.get("comparable")),
        schema=bool(c.get("schema_match")), error=d.get("error"),
        rows=d.get("n_rows_returned"), rows_exp=c.get("row_count_expected"),
        cost_usd=d.get("cost_usd") or 0.0, latenz=d.get("llm_latency_seconds") or 0.0,
        prompt_tokens=d.get("prompt_tokens") or 0,
        completion_tokens=d.get("completion_tokens") or 0))
dd = pd.DataFrame(zeilen).sort_values("task_id")
if len(dd):
    dd["acc_eff"] = dd.accuracy.fillna(0.0).astype(float)
    print((dd.pivot_table(index="task_id", columns="provider",
                          values="acc_eff") * 100).round(1).to_string())
    print("\nZeilen geliefert / erwartet:")
    print(dd.pivot_table(index="task_id", columns="provider",
                         values="rows").to_string())
    print("erwartet:", dd.groupby("task_id").rows_exp.first().to_dict())
    print(f"\nKosten {dd.cost_usd.sum():.2f} USD, "
          f"Token {dd.prompt_tokens.sum():,.0f} ein / "
          f"{dd.completion_tokens.sum():,.0f} aus, "
          f"Laufzeit {dd.latenz.sum() / 60:.1f} min")
    ab = dd[dd.rows.fillna(0) < dd.rows_exp.fillna(0)]
    print(f"\nunvollstaendige Antworten: {len(ab)}")
    if len(ab):
        print(ab[["provider", "task_id", "rows", "rows_exp", "acc_eff"]]
              .to_string(index=False))


# ------------------------------------------------------------------ Gruppen

kopf("4  GEDRITTELTE STRECKE (Gruppen), Seed 2")

gr = load_groups(SEED)
if len(gr):
    gr["acc_eff"] = np.where(gr.status == "ok", gr.accuracy, 0.0).astype(float)
    gr["strat"] = gr.prompt_id.str.replace(r"^v\d_", "", regex=True)
    print(f"Laeufe: {len(gr)}   verwertbar: {(gr.status == 'ok').sum()}   "
          f"Wiederholungen: {sorted(gr.get('repetition', pd.Series([1])).unique())}")
    print(f"Kosten {gr.cost_usd.sum():.2f} USD, "
          f"Laufzeit {gr.duration_s.sum() / 60:.1f} min, "
          f"erster Versuch erfolgreich: {(gr.attempts == 1).sum()}/{len(gr)}")
    print("\nje Gruppe x Strategie (%):")
    print((gr.pivot_table(index="group", columns="strat", values="acc_eff") * 100)
          .round(1).to_string())
    print("\nje Gruppe x Modell (%):")
    print((gr.pivot_table(index="group", columns="provider", values="acc_eff") * 100)
          .round(1).to_string())
    print("\nMittel je Strategie:",
          (gr.groupby("strat").acc_eff.mean() * 100).round(1).to_dict())


# ------------------------------------------------------------------ Composite

kopf("5  ZUSAMMENGESETZTE AUFGABE MIT EXPLIZITEN SCHRITTEN, Seed 2")

co_alle = load_composite(SEED)
if len(co_alle):
    print("Laeufe je Wiederholung:",
          co_alle.groupby("repetition").size().to_dict(),
          "(vollstaendig waeren 18 je Wiederholung)")
co = co_alle[co_alle.repetition == 1] if len(co_alle) else co_alle
if len(co):
    co = co.copy()
    co["strat"] = co.prompt_id.str.replace(r"^[vd]\d_", "", regex=True)
    print(f"\n[nur Wiederholung 1]  Laeufe: {len(co)}   "
          f"verwertbar: {(co.status == 'ok').sum()}")
    print(f"Kosten gesamt: {co.cost_usd.sum():.2f} USD")
    print("\nje Modus x Modell (%):")
    print((co.pivot_table(index="provider", columns="mode", values="acc_eff") * 100)
          .round(1).to_string())
    print("\nje Modus x Strategie (%):")
    print((co.pivot_table(index="strat", columns="mode", values="acc_eff") * 100)
          .round(1).to_string())
    print("\nLaendercodes je Lauf (11 = Bereinigung erfolgt):")
    print(co.pivot_table(index="provider", columns=["mode", "strat"],
                         values="n_country_codes").to_string())
    print("\nAufwand je Modus (Mittel je Lauf):")
    print(co.groupby("mode")[["cost_usd", "duration_s", "prompt_tokens",
                              "completion_tokens"]].mean().round(1).to_string())
    print("\nFehler:")
    for r in co[co.status != "ok"].itertuples():
        print(f"  {r.mode}/{r.provider}/{r.prompt_id}: "
              f"{str(r.error)[-120:].strip()}")
