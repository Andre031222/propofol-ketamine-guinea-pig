"""Ejecuta el pipeline completo, de las transcripciones verificadas a las tablas y figuras.

    python src/run_all.py

1. build_dataset.py  JSON (pasadas 1 y 2) -> tablas crudas
2. compare_passes.py concordancia de la doble transcripción
3. clean.py          conjunto analítico (animals.csv, monitoring.csv)
4. analysis.py       modelos mixtos, Friedman, IC, figuras principales
5. figures_extra.py  figura del diseño y figuras suplementarias
6. make_tables.py    tablas en LaTeX
"""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
STEPS = [("build_dataset.py", ["pass1"]), ("build_dataset.py", ["pass2"]), ("compare_passes.py", []),
         ("clean.py", []), ("analysis.py", []), ("figures_extra.py", []), ("make_tables.py", [])]

for script, args in STEPS:
    print(f"\n== {script} {' '.join(args)}")
    sys.argv = [script, *args]
    runpy.run_path(str(SRC / script), run_name="__main__")
print("\nPipeline completo.")
