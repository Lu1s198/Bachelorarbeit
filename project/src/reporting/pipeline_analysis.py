"""Auswertung der verketteten End-to-End-Pipeline (Kapitel 8).

Lädt die pipeline.json je Modell und stellt den Verlauf als Schritt-x-Modell-
Heatmap dar: pro Schritt Status (ok / Code-Crash / Schema-Bruch / blockiert) und,
wo auswertbar, die abgeglichene Genauigkeit gegen die verkettete Referenz. So wird
sichtbar, wie weit jedes Modell kommt und wo die Kaskade bricht.
"""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from config import settings
from experiments.pipeline_runner import PIPELINE
from reporting.analysis import PROVIDER_LABEL
from reporting.compare import FIG_DIR, MODEL_LABELS, MODEL_ORDER, save_fig

# Die regelbasierte Vergleichsbasis durchlaeuft dieselbe Kette (run_baseline_pipeline)
# und erscheint deshalb als zusaetzliche Spalte hinter den Modellen.
PIPE_ORDER = [*MODEL_ORDER, "baseline"]

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


def load_pipeline(seed: int = 1, isolated: bool = False,
                  mode: str = "codegen") -> pd.DataFrame:
    """Lädt die Schritt-Datensätze eines Seeds.

    ``isolated=True`` liest die entkoppelten Läufe (``<provider>_isolated``), in
    denen jeder Schritt die Soll-Ausgabe seines Vorgängers als Eingabe bekommt.

    ``mode="direct"`` liest die Läufe der In-Context-Verarbeitung
    (``<provider>_direct``), in denen das Modell die Ergebnistabelle unmittelbar
    zurückgibt, statt Code zu erzeugen. Die regelbasierte Baseline existiert nur
    im Code-Gen-Modus und entfällt dort entsprechend."""
    rows = []
    order = {s.name: i for i, s in enumerate(PIPELINE)}
    labels = {s.name: s.label for s in PIPELINE}
    teil = "_direct" if mode == "direct" else ""
    suffix = f"{teil}{'_isolated' if isolated else ''}"
    provider_liste = MODEL_ORDER if mode == "direct" else PIPE_ORDER
    teile = [_load_one(PIPELINE_RESULTS / str(seed) / f"{prov}{suffix}", prov, mode)
             for prov in provider_liste]
    teile = [t for t in teile if len(t)]
    if not teile:
        return pd.DataFrame(rows)
    return pd.concat(teile, ignore_index=True).sort_values(["provider", "order"])


def _load_one(verzeichnis, prov: str, mode: str) -> pd.DataFrame:
    """Liest die pipeline.json eines einzelnen Laufordners."""
    order = {s.name: i for i, s in enumerate(PIPELINE)}
    labels = {s.name: s.label for s in PIPELINE}
    p = verzeichnis / "pipeline.json"
    if not p.exists():
        return pd.DataFrame()
    d = json.loads(p.read_text(encoding="utf-8"))
    return pd.DataFrame([dict(
        provider=prov, label=PROVIDER_LABEL[prov], mode=mode,
        step=s["step"], step_label=labels.get(s["step"], s["step"]),
        order=order.get(s["step"], 99), status=s["status"],
        accuracy=s.get("accuracy"), attempts=s.get("attempts"),
        error=s.get("error"), truncated=bool(s.get("truncated")),
        duration_s=s.get("duration_s"), llm_s=s.get("llm_s"),
        exec_s=s.get("exec_s"),
        cost_usd=s.get("cost_usd", 0.0) or 0.0,
        prompt_tokens=s.get("prompt_tokens", 0) or 0,
        completion_tokens=s.get("completion_tokens", 0) or 0,
        row_actual=s.get("row_actual"), row_expected=s.get("row_expected"),
        model=d.get("model") or d.get("requested_model"),
    ) for s in d["steps"]])


def load_pipeline_reps(seed: int = 1, isolated: bool = False,
                       mode: str = "codegen") -> pd.DataFrame:
    """Alle Wiederholungen eines Laufs als Langformat mit Spalte ``rep``.

    Wiederholung 1 liegt im schlichten Ordner, ab der zweiten in ``..._r<N>``."""
    teil = "_direct" if mode == "direct" else ""
    iso = "_isolated" if isolated else ""
    provider_liste = MODEL_ORDER if mode == "direct" else PIPE_ORDER
    rahmen = []
    for prov in provider_liste:
        muster = f"{prov}{teil}{iso}"
        for d in sorted((PIPELINE_RESULTS / str(seed)).glob(f"{muster}*")):
            rest = d.name[len(muster):]
            if rest and not re.fullmatch(r"_r\d+", rest):
                continue          # anderer Lauf (z.B. ..._isolated bei muster ohne iso)
            rep = int(rest[2:]) if rest else 1
            df = _load_one(d, prov, mode)
            if len(df):
                df["rep"] = rep
                rahmen.append(df)
    if not rahmen:
        return pd.DataFrame()
    return pd.concat(rahmen, ignore_index=True).sort_values(["provider", "rep", "order"])


def mean_over_reps(seed: int = 1, isolated: bool = False,
                   mode: str = "codegen") -> pd.DataFrame:
    """Mittelt Genauigkeit und Aufwand je (Modell, Schritt) über die Wiederholungen.

    Ein Schritt, der in einzelnen Wiederholungen abbrach, geht dort mit 0 ein --
    andernfalls wuerde ein Modell dadurch besser dastehen, dass es haeufiger
    scheitert. Zusaetzlich wird die Streuung (``accuracy_std``) und die Zahl der
    verwertbaren Wiederholungen (``n_ok``) ausgewiesen."""
    lang = load_pipeline_reps(seed, isolated, mode)
    if not len(lang):
        return pd.DataFrame()
    lang = lang.copy()
    lang["acc_eff"] = np.where(lang.status == "ok", lang.accuracy, 0.0)
    g = lang.groupby(["provider", "label", "step", "step_label", "order"], as_index=False)
    out = g.agg(accuracy=("acc_eff", "mean"), accuracy_std=("acc_eff", "std"),
                n_reps=("rep", "nunique"), n_ok=("status", lambda s: (s == "ok").sum()),
                cost_usd=("cost_usd", "mean"), duration_s=("duration_s", "mean"),
                prompt_tokens=("prompt_tokens", "mean"),
                completion_tokens=("completion_tokens", "mean"))
    out["status"] = np.where(out.n_ok > 0, "ok", "failed")
    return out.sort_values(["provider", "order"])


def pipeline_heatmap(seed: int = 1, save: bool = True):
    """Schritt (Zeilen) x Modell (Spalten): Status/Genauigkeit der Pipeline."""
    df = load_pipeline(seed)
    steps = [s for s in PIPELINE]
    provs = [p for p in PIPE_ORDER if p in set(df.provider)]
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


def step_accuracy(seed: int = 1, save: bool = True):
    """Genauigkeitsverlauf entlang der Kette: eine Linie je Modell über die neun
    Schritte. Abgebrochene/blockierte Schritte enden als Lücke, sodass sichtbar
    wird, wie weit ein Modell kommt."""
    df = load_pipeline(seed)
    steps = list(PIPELINE)
    x = np.arange(len(steps))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for i, prov in enumerate([p for p in PIPE_ORDER if p in set(df.provider)]):
        sub = df[df.provider == prov].set_index("step")
        vals = [sub.loc[s.name, "accuracy"] if s.name in sub.index else np.nan
                for s in steps]
        vals = [v if v is not None else np.nan for v in vals]
        ax.plot(x, vals, "o-", lw=2, ms=6, color=f"C{i}", label=PROVIDER_LABEL[prov])
        # Abbruchstelle markieren
        for j, s in enumerate(steps):
            if s.name in sub.index and sub.loc[s.name, "status"] in STATUS_COLOR:
                ax.plot(j, 0, "x", ms=11, mew=2.5, color=f"C{i}")
    ax.set_xticks(x)
    ax.set_xticklabels([s.label for s in steps], rotation=30, ha="right", fontsize=8)
    ax.set_ylim(-0.05, 1.1)
    ax.set_ylabel("abgeglichene Genauigkeit")
    ax.set_title("Verkettete Pipeline – Genauigkeit entlang der Schrittfolge "
                 "(x = Abbruch, Lücke = blockiert)")
    ax.legend(fontsize=9)
    ax.grid(ls=":", alpha=0.5)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_genauigkeit")
    return fig, df


def effort(seed: int = 1, save: bool = True):
    """Aufwand der Pipeline: Kosten und Dauer je Schritt sowie benötigte Versuche.

    Die Dauer ist die Wanduhrzeit je Schritt inklusive Wiederholungen und Backoff;
    ältere Läufe ohne Zeitmessung erscheinen als Lücke."""
    df = load_pipeline(seed)
    provs = [p for p in PIPE_ORDER if p in set(df.provider)]
    labels = [PROVIDER_LABEL[p] for p in provs]
    steps = list(PIPELINE)

    fig, axes = plt.subplots(1, 3, figsize=(19, 4.6))

    def _stacked(ax, column, fmt, title, ylabel):
        bottom = np.zeros(len(provs))
        for k, s in enumerate(steps):
            vals = [float(df[(df.provider == p) & (df.step == s.name)][column]
                          .fillna(0).sum()) for p in provs]
            ax.bar(labels, vals, 0.55, bottom=bottom,
                   color=plt.cm.viridis(k / max(len(steps) - 1, 1)), label=s.label)
            bottom += np.array(vals)
        for i, v in enumerate(bottom):
            if v > 0:
                ax.text(i, v, fmt.format(v), ha="center", va="bottom", fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", ls=":", alpha=0.5)

    _stacked(axes[0], "cost_usd", "${:.3f}",
             "Kosten je Teilnehmer (gestapelt nach Schritt)", "Kosten ($)")
    _stacked(axes[1], "duration_s", "{:.0f}s",
             "Dauer je Teilnehmer (gestapelt nach Schritt)", "Dauer (s)")
    axes[1].legend(fontsize=6.5, ncol=1, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    att = df.pivot_table(index="step", columns="provider", values="attempts",
                         aggfunc="max").reindex([s.name for s in steps])
    att = att[[p for p in provs if p in att.columns]]
    im = axes[2].imshow(att.values.astype(float), cmap="OrRd", vmin=0, vmax=3,
                        aspect="auto")
    axes[2].set_xticks(range(att.shape[1]))
    axes[2].set_xticklabels([PROVIDER_LABEL[c] for c in att.columns])
    axes[2].set_yticks(range(att.shape[0]))
    axes[2].set_yticklabels([s.label for s in steps], fontsize=8)
    for r in range(att.shape[0]):
        for c in range(att.shape[1]):
            v = att.values[r, c]
            if not np.isnan(v):
                axes[2].text(c, r, f"{int(v)}", ha="center", va="center", fontsize=9)
    axes[2].set_title("Benötigte Versuche je Schritt (max. 3)", fontsize=10)
    fig.colorbar(im, ax=axes[2], fraction=0.03, pad=0.02)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_aufwand")
    return fig, df


def step_durations(seed: int = 1) -> pd.DataFrame:
    """Dauer je Schritt und Teilnehmer (Sekunden), plus Aufteilung in Modell- und
    Ausführungszeit für den Durchschnitt über die Modelle."""
    df = load_pipeline(seed)
    steps = [s.name for s in PIPELINE]
    T = df.pivot_table(index="step", columns="provider", values="duration_s",
                       aggfunc="first", dropna=False).reindex(steps)
    # Teilnehmer ohne Zeitmessung (Läufe vor deren Einführung) bleiben als
    # NaN-Spalte sichtbar, statt stillschweigend zu verschwinden.
    T = T.reindex(columns=[p for p in PIPE_ORDER if p in set(df.provider)])
    T.columns = [PROVIDER_LABEL[c] for c in T.columns]
    llm = df[df.provider != "baseline"]
    T.insert(0, "davon Skript (Ø)", llm.groupby("step").exec_s.mean().reindex(steps).round(2))
    T.insert(0, "davon Modell (Ø)", llm.groupby("step").llm_s.mean().reindex(steps).round(2))
    T.index = [s.label for s in PIPELINE]
    return T.round(2)


# Zuordnung Pipeline-Schritt -> unabhängige Aufgabe der Matrix-Läufe
STEP_TO_TASK = {
    "cleaning_easy": "cleaning_easy_missing_and_whitespace",
    "cleaning_medium": "cleaning_medium_date_formats",
    "cleaning_hard": "cleaning_hard_semantic_unification",
    "dedup_easy": "dedup_easy_exact_duplicates",
    "dedup_medium": "dedup_medium_key_duplicates",
    "dedup_hard": "dedup_hard_fuzzy_duplicates",
    "products": "transform_easy_type_conversion",
    "orders": "transform_medium_derived_columns",
    "final": "transform_hard_join_and_aggregate",
}


def pipeline_vs_matrix(runs: pd.DataFrame, seed: int = 1, save: bool = True):
    """Kette gegen Einzelläufe: Genauigkeit der Pipeline je Schritt gegenüber der
    besten klassischen Prompt-Strategie derselben Aufgabe auf den Rohdaten.

    Der Unterschied ist inhaltlich bedeutsam: In der Kette arbeitet ein Schritt auf
    bereits bereinigten Daten, in der Matrix immer auf den Rohdaten."""
    from reporting.compare import codegen_matrix

    df = load_pipeline(seed)
    cg = codegen_matrix(runs)
    steps = list(PIPELINE)
    rows = []
    for s in steps:
        task = STEP_TO_TASK[s.name]
        llm = df[(df.step == s.name) & (df.provider != "baseline")]
        base = df[(df.step == s.name) & (df.provider == "baseline")]
        rows.append({
            "Schritt": s.label,
            "Pipeline (Ø Modelle)": llm.accuracy.astype(float).mean() if not llm.empty else np.nan,
            "Einzellauf (beste Strategie, Ø Modelle)": cg.loc[task].mean() if task in cg.index else np.nan,
            "Baseline (Kette)": base.accuracy.astype(float).mean() if not base.empty else np.nan,
        })
    T = pd.DataFrame(rows).set_index("Schritt")
    T["Differenz"] = T.iloc[:, 0] - T.iloc[:, 1]

    x = np.arange(len(T))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.bar(x - w / 2, T.iloc[:, 0], w, color="#4e79a7", label="verkettete Pipeline")
    ax.bar(x + w / 2, T.iloc[:, 1], w, color="#f28e2b",
           label="unabhängige Einzelläufe (beste Strategie)")
    ax.plot(x, T["Baseline (Kette)"], "D", ms=7, color="#59a14f",
            label="regelbasierte Baseline (Kette)")
    ax.set_xticks(x)
    ax.set_xticklabels(T.index, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("abgeglichene Genauigkeit")
    ax.set_title("Verkettete Pipeline gegen unabhängige Einzelläufe "
                 "(Mittel über die Modelle)")
    ax.legend(fontsize=9)
    ax.grid(axis="y", ls=":", alpha=0.5)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_vs_einzellauf")
    return fig, T


def final_step_diagnosis(seed: int = 1) -> pd.DataFrame:
    """Spaltenweise Diagnose des Endschritts (Join & Aggregation).

    Der Endschritt fällt bei mehreren Modellen auf oder nahe 0, obwohl Zeilenzahl und
    Schema stimmen. Die Tabelle zeigt je Modell, welcher Anteil der Zellen je Spalte
    mit der verketteten Referenz übereinstimmt -- so wird sichtbar, ob die
    Gruppierung insgesamt danebenliegt oder nur einzelne Kennzahlen abweichen."""
    from experiments.pipeline_runner import build_chain_reference
    from reporting.analysis import _cellwise_eq

    exp = build_chain_reference(seed)["final"]
    keys = ["country_code", "category"]
    rows = []
    for prov in PIPE_ORDER:
        p = PIPELINE_RESULTS / str(seed) / prov / "final" / "output.parquet"
        if not p.exists():
            continue
        act = pd.read_parquet(p)
        rec = {"Modell": PROVIDER_LABEL[prov], "Zeilen Ist": len(act),
               "Zeilen Soll": len(exp)}
        if not set(exp.columns).issubset(act.columns):
            rec["Hinweis"] = f"fehlende Spalten: {set(exp.columns) - set(act.columns)}"
            rows.append(rec)
            continue
        e, a = exp.copy(), act[list(exp.columns)].copy()
        for k in keys:
            e[k], a[k] = e[k].astype(str), a[k].astype(str)
        m = e.merge(a, on=keys, how="inner", suffixes=("_soll", "_ist"))
        rec["Schluessel-Treffer"] = f"{len(m)}/{len(exp)}"
        for c in [c for c in exp.columns if c not in keys]:
            eq = _cellwise_eq(m[f"{c}_soll"], m[f"{c}_ist"]) if len(m) else np.array([])
            rec[f"{c} korrekt"] = round(float(eq.mean()) * 100, 1) if len(m) else 0.0
        rows.append(rec)
    return pd.DataFrame(rows).set_index("Modell")


def propagation_table(seed: int = 1) -> pd.DataFrame:
    """Schritt x Modell: isolierte Leistung, verkettetes Ergebnis und die Differenz.

    *isoliert* = jeder Schritt bekommt die Soll-Ausgabe seines Vorgängers, die
    Obergrenze liegt also für alle bei 1,0. *verkettet* = Realbetrieb mit der eigenen
    Vorgänger-Ausgabe. Die Differenz ist der Preis der Fehlerfortpflanzung; wo ein
    Lauf abgebrochen ist, steht der Status statt einer Zahl."""
    iso = load_pipeline(seed, isolated=True)
    ver = load_pipeline(seed)
    provs = [p for p in MODEL_ORDER if p in set(iso.provider) | set(ver.provider)]
    rows = []
    for step in PIPELINE:
        row = {"Schritt": step.label}
        for prov in provs:
            lbl = PROVIDER_LABEL[prov]
            a = iso[(iso.provider == prov) & (iso.step == step.name)]
            b = ver[(ver.provider == prov) & (ver.step == step.name)]
            av = float(a.accuracy.iloc[0]) if len(a) and a.status.iloc[0] == "ok" else np.nan
            bv = float(b.accuracy.iloc[0]) if len(b) and b.status.iloc[0] == "ok" else np.nan
            row[f"{lbl} isol."] = av
            row[f"{lbl} verk."] = bv
            row[f"{lbl} Diff."] = bv - av if not (np.isnan(av) or np.isnan(bv)) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index("Schritt")


def propagation_plot(seed: int = 1, save: bool = True):
    """Je Modell ein Panel: isolierte gegen verkettete Genauigkeit über alle Schritte.

    Die Lücke zwischen hellem und dunklem Balken ist die Fehlerfortpflanzung; ein
    rotes Kreuz markiert Schritte, die im jeweiligen Modus abgebrochen oder blockiert
    waren."""
    iso, ver = load_pipeline(seed, isolated=True), load_pipeline(seed)
    provs = [p for p in MODEL_ORDER if p in set(iso.provider) | set(ver.provider)]
    steps = list(PIPELINE)
    x = np.arange(len(steps))
    w = 0.38
    fig, axes = plt.subplots(2, 2, figsize=(15, 8), sharey=True)
    for ax, prov in zip(axes.ravel(), provs):
        for df, off, color, lab in ((iso, -w / 2, "#9ecae1", "isoliert (Soll-Eingabe)"),
                                    (ver, w / 2, "#08519c", "verkettet (Realbetrieb)")):
            sub = df[df.provider == prov].set_index("step")
            vals, marks = [], []
            for s in steps:
                if s.name in sub.index and sub.loc[s.name, "status"] == "ok":
                    vals.append(float(sub.loc[s.name, "accuracy"]))
                else:
                    vals.append(np.nan)
                    marks.append(s.name in sub.index)
            ax.bar(x + off, vals, w, color=color, label=lab)
            for j, s in enumerate(steps):
                if np.isnan(vals[j]):
                    ax.plot(j + off, 0.03, "x", ms=9, mew=2.2, color="#b2182b")
        ax.set_xticks(x)
        ax.set_xticklabels([s.label.split(" · ")[0] for s in steps])
        ax.set_ylim(0, 1.08)
        ax.set_title(PROVIDER_LABEL[prov], fontsize=11)
        ax.grid(axis="y", ls=":", alpha=0.5)
        ax.legend(fontsize=8, loc="lower left")
    axes[0][0].set_ylabel("abgeglichene Genauigkeit")
    axes[1][0].set_ylabel("abgeglichene Genauigkeit")
    fig.suptitle("Fehlerfortpflanzung: dieselbe Aufgabe mit sauberer Eingabe (hell) "
                 "und in der Kette (dunkel)\nrotes Kreuz = abgebrochen oder blockiert",
                 fontsize=12, y=1.0)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_fortpflanzung")
    return fig


def propagation_summary(seed: int = 1) -> pd.DataFrame:
    """Je Modell: mittlere isolierte Leistung, verkettetes Ergebnis, Verlust durch
    Fortpflanzung und der Endschritt als deutlichster Einzelfall."""
    T = propagation_table(seed)
    rows = []
    for prov in [p for p in MODEL_ORDER]:
        lbl = PROVIDER_LABEL[prov]
        if f"{lbl} isol." not in T.columns:
            continue
        iso, ver = T[f"{lbl} isol."], T[f"{lbl} verk."]
        rows.append({
            "Modell": lbl,
            "Schritte isoliert ok": int(iso.notna().sum()),
            "Schritte verkettet ok": int(ver.notna().sum()),
            "Genauigkeit isoliert (Ø)": round(float(iso.mean()), 3),
            "Genauigkeit verkettet (Ø)": round(float(ver.mean()), 3),
            "Endschritt isoliert": round(float(iso.iloc[-1]), 3) if pd.notna(iso.iloc[-1]) else None,
            "Endschritt verkettet": round(float(ver.iloc[-1]), 3) if pd.notna(ver.iloc[-1]) else None,
        })
    return pd.DataFrame(rows).set_index("Modell")


# ------------------------------------------------------- Code-Gen gegen Direkt

def mode_table(seed: int = 101, isolated: bool = False) -> pd.DataFrame:
    """Schritt x Modell: Genauigkeit im Code-Gen- und im Direkt-Modus.

    Beide Modi muessen auf **demselben Seed** gelaufen sein, sonst vergleicht man
    unterschiedliche Datenmengen. Leere Felder sind Schritte, die im jeweiligen
    Modus abgebrochen oder blockiert waren."""
    cg = load_pipeline(seed, isolated=isolated, mode="codegen")
    di = load_pipeline(seed, isolated=isolated, mode="direct")
    provs = [p for p in MODEL_ORDER
             if p in set(getattr(cg, "provider", [])) | set(getattr(di, "provider", []))]
    rows = []
    for step in PIPELINE:
        row = {"Schritt": step.label}
        for prov in provs:
            lbl = PROVIDER_LABEL[prov]
            for df, kuerzel in ((cg, "Code"), (di, "Direkt")):
                if len(df):
                    s = df[(df.provider == prov) & (df.step == step.name)]
                    wert = (float(s.accuracy.iloc[0])
                            if len(s) and s.status.iloc[0] == "ok"
                            and s.accuracy.iloc[0] is not None else np.nan)
                else:
                    wert = np.nan
                row[f"{lbl} {kuerzel}"] = wert
        rows.append(row)
    return pd.DataFrame(rows).set_index("Schritt")


def mode_plot(seed: int = 101, save: bool = True):
    """Je Modell ein Panel: Code-Generierung gegen Direktverarbeitung in der Kette.

    Beantwortet die Frage, ob der in der Einzelaufgaben-Matrix beobachtete Vorteil
    der Direktverarbeitung bei semantischen Aufgaben eine ganze Kette uebersteht --
    in der jeder Schritt zusaetzlich die vollstaendige Tabelle fehlerfrei
    durchreichen muss."""
    cg = load_pipeline(seed, mode="codegen")
    di = load_pipeline(seed, mode="direct")
    provs = [p for p in MODEL_ORDER
             if p in set(getattr(cg, "provider", [])) | set(getattr(di, "provider", []))]
    if not provs:
        raise ValueError(f"Keine Pipeline-Laeufe fuer Seed {seed} gefunden.")
    steps = list(PIPELINE)
    x = np.arange(len(steps))
    w = 0.38
    n = len(provs)
    fig, axes = plt.subplots((n + 1) // 2, 2, figsize=(15, 4 * ((n + 1) // 2)),
                             sharey=True, squeeze=False)
    for ax, prov in zip(axes.ravel(), provs):
        for df, off, farbe, lab in (
                (cg, -w / 2, "#4e79a7", "Code-Generierung"),
                (di, w / 2, "#f28e2b", "Direktverarbeitung")):
            werte = []
            sub = df[df.provider == prov].set_index("step") if len(df) else None
            for s in steps:
                if (sub is not None and s.name in sub.index
                        and sub.loc[s.name, "status"] == "ok"
                        and sub.loc[s.name, "accuracy"] is not None):
                    werte.append(float(sub.loc[s.name, "accuracy"]))
                else:
                    werte.append(np.nan)
            ax.bar(x + off, werte, w, color=farbe, label=lab)
            for j in range(len(steps)):
                if np.isnan(werte[j]):
                    ax.plot(j + off, 0.03, "x", ms=9, mew=2.2, color="#b2182b")
            # Abgeschnittene Antworten markieren -- dort ist die Tabelle
            # unvollstaendig, das Ergebnis also nicht inhaltlich falsch.
            if sub is not None and "truncated" in sub.columns:
                for j, s in enumerate(steps):
                    if s.name in sub.index and bool(sub.loc[s.name, "truncated"]):
                        ax.plot(j + off, 1.03, "v", ms=7, color="#b2182b")
        ax.set_xticks(x)
        ax.set_xticklabels([s.label.split(" · ")[0] for s in steps])
        ax.set_ylim(0, 1.10)
        ax.set_title(PROVIDER_LABEL[prov], fontsize=11)
        ax.grid(axis="y", ls=":", alpha=0.5)
        ax.legend(fontsize=8, loc="lower left")
    for ax in axes.ravel()[len(provs):]:
        ax.set_visible(False)
    for reihe in axes:
        reihe[0].set_ylabel("abgeglichene Genauigkeit")
    fig.suptitle("Verkettete Pipeline: Code-Generierung gegen Direktverarbeitung\n"
                 "rotes Kreuz = abgebrochen oder blockiert, Dreieck = Antwort "
                 "abgeschnitten", fontsize=12, y=1.0)
    fig.tight_layout()
    if save:
        save_fig(fig, "pipeline_modi")
    return fig


def mode_summary(seed: int = 101) -> pd.DataFrame:
    """Je Modell: durchlaufene Schritte, mittlere Genauigkeit, Endschritt, Aufwand
    -- im Code-Gen- gegen den Direkt-Modus."""
    rows = []
    for prov in MODEL_ORDER:
        for modus, kuerzel in (("codegen", "Code-Gen."), ("direct", "Direkt")):
            df = load_pipeline(seed, mode=modus)
            if not len(df):
                continue
            s = df[df.provider == prov]
            if not len(s):
                continue
            ok = s[s.status == "ok"]
            final = s[s.step == "final"]
            rows.append({
                "Modell": PROVIDER_LABEL[prov],
                "Modus": kuerzel,
                "Schritte ok": f"{len(ok)}/9",
                "Genauigkeit (Ø ok)": round(float(ok.accuracy.mean()), 3) if len(ok) else None,
                "Endschritt": (round(float(final.accuracy.iloc[0]), 3)
                               if len(final) and final.status.iloc[0] == "ok" else None),
                "Kosten ($)": round(float(s.cost_usd.sum()), 3),
                "Dauer (s)": round(float(s.duration_s.fillna(0).sum()), 1),
                "abgeschnitten": int(s.truncated.sum()) if "truncated" in s else 0,
            })
    return pd.DataFrame(rows).set_index(["Modell", "Modus"])


def final_step_decomposition(seed: int = 1) -> pd.DataFrame:
    """Zerlegt den Fehler des Endschritts in seine Ursachen.

    Drei Messungen je Teilnehmer:

    1. *eigener Code korrekt* -- die Referenz-Aggregationslogik wird auf **dieselben
       Zwischenstände** angewandt. Ein Wert von 1,0 heißt: Join, Gruppierung und
       Summen sind fehlerfrei, der gesamte Fehler ist stromaufwärts entstanden.
    2. *nur Dedup-Effekt* -- die Ländercodes werden aus der Referenz übernommen, die
       Kundenauswahl aus dem Lauf. Zeigt, was allein die Wahl des Duplikat-
       Repräsentanten kostet (verwaiste Bestellungen fallen beim Join heraus).
    3. *Endergebnis* -- der tatsächlich erreichte Wert.
    """
    from dataset import reference as ref
    from experiments.pipeline_runner import build_chain_reference
    from reporting.analysis import aligned_accuracy

    chain = build_chain_reference(seed)
    exp = chain["final"]
    ref_c = chain["dedup_hard"].rename(columns={"country": "country_code"}).copy()
    ref_c["customer_id"] = ref_c.customer_id.astype(str)

    rows = []
    for prov in PIPE_ORDER:
        d = PIPELINE_RESULTS / str(seed) / prov
        need = ["dedup_hard", "products", "orders", "final"]
        if not all((d / s / "output.parquet").exists() for s in need):
            continue
        cust = pd.read_parquet(d / "dedup_hard" / "output.parquet") \
            .rename(columns={"country": "country_code"})
        prod = pd.read_parquet(d / "products" / "output.parquet")
        orders = pd.read_parquet(d / "orders" / "output.parquet")
        fin = pd.read_parquet(d / "final" / "output.parquet")
        for t in (cust, orders):
            t["customer_id"] = t.customer_id.astype(str)
        for t in (cust, prod, orders):
            if "product_id" in t.columns:
                t["product_id"] = t.product_id.astype(str)

        eigen = ref._transform_hard(orders, cust, prod)
        fix = cust.drop(columns=["country_code"]).merge(
            ref_c[["customer_id", "country_code"]], on="customer_id", how="left")
        fix["country_code"] = fix["country_code"].fillna("UNKNOWN")
        nur_dedup = ref._transform_hard(orders, fix, prod)
        verwaist = int((~orders.customer_id.isin(cust.customer_id)).sum())
        rows.append({
            "Teilnehmer": PROVIDER_LABEL[prov],
            "eigener Code korrekt": round(aligned_accuracy(fin, eigen), 3),
            "nur Dedup-Effekt": round(aligned_accuracy(nur_dedup, exp), 3),
            "Endergebnis": round(aligned_accuracy(fin, exp), 3),
            "verwaiste Bestellungen": verwaist,
        })
    return pd.DataFrame(rows).set_index("Teilnehmer")


def pipeline_summary(seed: int = 1) -> pd.DataFrame:
    """Kompakte Übersicht je Modell: erreichte Schritte, Endergebnis, Abbruchstelle."""
    df = load_pipeline(seed)
    rows = []
    for prov in [p for p in PIPE_ORDER if p in set(df.provider)]:
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
