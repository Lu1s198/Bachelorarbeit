"""Übersicht aller Läufe des ausgewerteten Datensatzes (Startwert 2).

Stellt die sechs Untersuchungsebenen mit ihren Laufzahlen dar, aufgeschlüsselt
nach Modell. Sichtbar wird dabei zweierlei: wie sich die 711 Modellaufrufe auf
die Ebenen verteilen und dass das lokal betriebene Modell ausschließlich in der
Faktormatrix geführt wird.

Die Laufzahl je Ebene ist das Produkt ihrer Faktoren; die Formel steht an jedem
Balken. Ablage als PNG unter ``project/figures/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

FIG_DIR = Path(__file__).resolve().parents[1] / "figures"

# Farben wie in reporting/compare.py
C_ANTHROPIC = "#4e79a7"
C_OPENAI = "#f28e2b"
C_GOOGLE = "#59a14f"
C_OLLAMA = "#b07aa1"
MODEL_COLORS = [C_ANTHROPIC, C_OPENAI, C_GOOGLE, C_OLLAMA]
MODEL_LABELS = ["Anthropic", "OpenAI", "Google", "Meta (lokal)"]

# (Ebene, Läufe je Modell, Anzahl Modelle, Formel)
# Reihenfolge wie in Tabelle 7.1 der Ausarbeitung.
EBENEN = [
    ("Faktormatrix,\nCode-Generierung", 54, 4, "4 Modelle x 3 Strategien x 9 Aufgaben x 2 Wdh."),
    ("Faktormatrix,\nDirekt-Modus", 9, 3, "3 Modelle x 9 Aufgaben"),
    ("Verkettete Pipeline\nund isolierter Durchlauf", 90, 3, "3 x 9 Schritte x 5 Wdh. x 2 Formen"),
    ("Verkettet und isoliert,\nDirekt-Modus (Startwert 102)", 36, 3, "3 x 9 Schritte x 2 Formen x 2 Wdh."),
    ("Gruppierte Strecke", 18, 3, "3 x 3 Strategien x 3 Gruppen x 2 Wdh."),
    ("Explizit gegliederte\nAufgabe", 12, 3, "3 x 3 Strategien x 2 Modi x 2 Wdh."),
]


def build() -> Path:
    labels = [e[0] for e in EBENEN]
    y = range(len(EBENEN))

    fig, ax = plt.subplots(figsize=(10.5, 5.4))

    for row, (_, per_model, n_models, _) in enumerate(EBENEN):
        left = 0
        for m in range(n_models):
            ax.barh(row, per_model, left=left, height=0.62,
                    color=MODEL_COLORS[m], edgecolor="white", linewidth=1.1)
            if per_model >= 16:
                ax.text(left + per_model / 2, row, str(per_model),
                        ha="center", va="center", color="white",
                        fontsize=9, fontweight="bold")
            left += per_model

        total = per_model * n_models
        ax.text(left + 5, row, f"{total} Laeufe".replace("Laeufe", "Läufe"),
                ha="left", va="center", fontsize=10, fontweight="bold")
        ax.text(left + 5, row - 0.30, EBENEN[row][3],
                ha="left", va="center", fontsize=8, color="#555555")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Anzahl Modellaufrufe", fontsize=10)
    ax.set_xlim(0, 430)
    ax.set_title("Alle Läufe des ausgewerteten Datensatzes (Startwert 2): 711 Modellaufrufe",
                 fontsize=12, fontweight="bold", pad=14)

    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)

    handles = [Patch(facecolor=c, label=l) for c, l in zip(MODEL_COLORS, MODEL_LABELS)]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=9,
              title="Segment je Modell", title_fontsize=9)

    fig.text(0.01, -0.02,
             "Das lokal betriebene Modell wird ausschließlich in der Faktormatrix geführt. "
             "Hinzu kommen 27 deterministische Durchläufe der regelbasierten Vergleichspipeline.",
             fontsize=8, color="#555555")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "s2_laufzahlen.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    gesamt = sum(p * n for _, p, n, _ in EBENEN)
    if gesamt != 711:
        print(f"FEHLER: Summe {gesamt}, erwartet 711")
        return 1
    out = build()
    print(f"Summe geprueft: {gesamt} Modellaufrufe")
    print(f"geschrieben: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
