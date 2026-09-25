"""Etapa 2: construye el conjunto de datos analítico a partir de la transcripción verificada.

Entradas: data/transcription/pass1/*.json + data/transcription/resoluciones.csv
Salidas (data/processed/):
  animals.csv      una fila por animal, variables derivadas listas para análisis
  monitoring.csv   formato largo (animal x tiempo) con signos vitales armonizados
  dataset.xlsx     ambas tablas + diccionario de datos
Cada corrección está documentada en docs/decisiones.md.
"""
import json
import re

import numpy as np
import pandas as pd

import config as C

# Correcciones puntuales verificadas contra el escaneo (ver resoluciones.csv y decisiones.md)
MONIT_FIXES = {  # (ficha, tiempo, variable): valor
    (3, "50", "temp"): 34.5,
    (13, "basal", "fc"): 255,
    (2, "15", "fr"): 85,
    (6, "5", "fr"): 105,
}
TIME_FIXES = {  # (ficha, campo): "HH:MM"
    (9, "disminucion_actividad"): "14:42",
}
VOLUME_FIXES = {  # confirmado por el equipo: 0,39 mL como el resto de grupos
    (4, "propofol_ml"): 0.39,
}
POST_WEIGHT_IMPLAUSIBLE = {8, 13}


def to_min(hhmm, t0):
    """Minutos desde T0. Acepta 'HH:MM' o duraciones '38 min' / '2:00 hrs' (ya relativas a T0)."""
    if hhmm is None or t0 is None:
        return np.nan
    s = str(hhmm).strip().lower()
    if "min" in s:
        return float(re.findall(r"[\d.]+", s)[0].rstrip("."))
    if "hr" in s:
        h, m = re.findall(r"\d+", s)[:2]
        return int(h) * 60 + int(m)
    if not re.fullmatch(r"\d{1,2}:\d{2}", s):
        return np.nan
    h, m = map(int, s.split(":"))
    h0, m0 = map(int, t0.split(":"))
    return (h * 60 + m) - (h0 * 60 + m0)


def grams(x):
    """Peso en gramos (algunas fichas lo escribieron en kg)."""
    if x is None:
        return np.nan
    x = float(x)
    return x * 1000 if x < 5 else x


def pedal_absent(code):
    """Armoniza el reflejo pedal a 1 = ausente, 0 = presente/disminuido, NaN = no interpretable."""
    if code is None or (isinstance(code, float) and np.isnan(code)):
        return np.nan
    s = str(code).strip().lower()
    if s in {"2", "ausente", "no"}:
        return 1.0
    if s in {"0", "1", "si", "sí", "normal", "moderado"}:
        return 0.0
    return np.nan


def relaxation_score(code):
    """Relajación muscular 0–2 (0 normal, 1 moderada, 2 marcada); SI/NO → 1/0; otros → NaN."""
    s = str(code).strip().lower() if code is not None else ""
    return {"0": 0, "1": 1, "2": 2, "normal": 0, "moderada": 1, "marcada": 2,
            "no": 0, "si": 1, "sí": 1}.get(s, np.nan)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def build():
    fichas = [json.loads(p.read_text()) for p in sorted((C.TRANSCRIPTION / "pass1").glob("ficha_*.json"))]
    animals, monit = [], []

    for d in fichas:
        f = d["ficha"]
        ind, rec, pre, post = d["induccion"], d["recuperacion"], d["preanestesia"], d["postanestesia"]
        for (ff, campo), v in TIME_FIXES.items():
            if ff == f:
                ind[campo] = v
        t0 = ind["administracion"] or d["administracion"]["hora"]
        w = grams(pre["peso_g"] or d["identificacion"]["peso_g"])

        vol_p = VOLUME_FIXES.get((f, "propofol_ml"), num(d["administracion"]["propofol_ml"]))
        vol_k = VOLUME_FIXES.get((f, "ketamina_ml"), num(d["administracion"]["ketamina_ml"]))

        # --- monitorización ---
        rows = {str(r["tiempo"]): r for r in d["monitorizacion"]}
        for t in C.TIMEPOINTS:
            r = rows.get(t, {})
            vals = {v: num(r.get(v)) for v in ("fc", "fr", "temp", "spo2")}
            if f == 6 and vals["fc"] < 10:  # FC escrita con punto: "2.76" = 276
                vals["fc"] = round(vals["fc"] * 100)
            for v in vals:
                vals[v] = MONIT_FIXES.get((f, t, v), vals[v])
            if t == "basal":  # fila basal vacía → evaluación preanestésica
                fallback = {"fc": pre["fc_lpm"], "fr": pre["fr_rpm"], "temp": pre["temp_c"], "spo2": pre["spo2_pct"]}
                vals = {v: vals[v] if not np.isnan(vals[v]) else num(fallback[v]) for v in vals}
            pa = pedal_absent(r.get("ref_pedal"))
            if t == "basal" and pa == 1.0:  # reflejo "ausente" en animal despierto: error de codificación
                pa = np.nan
            monit.append({"animal": f, "tiempo": t, "min": 0 if t == "basal" else int(t), **vals,
                          "pedal_ausente": pa, "relajacion": relaxation_score(r.get("relajacion")),
                          "plano_raw": r.get("plano"), "pedal_raw": r.get("ref_pedal")})

        # --- una fila por animal ---
        animals.append({
            "animal": f,
            "sesion": C.SESSIONS.get(d["identificacion"]["fecha"]),
            "fecha": d["identificacion"]["fecha"],
            "sexo": d["identificacion"]["sexo"],
            "peso_g": w,
            "procedencia": d["identificacion"]["procedencia"],
            "prop_vol_ml": vol_p,
            "ket_vol_ml": vol_k,
            "prop_mg_kg": vol_p * C.PROPOFOL_MG_ML / (w / 1000),
            "ket_mg_kg": vol_k * C.KETAMINE_MG_ML / (w / 1000),
            "vol_total_ml_kg": (vol_p + vol_k) / (w / 1000),
            # inducción (min desde T0)
            "t_disminucion_actividad": to_min(ind["disminucion_actividad"], t0),
            "t_perdida_enderezamiento": to_min(ind["perdida_enderezamiento"], t0),
            "t_perdida_estimulo": to_min(ind["perdida_respuesta_estimulo"], t0),
            "t_perdida_pedal": to_min(ind["perdida_reflejo_pedal"], t0),
            "t_plano_adecuado": to_min(ind["plano_adecuado"], t0),
            "calidad_induccion": ind["calidad"],
            # recuperación (min desde T0)
            "t_primer_movimiento": to_min(rec["primer_movimiento"], t0),
            "t_retorno_pedal": to_min(rec["reflejo_pedal"], t0),
            "t_retorno_enderezamiento": to_min(rec["enderezamiento"], t0),
            "t_esternal": to_min(rec["posicion_esternal"], t0),
            "t_ambulacion": to_min(rec["ambulacion"], t0),
            "t_recuperacion_completa": to_min(rec["completa"], t0),
            "calidad_recuperacion": num(str(rec["calidad"])[0]) if rec["calidad"] else np.nan,
            # post y seguimiento
            "post_temp": num(post["temp_c"]), "post_fc": num(post["fc"]),
            "post_fr": num(post["fr"]), "post_spo2": num(post["spo2"]),
            "peso_post_g": np.nan if f in POST_WEIGHT_IMPLAUSIBLE else grams(d["seguimiento"]["peso_posterior_g"]),
            "seguimiento_24h": d["seguimiento"]["h24"],
            # registro del operador (casillas marcadas, no se usan como resultado)
            "ea_marcados_operador": "; ".join(d["eventos_adversos"]["marcados"] or []),
            "eficacia_operador": d["resultado_final"]["eficacia"],
            "seguridad_operador": d["resultado_final"]["seguridad"] if isinstance(d["resultado_final"]["seguridad"], str)
            else "; ".join(d["resultado_final"]["seguridad"]),
        })

    a = pd.DataFrame(animals)
    m = pd.DataFrame(monit)

    # Duraciones derivadas
    a["dur_perdida_enderezamiento"] = a["t_retorno_enderezamiento"] - a["t_perdida_enderezamiento"]
    a["dur_ausencia_pedal"] = a["t_retorno_pedal"] - a["t_perdida_pedal"]

    # Basales y eventos adversos por umbral (lecturas intraanestésicas 5–60 min)
    base = m[m.tiempo == "basal"].set_index("animal")[["fc", "fr", "temp", "spo2"]].add_prefix("basal_")
    intra = m[m.tiempo != "basal"].groupby("animal")
    ext = pd.concat([base,
                     intra["temp"].min().rename("temp_min"), intra["fc"].min().rename("fc_min"),
                     intra["fc"].max().rename("fc_max"), intra["fr"].min().rename("fr_min"),
                     intra["spo2"].min().rename("spo2_min")], axis=1)
    a = a.merge(ext, left_on="animal", right_index=True)
    a["spo2_fiable"] = a["basal_spo2"] >= C.SPO2_RELIABLE_BASELINE
    a["temp_descenso_max"] = a["basal_temp"] - a["temp_min"]
    a["ea_hipotermia"] = a["temp_descenso_max"] >= C.HYPOTHERMIA_DROP_C
    a["ea_hipotermia_grave"] = a["temp_descenso_max"] >= C.HYPOTHERMIA_SEVERE_DROP_C
    a["ea_temp_menor_35"] = a["temp_min"] < C.HYPOTHERMIA_ABS_C
    a["ea_bradicardia"] = (a["fc_min"] <= a["basal_fc"] * (1 - C.BRADYCARDIA_REL)) | (a["fc_min"] < C.BRADYCARDIA_ABS)
    a["ea_taquicardia"] = a["fc_max"] >= a["basal_fc"] * (1 + C.TACHYCARDIA_REL)
    a["ea_bradipnea"] = a["fr_min"] <= a["basal_fr"] * (1 - C.BRADYPNEA_REL)
    a["ea_hipoxemia"] = (a["spo2_min"] < C.HYPOXEMIA_SPO2).where(a["spo2_fiable"])
    a["ea_hipoxemia_grave"] = (a["spo2_min"] < C.HYPOXEMIA_SEVERE_SPO2).where(a["spo2_fiable"])

    # Cambios respecto del basal en formato largo
    m = m.merge(base, left_on="animal", right_index=True)
    for v in ("fc", "fr", "temp", "spo2"):
        m[f"d_{v}"] = m[v] - m[f"basal_{v}"]
        m[f"pct_{v}"] = 100 * m[f"d_{v}"] / m[f"basal_{v}"]
    m = m.drop(columns=[c for c in m if c.startswith("basal_")])
    m = m.merge(a[["animal", "sesion", "peso_g", "spo2_fiable"]], on="animal")
    return a, m


def main():
    a, m = build()
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    a.to_csv(C.PROCESSED / "animals.csv", index=False)
    m.to_csv(C.PROCESSED / "monitoring.csv", index=False)
    with pd.ExcelWriter(C.PROCESSED / "dataset.xlsx") as xw:
        a.to_excel(xw, sheet_name="animales", index=False)
        m.to_excel(xw, sheet_name="monitorizacion", index=False)
    print(f"animals.csv: {a.shape} | monitoring.csv: {m.shape}")


if __name__ == "__main__":
    main()
