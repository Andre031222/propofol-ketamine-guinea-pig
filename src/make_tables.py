"""Genera paper/sections/tables_generated.tex a partir de analysis/tables/*.csv.
Uso: .venv/bin/python src/make_tables.py
"""
import pandas as pd

import config as cfg

OUT = cfg.TABLES / "tables_latex.tex"
PAPER_COPY = cfg.ROOT / "paper" / "sections" / "tables_generated.tex"  # solo si existe el manuscrito


def fmt(x, d=0):
    return "--" if pd.isna(x) else f"{x:.{d}f}"


def times_table():
    t = pd.read_csv(cfg.TABLES / "t2_event_times.csv", index_col=0)
    rows = []
    groups = {"Induction": ["Reduced activity", "Loss of righting reflex (LORR)", "Loss of response to stimulus",
                            "Loss of pedal withdrawal reflex", "Adequate anaesthetic plane"],
              "Recovery": ["First movement", "Return of pedal reflex", "Return of righting reflex (RORR)",
                           "Sternal recumbency", "Ambulation", "Complete recovery"],
              "Duration": ["Duration of LORR (RORR − LORR)", "Duration of pedal reflex absence"]}
    for g, names in groups.items():
        rows.append(rf"\multicolumn{{5}}{{l}}{{\textit{{{g}}}}} \\")
        for n in names:
            r = t.loc[n]
            label = n.replace("−", "--")
            rows.append(f"\\quad {label} & {int(r.n)} & {fmt(r['median'])} ({fmt(r.q1)}--{fmt(r.q3)}) & "
                        f"{fmt(r['min'])}--{fmt(r['max'])} & {fmt(r.median_ci_lo)}--{fmt(r.median_ci_hi)} \\\\")
    body = "\n".join(rows)
    return rf"""\begin{{table}}[p]
\centering
\caption{{Induction and recovery times (minutes after intraperitoneal injection of propofol \SI{{7}}{{\milli\gram\per\kilo\gram}} and ketamine \SI{{50}}{{\milli\gram\per\kilo\gram}}) in 13 male guinea pigs.}}
\label{{tab:times}}
\small
\begin{{tabular}}{{lcccc}}
\toprule
Event & $n$ & Median (IQR) & Range & 95\% CI of median \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\par\smallskip\footnotesize IQR, interquartile range; CI, distribution-free confidence interval based on binomial order statistics.
\end{{table}}
"""


def adverse_table():
    t = pd.read_csv(cfg.TABLES / "t3_adverse_events.csv")
    rows = []
    for _, r in t.iterrows():
        ev = (r.event.replace("≥", r"$\geq$").replace("↓", r"$\downarrow$").replace("↑", r"$\uparrow$")
              .replace("°C", r"\si{\celsius}").replace("<", r"$<$").replace("%", r"\%").replace("min⁻¹", r"min$^{-1}$")
              .replace("SpO2", r"SpO$_2$").replace("†", r"$^{\dagger}$"))
        rows.append(f"{ev} & {r.k}/{r.n} & {fmt(r.pct)} & {fmt(r.ci_lo)}--{fmt(r.ci_hi)} \\\\")
    body = "\n".join(rows)
    return rf"""\begin{{table}}[p]
\centering
\caption{{Adverse events classified from the monitoring data with predefined thresholds (5--60 min after injection).}}
\label{{tab:adverse}}
\small
\begin{{tabular}}{{lccc}}
\toprule
Event & $k/n$ & \% & 95\% CI (exact) \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\par\smallskip\footnotesize Changes are relative to each animal's baseline. $^{{\dagger}}$Only animals with a physiologically plausible baseline SpO$_2$ ($\geq$90\%) while awake ($n=6$).
\end{{table}}
"""


def main():
    tex = "% Generado por src/make_tables.py — no editar a mano.\n" + times_table() + "\n" + adverse_table()
    OUT.write_text(tex)
    print(f"escrito {OUT.relative_to(cfg.ROOT)}")
    if PAPER_COPY.parent.exists():
        PAPER_COPY.write_text(tex)
        print(f"escrito {PAPER_COPY.relative_to(cfg.ROOT)}")


if __name__ == "__main__":
    main()
