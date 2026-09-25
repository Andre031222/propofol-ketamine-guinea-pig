"""Compara la transcripción pasada 1 vs pasada 2 (doble digitación) campo por campo.

Salida: data/processed/discrepancias.csv con ficha, campo, valor_p1, valor_p2.
Los campos de texto libre (observaciones, notas, nombres) se excluyen: solo se comparan
los campos que entran en el análisis.
Imprime la tasa de concordancia global y por sección.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "data" / "transcription"
OUT = ROOT / "data" / "processed"

FREE_TEXT = ("observaciones", "descripcion", "justificacion", "notas_transcriptor", "flags",
             "investigadores", "procedencia", "tecnica", "intervencion", "mucosas",
             "condicion_corporal", "medidas", "resultado", "causa", "paginas", "items_no_marcados")


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, f"{key}."))
        elif k == "monitorizacion":
            for row in v:
                t = row.get("tiempo")
                out.update({f"monit.{t}.{c}": x for c, x in row.items() if c != "tiempo"})
        elif isinstance(v, list):
            out[key] = sorted(map(str, v))
        else:
            out[key] = v
    return out


def norm(x):
    """Normaliza para comparar: números como float, textos en minúsculas sin espacios extremos."""
    if x is None or x == "" or x == []:
        return None
    if isinstance(x, list):
        return tuple(s.strip().lower() for s in x)
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return str(x).strip().lower()


def main():
    rows = []
    for p1 in sorted((T / "pass1").glob("ficha_*.json")):
        p2 = T / "pass2" / p1.name
        if not p2.exists():
            print(f"falta pasada 2: {p1.name}")
            continue
        a, b = flatten(json.loads(p1.read_text())), flatten(json.loads(p2.read_text()))
        for k in sorted(set(a) | set(b)):
            if any(ft in k for ft in FREE_TEXT):
                continue
            rows.append({"ficha": int(p1.stem[-2:]), "campo": k,
                         "valor_p1": a.get(k), "valor_p2": b.get(k),
                         "coincide": norm(a.get(k)) == norm(b.get(k))})

    df = pd.DataFrame(rows)
    df["seccion"] = df["campo"].str.split(".").str[0]
    disc = df[~df["coincide"]].drop(columns="coincide")
    disc.to_csv(OUT / "discrepancias.csv", index=False)

    print(f"Campos comparados: {len(df)} | concordancia global: {df['coincide'].mean():.1%} "
          f"| discrepancias: {len(disc)}")
    print(df.groupby("seccion")["coincide"].agg(["size", "mean"]).round(3).to_string())


if __name__ == "__main__":
    main()
