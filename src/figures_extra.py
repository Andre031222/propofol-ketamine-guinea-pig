"""Figuras adicionales: esquema del diseño, flujo de datos, cambios vs basal, reflejo pedal,
eventos adversos y asociaciones exploratorias.

Silueta del cuy: PhyloPic, Daniel Stadtmauer, CC0 1.0 (analysis/assets/guinea_pig_cc0_b.svg).
Uso: .venv/bin/python src/figures_extra.py
"""
import io

import cairosvg
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy import stats

import config as cfg
from analysis import ACCENT, GREY, INK, save  # mismo estilo que las figuras principales

LIGHT = "#dbe7f0"
ASSET = cfg.ROOT / "analysis" / "assets" / "guinea_pig_cc0_b.svg"


def silhouette(color="#1f5f8b"):
    svg = ASSET.read_text().replace("#000000", color).replace('fill="black"', f'fill="{color}"')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=600)
    return mpimg.imread(io.BytesIO(png), format="png")


def box(ax, x, y, w, h, text, fc=LIGHT, ec=ACCENT, size=7.5, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015",
                                fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK,
            weight=weight, linespacing=1.35)


def arrow(ax, x0, y0, x1, y1, color=INK, lw=1.0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9,
                                 color=color, lw=lw, shrinkA=0, shrinkB=0))


def _icon(name, width=300):
    png = cairosvg.svg2png(url=str(cfg.ROOT / "analysis" / "assets" / f"{name}.svg"), output_width=width)
    return mpimg.imread(io.BytesIO(png), format="png")


def _place(ax, img, cx, cy, w):
    """Coloca una imagen centrada en (cx, cy) con ancho w (unidades de datos), conservando proporción."""
    h = w * img.shape[0] / img.shape[1]
    ax.imshow(img, extent=(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2), zorder=3, interpolation="antialiased")
    return h


def _stethoscope(ax, cx, cy, s=0.55):
    from matplotlib.patches import Circle, PathPatch
    from matplotlib.path import Path
    col = "#37474f"
    ax.add_patch(Circle((cx + 0.25 * s, cy - 0.55 * s), 0.17 * s, fc="#b0bec5", ec=col, lw=1.2, zorder=4))
    verts = [(cx - 0.35 * s, cy + 0.55 * s), (cx - 0.45 * s, cy - 0.1 * s), (cx - 0.1 * s, cy - 0.35 * s),
             (cx + 0.25 * s, cy - 0.38 * s)]
    ax.add_patch(PathPatch(Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]), fc="none", ec=col, lw=1.6, zorder=4))
    verts = [(cx + 0.35 * s, cy + 0.55 * s), (cx + 0.45 * s, cy + 0.0 * s), (cx + 0.1 * s, cy - 0.25 * s),
             (cx - 0.1 * s, cy - 0.35 * s)]
    ax.add_patch(PathPatch(Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]), fc="none", ec=col, lw=1.6, zorder=4))
    for dx in (-0.35, 0.35):
        ax.add_patch(Circle((cx + dx * s, cy + 0.6 * s), 0.05 * s, fc=col, ec=col, zorder=4))


def _oximeter(ax, cx, cy, s=0.55):
    ax.add_patch(FancyBboxPatch((cx - 0.55 * s, cy - 0.32 * s), 1.1 * s, 0.64 * s,
                                boxstyle=f"round,pad=0,rounding_size={0.18 * s}", fc="#1e56a0", ec="#0d3570", lw=1, zorder=4))
    ax.add_patch(FancyBboxPatch((cx - 0.38 * s, cy - 0.18 * s), 0.62 * s, 0.36 * s,
                                boxstyle=f"round,pad=0,rounding_size={0.04 * s}", fc="#0b1a2e", ec="none", zorder=5))
    ax.text(cx - 0.07 * s, cy, "98", color="#4dd0e1", fontsize=6.5, ha="center", va="center", weight="bold", zorder=6)
    ax.add_patch(plt.Circle((cx + 0.39 * s, cy), 0.08 * s, fc="white", ec="none", zorder=5))


def fig_design(a):
    """Figura 1: (A) montaje experimental ilustrado; (B) cronología con medianas observadas."""
    med = a[["t_perdida_enderezamiento", "t_perdida_pedal", "t_retorno_enderezamiento", "t_ambulacion"]].median()
    fig = plt.figure(figsize=(7.2, 5.5))
    axA = fig.add_axes([0.0, 0.29, 1.0, 0.70])
    axB = fig.add_axes([0.05, 0.0, 0.92, 0.27])
    axA.set_xlim(0, 12); axA.set_ylim(0, 5.3); axA.set_aspect("equal"); axA.axis("off")

    # Cuy (Servier Medical Art, CC BY 3.0). Coordenadas de la ilustración: ancho 10, alto 6.44
    W, x0, y0 = 5.2, 3.4, 0.75
    H = _place(axA, _icon("guineapig-orange", 900), x0 + W / 2, y0 + W * 0.644 / 2, W)
    P = lambda u, v: (x0 + u * W / 10, y0 + v * H / 6.44)

    def callout(xy_text, target, text, ha):
        axA.annotate(text, xy=target, xytext=xy_text, fontsize=7, ha=ha, va="center", color=INK, linespacing=1.3,
                     arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.0, mutation_scale=8,
                                     connectionstyle="arc3,rad=0.12", shrinkA=4, shrinkB=2), zorder=6)

    # Columna izquierda: peso, FC, SpO2
    _place(axA, _icon("scale", 300), 0.55, 4.55, 0.75)
    axA.text(1.05, 4.55, "Body weight\n476–609 g (n = 13 ♂)", fontsize=7, va="center", color=INK)
    _stethoscope(axA, 0.55, 2.55)
    callout((1.05, 2.55), P(4.9, 1.1), "HR: auscultation,\nbeats in 15 s × 4", "left")
    _oximeter(axA, 0.55, 0.85)
    callout((1.05, 0.85), P(3.7, 0.08), "SpO$_2$: fingertip\noximeter on forelimb", "left")

    # Columna derecha: inyección, temperatura, tiempos
    _place(axA, _icon("syringe", 400), 11.15, 4.55, 1.3)
    callout((10.4, 4.55), P(6.6, 1.3), "IP injection (T0)\npropofol 7 mg kg$^{-1}$\n+ ketamine 50 mg kg$^{-1}$", "right")
    _place(axA, _icon("thermometer", 200), 11.3, 2.7, 0.42)
    callout((10.9, 2.7), P(9.4, 1.7), "Body temperature\n(digital thermometer)", "right")
    _place(axA, _icon("stopwatch", 300), 11.2, 1.0, 0.7)
    axA.text(10.75, 1.0, "Clock times of\nLORR, pedal reflex,\nRORR, ambulation", fontsize=7, va="center", ha="right", color=INK)

    # FR: excursiones torácicas (arriba al centro)
    callout((6.0, 5.1), P(5.2, 5.2), "RR: thoracic excursions", "center")
    axA.text(0.0, 5.25, "A", fontsize=11, weight="bold", color=INK, va="top")
    axA.text(12.0, -0.05, "Illustrations: Servier Medical Art (CC BY 3.0); thermometer: kehan (CC0)",
             fontsize=5.3, color="#888", ha="right", va="bottom")

    # Panel B: cronología
    tmax = 150
    axB.set_xlim(-3, tmax + 3); axB.set_ylim(-0.9, 1.5); axB.axis("off")
    axB.plot([0, tmax], [0, 0], color=INK, lw=0.8)
    for t in range(0, tmax + 1, 30):
        axB.plot([t, t], [-0.06, 0.06], color=INK, lw=0.8)
        axB.text(t, -0.2, f"{t}", ha="center", va="top", fontsize=7)
    axB.text(tmax / 2, -0.62, "Time after IP injection (min)", ha="center", fontsize=7.5)
    axB.add_patch(FancyBboxPatch((0, 0.1), 60, 0.16, boxstyle="square,pad=0", fc=LIGHT, ec="none"))
    axB.text(30, 0.18, "monitoring: baseline, 5–60 min", ha="center", va="center", fontsize=6.5, color=ACCENT)
    events = [(med.t_perdida_enderezamiento, "LORR", 0.62, -6), (med.t_perdida_pedal, "pedal reflex\nlost", 1.02, 7),
              (med.t_retorno_enderezamiento, "RORR", 0.62, -6), (med.t_ambulacion, "ambulation", 1.02, 8)]
    for t, lab, yy, dx in events:
        axB.annotate(f"{lab}\n{t:.0f} min", xy=(t, 0.02), xytext=(t + dx, yy), ha="center", va="bottom",
                     fontsize=6.8, color=INK, arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=0.9, mutation_scale=7))
    axB.text(tmax, 0.35, "follow-up 1, 2, 4 and 24 h →", ha="right", va="bottom", fontsize=6.8, color="#555")
    axB.text(-3, 1.45, "B", fontsize=11, weight="bold", color=INK, va="top")
    return fig


def fig_dataflow():
    """Figura suplementaria: flujo de digitalización y verificación de datos."""
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    steps = [
        (0.00, "13 handwritten\nanaesthetic records\n(104 scanned pages)"),
        (0.205, "Independent double\ntranscription\n(P1, P2; 1742 fields)"),
        (0.41, "Field-level agreement\n98.5 %; 3 value\ndiscrepancies resolved\nagainst the scan"),
        (0.615, "External third\ntranscription\n468 vital signs,\n97.4 % agreement"),
        (0.82, "Analytical dataset\n13 animals ×\n9 time points"),
    ]
    for i, (x, t) in enumerate(steps):
        box(ax, x, 0.30, 0.165, 0.45, t, size=6.5)
        if i:
            arrow(ax, x - 0.036, 0.525, x - 0.006, 0.525)
    ax.text(0.5, 0.12, "Every correction is recorded in a decision log with its justification; original transcriptions are never overwritten.",
            ha="center", fontsize=7, color="#555")
    return fig


def fig_change(contr, means):
    """Cambio vs basal estimado por el modelo mixto (IC95 %), por variable."""
    labels = {"fc": "Heart rate (beats min$^{-1}$)", "fr": "Respiratory rate (breaths min$^{-1}$)",
              "temp": "Body temperature (°C)"}
    times = [5, 10, 15, 20, 30, 40, 50, 60]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    for ax, (v, lab) in zip(axes, labels.items()):
        c = contr[(contr.variable == v) & (contr.set == "all")].copy()
        c["min"] = c.index.astype(int)
        c = c.sort_values("min")
        c["min"] = [times.index(t) for t in c["min"]]  # posiciones equiespaciadas
        sig = c["p_holm"] < 0.05
        ax.axhline(0, color=INK, lw=0.6)
        ax.errorbar(c["min"], c["estimate"], yerr=[c["estimate"] - c["ci_lo"], c["ci_hi"] - c["estimate"]],
                    fmt="none", ecolor=ACCENT, elinewidth=1, capsize=0)
        ax.scatter(c["min"][sig], c["estimate"][sig], color=ACCENT, s=18, zorder=3, label="Holm p < 0.05")
        ax.scatter(c["min"][~sig], c["estimate"][~sig], facecolor="white", edgecolor=ACCENT, s=18, zorder=3,
                   label="n.s.")
        ax.set_xticks(range(len(times))); ax.set_xticklabels(times)
        ax.set_title("Δ " + lab, loc="left", fontsize=7.5)
        ax.set_xlabel("Time after IP injection (min)")
        ax.grid(axis="y", color="#e6e6e6", lw=0.5)
    axes[0].set_ylabel("Change from baseline\n(LMM estimate, 95 % CI)")
    axes[0].legend(frameon=False, fontsize=6.5, loc="lower left")
    fig.tight_layout()
    return fig


def fig_pedal(m, a):
    """Mapa animal × tiempo del reflejo pedal armonizado (ausente / presente / no interpretable)."""
    order = a.sort_values("t_retorno_enderezamiento")["animal"].tolist()
    w = m.pivot(index="animal", columns="min", values="pedal_ausente").reindex(order)
    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    cmap = plt.matplotlib.colors.ListedColormap(["#f3f3f3", ACCENT])
    ax.imshow(np.ma.masked_invalid(w.values), cmap=cmap, aspect="auto", vmin=0, vmax=1)
    for (i, j), v in np.ndenumerate(w.values):
        if np.isnan(v):
            ax.text(j, i, "·", ha="center", va="center", color="#999", fontsize=8)
    ax.set_xticks(range(w.shape[1])); ax.set_xticklabels(["B"] + [str(c) for c in w.columns[1:]])
    ax.set_yticks(range(len(order))); ax.set_yticklabels([f"GP{x}" for x in order])
    ax.set_xlabel("Time after IP injection (min)")
    ax.set_xticks(np.arange(-.5, w.shape[1]), minor=True); ax.set_yticks(np.arange(-.5, len(order)), minor=True)
    ax.grid(which="minor", color="white", lw=1.5); ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=ACCENT, label="Pedal reflex absent"), Patch(color="#f3f3f3", label="Present / reduced"),
                       Patch(facecolor="white", edgecolor="#bbb", label="· not interpretable")],
              frameon=False, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3)
    fig.tight_layout()
    return fig


def fig_adverse(t3):
    d = t3.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(5.0, 2.8))
    ax.hlines(d.index, d["ci_lo"], d["ci_hi"], color=ACCENT, lw=1.4)
    ax.scatter(d["pct"], d.index, color=ACCENT, s=22, zorder=3)
    for i, r in d.iterrows():
        ax.text(101, i, f"{r.k}/{r.n}", va="center", fontsize=7, color=INK)
    ax.set_yticks(d.index); ax.set_yticklabels(d["event"], fontsize=7)
    ax.set_xlim(0, 110); ax.set_xticks(range(0, 101, 20))
    ax.set_xlabel("Animals affected (%, exact 95 % CI)")
    ax.grid(axis="x", color="#e6e6e6", lw=0.5)
    fig.tight_layout()
    fig.text(0.01, -0.03, "† SpO$_2$ events only in animals with a physiologically plausible baseline (≥90 %).",
             fontsize=6.3, color="#555")
    return fig


def fig_exploratory(a):
    pairs = [("temp_descenso_max", "Maximum temperature drop (°C)"), ("peso_g", "Body weight (g)")]
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.6), sharey=True)
    for ax, (x, lab) in zip(axes, pairs):
        s = a[[x, "dur_perdida_enderezamiento"]].dropna()
        rho, p = stats.spearmanr(s[x], s["dur_perdida_enderezamiento"])
        ax.scatter(s[x], s["dur_perdida_enderezamiento"], color=ACCENT, s=22, edgecolor="white", lw=0.6)
        ax.set_xlabel(lab)
        ax.set_title(f"Spearman ρ = {rho:.2f}, p = {p:.2f}", loc="left", fontsize=7.5)
        ax.grid(color="#e6e6e6", lw=0.5)
    axes[0].set_ylabel("Duration of LORR (min)")
    fig.tight_layout()
    return fig


def main():
    a = pd.read_csv(cfg.PROCESSED / "animals.csv")
    m = pd.read_csv(cfg.PROCESSED / "monitoring.csv", dtype={"tiempo": str})
    contr = pd.read_csv(cfg.TABLES / "t5_contrasts_vs_baseline.csv", index_col=0)
    t3 = pd.read_csv(cfg.TABLES / "t3_adverse_events.csv")
    save(fig_design(a), "fig0_design")
    save(fig_dataflow(), "figS1_dataflow")
    save(fig_change(contr, None), "fig4_change_from_baseline")
    save(fig_pedal(m, a), "figS2_pedal_reflex")
    save(fig_adverse(t3), "fig5_adverse_events")
    save(fig_exploratory(a), "figS3_exploratory")
    print("ok")


if __name__ == "__main__":
    main()
