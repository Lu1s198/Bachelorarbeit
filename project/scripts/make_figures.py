"""Abbildungen fuer Kapitel 8 -- ausschliesslich aus Seed 2 bzw. 102.

Die Auswertung der Arbeit stuetzt sich allein auf diesen Datensatz. Er war
waehrend der Entwicklung unbekannt, wurde ohne nachtraegliche Anpassung von
Prompts oder Auswertungslogik durchlaufen und liegt auf jeder
Untersuchungsebene mit mehreren Wiederholungen vor.

Gestaltung: hoechstens zwei Bildfelder je Abbildung, waagerechte Balken fuer
lange Beschriftungen, Schriftgroessen ab 11 Punkt und Legenden in einer Zeile.
Vielfeldrige Abbildungen sind im Druck nicht mehr lesbar.

    python scripts/make_figures.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config import settings  # noqa: E402
from experiments.composite_runner import load_composite  # noqa: E402
from experiments.group_runner import load_groups  # noqa: E402
from experiments.pipeline_runner import PIPELINE  # noqa: E402
from reporting.analysis import (  # noqa: E402
    aligned_accuracy, ground_truth, load_runs,
)
from reporting.pipeline_analysis import load_pipeline_reps, mean_over_reps  # noqa: E402

SEED, SEED_HALB = 2, 102
FIG_DIR = repo_root / "figures"
DOC_DIR = repo_root.parent / "documentation" / "resources" / "images"

plt.rcParams.update({
    "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150,
})

CLOUD = ["anthropic", "openai", "google"]
MODELLE = ["anthropic", "openai", "google", "ollama"]
M_LABEL = {"anthropic": "Claude", "openai": "GPT", "google": "Gemini",
           "ollama": "Llama", "baseline": "Regel"}
M_FARBE = {"Claude": "#4e79a7", "GPT": "#f28e2b", "Gemini": "#59a14f",
           "Llama": "#b07aa1", "Regel": "#7f7f7f"}

STRAT = ["v1_zero_shot", "v2_few_shot", "v3_chain_of_thought"]
S_LABEL = {"v1_zero_shot": "Zero-Shot", "v2_few_shot": "Few-Shot",
           "v3_chain_of_thought": "Chain-of-Thought"}
S_FARBE = {"Zero-Shot": "#4e79a7", "Few-Shot": "#76b7b2",
           "Chain-of-Thought": "#b07aa1"}

AUFGABEN = [
    ("cleaning_easy_missing_and_whitespace", "1  Leerzeichen & fehlende Werte"),
    ("cleaning_medium_date_formats", "2  Datumsformate"),
    ("cleaning_hard_semantic_unification", "3  Ländercodes (semantisch)"),
    ("dedup_easy_exact_duplicates", "4  exakte Duplikate"),
    ("dedup_medium_key_duplicates", "5  Schlüssel-Duplikate"),
    ("dedup_hard_fuzzy_duplicates", "6  unscharfe Duplikate"),
    ("transform_easy_type_conversion", "7  Typkonvertierung"),
    ("transform_medium_derived_columns", "8  abgeleitete Spalten"),
    ("transform_hard_join_and_aggregate", "9  Join & Aggregation"),
]
def _kurz(label: str) -> str:
    """Letztes Segment der Schrittbezeichnung; die Trenner sind uneinheitlich."""
    for trenner in (": ", " · ", "· "):
        if trenner in label:
            label = label.split(trenner)[-1]
    return label.strip()


SCHRITT = [f"{i + 1}  {_kurz(s.label)}" for i, s in enumerate(PIPELINE)]


def sichern(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ziel = FIG_DIR / f"{name}.png"
    fig.savefig(ziel, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if DOC_DIR.is_dir():
        shutil.copy2(ziel, DOC_DIR / f"{name}.png")
    print(f"  {name}.png")


def beschriften(ax, balken, fmt="{:.0f}", mindest=3.0) -> None:
    """Zahlenwert an jeden Balken; sehr kurze Balken werden aussen beschriftet."""
    for b in balken:
        w = b.get_width()
        if np.isnan(w):
            continue
        innen = w >= mindest
        ax.text(w + (-1.5 if innen else 1.5), b.get_y() + b.get_height() / 2,
                fmt.format(w), va="center", ha="right" if innen else "left",
                fontsize=9.5, color="white" if innen else "#333333")


# ------------------------------------------------------------------ Daten

def matrix() -> pd.DataFrame:
    return load_runs(seed=SEED, include_baseline=False)


def baseline_je_aufgabe() -> pd.Series:
    b = load_runs(seed=SEED, include_baseline=True)
    b = b[b.provider == "baseline"]
    return b.groupby("task_id").eff_accuracy.mean()


def direkt_einzel() -> pd.DataFrame:
    """Direkte Einzelaufgaben mit **abgeglichener** Genauigkeit.

    Der Ergebnisdatensatz fuehrt nur die strenge Genauigkeit, die bei
    abweichender Zeilenzahl auf null faellt. Kapitel 8 berichtet durchgehend die
    abgeglichene Variante; sie wird deshalb hier aus den Ausgabetabellen
    nachberechnet, damit beide Ausfuehrungsmodi mit demselben Mass verglichen
    werden."""
    zeilen = []
    wurzel = settings.data_dir / "results_direct" / str(SEED)
    soll_cache: dict[str, pd.DataFrame] = {}
    for p in sorted(wurzel.rglob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        c = d.get("correctness") or {}
        aufgabe = d.get("task_id")
        soll = soll_cache.get(aufgabe)
        if soll is None:
            soll = ground_truth(aufgabe, SEED)
            soll_cache[aufgabe] = soll
        ist = None
        for kandidat in (p.parent / p.stem / "output.parquet",
                         p.with_suffix(".parquet")):
            if kandidat.exists():
                ist = pd.read_parquet(kandidat)
                break
        if ist is None:
            treffer = sorted((p.parent).glob(f"{d.get('provider')}_direct*/output.parquet"))
            if treffer:
                ist = pd.read_parquet(treffer[0])
        zeilen.append(dict(provider=d.get("provider"), task_id=aufgabe,
                           acc=aligned_accuracy(ist, soll),
                           acc_streng=float(c.get("accuracy") or 0.0),
                           rows=d.get("n_rows_returned") or 0,
                           rows_exp=c.get("row_count_expected") or 0))
    return pd.DataFrame(zeilen)


# ------------------------------------------------------------------ 1 Aufgaben

def abb_aufgaben() -> None:
    """Neun Aufgaben gegen die drei Ansaetze -- waagerecht, ein Feld."""
    m = matrix()
    cg = (m[m.provider.isin(CLOUD)].groupby("task_id").eff_accuracy.max() * 100)
    de = direkt_einzel().groupby("task_id").acc.max() * 100
    bl = baseline_je_aufgabe() * 100

    ids = [t for t, _ in AUFGABEN]
    namen = [n for _, n in AUFGABEN]
    y = np.arange(len(ids))[::-1]
    h = 0.26

    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    reihen = [("Code-Generierung", cg, "#4e79a7", +h),
              ("Direktverarbeitung", de, "#f28e2b", 0.0),
              ("regelbasiert", bl, "#59a14f", -h)]
    for name, serie, farbe, versatz in reihen:
        werte = [float(serie.get(i, np.nan)) for i in ids]
        b = ax.barh(y + versatz, werte, height=h, color=farbe, label=name)
        beschriften(ax, b)

    ax.set_yticks(y)
    ax.set_yticklabels(namen)
    ax.set_xlim(0, 108)
    ax.set_xlabel("abgeglichene Genauigkeit in Prozent")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncols=3,
              frameon=False)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    sichern(fig, "s2_aufgaben")


# ------------------------------------------------------------------ 2 Modelle

def abb_modelle() -> None:
    """Genauigkeit und Ausgang je Modell -- zwei Felder untereinander."""
    m = matrix()
    m = m.assign(label=m.provider.map(M_LABEL))
    reihen = [M_LABEL[p] for p in MODELLE if M_LABEL[p] in set(m.label)]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.4),
                                 gridspec_kw={"height_ratios": [1, 1]})
    y = np.arange(len(reihen))[::-1]
    acc = [m[m.label == r].eff_accuracy.mean() * 100 for r in reihen]
    erf = [m[m.label == r].produced.mean() * 100 for r in reihen]
    b1 = a1.barh(y + 0.19, acc, height=0.36, color="#4e79a7", label="Genauigkeit")
    b2 = a1.barh(y - 0.19, erf, height=0.36, color="#a0cbe8", label="Erfolgsquote")
    beschriften(a1, b1)
    beschriften(a1, b2)
    a1.set_yticks(y)
    a1.set_yticklabels(reihen)
    a1.set_xlim(0, 108)
    a1.set_xlabel("Prozent")
    a1.set_title("Ergebnisqualität über alle 54 Läufe je Modell", loc="left",
                  pad=26)
    a1.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncols=2,
              frameon=False)
    a1.grid(axis="x", alpha=0.25)
    a1.set_axisbelow(True)

    farben = {"ok": "#59a14f", "wrong_output": "#f0c000", "code_error": "#b2182b"}
    texte = {"ok": "verwertbar", "wrong_output": "Schema abweichend",
             "code_error": "Programmfehler"}
    links = np.zeros(len(reihen))
    for st in ("ok", "wrong_output", "code_error"):
        werte = np.array([(m[m.label == r].status == st).sum() for r in reihen],
                         dtype=float)
        a2.barh(y, werte, left=links, height=0.5, color=farben[st], label=texte[st])
        for yy, w, l in zip(y, werte, links):
            if w > 1.5:
                a2.text(l + w / 2, yy, f"{w:.0f}", ha="center", va="center",
                        color="white", fontsize=10)
        links += werte
    a2.set_yticks(y)
    a2.set_yticklabels(reihen)
    a2.set_xlabel("Zahl der Läufe")
    a2.set_title("Ausgang der Läufe", loc="left", pad=26)
    a2.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncols=3,
              frameon=False)
    a2.grid(axis="x", alpha=0.25)
    a2.set_axisbelow(True)

    fig.tight_layout(h_pad=2.6)
    sichern(fig, "s2_modelle")


# ------------------------------------------------------------------ 3 Strategien

def abb_strategien() -> None:
    """Drei Strategien je Aufgabe, nur Cloud-Modelle -- ein Feld, waagerecht."""
    m = matrix()
    c = m[m.provider.isin(CLOUD)]
    p = c.pivot_table(index="task_id", columns="prompt_id",
                      values="eff_accuracy", aggfunc="mean") * 100

    ids = [t for t, _ in AUFGABEN]
    namen = [n for _, n in AUFGABEN]
    y = np.arange(len(ids))[::-1]
    h = 0.26

    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    for k, s in enumerate(STRAT):
        versatz = (1 - k) * h
        werte = [float(p.loc[i, s]) if i in p.index and s in p.columns else np.nan
                 for i in ids]
        b = ax.barh(y + versatz, werte, height=h, color=S_FARBE[S_LABEL[s]],
                    label=S_LABEL[s])
        beschriften(ax, b)

    ax.set_yticks(y)
    ax.set_yticklabels(namen)
    ax.set_xlim(0, 108)
    ax.set_xlabel("abgeglichene Genauigkeit in Prozent")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncols=3, frameon=False)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    sichern(fig, "s2_strategien")


# ------------------------------------------------------------------ 4 Pipeline

def abb_pipeline() -> None:
    """Verkettet oben, isoliert unten -- zwei Felder untereinander."""
    fig, achsen = plt.subplots(2, 1, figsize=(12, 8.4), sharex=True)
    for ax, iso, titel in zip(
            achsen, (False, True),
            ("verkettet: jeder Schritt erhält die Ausgabe seines Vorgängers",
             "isoliert: jeder Schritt erhält die fehlerfreie Soll-Eingabe")):
        mv = mean_over_reps(SEED, isolated=iso)
        reihen = [l for l in ["Claude", "GPT", "Gemini", "Baseline"]
                  if l in set(mv.label)]
        x = np.arange(len(PIPELINE))
        b = 0.8 / len(reihen)
        for k, lab in enumerate(reihen):
            teil = mv[mv.label == lab].set_index("order").accuracy
            werte = [float(teil.get(i, np.nan)) * 100 for i in range(len(PIPELINE))]
            farbe = M_FARBE.get("Regel" if lab == "Baseline" else lab, "#888")
            ax.bar(x + (k - (len(reihen) - 1) / 2) * b, werte, width=b,
                   color=farbe, label="Regel" if lab == "Baseline" else lab)
        ax.set_ylim(0, 108)
        ax.set_ylabel("Genauigkeit in %")
        ax.set_title(titel, loc="left")
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    achsen[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.14),
                     ncols=4, frameon=False)
    achsen[1].set_xticks(np.arange(len(PIPELINE)))
    achsen[1].set_xticklabels(SCHRITT, rotation=28, ha="right")
    fig.tight_layout(h_pad=1.8)
    sichern(fig, "s2_pipeline")


# ------------------------------------------------------------------ 5 Streuung

def abb_streuung() -> None:
    """Endschritt je Wiederholung, verkettet gegen isoliert -- ein Feld."""
    fig, ax = plt.subplots(figsize=(10.5, 4.0))
    reihen = ["Claude", "GPT", "Gemini"]
    y = np.arange(len(reihen))[::-1]
    for iso, versatz, farbe, name in ((False, 0.18, "#b2182b", "verkettet"),
                                      (True, -0.18, "#4e79a7", "isoliert")):
        lang = load_pipeline_reps(SEED, isolated=iso)
        lang = lang.copy()
        lang["acc"] = np.where(lang.status == "ok", lang.accuracy, 0.0)
        end = lang[lang.order == len(PIPELINE) - 1]
        for yy, lab in zip(y, reihen):
            w = end[end.label == lab].acc.to_numpy() * 100
            if not len(w):
                continue
            ax.scatter(w, np.full(len(w), yy + versatz), s=110, color=farbe,
                       alpha=0.75, zorder=3,
                       label=name if lab == reihen[0] else None)
            ax.plot([w.min(), w.max()], [yy + versatz] * 2, color=farbe,
                    lw=2, alpha=0.35, zorder=2)
            ax.text(103, yy + versatz, f"σ {w.std(ddof=1):.1f}", va="center",
                    fontsize=10, color=farbe)
    ax.set_yticks(y)
    ax.set_yticklabels(reihen)
    ax.set_xlim(0, 118)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("Genauigkeit des Endschritts in Prozent, je Wiederholung")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncols=2, frameon=False)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    sichern(fig, "s2_streuung")


# ------------------------------------------------------------------ 6 Aufwand

def abb_aufwand() -> None:
    """Kosten, Laufzeit und Token je vollstaendiger Strecke -- drei knappe Felder."""
    cg = mean_over_reps(SEED, isolated=False)
    dm = mean_over_reps(SEED_HALB, isolated=False, mode="direct")
    reihen = ["Claude", "GPT", "Gemini"]

    def summe(mv, spalte):
        g = mv.groupby("label")[spalte].sum()
        return [float(g.get(r, np.nan)) for r in reihen]

    felder = [
        ("Kosten je Strecke in US-Dollar", summe(cg, "cost_usd"),
         summe(dm, "cost_usd"), "{:.2f}"),
        ("Laufzeit je Strecke in Sekunden", summe(cg, "duration_s"),
         summe(dm, "duration_s"), "{:.0f}"),
        ("Token je Strecke in Tausend",
         [(a + b) / 1000 for a, b in zip(summe(cg, "prompt_tokens"),
                                         summe(cg, "completion_tokens"))],
         [(a + b) / 1000 for a, b in zip(summe(dm, "prompt_tokens"),
                                         summe(dm, "completion_tokens"))], "{:.0f}"),
    ]
    fig, achsen = plt.subplots(1, 3, figsize=(13, 4.3))
    x = np.arange(len(reihen))
    for ax, (titel, a, b, fmt) in zip(achsen, felder):
        ax.bar(x - 0.2, a, width=0.4, color="#4e79a7", label="Code-Generierung")
        ax.bar(x + 0.2, b, width=0.4, color="#f28e2b", label="Direktverarbeitung")
        for xx, v in zip(x - 0.2, a):
            ax.text(xx, v, fmt.format(v), ha="center", va="bottom", fontsize=10)
        for xx, v in zip(x + 0.2, b):
            ax.text(xx, v, fmt.format(v), ha="center", va="bottom", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(reihen)
        ax.set_title(titel, fontsize=12)
        ax.margins(y=0.18)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    griffe, namen = achsen[0].get_legend_handles_labels()
    fig.legend(griffe, namen, loc="lower center", bbox_to_anchor=(0.5, 1.0),
               ncols=2, frameon=False)
    fig.tight_layout()
    sichern(fig, "s2_aufwand")


# ------------------------------------------------------------------ 7 Zuschnitt

def abb_zuschnitt() -> None:
    """Dieselben Schritte als Einzelaufgabe gegen gedrittelte Strecke."""
    gr = load_groups(SEED).copy()          # beide Wiederholungen
    gr["acc"] = np.where(gr.status == "ok", gr.accuracy, 0.0)
    gr["strat"] = gr.prompt_id.map(S_LABEL)

    m = matrix()
    c = m[m.provider.isin(CLOUD)].copy()
    c["strat"] = c.prompt_id.map(S_LABEL)
    KAT = {"cleaning": "Bereinigung", "deduplication": "Duplikate",
           "transformation": "Transformation"}
    GRP = {"cleaning": "Bereinigung", "dedup": "Duplikate",
           "transform": "Transformation"}
    c["kat"] = c.category.map(KAT)
    gr["kat"] = gr.group.map(GRP)

    kats = ["Bereinigung", "Duplikate", "Transformation"]
    fig, achsen = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
    for ax, (daten, titel) in zip(achsen, [
            (c, "Einzelaufgaben auf den Rohdaten"),
            (gr, "gedrittelte Strecke mit Soll-Eingabe")]):
        x = np.arange(len(kats))
        for k, s in enumerate(["Zero-Shot", "Few-Shot", "Chain-of-Thought"]):
            werte = [daten[(daten.kat == kk) & (daten.strat == s)]
                     [("eff_accuracy" if "eff_accuracy" in daten else "acc")].mean() * 100
                     for kk in kats]
            ax.bar(x + (k - 1) * 0.27, werte, width=0.27, color=S_FARBE[s], label=s)
            for xx, v in zip(x + (k - 1) * 0.27, werte):
                if not np.isnan(v):
                    ax.text(xx, v + 1.5, f"{v:.0f}", ha="center", fontsize=9.5)
        ax.set_xticks(x)
        ax.set_xticklabels(kats)
        ax.set_ylim(0, 112)
        ax.set_title(titel, fontsize=12)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    achsen[0].set_ylabel("Genauigkeit in %")
    achsen[0].legend(loc="lower center", bbox_to_anchor=(1.03, 1.10), ncols=3,
                     frameon=False)
    fig.tight_layout()
    sichern(fig, "s2_zuschnitt")


# ------------------------------------------------------------------ 8 Komposition

def abb_komposition() -> None:
    """Zusammengesetzte Aufgabe: vage gegen explizite Anweisung, beide Modi."""
    co = load_composite(SEED)
    if not len(co):
        return
    co = co.copy()                          # beide Wiederholungen
    co["strat"] = co.prompt_id.str.replace(r"^[vd]\d_", "", regex=True)
    S = {"zero_shot": "Zero-Shot", "few_shot": "Few-Shot",
         "chain_of_thought": "Chain-of-Thought"}
    co["strat"] = co.strat.map(S)

    m = matrix()
    vage = (m[(m.task_id == "transform_hard_join_and_aggregate")
              & (m.provider.isin(CLOUD))].groupby("provider").eff_accuracy.mean() * 100)

    reihen = ["Claude", "GPT", "Gemini"]
    prov = {"Claude": "anthropic", "GPT": "openai", "Gemini": "google"}
    fig, achsen = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)

    x = np.arange(len(reihen))
    a = achsen[0]
    v = [float(vage.get(prov[r], np.nan)) for r in reihen]
    n = [co[(co["mode"] == "codegen") & (co.provider == prov[r])].acc_eff.mean() * 100
         for r in reihen]
    a.bar(x - 0.2, v, width=0.4, color="#bbbbbb", label="vage Anweisung")
    a.bar(x + 0.2, n, width=0.4, color="#4e79a7", label="explizite Teilschritte")
    for xx, w in list(zip(x - 0.2, v)) + list(zip(x + 0.2, n)):
        if not np.isnan(w):
            a.text(xx, w + 1.5, f"{w:.0f}", ha="center", fontsize=10)
    a.set_xticks(x)
    a.set_xticklabels(reihen)
    a.set_title("Code-Generierung: Wirkung der Aufgabenstellung", fontsize=12)
    a.legend(frameon=False, fontsize=10, loc="upper left")

    b = achsen[1]
    for k, s in enumerate(["Zero-Shot", "Few-Shot", "Chain-of-Thought"]):
        teil = [co[(co["mode"] == "codegen") & (co.provider == prov[r])
                   & (co.strat == s)] for r in reihen]
        cgv = [t.acc_eff.mean() * 100 for t in teil]
        b.bar(x + (k - 1) * 0.27, cgv, width=0.27, color=S_FARBE[s], label=s)
        for xx, v, t in zip(x + (k - 1) * 0.27, cgv, teil):
            if np.isnan(v):
                continue
            gescheitert = len(t) and not (t.status == "ok").any()
            b.text(xx, v + 1.5, "Fehler" if gescheitert else f"{v:.0f}",
                   ha="center", fontsize=9 if gescheitert else 9.5,
                   color="#b2182b" if gescheitert else "black",
                   rotation=90 if gescheitert else 0,
                   va="bottom")
    dmv = [co[(co["mode"] == "direct") & (co.provider == prov[r])].acc_eff.mean() * 100
           for r in reihen]
    b.plot(x, dmv, "o--", color="#f28e2b", lw=2, ms=9,
           label="Direktverarbeitung (Mittel)")
    b.set_xticks(x)
    b.set_xticklabels(reihen)
    b.set_title("explizite Teilschritte: Strategien und Modus", fontsize=12)
    b.legend(frameon=False, fontsize=9.5, ncols=2, loc="upper left")

    for ax in achsen:
        ax.set_ylim(0, 108)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    achsen[0].set_ylabel("Genauigkeit in %")
    fig.tight_layout()
    sichern(fig, "s2_komposition")


if __name__ == "__main__":
    print("Abbildungen aus Seed 2 / 102:")
    abb_aufgaben()
    abb_modelle()
    abb_strategien()
    abb_pipeline()
    abb_streuung()
    abb_aufwand()
    abb_zuschnitt()
    abb_komposition()
    print(f"\nabgelegt in {FIG_DIR} und {DOC_DIR}")
