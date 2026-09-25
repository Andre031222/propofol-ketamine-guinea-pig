"""Etapa 3: análisis estadístico y figuras.

Entradas: data/processed/animals.csv, data/processed/monitoring.csv (de clean.py)
Salidas:  analysis/tables/*.csv  y  analysis/figures/*.pdf|png
Uso:      .venv/bin/python src/analysis.py
"""
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

import config as cfg

warnings.filterwarnings("ignore", category=UserWarning)  # avisos de convergencia de MixedLM se reportan abajo
rng = np.random.default_rng(20260924)

VITALS = {
    "fc": ("Heart rate", "beats min$^{-1}$"),
    "fr": ("Respiratory rate", "breaths min$^{-1}$"),
    "temp": ("Body temperature", "°C"),
    "spo2": ("SpO$_2$", "%"),
}
ACCENT, GREY, INK = "#1f5f8b", "#b8b8b8", "#222222"
REF_RANGES = {"fc": (200, 350), "fr": (40, 100), "temp": (38.0, 39.5)}  # sadar2026msd
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"], "pdf.fonttype": 42, "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "savefig.dpi": 600, "savefig.bbox": "tight"})


# ---------- utilidades estadísticas ----------
def median_ci(x, conf=0.95):
    """IC exacto (sin supuestos) de la mediana por estadísticos de orden binomiales."""
    x = np.sort(np.asarray(x, float))
    x = x[~np.isnan(x)]
    n = len(x)
    # j = mayor orden tal que P(Bin(n, .5) <= j-1) <= alfa/2; IC = [x_(j), x_(n-j+1)]
    j = max((k for k in range(1, n // 2 + 1) if stats.binom.cdf(k - 1, n, 0.5) <= (1 - conf) / 2), default=None)
    if j is None:
        return np.nan, np.nan
    return x[j - 1], x[n - j]


def describe(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna()
    lo, hi = median_ci(x.values)
    return {"n": len(x), "mean": x.mean(), "sd": x.std(ddof=1), "median": x.median(),
            "q1": x.quantile(.25), "q3": x.quantile(.75), "min": x.min(), "max": x.max(),
            "median_ci_lo": lo, "median_ci_hi": hi}


def prop_ci(k, n):
    """Proporción con IC95 % exacto de Clopper–Pearson."""
    if n == 0:
        return np.nan, np.nan, np.nan
    r = stats.binomtest(int(k), int(n)).proportion_ci(method="exact")
    return k / n, r.low, r.high


# ---------- tablas ----------
def table_characteristics(a):
    cols = {"peso_g": "Body weight (g)", "prop_mg_kg": "Propofol dose (mg/kg)",
            "ket_mg_kg": "Ketamine dose (mg/kg)", "vol_total_ml_kg": "Injected volume (mL/kg)",
            "basal_fc": "Baseline HR", "basal_fr": "Baseline RR", "basal_temp": "Baseline temperature (°C)",
            "basal_spo2": "Baseline SpO2 (%)"}
    return pd.DataFrame({lab: describe(a[c]) for c, lab in cols.items()}).T


def table_times(a):
    cols = {
        "t_disminucion_actividad": "Reduced activity",
        "t_perdida_enderezamiento": "Loss of righting reflex (LORR)",
        "t_perdida_estimulo": "Loss of response to stimulus",
        "t_perdida_pedal": "Loss of pedal withdrawal reflex",
        "t_plano_adecuado": "Adequate anaesthetic plane",
        "t_primer_movimiento": "First movement",
        "t_retorno_pedal": "Return of pedal reflex",
        "t_retorno_enderezamiento": "Return of righting reflex (RORR)",
        "t_esternal": "Sternal recumbency",
        "t_ambulacion": "Ambulation",
        "t_recuperacion_completa": "Complete recovery",
        "dur_perdida_enderezamiento": "Duration of LORR (RORR − LORR)",
        "dur_ausencia_pedal": "Duration of pedal reflex absence",
    }
    return pd.DataFrame({lab: describe(a[c]) for c, lab in cols.items()}).T


def table_adverse(a):
    rows = {
        "ea_hipotermia": "Hypothermia (drop ≥1.0 °C)",
        "ea_hipotermia_grave": "Marked hypothermia (drop ≥2.0 °C)",
        "ea_temp_menor_35": "Temperature <35.0 °C",
        "ea_bradicardia": "Bradycardia (↓≥20 % or <200 min⁻¹)",
        "ea_taquicardia": "Tachycardia (↑≥20 %)",
        "ea_bradipnea": "Bradypnoea (↓≥50 %)",
        "ea_hipoxemia": "Hypoxaemia (SpO2 <90 %)†",
        "ea_hipoxemia_grave": "Severe hypoxaemia (SpO2 <80 %)†",
    }
    out = []
    for c, lab in rows.items():
        s = a[c].dropna().astype(bool)
        p, lo, hi = prop_ci(s.sum(), len(s))
        out.append({"event": lab, "k": int(s.sum()), "n": len(s), "pct": 100 * p,
                    "ci_lo": 100 * lo, "ci_hi": 100 * hi})
    return pd.DataFrame(out)


def longitudinal(m, var, subset=None):
    """Modelo lineal mixto: var ~ tiempo (categórico) + sesión, intercepto aleatorio por animal.
    Devuelve medias por tiempo, contrastes vs basal y pruebas globales (LMM y Friedman)."""
    d = m if subset is None else m[subset]
    d = d.dropna(subset=[var]).copy()
    d["t"] = pd.Categorical(d["tiempo"].astype(str), categories=cfg.TIMEPOINTS)

    by_t = d.groupby("t", observed=True)[var]
    summ = pd.DataFrame({"n": by_t.size(), "mean": by_t.mean(), "sd": by_t.std(ddof=1)})
    summ["ci_lo"] = summ["mean"] - stats.t.ppf(.975, summ["n"] - 1) * summ["sd"] / np.sqrt(summ["n"])
    summ["ci_hi"] = summ["mean"] + stats.t.ppf(.975, summ["n"] - 1) * summ["sd"] / np.sqrt(summ["n"])

    formula = f"{var} ~ C(t, Treatment('basal'))"
    if d["sesion"].nunique() > 1:
        formula += " + C(sesion)"
    fit = smf.mixedlm(formula, d, groups=d["animal"]).fit(reml=True, method="lbfgs")
    tnames = [p for p in fit.params.index if p.startswith("C(t")]
    contr = pd.DataFrame({"estimate": fit.params[tnames], "ci_lo": fit.conf_int().loc[tnames, 0],
                          "ci_hi": fit.conf_int().loc[tnames, 1], "p": fit.pvalues[tnames]})
    contr.index = [n.split("T.")[-1].rstrip("]") for n in tnames]
    # Holm para los 8 contrastes vs basal
    order = np.argsort(contr["p"].values)
    adj = np.empty(len(order))
    running = 0
    for rank, i in enumerate(order):
        running = max(running, (len(order) - rank) * contr["p"].values[i])
        adj[i] = min(running, 1)
    contr["p_holm"] = adj

    # Prueba global del tiempo: Wald conjunto de los contrastes
    R = np.zeros((len(tnames), len(fit.params)))
    for i, n in enumerate(tnames):
        R[i, list(fit.params.index).index(n)] = 1
    wald = fit.wald_test(R, scalar=True)

    wide = d.pivot(index="animal", columns="t", values=var).dropna()
    fr = stats.friedmanchisquare(*[wide[c] for c in wide.columns]) if len(wide) >= 3 else None
    icc = fit.cov_re.iloc[0, 0] / (fit.cov_re.iloc[0, 0] + fit.scale)
    glob = {"variable": var, "n_animals": d["animal"].nunique(), "n_obs": len(d),
            "lmm_wald_chi2": float(wald.statistic), "lmm_df": len(tnames), "lmm_p": float(wald.pvalue),
            "icc_animal": icc, "friedman_n_complete": len(wide),
            "friedman_chi2": fr.statistic if fr else np.nan, "friedman_p": fr.pvalue if fr else np.nan,
            "kendall_w": fr.statistic / (len(wide) * (len(wide.columns) - 1)) if fr else np.nan}
    return summ, contr, glob


# ---------- figuras ----------
def fig_vitals(m, spo2_subset):
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2))
    for ax, (var, (title, unit)) in zip(axes.flat, VITALS.items()):
        d = m[m["spo2_fiable"]] if (var == "spo2" and spo2_subset) else m
        for _, g in d.groupby("animal"):
            ax.plot(g["min"], g[var], color=GREY, lw=0.6, alpha=0.55, zorder=1)
        s = d.groupby("min")[var].agg(["mean", "std", "count"])
        half = stats.t.ppf(.975, s["count"] - 1) * s["std"] / np.sqrt(s["count"])
        ax.fill_between(s.index, s["mean"] - half, s["mean"] + half, color=ACCENT, alpha=0.18, lw=0, zorder=2)
        ax.plot(s.index, s["mean"], color=ACCENT, lw=2, marker="o", ms=3.5, zorder=3)
        ylim = ax.get_ylim()
        ref = REF_RANGES.get(var)
        if ref:  # rango de referencia en cobayo despierto (Sadar 2026, MSD Vet Manual)
            ax.axhspan(*ref, color="#2e7d32", alpha=0.08, lw=0, zorder=0)
        if var == "spo2":
            ax.axhline(90, color="#9b2226", lw=0.8, ls="--", zorder=1)
            ylim = (ylim[0], 101)
        ax.set_ylim(ylim)
        ax.set_title(title + (f" (reliable baseline, n={d['animal'].nunique()})" if var == "spo2" else ""),
                     loc="left", fontsize=8.5, color=INK)
        ax.set_ylabel(unit)
        ax.set_xticks([0, 5, 10, 15, 20, 30, 40, 50, 60])
        ax.set_xticklabels(["B", "5", "10", "15", "20", "30", "40", "50", "60"])
        ax.grid(axis="y", color="#e6e6e6", lw=0.5)
    for ax in axes[1]:
        ax.set_xlabel("Time after IP injection (min); B = baseline")
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Line2D([], [], color=GREY, lw=0.8, label="Individual animals"),
               Line2D([], [], color=ACCENT, lw=2, marker="o", ms=3.5, label="Mean"),
               Patch(color=ACCENT, alpha=0.18, label="95 % CI of the mean"),
               Patch(color="#2e7d32", alpha=0.15, label="Reference range (awake)"),
               Line2D([], [], color="#9b2226", lw=0.8, ls="--", label="Hypoxaemia threshold (90 %)")]
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=6.8,
               bbox_to_anchor=(0.5, 1.0), handlelength=1.8, columnspacing=1.2)
    return fig


def fig_timeline(a):
    """Diagrama por animal de los eventos de inducción y recuperación (min desde la inyección)."""
    ev = [("t_perdida_enderezamiento", "LORR", "v"), ("t_perdida_pedal", "Pedal lost", "x"),
          ("t_retorno_pedal", "Pedal returned", "+"), ("t_retorno_enderezamiento", "RORR", "^"),
          ("t_ambulacion", "Ambulation", "s")]
    d = a.sort_values("t_retorno_enderezamiento").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    for i, r in d.iterrows():
        ax.plot([r["t_perdida_enderezamiento"], r["t_retorno_enderezamiento"]], [i, i],
                color=ACCENT, lw=4, alpha=0.35, solid_capstyle="round")
        ax.plot([r["t_retorno_enderezamiento"], r["t_ambulacion"]], [i, i], color=GREY, lw=1.2)
    for c, lab, mk in ev:
        ax.scatter(d[c], d.index, marker=mk, s=22, color=INK, lw=0.8, label=lab, zorder=3,
                   facecolors="white" if mk in "s^v" else INK)
    ax.set_yticks(d.index)
    ax.set_yticklabels([f"GP{int(x)}" for x in d["animal"]])
    ax.set_xlabel("Time after IP injection (min)")
    ax.grid(axis="x", color="#e6e6e6", lw=0.5)
    ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12), fontsize=7)
    fig.tight_layout()
    return fig


def fig_cumulative(a):
    """Proporción acumulada de animales que alcanzan cada evento (todos los eventos observados)."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    panels = [("Induction", [("t_perdida_enderezamiento", "LORR", "-"), ("t_perdida_pedal", "Loss of pedal reflex", "--")]),
              ("Recovery", [("t_retorno_enderezamiento", "RORR", "-"), ("t_ambulacion", "Ambulation", "--")])]
    for ax, (title, evs) in zip(axes, panels):
        for c, lab, ls in evs:
            x = np.sort(a[c].dropna().values)
            y = np.arange(1, len(x) + 1) / len(a)
            ax.step(np.r_[0, x], np.r_[0, y], where="post", color=ACCENT if ls == "-" else INK, ls=ls, lw=1.6, label=lab)
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.set_xlabel("Time after IP injection (min)")
        ax.grid(color="#e6e6e6", lw=0.5)
        ax.legend(frameon=False, fontsize=7, loc="lower right")
    axes[0].set_ylabel("Cumulative proportion of animals")
    fig.tight_layout()
    return fig


# Traducción al español de los textos de las figuras (versión para presentación local)
ES = [
    ("Time after IP injection (min); B = baseline", "Tiempo tras la inyección IP (min); B = basal"),
    ("Time after IP injection (min)", "Tiempo tras la inyección IP (min)"),
    ("Heart rate (beats min$^{-1}$)", "Frecuencia cardíaca (lat. min$^{-1}$)"),
    ("Respiratory rate (breaths min$^{-1}$)", "Frecuencia respiratoria (resp. min$^{-1}$)"),
    ("Body temperature (°C)", "Temperatura corporal (°C)"),
    ("Heart rate", "Frecuencia cardíaca"), ("Respiratory rate", "Frecuencia respiratoria"),
    ("Body temperature", "Temperatura corporal"), ("beats min$^{-1}$", "lat. min$^{-1}$"),
    ("breaths min$^{-1}$", "resp. min$^{-1}$"), ("reliable baseline", "basal fiable"),
    ("reference range", "rango de referencia"), ("hypoxaemia threshold (90 %)", "umbral de hipoxemia (90 %)"),
    ("Pedal lost", "Pérdida pedal"), ("Pedal returned", "Retorno pedal"), ("Ambulation", "Deambulación"),
    ("Induction", "Inducción"), ("Recovery", "Recuperación"), ("Loss of pedal reflex", "Pérdida del reflejo podal"),
    ("Cumulative proportion of animals", "Proporción acumulada de animales"),
    ("Study design and anaesthetic timeline (medians of observed event times)",
     "Diseño del estudio y cronología anestésica (medianas de los tiempos observados)"),
    ("Pre-anaesthetic\nexamination\nweight, T°, HR,\nRR, SpO$_2$", "Evaluación\npreanestésica\npeso, T°, FC,\nFR, SpO$_2$"),
    ("Single IP injection\n(T0)\npropofol 7 mg kg$^{-1}$\n+ ketamine 50 mg kg$^{-1}$",
     "Inyección IP única\n(T0)\npropofol 7 mg kg$^{-1}$\n+ ketamina 50 mg kg$^{-1}$"),
    ("Intra-anaesthetic monitoring\nHR, RR, T°, SpO$_2$,\npedal reflex, muscle relaxation\nbaseline and 5–60 min",
     "Monitorización intraanestésica\nFC, FR, T°, SpO$_2$,\nreflejo podal, relajación muscular\nbasal y 5–60 min"),
    ("monitoring window (0–60 min)", "ventana de monitorización (0–60 min)"),
    ("pedal reflex\nlost", "pérdida del\nreflejo podal"), ("ambulation", "deambulación"),
    ("follow-up\n1, 2, 4, 24 h →", "seguimiento\n1, 2, 4, 24 h →"),
    (" male\nCavia porcellus", " machos\nCavia porcellus"),
    ("Silhouette: PhyloPic (D. Stadtmauer), CC0 1.0", "Silueta: PhyloPic (D. Stadtmauer), CC0 1.0"),
    ("Change from baseline\n(LMM estimate, 95 % CI)", "Cambio respecto del basal\n(estimación MLM, IC 95 %)"),
    ("Holm p < 0.05", "Holm p < 0,05"), ("n.s.", "n.s."),
    ("Individual animals", "Animales individuales"), ("Mean", "Media"), ("95 % CI of the mean", "IC 95 % de la media"),
    ("Reference range (awake)", "Rango de referencia (despierto)"),
    ("Hypoxaemia threshold (90 %)", "Umbral de hipoxemia (90 %)"),
    ("Body weight\n476–609 g (n = 13 ♂)", "Peso corporal\n476–609 g (n = 13 ♂)"),
    ("HR: auscultation,\nbeats in 15 s × 4", "FC: auscultación,\nlatidos en 15 s × 4"),
    ("SpO$_2$: fingertip\noximeter on forelimb", "SpO$_2$: oxímetro de dedo\nen miembro torácico"),
    ("IP injection (T0)\npropofol 7 mg kg$^{-1}$\n+ ketamine 50 mg kg$^{-1}$",
     "Inyección IP (T0)\npropofol 7 mg kg$^{-1}$\n+ ketamina 50 mg kg$^{-1}$"),
    ("Body temperature\n(digital thermometer)", "Temperatura corporal\n(termómetro digital)"),
    ("Clock times of\nLORR, pedal reflex,\nRORR, ambulation", "Horas de LORR,\nreflejo podal,\nRORR y deambulación"),
    ("RR: thoracic excursions", "FR: excursiones torácicas"),
    ("Illustrations: Servier Medical Art (CC BY 3.0); thermometer: kehan (CC0)",
     "Ilustraciones: Servier Medical Art (CC BY 3.0); termómetro: kehan (CC0)"),
    ("monitoring: baseline, 5–60 min", "monitorización: basal, 5–60 min"),
    ("follow-up 1, 2, 4 and 24 h →", "seguimiento 1, 2, 4 y 24 h →"),
    ("Maximum temperature drop (°C)", "Descenso máximo de temperatura (°C)"), ("Body weight (g)", "Peso corporal (g)"),
    ("Duration of LORR (min)", "Duración de la LORR (min)"),
    ("Pedal reflex absent", "Reflejo podal ausente"), ("Present / reduced", "Presente / disminuido"),
    ("· not interpretable", "· no interpretable"),
]


def _to_spanish(fig):
    for t in fig.findobj(match=lambda a: hasattr(a, "get_text") and hasattr(a, "set_text")):
        txt = t.get_text()
        for en, es in sorted(ES, key=lambda p: -len(p[0])):  # frases largas primero
            txt = txt.replace(en.replace("\\n", "\n"), es.replace("\\n", "\n"))
        t.set_text(txt)


def save(fig, name):
    cfg.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(cfg.FIGURES / f"{name}.pdf")
    fig.savefig(cfg.FIGURES / f"{name}.png", dpi=200)
    _to_spanish(fig)
    (cfg.FIGURES / "es").mkdir(exist_ok=True)
    fig.savefig(cfg.FIGURES / "es" / f"{name}.pdf")
    fig.savefig(cfg.FIGURES / "es" / f"{name}.png", dpi=200)
    plt.close(fig)


def main():
    a = pd.read_csv(cfg.PROCESSED / "animals.csv")
    m = pd.read_csv(cfg.PROCESSED / "monitoring.csv", dtype={"tiempo": str})
    cfg.TABLES.mkdir(parents=True, exist_ok=True)

    t1 = table_characteristics(a); t1.to_csv(cfg.TABLES / "t1_characteristics.csv")
    t2 = table_times(a); t2.to_csv(cfg.TABLES / "t2_event_times.csv")
    t3 = table_adverse(a); t3.to_csv(cfg.TABLES / "t3_adverse_events.csv", index=False)

    glob_rows, contr_rows, summ_rows = [], [], []
    for var in VITALS:
        analyses = [("all", None)]
        if var == "spo2":
            analyses = [("reliable", m["spo2_fiable"]), ("all_sensitivity", None)]
        for label, subset in analyses:
            summ, contr, glob = longitudinal(m, var, subset)
            glob_rows.append({**glob, "set": label})
            contr_rows.append(contr.assign(variable=var, set=label))
            summ_rows.append(summ.assign(variable=var, set=label))
    pd.DataFrame(glob_rows).to_csv(cfg.TABLES / "t4_longitudinal_global.csv", index=False)
    pd.concat(contr_rows).to_csv(cfg.TABLES / "t5_contrasts_vs_baseline.csv")
    pd.concat(summ_rows).to_csv(cfg.TABLES / "t6_means_by_time.csv")

    # Exploratorio: asociaciones con la duración de la anestesia (Spearman)
    expl = []
    for x in ["peso_g", "ket_mg_kg", "temp_descenso_max", "basal_temp"]:
        for y in ["dur_perdida_enderezamiento", "t_ambulacion"]:
            s = a[[x, y]].dropna()
            rho, p = stats.spearmanr(s[x], s[y])
            expl.append({"x": x, "y": y, "n": len(s), "rho": rho, "p": p})
    pd.DataFrame(expl).to_csv(cfg.TABLES / "t7_exploratory_spearman.csv", index=False)

    save(fig_vitals(m, spo2_subset=True), "fig2_vitals")
    save(fig_timeline(a), "fig1_timeline")
    save(fig_cumulative(a), "fig3_cumulative")

    pd.set_option("display.width", 200)
    print(t2[["n", "median", "q1", "q3", "min", "max", "median_ci_lo", "median_ci_hi"]].round(1))
    print(t3.round(1).to_string(index=False))
    print(pd.DataFrame(glob_rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
