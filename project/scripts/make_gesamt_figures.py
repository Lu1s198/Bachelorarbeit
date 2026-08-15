"""Erzeugt die beiden aggregierten Übersichtsgrafiken für Kapitel 8.

    python scripts/make_gesamt_figures.py [--seed 1]

Ergebnis (in project/figures/):
    gesamt_modelle.png            Modellvergleich: Genauigkeit, Erfolgsquote,
                                  Statusverteilung und Kosten je Modell
    gesamt_strategien.png         Prompting-Strategien gesamt, je Kategorie
                                  und ihr Token-Aufwand
    gesamt_reproduzierbarkeit.png Streuung ueber die drei Wiederholungen,
                                  je Aufgabe und je Modell

Die Grafiken beziehen sich ausschliesslich auf den Modus der Code-Generierung
(432 Laeufe) und nutzen dieselbe abgeglichene Genauigkeit wie die Notebooks.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

import matplotlib.pyplot as plt  # noqa: E402

from reporting.analysis import PROVIDER_LABEL, load_runs  # noqa: E402
from reporting.compare import (  # noqa: E402
    CAT_LABEL, MODEL_ORDER, STRATEGY_COLORS, STRATEGY_LABELS, TASK_LABEL, save_fig,
)

STATUS_LABEL = {"ok": "verwertbar", "code_error": "Code-Absturz",
                "wrong_output": "Schema-/Zeilenbruch", "api_error": "API-Fehler"}
STATUS_COLOR = {"ok": "#59a14f", "code_error": "#e15759",
                "wrong_output": "#f28e2b", "api_error": "#bab0ac"}


def modelle(runs, save=True):
    llm = runs[runs.provider != "baseline"]
    labels = [PROVIDER_LABEL[p] for p in MODEL_ORDER]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

    acc = [llm[llm.provider == p].acc_aligned.mean() for p in MODEL_ORDER]
    ok = [llm[llm.provider == p].produced.mean() for p in MODEL_ORDER]
    x = range(len(MODEL_ORDER))
    axes[0].bar([i - 0.2 for i in x], acc, 0.4, label="Genauigkeit", color="#4e79a7")
    axes[0].bar([i + 0.2 for i in x], ok, 0.4, label="Erfolgsquote", color="#76b7b2")
    for i, (a, o) in enumerate(zip(acc, ok)):
        axes[0].text(i - 0.2, a + 0.02, f"{a:.2f}", ha="center", fontsize=9)
        axes[0].text(i + 0.2, o + 0.02, f"{o:.2f}", ha="center", fontsize=9)
    axes[0].set_title("Genauigkeit und Erfolgsquote")
    axes[0].set_ylim(0, 1.12)
    axes[0].legend(fontsize=9)

    counts = llm.pivot_table(index="provider", columns="status", values="task_id",
                             aggfunc="count").reindex(MODEL_ORDER).fillna(0)
    unten = [0] * len(MODEL_ORDER)
    for s in ["ok", "code_error", "wrong_output", "api_error"]:
        if s not in counts.columns:
            continue
        axes[1].bar(labels, counts[s], bottom=unten, label=STATUS_LABEL[s],
                    color=STATUS_COLOR[s])
        unten = [u + v for u, v in zip(unten, counts[s])]
    axes[1].set_title("Ausgang der 108 Läufe je Modell")
    axes[1].set_ylabel("Anzahl Läufe")
    axes[1].legend(fontsize=8)

    kosten = [llm[llm.provider == p].cost_usd.sum() for p in MODEL_ORDER]
    lat = [llm[llm.provider == p].latency_s.mean() for p in MODEL_ORDER]
    axes[2].bar(labels, kosten, color="#b07aa1")
    for i, k in enumerate(kosten):
        axes[2].text(i, k + 0.03, f"{k:.2f} $", ha="center", fontsize=9)
    ax2 = axes[2].twinx()
    ax2.plot(labels, lat, "o--", color="#333333", label="Latenz")
    ax2.set_ylabel("mittlere Latenz je Aufruf (s)")
    ax2.set_ylim(0, max(lat) * 1.4)
    axes[2].set_title("Kosten (Balken) und Latenz (Linie)")
    axes[2].set_ylabel("Kosten gesamt (USD)")
    axes[2].set_ylim(0, max(kosten) * 1.25)

    for ax in axes[:1]:
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
    for ax in axes:
        ax.grid(axis="y", ls=":", alpha=0.5)
    fig.suptitle("Modellvergleich über alle 432 Läufe der Code-Generierung")
    fig.tight_layout()
    if save:
        save_fig(fig, "gesamt_modelle")
    return fig


def strategien(runs, save=True):
    llm = runs[runs.provider != "baseline"]
    strats = [s for s in STRATEGY_LABELS if s in set(llm.prompt_id)]
    labels = [STRATEGY_LABELS[s] for s in strats]
    farben = [STRATEGY_COLORS[s] for s in strats]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))

    acc = [llm[llm.prompt_id == s].acc_aligned.mean() for s in strats]
    ok = [llm[llm.prompt_id == s].produced.mean() for s in strats]
    x = range(len(strats))
    axes[0].bar([i - 0.2 for i in x], acc, 0.4, label="Genauigkeit", color="#4e79a7")
    axes[0].bar([i + 0.2 for i in x], ok, 0.4, label="Erfolgsquote", color="#76b7b2")
    for i, (a, o) in enumerate(zip(acc, ok)):
        axes[0].text(i - 0.2, a + 0.02, f"{a:.2f}", ha="center", fontsize=9)
        axes[0].text(i + 0.2, o + 0.02, f"{o:.2f}", ha="center", fontsize=9)
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(labels, rotation=15, ha="right")
    axes[0].set_title("Über alle Modelle und Aufgaben")
    axes[0].set_ylim(0, 1.12)
    axes[0].legend(fontsize=9)

    cats = ["cleaning", "deduplication", "transformation"]
    breite = 0.8 / len(strats)
    for j, s in enumerate(strats):
        werte = [llm[(llm.prompt_id == s) & (llm.category == c)].acc_aligned.mean()
                 for c in cats]
        pos = [i + j * breite - 0.4 + breite / 2 for i in range(len(cats))]
        axes[1].bar(pos, werte, breite, label=STRATEGY_LABELS[s], color=farben[j])
        for p, w in zip(pos, werte):
            axes[1].text(p, w + 0.02, f"{w * 100:.0f}", ha="center", fontsize=8)
    axes[1].set_xticks(range(len(cats)))
    axes[1].set_xticklabels([CAT_LABEL[c] for c in cats])
    axes[1].set_title("Je Aufgabenkategorie")
    axes[1].set_ylim(0, 1.12)
    axes[1].legend(fontsize=8)

    tok = [llm[llm.prompt_id == s].prompt_tokens.mean() for s in strats]
    axes[2].bar(labels, tok, color=farben)
    for i, t in enumerate(tok):
        axes[2].text(i, t + 15, f"{t:.0f}", ha="center", fontsize=9)
    axes[2].set_xticklabels(labels, rotation=15, ha="right")
    axes[2].set_title("Mittlere Prompt-Länge (Eingabe-Token)")
    axes[2].set_ylabel("Token je Aufruf")
    axes[2].set_ylim(0, max(tok) * 1.2)

    for ax in axes:
        ax.grid(axis="y", ls=":", alpha=0.5)
    axes[0].set_ylabel("abgeglichene Genauigkeit / Anteil")
    fig.suptitle("Prompting-Strategien im Vergleich (Code-Generierung, 432 Läufe)")
    fig.tight_layout()
    if save:
        save_fig(fig, "gesamt_strategien")
    return fig


def reproduzierbarkeit(runs, save=True):
    llm = runs[runs.provider != "baseline"]
    std = llm.groupby(["task_id", "provider", "prompt_id"]).acc_aligned.std()
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.6))

    je_aufgabe = std.groupby("task_id").mean().sort_values()
    namen = [TASK_LABEL.get(t, t) for t in je_aufgabe.index]
    axes[0].barh(namen, je_aufgabe.values, color="#4e79a7")
    for i, v in enumerate(je_aufgabe.values):
        axes[0].text(v + 0.002, i, f"{v:.3f}", va="center", fontsize=9)
    axes[0].set_title("Mittlere Standardabweichung je Aufgabe")
    axes[0].set_xlabel("Standardabweichung der Genauigkeit über drei Wiederholungen")
    axes[0].set_xlim(0, je_aufgabe.max() * 1.25)

    je_modell = std.groupby("provider").mean().reindex(MODEL_ORDER)
    stabil = (std.fillna(0) < 0.001).groupby("provider").mean().reindex(MODEL_ORDER)
    labels = [PROVIDER_LABEL[p] for p in MODEL_ORDER]
    x = range(len(MODEL_ORDER))
    axes[1].bar([i - 0.2 for i in x], je_modell.values, 0.4,
                label="mittlere Streuung", color="#e15759")
    axes[1].bar([i + 0.2 for i in x], stabil.values, 0.4,
                label="Anteil völlig stabiler Konfigurationen", color="#59a14f")
    for i, (s, q) in enumerate(zip(je_modell.values, stabil.values)):
        axes[1].text(i - 0.2, s + 0.01, f"{s:.3f}", ha="center", fontsize=9)
        axes[1].text(i + 0.2, q + 0.01, f"{q:.2f}", ha="center", fontsize=9)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels)
    axes[1].set_title("Streuung und Stabilitätsanteil je Modell")
    axes[1].set_ylim(0, 1.1)
    axes[1].legend(fontsize=9)

    for ax in axes:
        ax.grid(axis="x" if ax is axes[0] else "y", ls=":", alpha=0.5)
    fig.suptitle("Reproduzierbarkeit: Abweichung identischer Konfigurationen "
                 "über drei Wiederholungen")
    fig.tight_layout()
    if save:
        save_fig(fig, "gesamt_reproduzierbarkeit")
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    runs = load_runs(seed=args.seed, include_baseline=True)
    modelle(runs)
    strategien(runs)
    reproduzierbarkeit(runs)
    print("geschrieben: gesamt_modelle.png, gesamt_strategien.png, "
          "gesamt_reproduzierbarkeit.png")


if __name__ == "__main__":
    main()
