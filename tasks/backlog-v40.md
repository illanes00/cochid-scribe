# Backlog v4.0 — Informe Medicamentos CIF-EP

**Objetivo:** dejar el informe listo, publicable, con todos los cambios del feedback Martín 7-may.
**Plazo aspiracional:** próximas 2-3 horas con agentes paralelos.
**Fuente del feedback:** `feedback-2026-05-07-leyendo-esqueleto.md` y `feedback-2026-05-07-respuestas.md`.

---

## Arquitectura del trabajo paralelo

Cada agente recibe:
- **Texto actual** de su capítulo (extraído de v3.18) en `/tmp/v40-context/cap-X.md`
- **Feedback específico** del usuario para su capítulo
- **Estilo Espacio Público** (apertura afirmativa, conectores formales, sin em-dashes, sin antítesis "no es A, sino B", tono técnico-declarativo)
- **Datos disponibles** (rutas a CSVs, scripts, cifras verificadas)
- **Salida esperada:** archivo `.md` con texto nuevo por sub-sección, listo para reemplazar bloques en el .docx vía tracked changes

Ningún agente escribe en el .docx. Yo consolido todo en `build_v4_0.py` al final.

---

## Tareas (8 paquetes paralelos + integración secuencial)

### Pack A — Cap 2 (Acceso a medicamentos en Chile) [Agent CAP2]
**Insumos:**
- v3.18 Cap 2 actual
- Feedback: sacar MLE de tabla protección (canal, no instrumento), agregar CAEC con gap (CAEC es seguro adicional, NO red Isapre), ampliar Cenabast Ley 21.198 con datos 2024, explicitar Servicios de Salud 60,8%, vía judicial $81.000M, GES sin glosa, agregar farmacia municipal como canal, distinguir instrumento de cobertura / canal de acceso / financiamiento / esquema institucional, listar todas las leyes (incluida reducción IVA medicamentos, sin tomar partido), aclarar Plan SU / Fármacos III / PUMA / Lista Positiva
- Datos: cubo OMS por programa con presupuestos verificables (en `feedback-2026-05-06/04-anexo-metodologico-v318.md`)

**Salida:** `/tmp/v40-context/output/cap2.md` con sub-secciones:
- 2.1 Canales de acceso (4 canales: retail comercial, APS pública, intra-hospitalario, **farmacia municipal**)
- 2.2 Instrumentos de cobertura (con tabla maestra)
- 2.3 Financiamiento y ejecutores
- 2.4 Matriz cobertura × subsistema × canal (con CAEC bien clasificado)
- 2.5 Otros esfuerzos pro-competencia (Cenabast, Ley genéricos II, IVA reducido)
- 2.6 Propuestas de reforma (Plan SU, Fármacos III, PUMA, Lista Positiva, aclaradas)

### Pack B — Cap 3 (Ruta + puntos de quiebre) [Agent CAP3]
**Insumos:**
- v3.18 Cap 3 actual
- Feedback: "principales mecanismos" (no "los seis"), NO adelantar BFU acá (eso va al Cap 7), 3.2.4 ampliar precio alto (gente que no tiene cómo pagar), 3.3 ETESA con cita y vinculación, 3.4 quitar mención "beneficio común" (es propuesta, esto es diagnóstico)
- Comentario DOCX54 del usuario: la articulación BFU/MLE/MAI debe estar en Cap 7, no acá

**Salida:** `/tmp/v40-context/output/cap3.md` con:
- 3.1 Ruta (5 etapas)
- 3.2 Puntos de quiebre (los 6 principales, sin presentar BFU)
- 3.3 ETESA con justificación citada
- 3.4 Implicancias para diseño (sin proponer beneficio común)

### Pack C — Cap 4 (Diagnóstico cuantitativo) [Agent CAP4]
**Insumos:**
- v3.18 Cap 4 actual
- Feedback: aclarar retail = ambulatorio, sacar siglas crípticas (HF3/HC51), 71% retail explicado como "gasto de hogares declarado en OECD sobre meds en farmacia", 62% como "gasto de hogares incluyendo hospitalarios", aclarar si 62% incluye solo meds hospitalarios o también hospitalizaciones, mencionar dos lentes, sacar también % hospitalario sobre total (mostrar que ahí hay menos problema), gráficos continuos (no por quintil), comparativa con CIF/UC explícita (los autores son amigos pero quizás no fueron tan prolijos como nosotros)
- Datos: EPF IX 2021-2022 procesada, OECD SHA, CIF/UC 2025

**Salida:** `/tmp/v40-context/output/cap4.md` con:
- 4.1 Magnitud y composición — apertura natural sin siglas, doble cifra explicada
- 4.2 Distribución del gasto en hogares — gráficos continuos, no quintiles

### Pack D — Cap 5 (Comparación internacional) [Agent CAP5]
**Insumos:**
- v3.18 Cap 5 actual
- Feedback: 13 países OCDE muestran círculo de arquetipos, hablar de elementos combinables, sin sesgo, ejemplos claros, explicaciones detalladas
- Datos: `paises_oecd_clean.csv`, `tabla_oecd_paises.csv` en `feedback-2026-05-06/`

**Salida:** `/tmp/v40-context/output/cap5.md` con:
- 5.1 Criterios de selección
- 5.2 Modelos de protección (5 arquetipos + elementos combinables)
- 5.3 Lecciones para Chile (6 sub-lecciones)
- 5.4 Síntesis comparada — tabla principal nueva con público total / PIB

### Pack E — Cap 6 (Escenarios) [Agent CAP6]
**Insumos:**
- v3.18 Cap 6 actual
- Feedback: explicar qué es cada escenario (E1: tope hogar o aumentar LRS?), conectar con clusters fiscales (cluster 0,5% PIB · Chile 0,4% · subir 0,1% = 400-500M USD), mostrar metodología explícita, ¿con E2 alcanza para BFU? ¿en qué se diferencia E3 de E2 si E2 ya alcanza para universal?, datos EPF + CASEN + peticiones LRS
- Datos: scripts `calc_complete.py`, `calc_v2_oecd_first.py`, `calc_v3_grafico.py` en `feedback-2026-05-06/`

**Salida:** `/tmp/v40-context/output/cap6.md` con:
- 6.1 Variables de diseño
- 6.2 Tres escenarios con cálculo y conexión a clusters
  - E1: ajuste gradual (qué significa concretamente)
  - E2: convergencia intermedia OCDE (BFU)
  - E3: convergencia plena
- 6.3 Implicancias distributivas

### Pack F — Cap 7 (BFU detallado) [Agent CAP7]
**Insumos:**
- v3.18 Cap 7 actual
- Feedback: "red de seguridad / security net" en lugar de "piso universal", articulación BFU/MLE/MAI/CAEC con precisión (DOCX54), BFU actúa sobre retail Y hospitalario (DOCX56), tope para todos los meds y todo el gasto de bolsillo (DOCX57), tope 13-15% calculado con convergencia OCDE = aumento presupuesto (verificar), mencionar restricciones de la estimación (elasticidad consumo: si meds más baratos → más consumo), mencionar cómo BFU se podría aumentar en E3 o qué elementos en E1, hablar más de los otros escenarios

**Salida:** `/tmp/v40-context/output/cap7.md` con todas las sub-secciones detalladas

### Pack G — Cap 8 + Mensajes Clave + RE [Agent CAP8]
**Insumos:**
- v3.18 Cap 8 + Mensajes + RE actuales
- Feedback: preguntas SIN respuesta obvia (filosóficas, políticas, no respondibles con razonamiento puro), quitar Q1 (fuente unificada), mantener Q3 (unidad tope), no tan importante Q4 (clasificación), cambiar Q5 a "rol farmacias" (provisión pública vs farmacia con compensación vs devolución impuestos en vivo), agregar provisión pública vs privada, qué pasa con bioequivalentes, criterios priorización
- Mensajes clave: nombrar instrumentos por nombre y sus limitaciones, "varios países OCDE" no "todos", condiciones múltiples (no solo transparencia)
- RE: sacar mención BFU como propuesta en intro

**Restricción de extensión (importante):**
- **Mensajes clave: máximo 1 página** (~3.500 caracteres, ~600 palabras). Síntesis tipo bullets + texto corto. Hoy ocupa más de una plana — hay que **acortarlo**.
- **Resumen Ejecutivo: más largo que hoy** (objetivo ~3-4 páginas, ~1.800-2.500 palabras). Cubre diagnóstico + comparado + propuesta + horizontes + preguntas, con el detalle suficiente para que un lector que solo lea el RE entienda todo.

**Salida:** `/tmp/v40-context/output/cap8-mensajes-re.md` con:
- Mensajes clave reformulados (~10 mensajes en 1 página)
- Resumen ejecutivo expandido (3-4 páginas)
- Cap 8.1 horizontes
- Cap 8.2 preguntas filosóficas/políticas (5-6 preguntas con criterios)

### Pack H — Anexo 4 metodológico nuevo [Agent ANEXO4]
**Insumos:**
- Borrador en `feedback-2026-05-06/04-anexo-metodologico-v318.md`
- Feedback: cuadro doble entrada con desagregación completa del gasto, KPIs e indicadores Chile, mostrar datos brutos para cada cifra

**Salida:** `/tmp/v40-context/output/anexo4.md` con ~3pp:
- Marco SHA + dos cifras
- Cubo OMS aplicado a Chile (tabla por programa)
- EPF cálculo por quintil
- Calibración tope BFU
- Cuadro doble entrada gasto del Estado / privado / público / bolsillo

---

## Tareas que hago YO (en paralelo a los agentes)

### TAREA 1 — Limpieza patrones IA sobre v3.18 (los 6 skipped del v3.19)
- "no es un fenómeno colateral ni marginal: es un síntoma" → ajustar matching laxo
- "no es un fenómeno homogéneo: responde a dos frentes" → idem
- "no solo definir beneficios, sino asegurar" → idem
- "Una opción priorizada para la discusión" → idem
- "los países que han reducido" → idem
- En-dashes (–) revisar caso por caso (algunos son rangos legítimos)

### TAREA 2 — Bibliografía
Agregar 5 referencias al final del informe:
- Aguilera & Castillo (UDD 2022) — Ruta del medicamento
- Bitrán R. (2018) — Salud y medicamentos LatAm
- Vargas-Pelaez et al. (2019) — Int J Equity Health
- Kirchlechner & Cohen (2025) — biosimilares
- CIF/UC 2025 — Caracterización Gasto Público Medicamentos (2da ed.)

### TAREA 3 — DEFER residuales matizados
Reformular replies según feedback:
- DOCX47: "CAEC no es red de Isapre, es seguro adicional. FONASA MLE puede atenderse en red privada"
- DOCX53: aclarar cuál de las 4 (Plan SU / Fármacos / PUMA / Lista Positiva)
- DOCX54: mover articulación BFU/MLE/MAI al Cap 7
- DOCX56: BFU sobre retail Y hospitalario
- DOCX57: tope para todos los meds, todo OOP

### TAREA 4 — Numeración tarjetas país
Numerar individualmente Tarjeta 2 a 23 + mantener referencia agrupada en intro

### TAREA 5 — Figuras
- Figura 3 y 4: convertir de quintiles a continuo
- Figura nueva: composición OOP por quintil con simulación BFU
- Figura nueva: comparación países HF1/HF2/HF3
- Figuras 1, 2, 5: validar leyendas

---

## Integración (secuencial, post-agentes)

### INTEGRA-1 — build_v4_0.py
- Para cada capítulo: leer .md devuelto por agente → identificar bloques de v3.18 a reemplazar → generar tracked changes con autor "Martín Illanes" fecha 2026-05-07
- Aplicar limpiezas de TAREAS 1-5
- Generar `informe-final-v4.0.docx` + `informe-final-v4.0-aceptada.docx`

### INTEGRA-2 — Subida a Drive
- `[CIF-EP v4.0 SUGERENCIAS]` y `[CIF-EP v4.0 LIMPIA]`
- Actualizar URLs en cif-review

### INTEGRA-3 — Actualización cif-review
- Capturar respuestas del usuario en página nueva
- Marcar 02-informe como "respondido por Martín 7-may"
- Mostrar v4.0 como versión actual

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Agente devuelve texto fuera de estilo EP | Cada prompt incluye reglas estilo EP + ejemplos |
| Texto nuevo no calza con texto viejo (no se puede aplicar como tracked change) | El agente devuelve mapping {bloque_viejo → bloque_nuevo}; si bloque_viejo no existe literal, fallback: insertar como párrafo nuevo y marcar el bloque viejo como deletion |
| Cifras nuevas inventadas | Agente usa solo cifras verificadas del Anexo 4 borrador o pide flag de "verificar" |
| Tiempo: agentes demoran más de lo esperado | Lanzo todos en background simultáneo; trabajo en paralelo en TAREAS 1-5 |
| Conflictos entre capítulos (ej. Cap 7 menciona algo que Cap 6 cambió) | Yo reviso al integrar; los agentes que se solapan (3-4 y 6-7) los lanzo como pares |

---

## Cronograma estimado

- T+0 a T+5 min: extraer texto v3.18 por capítulo → `/tmp/v40-context/`
- T+5 a T+10 min: lanzar 8 agentes en background con sus contextos
- T+10 a T+60 min: agentes corriendo · yo en TAREAS 1-5
- T+60 a T+120 min: agentes terminan + integración build_v4_0.py
- T+120 a T+150 min: validación, subida Drive, actualización cif-review
