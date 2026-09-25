# Registro de decisiones de datos

Toda corrección aplicada en `src/clean.py` debe figurar aquí con su justificación.
Los JSON de `data/transcription/` nunca se modifican: reflejan lo escrito en las fichas.

## Información confirmada por el equipo (2026-09-24)
- **Ficha 4:** el volumen de propofol administrado fue 0,39 mL, igual que el resto de grupos
  (confirmado por el equipo). El valor 0,039 mL de la ficha es un error de registro.
- **Pulsioxímetro:** equipo genérico de uso humano/veterinario, oxímetro de dedo de uso humano, tipo JZK-301 (foto enviada por el equipo); sensor en el
  miembro torácico (pata delantera). No validado en cobayos.
- FC: estetoscopio, latidos contados en 15 s × 4 (confirmado por el equipo). Independiente del oxímetro.
- Animales: cuy criollo (nativo andino), no cepa de laboratorio (confirmado por el equipo).
- Oxímetro: el equipo indica que se usa también en animales, adaptado a la extremidad. → la SpO₂ se interpreta con validez limitada.
- Curso: Farmacología y Terapéutica Veterinaria I, Facultad de Medicina Veterinaria y Zootecnia.
  Responsable: veterinario del curso Mario Rubén. Protocolo redactado por R. [redacted] .
- **Aprobación ética: pendiente de confirmar.** Requisito para cualquier revista indexada.

## Verificación de la transcripción
- Doble transcripción independiente (P1, P2): 1742 campos, concordancia 98,5 %; las diferencias
  restantes son de formato salvo 3 valores, resueltos contra el escaneo.
- Tercera fuente: transcripción externa (`data/external/`): 468 valores de signos vitales,
  12 diferencias (97,4 %); 9 a favor de P1/P2, 3 a favor de la externa. Ver `resoluciones.csv`.

## Tiempo
- **T0 = hora de inyección IP** (sección F, "Administración"). Todos los tiempos de inducción y
  recuperación se expresan en minutos desde T0.
- La "hora de suspensión anestésica" no se usa: con un bolo único no hay suspensión real, y el campo
  se llenó de forma inconsistente (vacío, igual a T0, o posterior a eventos de recuperación).
- Horas sin am/pm: asignadas a la tarde en las sesiones del 08/09 (todas las fichas del mismo día
  comienzan ~14:00).
- Ficha 2: la recuperación se registró como duraciones ("38 min"). Se interpretan desde T0:
  concuerda con la tabla de monitorización (reflejo pedal 0 a los 40 min).
- Ficha 9: "disminución de actividad" 14:12 es anterior a T0 (14:40) → se usa 14:42
  (lectura alternativa del mismo trazo; 1 ↔ 4).
- Ficha 8: "plano adecuado" contiene "I" (no es una hora) → dato faltante.
- Secuencias fuera de orden (p. ej. pérdida del pedal antes que la del enderezamiento, ficha 4)
  se mantienen tal como se registraron y se informan.

## Dosis
- Dosis real (mg/kg) = volumen administrado × concentración comercial / peso (kg), con
  propofol 10 mg/mL y ketamina 100 mg/mL (concentraciones declaradas en 12/13 fichas).
- Ficha 1 escribió concentración 7 mg/mL y dosis 10 mg/kg de propofol (campos invertidos respecto al
  resto); su volumen (0,42 mL) corresponde a 6,9 mg/kg → mismo protocolo.
- Peso para el cálculo: peso preanestésico en gramos (varias fichas lo escribieron en el campo "kg").

## Signos vitales
- Ficha 6: la FC se escribió con punto ("2.76") → 276 lpm.
- Basal: fila "Basal" de la tabla de monitorización; si falta (ficha 9) se usa la evaluación
  preanestésica.
- SpO₂: se marca como **no fiable** cuando la SpO₂ basal en el animal despierto es < 90 %
  (imposible fisiológicamente en un animal sano en reposo → fallo de lectura del equipo).
  Análisis principal de SpO₂ solo con animales de basal fiable; análisis de sensibilidad con todos.

## Profundidad anestésica
- Resultados principales de eficacia = tiempos de eventos (pérdida/recuperación del reflejo de
  enderezamiento y del reflejo pedal), registrados como horas en las 13 fichas.
- Reflejo pedal en la tabla: armonizado a binario "ausente" (sí/no):
  0/1/2 (protocolo: 2 = ausente); SI/NO (SI = presente); palabras (Ausente / no = ausente).
  Ficha 9 (X/✓ sin definición) → faltante.
- Filas basales que indican reflejo ausente en el animal despierto (fichas 5, 7, 10, 13) → faltante
  (error de codificación); se informa.
- Columna "Plano": codificación heterogénea (Δ, I–III, 1–3, palabras) → solo descriptiva.

## Eventos adversos (definidos por umbral, no por las casillas marcadas; umbrales fijados durante el manejo de datos, antes del análisis estadístico — NO a priori)
Las casillas de eventos adversos se contradicen con los datos en la mayoría de fichas
(p. ej. "Ninguno" marcado con SpO₂ 45–61 %). Se reclasifican con umbrales basados en valores de referencia
(ver `src/config.py`). Las casillas originales se informan aparte como "registro del operador".

## Peso posterior
- Ficha 6: "0.534" → 534 g. Fichas 8 (475 g, −14 %) y 13 (430 g, −14 %) → implausibles en 24 h;
  se informan, no se analizan como resultado.