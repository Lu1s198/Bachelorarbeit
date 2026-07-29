"""Vergleichsgrafiken für die Auswertung (Kapitel 8).

Stellt je \ac{ETL}-Aufgabe die *abgeglichene* Genauigkeit (siehe
``analysis.aligned_accuracy``) der drei Ansätze nebeneinander:

- **Code-Generierung** -- beste der vier Prompt-Strategien (Mittel über Wdh.),
- **Direkt-Verarbeitung** -- der einzelne Direkt-Lauf,
- **regelbasierte Baseline** -- als Referenzlinie.

Die Baseline-Linie macht sichtbar, dass etwa bei der semantischen
Länder-Vereinheitlichung auch das regelbasierte Verfahren nur ~95 % erreicht,
eine Genauigkeit von 100 % also kein sinnvoller Maßstab ist.

Alle Grafiken werden zusätzlich als PNG unter ``project/figures/`` abgelegt,
sodass sie unmittelbar in die Projektarbeit übernommen werden können.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import settings
from reporting.analysis import PROVIDER_LABEL, load_runs
from reporting.direct_analysis import load_direct

FIG_DIR = settings.data_dir.parent / "figures"

MODEL_ORDER = ["anthropic", "openai", "google", "ollama"]
MODEL_LABELS = [PROVIDER_LABEL[p] for p in MODEL_ORDER]

CAT_LABEL = {
    "cleaning": "Datenbereinigung",
    "deduplication": "Duplikaterkennung",
    "transformation": "Datentransformation",
}

TASK_LABEL = {
    "cleaning_easy_missing_and_whitespace": "Einfach – Leerzeichen & fehlende Werte",
    "cleaning_medium_date_formats": "Mittel – Datumsformate vereinheitlichen",
    "cleaning_hard_semantic_unification": "Schwer – ISO-Ländercodes (semantisch)",
    "dedup_easy_exact_duplicates": "Einfach – exakte Duplikate",
    "dedup_medium_key_duplicates": "Mittel – Schlüssel-Duplikate (E-Mail)",
    "dedup_hard_fuzzy_duplicates": "Schwer – unscharfe Duplikate (Fuzzy)",
    "transform_easy_type_conversion": "Einfach – Typkonvertierung",
    "transform_medium_derived_columns": "Mittel – abgeleitete Spalten",
    "transform_hard_join_and_aggregate": "Schwer – Join & Aggregation",
}

C_CODE = "#4e79a7"      # Code-Generierung
C_DIRECT = "#f28e2b"    # Direkt-Verarbeitung
C_BASE = "#59a14f"      # Baseline-Referenz

# Prompt-Strategien: die drei klassischen (Zero-/Few-Shot, Chain-of-Thought) plus
# die schema-angereicherte Variante, die separat betrachtet wird.
STRATEGY_LABELS = {
    "v1_zero_shot": "Zero-Shot",
    "v2_few_shot": "Few-Shot",
    "v3_chain_of_thought": "Chain-of-Thought",
    "v4_schema": "Schema",
}
CLASSIC_STRATEGIES = ["v1_zero_shot", "v2_few_shot", "v3_chain_of_thought"]
STRATEGY_COLORS = {
    "v1_zero_shot": "#4e79a7",
    "v2_few_shot": "#76b7b2",
    "v3_chain_of_thought": "#b07aa1",
    "v4_schema": "#9c755f",
}


# ---------------------------------------------------------------- Laden / Aggregation

def load_all(seed: int = 1):
    """Lädt Code-Gen-Läufe (inkl. Baseline) und Direkt-Läufe eines Seeds."""
    runs = load_runs(seed=seed, include_baseline=True)
    direct = load_direct(seed)
    return runs, direct


def task_order(runs: pd.DataFrame) -> list[str]:
    llm = runs[runs.provider != "baseline"]
    return list(llm.sort_values(["_cat", "_diff"]).drop_duplicates("task_id").task_id)


def codegen_matrix(runs: pd.DataFrame) -> pd.DataFrame:
    """Aufgabe x Modell: abgeglichene Genauigkeit der BESTEN klassischen Strategie.

    Berücksichtigt nur die drei klassischen Strategien (Zero-/Few-Shot,
    Chain-of-Thought); zuerst wird je (Aufgabe, Modell, Strategie) über die
    Wiederholungen gemittelt, dann über die Strategien das Maximum gebildet. So
    spiegelt die Zahl wider, was ein Modell mit gut gewähltem Prompt erreicht. Die
    schema-angereicherte Variante wird als separater Robustheits-Befund behandelt
    (sie verleitet zu abstürzenden Typkonvertierungen) und geht hier nicht ein."""
    llm = runs[(runs.provider != "baseline") & runs.prompt_id.isin(CLASSIC_STRATEGIES)]
    per_strat = llm.pivot_table(index=["task_id", "provider"], columns="prompt_id",
                                values="acc_aligned", aggfunc="mean")
    return per_strat.max(axis=1).unstack("provider")


def direct_matrix(direct: pd.DataFrame) -> pd.DataFrame:
    return direct.pivot_table(index="task_id", columns="provider",
                              values="acc_effektiv", aggfunc="mean")


def baseline_series(runs: pd.DataFrame) -> pd.Series:
    return runs[runs.provider == "baseline"].set_index("task_id")["acc_aligned"]


def tasks_in(runs: pd.DataFrame, category: str) -> list[str]:
    llm = runs[(runs.provider != "baseline") & (runs.category == category)]
    return list(llm.sort_values("_diff").drop_duplicates("task_id").task_id)


# ---------------------------------------------------------------- Speichern

def save_fig(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.png", dpi=150, bbox_inches="tight")


# ---------------------------------------------------------------- Balken je Aufgabe

def _vals(mat: pd.DataFrame, task_id: str) -> list[float]:
    return [mat.loc[task_id, m] if (task_id in mat.index and m in mat.columns)
            else np.nan for m in MODEL_ORDER]


def compare_task(task_id, cg, dm, bl, ax=None, save=True):
    """Gruppierte Balken (Modell x {Code-Gen, Direkt}) plus Baseline-Referenzlinie."""
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
    cg_v, dm_v = _vals(cg, task_id), _vals(dm, task_id)
    base = float(bl.get(task_id, np.nan))
    x = np.arange(len(MODEL_ORDER))
    w = 0.38
    b1 = ax.bar(x - w / 2, cg_v, w, label="Code-Gen. (beste Strategie)", color=C_CODE)
    b2 = ax.bar(x + w / 2, dm_v, w, label="Direkt-Verarbeitung", color=C_DIRECT)
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            if not np.isnan(h):
                ax.text(rect.get_x() + rect.get_width() / 2, h + 0.02,
                        f"{h * 100:.0f}", ha="center", va="bottom", fontsize=8)
    if not np.isnan(base):
        ax.axhline(base, ls="--", lw=2, color=C_BASE,
                   label=f"Baseline ({base * 100:.0f} %)")
    ax.set_xticks(x)
    ax.set_xticklabels(MODEL_LABELS)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("abgeglichene Genauigkeit")
    ax.set_title(TASK_LABEL.get(task_id, task_id))
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.grid(axis="y", ls=":", alpha=0.5)
    if own:
        fig.tight_layout()
        if save:
            save_fig(fig, f"task_{task_id}")
    return ax


def codegen_by_strategy(runs: pd.DataFrame) -> pd.Series:
    """Abgeglichene Genauigkeit je (Aufgabe, Modell, Strategie), Mittel über Wdh."""
    llm = runs[runs.provider != "baseline"]
    return llm.groupby(["task_id", "provider", "prompt_id"])["acc_aligned"].mean()


def _strat_val(g: pd.Series, task_id: str, provider: str, strat: str) -> float:
    try:
        return float(g.loc[(task_id, provider, strat)])
    except KeyError:
        return np.nan


def compare_task_strategies(task_id, g, dm, bl, strategies=None, ax=None, save=True):
    """Je Modell ein kleiner Balken pro Prompt-Strategie plus ein Direkt-Balken;
    Baseline als Referenzlinie. So werden Strategie-Unterschiede und der Vergleich
    der Ausführungsmodi in einer Grafik sichtbar."""
    strategies = strategies or CLASSIC_STRATEGIES
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(1.9 * len(MODEL_ORDER) + 1.5, 4.4))
    n_bars = len(strategies) + 1                 # Strategien + Direkt
    group_w = 0.82
    w = group_w / n_bars
    x = np.arange(len(MODEL_ORDER))
    base = float(bl.get(task_id, np.nan))

    def _lab(rect, ax):
        h = rect.get_height()
        if not np.isnan(h):
            ax.text(rect.get_x() + rect.get_width() / 2, h + 0.015,
                    f"{h * 100:.0f}", ha="center", va="bottom", fontsize=6.5)

    for j, strat in enumerate(strategies):
        vals = [_strat_val(g, task_id, m, strat) for m in MODEL_ORDER]
        off = (j - (n_bars - 1) / 2) * w
        bars = ax.bar(x + off, vals, w, color=STRATEGY_COLORS.get(strat, "#888"),
                      label=STRATEGY_LABELS.get(strat, strat))
        for r in bars:
            _lab(r, ax)
    # Direkt-Balken als letzter im Cluster
    dvals = _vals(dm, task_id)
    off = ((n_bars - 1) - (n_bars - 1) / 2) * w
    bars = ax.bar(x + off, dvals, w, color=C_DIRECT, label="Direkt-Verarbeitung")
    for r in bars:
        _lab(r, ax)

    if not np.isnan(base):
        ax.axhline(base, ls="--", lw=2, color=C_BASE,
                   label=f"Baseline ({base * 100:.0f} %)")
    ax.set_xticks(x)
    ax.set_xticklabels(MODEL_LABELS)
    ax.set_ylim(0, 1.14)
    ax.set_ylabel("abgeglichene Genauigkeit")
    ax.set_title(TASK_LABEL.get(task_id, task_id))
    ax.legend(loc="lower right", fontsize=7, ncol=2, framealpha=0.9)
    ax.grid(axis="y", ls=":", alpha=0.5)
    if own:
        fig.tight_layout()
        if save:
            save_fig(fig, f"strat_{task_id}")
    return ax


def compare_category_strategies(category, runs, direct, strategies=None, save=True):
    """Eine Zeile mit den drei Schwierigkeitsgraden, je Strategie ein Balken."""
    g, dm, bl = codegen_by_strategy(runs), direct_matrix(direct), baseline_series(runs)
    tasks = tasks_in(runs, category)
    fig, axes = plt.subplots(1, len(tasks),
                             figsize=(6.8 * len(tasks), 4.6), sharey=True)
    if len(tasks) == 1:
        axes = [axes]
    for ax, t in zip(axes, tasks):
        compare_task_strategies(t, g, dm, bl, strategies=strategies, ax=ax, save=False)
        ax.legend(loc="lower right", fontsize=6.5, ncol=2)
    fig.suptitle(f"{CAT_LABEL.get(category, category)} – Genauigkeit je "
                 f"Prompt-Strategie, Direkt-Verarbeitung und Baseline",
                 fontsize=13, y=1.02)
    fig.tight_layout()
    if save:
        save_fig(fig, f"kategorie_{category}_strategien")
    return fig


def task_table(task_id, cg, dm, bl) -> pd.DataFrame:
    """Werte-Tabelle (in %) je Modell für eine Aufgabe, plus Baseline-Zeile."""
    df = pd.DataFrame({
        "Code-Gen (beste Strat.)": _vals(cg, task_id),
        "Direkt-Verarbeitung": _vals(dm, task_id),
    }, index=MODEL_LABELS)
    df.loc["Baseline (Referenz)"] = [float(bl.get(task_id, np.nan)), np.nan]
    return (df * 100).round(1)


def strategy_table(task_id, g, dm, bl, strategies=None) -> pd.DataFrame:
    """Werte-Tabelle (in %) je Modell und Prompt-Strategie plus Direkt-Spalte;
    die Baseline steht als Referenzzeile (konstant über die Spalten)."""
    strategies = strategies or CLASSIC_STRATEGIES
    data = {STRATEGY_LABELS[s]: [_strat_val(g, task_id, m, s) for m in MODEL_ORDER]
            for s in strategies}
    df = pd.DataFrame(data, index=MODEL_LABELS)
    df["Direkt"] = _vals(dm, task_id)
    base = float(bl.get(task_id, np.nan))
    df.loc["Baseline (Referenz)"] = [base] * len(strategies) + [np.nan]
    return (df * 100).round(1)


def compare_category(category, runs, direct, save=True):
    """Eine Zeile mit den drei Schwierigkeitsgraden einer Kategorie."""
    cg, dm, bl = codegen_matrix(runs), direct_matrix(direct), baseline_series(runs)
    tasks = tasks_in(runs, category)
    fig, axes = plt.subplots(1, len(tasks), figsize=(6.2 * len(tasks), 4.4),
                             sharey=True)
    if len(tasks) == 1:
        axes = [axes]
    for ax, t in zip(axes, tasks):
        compare_task(t, cg, dm, bl, ax=ax, save=False)
        ax.legend(loc="lower right", fontsize=7)
    fig.suptitle(f"{CAT_LABEL.get(category, category)} – abgeglichene Genauigkeit "
                 f"nach Modell und Ansatz", fontsize=13, y=1.02)
    fig.tight_layout()
    if save:
        save_fig(fig, f"kategorie_{category}")
    return fig


# ---------------------------------------------------------------- Gesamtübersicht

def full_matrix(runs, direct) -> pd.DataFrame:
    """Aufgabe x (jedes Modell in beiden Modi + Baseline), abgeglichene Genauigkeit."""
    cg, dm, bl = codegen_matrix(runs), direct_matrix(direct), baseline_series(runs)
    order = task_order(runs)
    cols: dict[str, pd.Series] = {}
    for m, lbl in zip(MODEL_ORDER, MODEL_LABELS):
        cols[f"{lbl}\nCode"] = cg[m] if m in cg.columns else pd.Series(dtype=float)
    for m, lbl in zip(MODEL_ORDER, MODEL_LABELS):
        cols[f"{lbl}\nDirekt"] = dm[m] if m in dm.columns else pd.Series(dtype=float)
    cols["Baseline"] = bl
    M = pd.DataFrame(cols).reindex(order)
    M.index = [TASK_LABEL.get(t, t) for t in order]
    return M


def overview_heatmap(runs, direct, save=True):
    """Große Heatmap: alle neun Aufgaben x alle Modelle/Ansätze + Baseline."""
    M = full_matrix(runs, direct)
    fig, ax = plt.subplots(figsize=(1.05 * M.shape[1] + 3, 0.62 * M.shape[0] + 2))
    vals = M.values.astype(float)
    im = ax.imshow(vals, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(M.shape[1]))
    ax.set_xticklabels(M.columns, fontsize=9)
    ax.set_yticks(range(M.shape[0]))
    ax.set_yticklabels(M.index, fontsize=9)
    for r in range(vals.shape[0]):
        for c in range(vals.shape[1]):
            v = vals[r, c]
            if not np.isnan(v):
                ax.text(c, r, f"{v * 100:.0f}", ha="center", va="center", fontsize=8)
    # Trennlinien zwischen Code-Gen | Direkt | Baseline
    ax.axvline(len(MODEL_ORDER) - 0.5, color="white", lw=3)
    ax.axvline(2 * len(MODEL_ORDER) - 0.5, color="white", lw=3)
    ax.set_title("Abgeglichene Genauigkeit in % – alle Aufgaben, Modelle und Ansätze",
                 fontsize=12)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="Genauigkeit")
    fig.tight_layout()
    if save:
        save_fig(fig, "uebersicht_heatmap")
    return fig, M


def mode_summary(runs, direct, save=True):
    """Mittlere abgeglichene Genauigkeit je Kategorie und Ansatz (Balken)."""
    cg, dm, bl = codegen_matrix(runs), direct_matrix(direct), baseline_series(runs)
    cats = ["cleaning", "deduplication", "transformation"]
    rows = []
    for cat in cats:
        tasks = tasks_in(runs, cat)
        rows.append({
            "Kategorie": CAT_LABEL[cat],
            "Code-Gen. (beste Strategie)": np.nanmean([cg.loc[t].mean() for t in tasks]),
            "Direkt-Verarbeitung": np.nanmean([dm.loc[t].mean() for t in tasks]),
            "Baseline": np.nanmean([bl.get(t, np.nan) for t in tasks]),
        })
    S = pd.DataFrame(rows).set_index("Kategorie")
    x = np.arange(len(S))
    w = 0.26
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for i, (col, color) in enumerate(zip(
            ["Code-Gen. (beste Strategie)", "Direkt-Verarbeitung", "Baseline"],
            [C_CODE, C_DIRECT, C_BASE])):
        bars = ax.bar(x + (i - 1) * w, S[col], w, label=col, color=color)
        for rect in bars:
            h = rect.get_height()
            if not np.isnan(h):
                ax.text(rect.get_x() + rect.get_width() / 2, h + 0.01,
                        f"{h * 100:.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(S.index)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("mittlere abgeglichene Genauigkeit")
    ax.set_title("Ansätze im Vergleich – Mittel je Kategorie")
    ax.legend(fontsize=9)
    ax.grid(axis="y", ls=":", alpha=0.5)
    fig.tight_layout()
    if save:
        save_fig(fig, "uebersicht_modi")
    return fig, S
