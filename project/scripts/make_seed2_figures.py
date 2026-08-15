"""Abbildungen des Bestaetigungslaufs (Seed 2 bzw. 102) fuer Kapitel 8.

Seed 1 diente der Entwicklung: Prompts, Aufgabenzuschnitt und Auswertungslogik
wurden an ihm justiert. Seine Werte sind damit nicht unbefangen. Seed 2 wurde
erst nach Abschluss aller Aenderungen erzeugt und ohne weiteren Eingriff
mehrfach durchlaufen -- er traegt deshalb die bestaetigende Aussage.

    python scripts/make_seed2_figures.py

Erzeugt in project/figures/:
    bestaetigung_pipeline.png    Genauigkeit je Schritt, Mittel und Bestwert
    bestaetigung_streuung.png    Streuung ueber die Wiederholungen
    bestaetigung_aufwand.png     Kosten, Token und Zeit je Modus
    bestaetigung_strategien.png  drei Strategien x neun Aufgaben x Modelle
"""

from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from experiments.pipeline_runner import PIPELINE  # noqa: E402
from reporting.analysis import PROVIDER_LABEL  # noqa: E402
from reporting.compare import (  # noqa: E402
    CLASSIC_STRATEGIES, MODEL_ORDER, STRATEGY_COLORS, STRATEGY_LABELS,
    TASK_LABEL, save_fig,
)
from reporting.pipeline_analysis import load_pipeline_reps  # noqa: E402

# Seed des vollstaendigen Datensatzes und der halbierten Fassung fuer den
# Direkt-Modus. Die Konvention lautet: halbiert = Quell-Seed + 100.
SEED_VOLL = 2
SEED_HALB = 102

C_CODE = "#4e79a7"
C_DIRECT = "#f28e2b"
C_BASE = "#59a14f"

MODELLE = ["anthropic", "openai", "google"]
# Kurzform der Schrittbezeichnung fuer die Achsen: "1 · Bereinigung: Leerzeichen
# & fehlende Werte" wird zu "1 Leerzeichen & fehl. Werte".
KURZ = [f"{i + 1} {s.label.split(': ')[-1] if ': ' in s.label else s.label.split('· ')[-1]}"
        for i, s in enumerate(PIPELINE)]


# ------------------------------------------------------------------ Aggregation

def lauf_kennzahlen(seed: int, isolated: bool, mode: str) -> pd.DataFrame:
    """Je (Modell, Wiederholung) eine Zeile: Mittel ueber die neun Schritte,
    Endschritt und Aufwand.

    Ein abgebrochener Schritt geht mit 0 ein. Andernfalls stuende ein Lauf besser
    da, gerade weil er weniger Schritte geliefert hat."""
    d = load_pipeline_reps(seed, isolated=isolated, mode=mode)
    if not len(d):
        return pd.DataFrame()
    d = d.copy()
    d["acc"] = np.where(d.status == "ok", d.accuracy, 0.0)
    end = d[d.step == "final"].set_index(["label", "rep"]).acc
    g = d.groupby(["label", "rep"]).agg(
        mittel=("acc", "mean"), n_ok=("status", lambda s: (s == "ok").sum()),
        kosten=("cost_usd", "sum"), dauer=("duration_s", "sum"),
        eingabe=("prompt_tokens", "sum"), ausgabe=("completion_tokens", "sum"))
    g["endschritt"] = end.reindex(g.index).fillna(0.0)
    return g.reset_index()


def schritt_kennzahlen(seed: int, isolated: bool, mode: str) -> pd.DataFrame:
    """Je (Modell, Schritt): Mittel, Bestwert und Schlechtwert ueber die Wdh."""
    d = load_pipeline_reps(seed, isolated=isolated, mode=mode)
    if not len(d):
        return pd.DataFrame()
    d = d.copy()
    d["acc"] = np.where(d.status == "ok", d.accuracy, 0.0)
    T = d.groupby(["label", "step"], as_index=False).agg(
        mittel=("acc", "mean"), best=("acc", "max"), schlecht=("acc", "min"),
        n=("rep", "nunique"))
    # Schritte, die ein Lauf gar nicht mehr erreicht hat, fehlen im Datensatz
    # vollstaendig. Sie muessen als 0 erscheinen und nicht als Luecke, sonst
    # haben die Modelle unterschiedlich lange Balkenreihen.
    voll = pd.MultiIndex.from_product(
        [sorted(set(T.label)), [s.name for s in PIPELINE]], names=["label", "step"])
    T = (T.set_index(["label", "step"]).reindex(voll)
         .fillna({"mittel": 0.0, "best": 0.0, "schlecht": 0.0}).reset_index())
    T["n"] = T.groupby("label").n.transform(lambda s: s.max())
    T["order"] = T.step.map({s.name: i for i, s in enumerate(PIPELINE)})
    return T


# ------------------------------------------------------------------- Abbildungen

def abb_pipeline():
    """Vier Felder: Code-Gen und Direkt, jeweils verkettet und isoliert.

    Der Balken zeigt das Mittel ueber die Wiederholungen, der aufgesetzte helle
    Aufsatz reicht bis zum Bestwert. So sind Durchschnitts- und Spitzenleistung
    in einer Darstellung ablesbar, ohne den Mittelwert zu beschoenigen."""
    felder = [
        (SEED_VOLL, False, "codegen", "Code-Generierung, verkettet", C_CODE),
        (SEED_VOLL, True, "codegen", "Code-Generierung, isoliert", C_CODE),
        (SEED_HALB, False, "direct", "Direktverarbeitung, verkettet", C_DIRECT),
        (SEED_HALB, True, "direct", "Direktverarbeitung, isoliert", C_DIRECT),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 8.4), sharey=True)
    x = np.arange(len(PIPELINE))
    for ax, (seed, iso, mode, titel, farbe) in zip(axes.ravel(), felder):
        T = schritt_kennzahlen(seed, iso, mode)
        if not len(T):
            ax.text(0.5, 0.5, "keine Daten", ha="center", va="center",
                    transform=ax.transAxes, color="#888")
            ax.set_title(titel, fontsize=11)
            continue
        labels = [PROVIDER_LABEL[p] for p in MODELLE if PROVIDER_LABEL[p] in set(T.label)]
        w = 0.8 / max(len(labels), 1)
        for i, lbl in enumerate(labels):
            sub = T[T.label == lbl].sort_values("order")
            off = (i - (len(labels) - 1) / 2) * w
            m = sub.mittel.to_numpy()
            b = sub.best.to_numpy()
            ax.bar(x + off, m, w * 0.92, color=f"C{i}", label=lbl, zorder=3)
            # Aufsatz bis zum Bestwert: der Spielraum, den die beste
            # Wiederholung gegenueber dem Mittel gewinnt.
            ax.bar(x + off, b - m, w * 0.92, bottom=m, color=f"C{i}",
                   alpha=0.28, zorder=3)
        n = int(T.n.max())
        ax.set_xticks(x)
        ax.set_xticklabels(KURZ, rotation=35, ha="right", fontsize=7.5)
        ax.set_ylim(0, 1.08)
        ax.set_title(f"{titel} ({n} Wdh.)", fontsize=11)
        ax.grid(axis="y", ls=":", alpha=0.5, zorder=0)
        ax.legend(fontsize=8, loc="lower left", ncol=3)
    for reihe in axes:
        reihe[0].set_ylabel("abgeglichene Genauigkeit")
    fig.suptitle("Bestätigungslauf auf unbekanntem Datensatz: Genauigkeit je "
                 "Pipeline-Schritt\nBalken = Mittel über die Wiederholungen, "
                 "heller Aufsatz = beste Wiederholung", fontsize=12.5, y=1.0)
    fig.tight_layout()
    save_fig(fig, "bestaetigung_pipeline")
    plt.close(fig)


def abb_streuung():
    """Reproduzierbarkeit: Lage und Spannweite der Wiederholungen.

    Links der Gesamtwert eines Laufs (Mittel ueber neun Schritte), rechts der
    Endschritt. Der Endschritt traegt die gesamte Fehlerfortpflanzung und ist
    deshalb die empfindlichste Einzelgroesse der Kette."""
    quellen = [
        (SEED_VOLL, False, "codegen", "Code-Gen.\nverkettet"),
        (SEED_VOLL, True, "codegen", "Code-Gen.\nisoliert"),
        (SEED_HALB, False, "direct", "Direkt\nverkettet"),
        (SEED_HALB, True, "direct", "Direkt\nisoliert"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.0))
    for ax, spalte, titel in ((axes[0], "mittel", "Gesamtwert des Laufs (Ø neun Schritte)"),
                              (axes[1], "endschritt", "Endschritt (Join & Aggregation)")):
        pos, ticks, tickpos = 0, [], []
        for seed, iso, mode, qlabel in quellen:
            L = lauf_kennzahlen(seed, iso, mode)
            if not len(L):
                pos += 1
                continue
            start = pos
            for i, p in enumerate(MODELLE):
                lbl = PROVIDER_LABEL[p]
                v = L[L.label == lbl][spalte].to_numpy()
                if not len(v):
                    continue
                ax.plot([pos, pos], [v.min(), v.max()], color="#bbb", lw=6,
                        solid_capstyle="round", zorder=2)
                ax.plot([pos] * len(v), v, "o", ms=5, color=f"C{i}", zorder=3,
                        alpha=0.75)
                ax.plot(pos, v.mean(), "_", ms=22, mew=2.6, color="black", zorder=4)
                ticks.append(lbl)
                tickpos.append(pos)
                pos += 1
            ax.text((start + pos - 1) / 2, -0.20, qlabel, ha="center", va="top",
                    fontsize=9, transform=ax.get_xaxis_transform())
            ax.axvline(pos - 0.5, color="#ddd", lw=1)
            pos += 1
        ax.set_xticks(tickpos)
        ax.set_xticklabels(ticks, rotation=45, ha="right", fontsize=8)
        ax.set_ylim(-0.03, 1.06)
        ax.set_ylabel("abgeglichene Genauigkeit")
        ax.set_title(titel, fontsize=11)
        ax.grid(axis="y", ls=":", alpha=0.5)
    fig.suptitle("Reproduzierbarkeit über die Wiederholungen: jeder Punkt ein Lauf, "
                 "Strich das Mittel", fontsize=12.5, y=1.0)
    fig.tight_layout()
    save_fig(fig, "bestaetigung_streuung")
    plt.close(fig)


def abb_aufwand():
    """Kosten, Token und Zeit einer vollstaendigen Strecke je Modus.

    Die Gegenueberstellung ist der eigentliche Preis der Direktverarbeitung: Sie
    laeuft auf dem *halbierten* Datensatz und ist trotzdem um ein Vielfaches
    teurer, weil die Tabelle in jedem Schritt vollstaendig durch das Modell
    hindurchgereicht wird, statt nur die Vorschrift zu ihrer Verarbeitung."""
    zeilen = []
    for seed, mode, mlabel in ((SEED_VOLL, "codegen", "Code-Generierung"),
                               (SEED_HALB, "direct", "Direktverarbeitung")):
        L = lauf_kennzahlen(seed, False, mode)
        if not len(L):
            continue
        for p in MODELLE:
            sub = L[L.label == PROVIDER_LABEL[p]]
            if not len(sub):
                continue
            zeilen.append(dict(
                modus=mlabel, modell=PROVIDER_LABEL[p],
                kosten=sub.kosten.mean(), dauer=sub.dauer.mean(),
                eingabe=sub.eingabe.mean(), ausgabe=sub.ausgabe.mean()))
    D = pd.DataFrame(zeilen)
    if not len(D):
        print("  bestaetigung_aufwand: keine Daten")
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    modi = list(dict.fromkeys(D.modus))
    modelle = list(dict.fromkeys(D.modell))
    x = np.arange(len(modelle))
    w = 0.8 / len(modi)

    def gruppe(ax, spalte, titel, ylabel, fmt, log=False):
        for i, m in enumerate(modi):
            sub = D[D.modus == m].set_index("modell").reindex(modelle)
            off = (i - (len(modi) - 1) / 2) * w
            farbe = C_CODE if m.startswith("Code") else C_DIRECT
            b = ax.bar(x + off, sub[spalte].fillna(0), w * 0.9, color=farbe, label=m)
            for r in b:
                h = r.get_height()
                if h > 0:
                    ax.text(r.get_x() + r.get_width() / 2, h, fmt.format(h),
                            ha="center", va="bottom", fontsize=7.5)
        ax.set_xticks(x)
        ax.set_xticklabels(modelle)
        ax.set_ylabel(ylabel)
        ax.set_title(titel, fontsize=10.5)
        if log:
            ax.set_yscale("log")
        ax.grid(axis="y", ls=":", alpha=0.5)

    gruppe(axes[0], "kosten", "Kosten einer vollständigen Strecke", "Kosten ($)",
           "${:.2f}")
    gruppe(axes[1], "dauer", "Dauer einer vollständigen Strecke", "Dauer (s)",
           "{:.0f}s")
    D["token"] = D.eingabe + D.ausgabe
    gruppe(axes[2], "token", "Token je Strecke (Ein- und Ausgabe)", "Token",
           "{:.0f}", log=True)
    axes[0].legend(fontsize=8.5)
    fig.suptitle("Aufwand der beiden Ausführungsmodi je vollständigem Durchlauf "
                 "(Mittel über die Wiederholungen)\nDie Direktverarbeitung "
                 "arbeitet dabei auf dem halbierten Datensatz",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    save_fig(fig, "bestaetigung_aufwand")
    plt.close(fig)
    return D


def abb_strategien():
    """Drei Prompting-Strategien x neun Aufgaben x drei Modelle auf Seed 2.

    Die Einzelaufgaben-Matrix ist von Haus aus isoliert: Jede Aufgabe liest die
    Rohdaten, kein Ergebnis wird weitergereicht. Ein gesonderter isolierter Lauf
    wie bei der Pipeline ist hier deshalb weder noetig noch definierbar."""
    from reporting.analysis import load_runs
    try:
        runs = load_runs(SEED_VOLL, include_baseline=True)
    except Exception as exc:  # noqa: BLE001
        print(f"  bestaetigung_strategien: keine Matrix-Laeufe fuer Seed "
              f"{SEED_VOLL} ({exc})")
        return
    llm = runs[(runs.provider.isin(MODELLE))
               & (runs.prompt_id.isin(CLASSIC_STRATEGIES))]
    if not len(llm):
        print(f"  bestaetigung_strategien: keine Matrix-Laeufe fuer Seed {SEED_VOLL}"
              f" -- zuerst scripts/run_experiments.py --seed {SEED_VOLL} ausfuehren")
        return

    base = (runs[runs.provider == "baseline"].groupby("task_id").acc_aligned.mean()
            if "baseline" in set(runs.provider) else pd.Series(dtype=float))
    g = llm.groupby(["task_id", "provider", "prompt_id"]).acc_aligned.mean()
    aufgaben = [t for t in TASK_LABEL if t in set(llm.task_id)]

    fig, axes = plt.subplots(3, 3, figsize=(15.5, 10), sharey=True)
    x = np.arange(len(MODELLE))
    w = 0.8 / len(CLASSIC_STRATEGIES)
    for ax, task in zip(axes.ravel(), aufgaben):
        for j, strat in enumerate(CLASSIC_STRATEGIES):
            vals = [g.get((task, p, strat), np.nan) for p in MODELLE]
            off = (j - (len(CLASSIC_STRATEGIES) - 1) / 2) * w
            ax.bar(x + off, vals, w * 0.9, color=STRATEGY_COLORS[strat],
                   label=STRATEGY_LABELS[strat], zorder=3)
        if task in base.index:
            ax.axhline(float(base[task]), ls="--", lw=1.4, color=C_BASE, zorder=4,
                       label="regelbasiert")
        ax.set_xticks(x)
        ax.set_xticklabels([PROVIDER_LABEL[p] for p in MODELLE], fontsize=8.5)
        ax.set_ylim(0, 1.08)
        ax.set_title(TASK_LABEL[task], fontsize=9)
        ax.grid(axis="y", ls=":", alpha=0.5, zorder=0)
    for ax in axes.ravel()[len(aufgaben):]:
        ax.set_visible(False)
    for reihe in axes:
        reihe[0].set_ylabel("abgegl. Genauigkeit")
    handles, labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=9.5,
               frameon=False, bbox_to_anchor=(0.5, -0.015))
    fig.suptitle("Bestätigungslauf: Prompting-Strategien je Aufgabe und Modell "
                 "(Seed 2, Mittel über die Wiederholungen)", fontsize=12.5, y=1.0)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    save_fig(fig, "bestaetigung_strategien")
    plt.close(fig)


def kennzahlen_ausgeben() -> None:
    """Druckt die Zahlen, die im Text von Kapitel 8 zitiert werden."""
    for seed, iso, mode, titel in (
            (SEED_VOLL, False, "codegen", "Code-Gen. verkettet"),
            (SEED_VOLL, True, "codegen", "Code-Gen. isoliert"),
            (SEED_HALB, False, "direct", "Direkt verkettet"),
            (SEED_HALB, True, "direct", "Direkt isoliert")):
        L = lauf_kennzahlen(seed, iso, mode)
        if not len(L):
            print(f"\n{titel}: keine Daten")
            continue
        A = L.groupby("label").agg(
            n=("rep", "size"), mittel=("mittel", "mean"), best=("mittel", "max"),
            std=("mittel", "std"), end_m=("endschritt", "mean"),
            end_best=("endschritt", "max"), end_min=("endschritt", "min"),
            kosten=("kosten", "mean"), dauer=("dauer", "mean"),
            ein=("eingabe", "mean"), aus=("ausgabe", "mean"))
        print(f"\n{titel} (Seed {seed})")
        print(A.round(4).to_string())


def abb_gruppen():
    """Gedrittelte Strecke: Strategien ohne Fehlerfortpflanzung.

    Links die drei Gruppen je Strategie, rechts dieselben Aufgaben als
    Einzelaufgaben der Faktormatrix. Die Gegenueberstellung zeigt, wieviel des
    scheinbaren Strategieunterschieds in Wahrheit vom Aufgabenzuschnitt kommt."""
    from experiments.group_runner import GROUPS, load_groups
    from reporting.analysis import load_runs

    g = load_groups(SEED_VOLL)
    if not len(g):
        print(f"  bestaetigung_gruppen: keine Gruppenlaeufe fuer Seed {SEED_VOLL}"
              f" -- zuerst scripts/run_groups.py --seed {SEED_VOLL} ausfuehren")
        return

    # Die Gruppen fassen je drei Pipeline-Schritte zusammen; ihnen entsprechen
    # in der Matrix die drei Aufgaben derselben Kategorie.
    KAT = {"cleaning": "cleaning", "dedup": "deduplication",
           "transform": "transformation"}
    runs = load_runs(SEED_VOLL, include_baseline=False)
    runs = runs[runs.provider.isin(MODELLE) & runs.prompt_id.isin(CLASSIC_STRATEGIES)]

    gruppen = [gr.name for gr in GROUPS]
    x = np.arange(len(gruppen))
    w = 0.8 / len(CLASSIC_STRATEGIES)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.0), sharey=True)
    for ax, quelle in zip(axes, ("gruppe", "matrix")):
        for j, strat in enumerate(CLASSIC_STRATEGIES):
            werte = []
            for gr in gruppen:
                if quelle == "gruppe":
                    s = g[(g.group == gr) & (g.prompt_id == strat)]
                    werte.append(float(s.acc_eff.mean()) if len(s) else np.nan)
                else:
                    s = runs[(runs.category == KAT[gr]) & (runs.prompt_id == strat)]
                    werte.append(float(s.acc_aligned.mean()) if len(s) else np.nan)
            off = (j - (len(CLASSIC_STRATEGIES) - 1) / 2) * w
            b = ax.bar(x + off, werte, w * 0.9, color=STRATEGY_COLORS[strat],
                       label=STRATEGY_LABELS[strat], zorder=3)
            for r in b:
                h = r.get_height()
                if not np.isnan(h):
                    ax.text(r.get_x() + r.get_width() / 2, h + 0.015,
                            f"{h * 100:.0f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(["Bereinigung\n(Schritte 1-3)", "Deduplizierung\n(4-6)",
                            "Transformation\n(7-9)"], fontsize=9)
        ax.set_ylim(0, 1.12)
        ax.grid(axis="y", ls=":", alpha=0.5, zorder=0)
        ax.set_title("gedrittelte Strecke – Soll-Eingabe je Gruppe"
                     if quelle == "gruppe"
                     else "Einzelaufgaben der Matrix – Rohdaten je Aufgabe",
                     fontsize=10.5)
    axes[0].set_ylabel("abgeglichene Genauigkeit")
    axes[0].legend(fontsize=9, loc="lower left")
    fig.suptitle("Prompting-Strategien mit und ohne Fehlerfortpflanzung "
                 "(Seed 2, Mittel über die drei Modelle)", fontsize=12.5, y=1.0)
    fig.tight_layout()
    save_fig(fig, "bestaetigung_gruppen")
    plt.close(fig)


def in_arbeit_kopieren() -> None:
    """Legt die erzeugten Abbildungen dort ab, wo LaTeX sie sucht.

    Ohne diesen Schritt muesste nach jedem Lauf von Hand kopiert werden, was
    erfahrungsgemaess irgendwann vergessen wird und dann eine veraltete
    Abbildung in der Arbeit stehen laesst."""
    import shutil
    ziel = repo_root.parent / "documentation" / "resources" / "images"
    if not ziel.is_dir():
        print(f"  Zielverzeichnis {ziel} nicht gefunden -- nicht kopiert.")
        return
    quelle = repo_root / "figures"
    for p in sorted(quelle.glob("bestaetigung_*.png")):
        shutil.copy2(p, ziel / p.name)
        print(f"  kopiert: {p.name}")


def main() -> None:
    abb_pipeline()
    abb_streuung()
    abb_aufwand()
    abb_strategien()
    abb_gruppen()
    in_arbeit_kopieren()
    kennzahlen_ausgeben()
    print("\nFertig.")


if __name__ == "__main__":
    main()
