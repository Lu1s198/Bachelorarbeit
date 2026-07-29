"""Auswertung der verketteten End-to-End-Pipeline (Kapitel 8).

Lädt die pipeline.json je Modell und stellt den Verlauf als Schritt-x-Modell-
Heatmap dar: pro Schritt Status (ok / Code-Crash / Schema-Bruch / blockiert) und,
wo auswertbar, die abgeglichene Genauigkeit gegen die verkettete Referenz. So wird
sichtbar, wie weit jedes Modell kommt und wo die Kaskade bricht.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from config import settings
from experiments.pipeline_runner import PIPELINE
from reporting.analysis import PROVIDER_LABEL
from reporting.compare import FIG_DIR, MODEL_LABELS, MODEL_ORDER, save_fig

PIPELINE_RESULTS = settings.data_dir / "results_pipeline"

STATUS_COLOR = {
    "code_error": "#b2182b",     # Crash
    "schema_break": "#d6604d",   # Schema unvollständig
    "blocked": "#cfcfcf",        # durch vorherigen Fehler blockiert
}
STATUS_TEXT = {
    "code_error": "Crash",
    "schema_break": "Schema",
    "blocked": "blockiert",
}


def load_pipeline(seed: int = 1) -> pd.DataFrame:
    rows = []
    order = {s.name: i for i, s in enumerate(PIPELINE)}
    labels = {s.name: s.label for s in PIPELINE}
    for prov in MODEL_ORDER:
        p = PIPELINE_RESULTS / str(seed) / prov / "pipeline.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for s in d["steps"]:
            rows.append(dict(
                provider=prov, label=PROVIDER_LABEL[prov],
                step=s["step"], step_label=labels.get(s["step"], s["step"]),
                order=order.get(s["step"], 99), status=s["status"],
                accuracy=s.get("accuracy"), attempts=s.get("attempts"),
                error=s.get("error"),
            ))
    return pd.DataFrame(rows)


def pipeline_heatmap(seed: int = 1, save: bool = True):
    """Schritt (Zeilen) x Modell (Spalten): Status/Genauigkeit der Pipeline."""
    df = load_pipeline(seed)
    steps = [s for s in PIPELINE]
    provs = [p for p in MODEL_ORDER if p in set(df.provider)]
    labels = [PROVIDER_LABEL[p] for p in provs]
    cmap = plt.cm.RdYlGn

    fig, ax = plt.subplots(figsize=(1.6 * len(provs) + 4, 0.66 * len(steps) + 2))
    for i, step in enumerate(steps):
        for j, prov in enumerate(provs):
            r = df[(df.provider == prov) & (df.step == step.name)]
            if r.empty:
                continue
            r = r.iloc[0]
            if r.status == "ok" and r.accuracy is not None:
                color = cmap(float(r.accuracy))
                txt = f"{r.accuracy * 100:.0f}"
                tcol = "black"
            else:
                color = STATUS_COLOR.get(r.status, "#999999")
                txt = STATUS_TEXT.get(r.status, r.status)
                tcol = "white"
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=color,
                                   edgecolor="white", linewidth=2))
            ax.text(j + 0.5, i + 0.5, txt, ha="center", va="center",
                    color=tcol, fontsize=9,
                    fontweight="bold" if r.status != "ok" else "normal")

    ax.set_xlim(0, len(provs))
    ax.set_ylim(0, len(steps))
    ax.invert_yaxis()  # Schritt 1 oben -> Fluss von oben nach unten
    ax.set_xticks(np.arange(len(provs)) + 0.5)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_yticks(np.arange(len(steps)) + 0.5)
    ax.set_yticklabels([s.label for s in steps], fontsize=9)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Verkettete Pipeline – abgeglichene Genauigkeit je Schritt (%)\n"
                 "und wo die Kaskade bricht", fontsize=12, pad=28)

    legend = [
        Patch(facecolor=cmap(0.95), label="ok (Farbe = Genauigkeit)"),
        Patch(facecolor=STATUS_COLOR["code_error"], label="Code-Crash"),
        Patch(facecolor=STATUS_COLOR["schema_break"], label="Schema-Bruch"),
        Patch(facecolor=STATUS_COLOR["blocked"], label="blockiert (Folgefehler)"),
    ]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              fontsize=9, frameon=False)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_verlauf")
    return fig, df


def pipeline_summary(seed: int = 1) -> pd.DataFrame:
    """Kompakte Übersicht je Modell: erreichte Schritte, Endergebnis, Abbruchstelle."""
    df = load_pipeline(seed)
    rows = []
    for prov in [p for p in MODEL_ORDER if p in set(df.provider)]:
        sub = df[df.provider == prov].sort_values("order")
        n_ok = int((sub.status == "ok").sum())
        fin = sub[sub.step == "final"]
        reached = not fin.empty and fin.iloc[0].status == "ok"
        broke = sub[sub.status.isin(["code_error", "schema_break"])]
        first_break = broke.iloc[0].step_label if not broke.empty else "—"
        final_acc = fin.iloc[0].accuracy if reached else None
        rows.append({
            "Modell": PROVIDER_LABEL[prov],
            "Schritte ok": f"{n_ok}/9",
            "Ende erreicht": "ja" if reached else "nein",
            "Endgenauigkeit": (f"{final_acc * 100:.1f}%" if final_acc is not None else "—"),
            "Erster Abbruch": first_break,
        })
    return pd.DataFrame(rows).set_index("Modell")
