# Esquema de transcripción — una ficha = un archivo `ficha_XX.json`

Reglas:
- Transcribir **exactamente lo escrito** (no corregir cálculos ni unidades). Correcciones van en la etapa de limpieza (`src/clean.py`).
- Horas en formato `"HH:MM"` 24 h. Valor vacío/no llenado → `null`.
- Casillas: guardar la opción marcada como texto; ninguna marcada → `null`.
- Cualquier valor dudoso: registrarlo igual y añadir entrada en `flags`
  (`{"campo": "...", "leido": "...", "alternativa": "...", "motivo": "..."}`).
- `paginas`: números de página del PDF (1–104) que componen la ficha.

```json
{
  "ficha": 1,
  "paginas": [1,2,3,4,5,6,7,8],
  "identificacion": {
    "codigo_estudio": null, "codigo_animal": null,
    "fecha": "2026-09-16", "hora_inicio": "07:08",
    "investigadores": ["...", "..."],
    "sexo": "Macho", "peso_g": 609, "procedencia": "..."
  },
  "preanestesia": {
    "peso_g": 609, "temp_c": 34.1, "fc_lpm": 220, "fr_rpm": 110, "spo2_pct": 98,
    "mucosas": "...", "hidratacion": null, "condicion_corporal": "...",
    "estado_general": "Bueno", "evaluacion_clinica": "Animal aparentemente sano",
    "observaciones": "..."
  },
  "checklist": {"todo_preparado": "SI", "items_no_marcados": []},
  "calculo": {
    "peso_escrito": "609", "peso_unidad_impresa": "kg",
    "propofol": {"conc_mg_ml": 7, "dosis_mg_kg": 10, "dosis_mg": 4.263, "vol_ml": 0.42},
    "ketamina": {"conc_mg_ml": 100, "dosis_mg_kg": 50, "dosis_mg": 30.45, "vol_ml": 0.30}
  },
  "administracion": {
    "hora": "07:10", "tecnica": "...",
    "propofol_ml": 0.42, "ketamina_ml": 0.30, "observaciones": "..."
  },
  "induccion": {
    "administracion": "07:10", "disminucion_actividad": "07:12",
    "perdida_enderezamiento": "07:13", "perdida_respuesta_estimulo": "07:13",
    "perdida_reflejo_pedal": "07:14", "plano_adecuado": "07:14",
    "calidad": "Muy buena"
  },
  "monitorizacion": [
    {"tiempo": "basal", "fc": 220, "fr": 110, "temp": 34.1, "spo2": 98, "ref_pedal": "0", "relajacion": "0", "plano": "Vigilia"},
    {"tiempo": "5", "...": "..."}
  ],
  "escala_profundidad": {
    "movimiento": 2, "enderezamiento": 2, "reflejo_pedal": 2, "relajacion": 1,
    "evaluacion_global": "Plano adecuado"
  },
  "eventos_adversos": {
    "marcados": ["Hipotermia"], "otro": null,
    "descripcion": "...", "intervencion": null
  },
  "suspension": {"presento": "No", "causa": null, "hora": null, "medidas": null, "resultado": null},
  "recuperacion": {
    "hora_suspension": null,
    "primer_movimiento": "08:19", "reflejo_pedal": "08:34", "enderezamiento": "08:34",
    "posicion_esternal": "08:35", "ambulacion": "08:43", "completa": "09:30",
    "calidad": null
  },
  "postanestesia": {
    "temp_c": 33.8, "fc": 210, "fr": 102, "spo2": 97,
    "actividad": "Disminuida", "postura": "Normal", "apetito": "Disminuido",
    "agua": "Disminuido", "heces": "Normal", "respiracion": "Normal",
    "dolor": "No evidente", "conducta": null
  },
  "seguimiento": {"h1": "Normal", "h2": "Normal", "h4": "Normal", "h24": "Normal",
                   "peso_posterior_g": 608, "observaciones": "..."},
  "resultado_final": {
    "eficacia": "Excelente", "seguridad": "Sin eventos adversos",
    "recuperacion": "Excelente", "satisfactorio": "SI", "justificacion": "..."
  },
  "fecha_firma": "2026-09-16",
  "notas_transcriptor": "texto libre: tachones, anotaciones al margen, páginas fuera de orden, etc.",
  "flags": []
}
```
