"""Aplana las transcripciones JSON (pasada 1) a tablas CSV/XLSX sin corregir valores.

Salidas en data/processed/:
  animals_raw.csv         una fila por ficha (campos tal como fueron escritos)
  monitoring_long_raw.csv una fila por ficha x tiempo (basal, 5 ... 60 min)
  flags.csv               valores dudosos marcados por el transcriptor
  dataset_raw.xlsx        las tres tablas + notas del transcriptor, una hoja cada una

Uso: .venv/bin/python src/build_dataset.py [pass1|pass2]
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PASS = sys.argv[1] if len(sys.argv) > 1 else "pass1"
SRC = ROOT / "data" / "transcription" / PASS
OUT = ROOT / "data" / "processed"


def flatten(d, prefix=""):
    """Aplana dicts anidados; las listas se guardan como texto separado por ' | '."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, f"{key}."))
        elif isinstance(v, list):
            out[key] = " | ".join(map(str, v)) if v else None
        else:
            out[key] = v
    return out


def main():
    fichas = [json.loads(p.read_text()) for p in sorted(SRC.glob("ficha_*.json"))]
    if not fichas:
        sys.exit(f"No hay fichas en {SRC}")

    animals, monitoring, flags, notes = [], [], [], []
    for d in fichas:
        fid = d["ficha"]
        skip = {"monitorizacion", "flags", "notas_transcriptor"}
        animals.append({"ficha": fid, **flatten({k: v for k, v in d.items() if k not in skip and k != "ficha"})})
        for row in d["monitorizacion"]:
            monitoring.append({"ficha": fid, **row})
        for fl in d["flags"]:
            flags.append({"ficha": fid, **fl})
        notes.append({"ficha": fid, "notas_transcriptor": d.get("notas_transcriptor")})

    animals = pd.DataFrame(animals)
    monitoring = pd.DataFrame(monitoring)
    flags = pd.DataFrame(flags)
    notes = pd.DataFrame(notes)

    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "" if PASS == "pass1" else f"_{PASS}"
    animals.to_csv(OUT / f"animals_raw{suffix}.csv", index=False)
    monitoring.to_csv(OUT / f"monitoring_long_raw{suffix}.csv", index=False)
    flags.to_csv(OUT / f"flags{suffix}.csv", index=False)
    with pd.ExcelWriter(OUT / f"dataset_raw{suffix}.xlsx") as xw:
        animals.to_excel(xw, sheet_name="animales", index=False)
        monitoring.to_excel(xw, sheet_name="monitorizacion", index=False)
        flags.to_excel(xw, sheet_name="flags", index=False)
        notes.to_excel(xw, sheet_name="notas", index=False)

    print(f"{len(animals)} fichas, {animals.shape[1]} columnas | "
          f"{len(monitoring)} filas de monitorización | {len(flags)} flags")


if __name__ == "__main__":
    main()
