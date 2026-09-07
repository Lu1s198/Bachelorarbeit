"""Systemarchitektur und Datenfluss eines Laufs.

Stellt die sechs Module des Versuchsaufbaus in der Reihenfolge dar, in der ein
einzelner Lauf sie durchläuft, und benennt an jedem Übergang das übergebene
Artefakt. Sichtbar wird dabei zweierlei: dass das Modell nicht das Ergebnis,
sondern ein Verarbeitungsskript liefert, und dass die regelbasierte
Vergleichspipeline auf derselben Datengrundlage in dieselbe Bewertung mündet.

Ablage als PNG unter ``project/figures/``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FIG_DIR = Path(__file__).resolve().parents[1] / "figures"

# Farben wie in reporting/compare.py
C_LLM = "#4e79a7"
C_KLASSISCH = "#f28e2b"
C_BEWERTUNG = "#59a14f"
C_KONFIG = "#7f7f7f"

# (Titel, Beschreibung, Farbe)
MODULE = [
    ("Datenmodul", "Datensatz,\nSoll-Lösungen,\nneun Aufgaben", C_KONFIG),
    ("Modellmodul", "Prompt-Erzeugung,\neinheitliche\nLLM-Schnittstelle", C_LLM),
    ("Experimentmodul", "deterministische\nAusführung des\nerzeugten Skripts", C_LLM),
    ("Evaluationsmodul", "Abgleich mit der\nSoll-Lösung", C_BEWERTUNG),
    ("Auswertungsmodul", "Aggregation\nüber alle\nLäufe", C_BEWERTUNG),
]

# Artefakt an jedem Übergang, unter dem zugehörigen Pfeil
ARTEFAKTE = ["Aufgabe\nund Daten", "Verarbeitungs-\nskript", "Ergebnis-\ntabelle", "Kennzahlen\nje Lauf"]

BREITE = 1.60
ABSTAND = 0.20
SCHRITT = BREITE + ABSTAND
BOX_UNTEN = 1.46
BOX_HOEHE = 0.96
BOX_OBEN = BOX_UNTEN + BOX_HOEHE
MITTE_Y = BOX_UNTEN + BOX_HOEHE / 2


def _mitte(i: int) -> float:
    return i * SCHRITT + BREITE / 2


def _kasten(ax, x, y, breite, hoehe, farbe, *, gestrichelt=False):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            breite,
            hoehe,
            boxstyle="round,pad=0,rounding_size=0.06",
            linewidth=1.1,
            edgecolor=farbe,
            facecolor=farbe,
            alpha=0.10,
            zorder=1,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            breite,
            hoehe,
            boxstyle="round,pad=0,rounding_size=0.06",
            linewidth=1.1,
            edgecolor=farbe,
            facecolor="none",
            linestyle="--" if gestrichelt else "-",
            zorder=2,
        )
    )


def _pfeil(ax, start, ziel, farbe, *, stil="arc3,rad=0", gestrichelt=False):
    ax.add_patch(
        FancyArrowPatch(
            start,
            ziel,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.1,
            color=farbe,
            linestyle="--" if gestrichelt else "-",
            connectionstyle=stil,
            shrinkA=0,
            shrinkB=0,
            zorder=3,
        )
    )


def main() -> None:
    gesamtbreite = len(MODULE) * SCHRITT - ABSTAND

    fig, ax = plt.subplots(figsize=(gesamtbreite, 3.10))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(-0.05, gesamtbreite + 0.05)
    ax.set_ylim(0.05, 3.15)
    ax.axis("off")

    # Zentrale Konfiguration als Band über allen Modulen
    _kasten(ax, 0, 2.60, gesamtbreite, 0.42, C_KONFIG, gestrichelt=True)
    ax.text(
        gesamtbreite / 2,
        2.81,
        "Zentrale Konfiguration:  Zufallskern  ·  Temperatur  ·  Ausgabe-Token  ·  Wiederholungen",
        ha="center",
        va="center",
        fontsize=10.0,
        color="#333333",
    )

    for i, (titel, beschreibung, farbe) in enumerate(MODULE):
        x = i * SCHRITT
        _kasten(ax, x, BOX_UNTEN, BREITE, BOX_HOEHE, farbe)
        ax.text(_mitte(i), BOX_OBEN - 0.21, titel, ha="center", va="center",
                fontsize=10.2, fontweight="bold", color="#222222")
        ax.text(_mitte(i), BOX_OBEN - 0.60, beschreibung, ha="center", va="center",
                fontsize=8.8, color="#444444", linespacing=1.35)

        # Gestrichelte Wirkung der Konfiguration auf jedes Modul
        _pfeil(ax, (_mitte(i), 2.60), (_mitte(i), BOX_OBEN + 0.02), C_KONFIG, gestrichelt=True)

        if i < len(MODULE) - 1:
            _pfeil(ax, (x + BREITE, MITTE_Y), (x + SCHRITT - 0.02, MITTE_Y), "#555555")
            ax.text(x + BREITE + ABSTAND / 2, BOX_UNTEN - 0.25, ARTEFAKTE[i],
                    ha="center", va="center", fontsize=8.6, style="italic",
                    color="#555555", linespacing=1.3)

    # Regelbasierte Vergleichspipeline auf derselben Datengrundlage
    pipe_links, pipe_rechts, pipe_unten, pipe_hoehe = _mitte(0) + 0.20, _mitte(3) - 0.40, 0.24, 0.52
    _kasten(ax, pipe_links, pipe_unten, pipe_rechts - pipe_links, pipe_hoehe, C_KLASSISCH)
    ax.text((pipe_links + pipe_rechts) / 2, pipe_unten + pipe_hoehe / 2,
            "Pipeline-Modul:  regelbasierte Vergleichslösung",
            ha="center", va="center", fontsize=10.0, color="#222222")

    y_pipe = pipe_unten + pipe_hoehe / 2
    _pfeil(ax, (_mitte(0), BOX_UNTEN - 0.02), (pipe_links - 0.02, y_pipe), C_KLASSISCH,
           stil="angle,angleA=-90,angleB=180,rad=8")
    _pfeil(ax, (pipe_rechts + 0.02, y_pipe), (_mitte(3), BOX_UNTEN - 0.02), C_KLASSISCH,
           stil="angle,angleA=0,angleB=-90,rad=8")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ziel = FIG_DIR / "s2_architektur.png"
    fig.savefig(ziel, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"geschrieben: {ziel}")


if __name__ == "__main__":
    main()
