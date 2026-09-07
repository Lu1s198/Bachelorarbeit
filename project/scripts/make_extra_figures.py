"""Zusaetzliche Vergleichsgrafiken aus den vorhandenen Ergebnisdaten.

Deckt die Ebenen ab, deren Rohlaeufe vorliegen: verkettete Pipeline und
isolierter Durchlauf, gruppierte Strecke, explizit gegliederte Aufgabe sowie
den Direkt-Modus. Die Faktormatrix bleibt aussen vor, ihre Einzelaufzeichnungen
liegen nicht im Repositorium.

Ausgabe als PNG unter ``project/figures/`` mit dem Praefix ``x_``. Die Grafiken
werden bewusst noch nicht in die Ausarbeitung eingebunden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"

SEEDS = {2, 102}          # ausgewerteter Datensatz und seine halbierte Fassung

PROV_LABEL = {"anthropic": "Anthropic", "openai": "OpenAI",
              "google": "Google", "ollama": "Meta (lokal)", "baseline": "Regelbasiert"}
PROV_COLOR = {"anthropic": "#4e79a7", "openai": "#f28e2b",
              "google": "#59a14f", "ollama": "#b07aa1", "baseline": "#9c755f"}
MODE_COLOR = {"codegen": "#4e79a7", "pipeline": "#4e79a7", "direct": "#f28e2b"}
MODE_LABEL = {"codegen": "Code-Gen.", "pipeline": "Code-Gen.", "direct": "Direkt"}
STRAT_LABEL = {"zero_shot": "Zero-Shot", "few_shot": "Few-Shot",
               "chain_of_thought": "Chain-of-Thought"}
STRAT_COLOR = {"zero_shot": "#4e79a7", "few_shot": "#f28e2b", "chain_of_thought": "#59a14f"}


# ------------------------------------------------------------------ laden
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return np.nan


def load() -> pd.DataFrame:
    rows = []

    for p in DATA.glob("results_pipeline/*/*/pipeline.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("seed") not in SEEDS:
            continue
        isoliert = "isolated" in p.parent.name
        for st in d.get("steps", []):
            rows.append(dict(
                ebene="Isolierter Durchlauf" if isoliert else "Verkettete Pipeline",
                seed=d.get("seed"), provider=d.get("provider"), mode=d.get("mode"),
                strategy=None, einheit=st.get("label") or st.get("step"),
                accuracy=_num(st.get("accuracy")), cost_usd=_num(st.get("cost_usd")),
                prompt_tokens=_num(st.get("prompt_tokens")),
                completion_tokens=_num(st.get("completion_tokens")),
                duration_s=_num(st.get("duration_s")), llm_s=_num(st.get("llm_s")),
                exec_s=_num(st.get("exec_s")), status=st.get("status"),
            ))

    for ordner, ebene in [("results_group", "Gruppierte Strecke"),
                          ("results_composite", "Explizit gegliederte Aufgabe")]:
        for p in DATA.glob(f"{ordner}/*/**/record.json"):
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("seed") not in SEEDS:
                continue
            rows.append(dict(
                ebene=ebene, seed=d.get("seed"), provider=d.get("provider"),
                mode=d.get("mode", "codegen"), strategy=d.get("prompt_strategy"),
                einheit=d.get("group_label") or d.get("group") or d.get("task"),
                accuracy=_num(d.get("accuracy")), cost_usd=_num(d.get("cost_usd")),
                prompt_tokens=_num(d.get("prompt_tokens")),
                completion_tokens=_num(d.get("completion_tokens")),
                duration_s=_num(d.get("duration_s")), llm_s=_num(d.get("llm_s")),
                exec_s=_num(d.get("exec_s")), status=d.get("status"),
            ))

    for p in DATA.glob("results_direct/*/*/*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("seed") not in SEEDS:
            continue
        rows.append(dict(
            ebene="Faktormatrix, Direkt-Modus", seed=d.get("seed"),
            provider=d.get("provider"), mode="direct", strategy=d.get("prompt_strategy"),
            einheit=d.get("task_id"), accuracy=_num(d.get("correctness")),
            cost_usd=_num(d.get("cost_usd")), prompt_tokens=_num(d.get("prompt_tokens")),
            completion_tokens=_num(d.get("completion_tokens")),
            duration_s=_num(d.get("llm_latency_seconds")),
            llm_s=_num(d.get("llm_latency_seconds")), exec_s=np.nan,
            status=None,
        ))

    df = pd.DataFrame(rows)
    df["provider"] = df["provider"].fillna("baseline")
    return df


# ------------------------------------------------------------------ helfer
def _save(fig, name, titel):
    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / f"x_{name}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {out.name:28s} {titel}")


def _stil(ax, ylabel="", xlabel=""):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)


def _beschriften(ax, bars, fmt="{:.0f}", dy=0):
    for b in bars:
        h = b.get_height()
        if np.isfinite(h):
            ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h),
                    ha="center", va="bottom", fontsize=8)


# ------------------------------------------------------------------ figuren
def f_modus(df):
    """Direkt-Modus gegen Code-Generierung, dort wo beide gelaufen sind."""
    d = df[(df.ebene == "Explizit gegliederte Aufgabe") & df.accuracy.notna()]
    if d.empty:
        return
    piv = d.groupby(["provider", "mode"]).accuracy.mean().unstack() * 100
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    x = np.arange(len(piv)); w = 0.36
    for i, m in enumerate([c for c in ["codegen", "direct"] if c in piv.columns]):
        b = ax.bar(x + (i - 0.5) * w, piv[m], w, color=MODE_COLOR[m],
                   label="Code-Generierung" if m == "codegen" else "Direkt-Verarbeitung")
        _beschriften(ax, b, "{:.1f}")
    ax.set_xticks(x); ax.set_xticklabels([PROV_LABEL.get(p, p) for p in piv.index])
    ax.set_ylim(0, 105)
    ax.set_title("Ausführungsmodus im direkten Vergleich\n(explizit gegliederte Aufgabe, Startwert 2)",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    _stil(ax, "Mittlere Genauigkeit in Prozent")
    _save(fig, "modusvergleich", "Direkt vs. Code-Generierung")


def f_anbieter(df):
    """Genauigkeit je Anbieter ueber die Ebenen mit Modellbeteiligung."""
    d = df[df.accuracy.notna() & (df.provider != "baseline")]
    piv = d.groupby(["ebene", "provider"]).accuracy.mean().unstack() * 100
    if piv.empty:
        return
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    x = np.arange(len(piv)); provs = [p for p in PROV_LABEL if p in piv.columns]
    w = 0.8 / max(len(provs), 1)
    for i, p in enumerate(provs):
        b = ax.bar(x + (i - (len(provs) - 1) / 2) * w, piv[p], w,
                   color=PROV_COLOR[p], label=PROV_LABEL[p])
        _beschriften(ax, b, "{:.0f}")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(", ", ",\n").replace(" und ", "\nund ") for t in piv.index],
                       fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_title("Anbietervergleich je Untersuchungsebene", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3)
    _stil(ax, "Mittlere Genauigkeit in Prozent")
    _save(fig, "anbieter_ebenen", "Anbieter je Ebene")


def f_strategie(df):
    d = df[df.strategy.notna() & df.accuracy.notna() & df.strategy.isin(STRAT_LABEL)]
    if d.empty:
        return
    piv = d.groupby(["ebene", "strategy"]).accuracy.mean().unstack() * 100
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    x = np.arange(len(piv)); strats = [s for s in STRAT_LABEL if s in piv.columns]
    w = 0.8 / max(len(strats), 1)
    for i, s in enumerate(strats):
        b = ax.bar(x + (i - (len(strats) - 1) / 2) * w, piv[s], w,
                   color=STRAT_COLOR[s], label=STRAT_LABEL[s])
        _beschriften(ax, b, "{:.1f}")
    ax.set_xticks(x); ax.set_xticklabels([t.replace(" ", "\n", 1) for t in piv.index], fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_title("Prompting-Strategien je Untersuchungsebene", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3)
    _stil(ax, "Mittlere Genauigkeit in Prozent")
    _save(fig, "strategien", "Prompting-Strategien")


def f_kosten(df):
    d = df[df.cost_usd.notna() & (df.provider != "baseline") & (df.cost_usd > 0)]
    if d.empty:
        return
    piv = d.groupby(["ebene", "provider"]).cost_usd.sum().unstack()
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    x = np.arange(len(piv)); provs = [p for p in PROV_LABEL if p in piv.columns]
    w = 0.8 / max(len(provs), 1)
    for i, p in enumerate(provs):
        b = ax.bar(x + (i - (len(provs) - 1) / 2) * w, piv[p], w,
                   color=PROV_COLOR[p], label=PROV_LABEL[p])
        _beschriften(ax, b, "{:.2f}")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(", ", ",\n").replace(" und ", "\nund ") for t in piv.index],
                       fontsize=9)
    ax.set_title("Nutzungskosten je Untersuchungsebene und Anbieter",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3)
    _stil(ax, "Summe der Nutzungskosten in US-Dollar")
    _save(fig, "kosten_ebenen", "Kosten je Ebene und Anbieter")


def f_token(df):
    """Token je Aufruf fuer dieselbe Aufgabe, beide Ausfuehrungsmodi.

    Nur die explizit gegliederte Aufgabe erlaubt den direkten Vergleich: Dort
    liefen beide Modi auf identischer Aufgabenstellung.
    """
    d = df[(df.ebene == "Explizit gegliederte Aufgabe") & df.prompt_tokens.notna()]
    if d.empty:
        return
    g = d.groupby(["provider", "mode"])[["prompt_tokens", "completion_tokens"]].mean()
    provs = [p for p in PROV_LABEL if p in g.index.get_level_values(0)]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    x = np.arange(len(provs)); w = 0.36
    for i, m in enumerate(["codegen", "direct"]):
        pt = [g.loc[(p, m), "prompt_tokens"] if (p, m) in g.index else np.nan for p in provs]
        ct = [g.loc[(p, m), "completion_tokens"] if (p, m) in g.index else np.nan for p in provs]
        off = (i - 0.5) * w
        ax.bar(x + off, pt, w, color="#4e79a7" if i == 0 else "#a0c4e4",
               label="Eingabe-Token" if i == 0 else None)
        ax.bar(x + off, ct, w, bottom=pt, color="#f28e2b" if i == 0 else "#f7c08a",
               label="Ausgabe-Token" if i == 0 else None)
        for xi, (a, b) in enumerate(zip(pt, ct)):
            if np.isfinite(a) and np.isfinite(b):
                ax.text(xi + off, a + b, f"{int(a + b):,}".replace(",", "."),
                        ha="center", va="bottom", fontsize=8)
                ax.text(xi + off, -2600, "Code-Gen." if i == 0 else "Direkt",
                        ha="center", va="top", fontsize=8, color="#555555")
    ax.set_xticks(x); ax.set_xticklabels([PROV_LABEL[p] for p in provs], fontsize=10)
    ax.tick_params(axis="x", pad=18)
    ax.set_title("Token-Verbrauch je Aufruf bei identischer Aufgabe\n"
                 "(explizit gegliederte Aufgabe, heller = Direkt-Verarbeitung)",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    _stil(ax, "Token je Aufruf")
    _save(fig, "token", "Token-Verbrauch, gleiche Aufgabe")


def f_dauer(df):
    """Dauer je Aufruf, getrennt nach Ebene statt ueber Ebenen gemittelt."""
    d = df[(df.provider != "baseline") & df.llm_s.notna()]
    if d.empty:
        return
    g = d.groupby(["ebene", "provider"]).llm_s.mean().unstack()
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    x = np.arange(len(g)); provs = [p for p in PROV_LABEL if p in g.columns]
    w = 0.8 / max(len(provs), 1)
    for i, p in enumerate(provs):
        b = ax.bar(x + (i - (len(provs) - 1) / 2) * w, g[p], w,
                   color=PROV_COLOR[p], label=PROV_LABEL[p])
        _beschriften(ax, b, "{:.1f}")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(", ", ",\n").replace(" und ", "\nund ") for t in g.index],
                       fontsize=9)
    ax.set_title("Mittlere Dauer eines Modellaufrufs je Untersuchungsebene",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3)
    _stil(ax, "Sekunden je Aufruf")
    _save(fig, "dauer", "Dauer je Ebene")


def f_kette(df):
    d = df[df.ebene.isin(["Verkettete Pipeline", "Isolierter Durchlauf"])
           & df.accuracy.notna() & (df["mode"] == "pipeline")]
    if d.empty:
        return
    fig, ax = plt.subplots(figsize=(10.4, 4.8))
    for eb, ls, mk in [("Verkettete Pipeline", "-", "o"), ("Isolierter Durchlauf", "--", "s")]:
        s = d[d.ebene == eb]
        if s.empty:
            continue
        m = s.groupby("einheit").accuracy.mean() * 100
        ax.plot(range(len(m)), m.values, ls, marker=mk, lw=2, ms=5,
                color="#4e79a7" if eb == "Verkettete Pipeline" else "#59a14f", label=eb)
        ax.set_xticks(range(len(m)))
        ax.set_xticklabels([str(v).replace(" · ", ". ") for v in m.index], rotation=28, ha="right", fontsize=8)
    base = df[(df.provider == "baseline") & (df.ebene == "Verkettete Pipeline")
              & df.accuracy.notna()]
    if not base.empty:
        bm = base.groupby("einheit").accuracy.mean() * 100
        ax.plot(range(len(bm)), bm.values, ":", lw=2, color="#9c755f",
                label="Regelbasierte Pipeline")
    ax.set_ylim(0, 105)
    ax.set_title("Qualitätsverlauf über die Kette: geerbter gegen eigener Fehler",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    _stil(ax, "Mittlere Genauigkeit in Prozent")
    _save(fig, "kette", "Kettenverlauf verkettet vs. isoliert")


def f_kosten_kpi(df):
    """Kosten je vollstaendigem Durchlauf, als vergleichbare Kennzahl."""
    d = df[(df.provider != "baseline") & df.cost_usd.notna() & (df.cost_usd > 0)]
    if d.empty:
        return
    g = d.groupby(["ebene", "provider"]).cost_usd.mean().unstack() * 1000
    fig, ax = plt.subplots(figsize=(9.5, 4.3))
    x = np.arange(len(g)); provs = [p for p in PROV_LABEL if p in g.columns]
    w = 0.8 / max(len(provs), 1)
    for i, p in enumerate(provs):
        b = ax.bar(x + (i - (len(provs) - 1) / 2) * w, g[p], w,
                   color=PROV_COLOR[p], label=PROV_LABEL[p])
        _beschriften(ax, b, "{:.1f}")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(", ", ",\n").replace(" und ", "\nund ") for t in g.index],
                       fontsize=9)
    ax.set_title("Kosten je Einzelaufruf (Tausendstel US-Dollar)", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3)
    _stil(ax, "Kosten je Aufruf in Tausendstel USD")
    _save(fig, "kosten_je_aufruf", "Kosten je Aufruf")


def main() -> int:
    df = load()
    if df.empty:
        print("keine Daten gefunden")
        return 1
    print(f"geladen: {len(df)} Einzelmessungen aus den Startwerten {sorted(SEEDS)}")
    print(df.groupby("ebene").size().to_string())
    print("\nerzeugte Abbildungen:")
    for fn in (f_modus, f_anbieter, f_strategie, f_kosten, f_kosten_kpi,
               f_token, f_dauer, f_kette):
        try:
            fn(df)
        except Exception as e:  # eine fehlende Ebene soll den Rest nicht stoppen
            print(f"  !! {fn.__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
