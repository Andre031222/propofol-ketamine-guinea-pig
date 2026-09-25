"""Constantes del estudio: rutas, concentraciones, umbrales de eventos adversos definidos a priori.

Valores de referencia del cobayo (adulto, despierto): FC 230–380 lpm, FR 42–104 rpm,
T° 37,2–39,5 °C (Quesenberry & Carpenter, Ferrets, Rabbits and Rodents, 4.ª ed.).
Los umbrales se fijaron durante el manejo de datos (tras ver los datos crudos) y antes del análisis estadístico; así se declara en Métodos.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTION = ROOT / "data" / "transcription"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "analysis" / "figures"
TABLES = ROOT / "analysis" / "tables"

TIMEPOINTS = ["basal", "5", "10", "15", "20", "30", "40", "50", "60"]

# Concentraciones comerciales (mg/mL)
PROPOFOL_MG_ML = 10.0
KETAMINE_MG_ML = 100.0

# Sesiones experimentales (fecha -> etiqueta)
SESSIONS = {"2026-09-08": "S1", "2026-09-11": "S2", "2026-09-16": "S3"}

# Umbrales de eventos adversos (evaluados en las lecturas intraanestésicas 5–60 min)
HYPOTHERMIA_DROP_C = 1.0          # descenso ≥ 1,0 °C respecto del basal
HYPOTHERMIA_SEVERE_DROP_C = 2.0   # descenso ≥ 2,0 °C
HYPOTHERMIA_ABS_C = 35.0          # T° absoluta < 35,0 °C
BRADYCARDIA_REL = 0.20            # FC ↓ ≥ 20 % respecto del basal
BRADYCARDIA_ABS = 200             # o FC < 200 lpm
TACHYCARDIA_REL = 0.20            # FC ↑ ≥ 20 %
BRADYPNEA_REL = 0.50              # FR ↓ ≥ 50 % respecto del basal
HYPOXEMIA_SPO2 = 90               # SpO₂ < 90 %
HYPOXEMIA_SEVERE_SPO2 = 80        # SpO₂ < 80 %
SPO2_RELIABLE_BASELINE = 90       # basal < 90 % en animal despierto → lectura no fiable
