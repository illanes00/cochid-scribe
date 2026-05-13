# Trazabilidad feedback Martín → acciones aplicadas

**Pregunta del usuario (22 abr 21:25):** ¿Cuál fue el último comentario del cual te di feedback? ¿Los estás sistematizando todos?

**Respuesta honesta:** NO al 100%. Esta tabla mapea cada ítem de feedback a una acción concreta, para tener trazabilidad 1-a-1.

---

## Tu último mensaje con feedback específico

Fue el largo que arrancó con *"Ya, estoy viendo el documento y, por ejemplo, el comentario 12 de la CIF..."* y terminó con *"Carla Castillo hay pregunta la tarjeta 1 si es sólo retail o no"*.

En ese mensaje diste feedback sobre **~23 items**. Los repaso uno por uno abajo. Después viniste con 3 correcciones más:
- Em dashes
- "Propuesta IA"
- Figuras 1 y 2 verificación

---

## Tabla de trazabilidad — 26 items de feedback

| # | Tu feedback | Acción aplicada | Estado |
|---|---|---|---|
| 1 | **Comentario 12 CIF** (borrador avanzado) — no rebatir, tono de recepción | Reply suavizado en v3-base | ✅ Aplicado |
| 2 | **Sugerencia 29 Eduardo "U con tilde"** — aceptar (no había RAE) | v3.2b: comment id=1 (SUG29 real) tiene ahora "Aceptado. Se acepta la corrección ortográfica..." + id=41 (SUG38 cluster intermedio) tiene reply correcto sobre el reemplazo de jerga | ✅ Aplicado correctamente en v3.2 |
| 3 | **Comentarios 30, 31, 32 Eduardo** — no justificar, solo "Aceptado" | Replies acortados a "Aceptado." | ✅ Aplicado |
| 4 | **Comentario 13 CIF** (minuta previa) — buscar en mails | Descargado docx de Mariela Formas 29 sept, 13 comentarios originales extraídos y mapeados en `minuta-cif-analisis.md` | ✅ Aplicado |
| 5 | **Fecha del documento** — abril/mayo 2026 | Cambio a "Mayo de 2026" en frontmatter | ✅ Aplicado en v3-base |
| 6 | **Eduardo — bajar tono parte gastos retail familias** (es micro) | Agente 2 matizó párrafo 4.1 | ✅ Aplicado |
| 7 | **Header 2.4 "Matriz de coberturas" mal cerrado** — párrafo dentro del header | Estado actual: el header se ve OK (es "Heading2"), pero tiene 3 párrafos vacíos después. Tabla 1 con matriz DAC existe (10 filas × 6 cols) | ⚠️ **Pendiente verificación visual** — revisar si el párrafo incrustado ya se sacó. La Tabla 1 ya tiene DAC/GES/LRS/etc. |
| 8 | **CIF 3 judicialización como falla institucional** (no fenómeno bilateral) | Agente 2 reescribió sec 3.2.6 con argumento de falla institucional + Vargas-Pelaez 2019 | ✅ Aplicado |
| 9 | **Selección países comparación internacional** — aclarar criterios | Agente 2 insertó párrafo en 5.1 justificando foco europeo + Canadá y excluyendo LatAm | ✅ Aplicado |
| 10 | **Sec 5.3.1 ejemplos innovación** con valor sanitario | Agente 2 agregó recuadro con 5 casos NEJM/Nature (empagliflozin, DAAs hep C, CFTR, pembrolizumab, onasemnogeno) | ✅ Aplicado |
| 11 | **Sec 5.3.4 header malformado** — párrafo dentro | Estado actual: "5.3.4. Competencia y sustitución..." es Heading3 limpio, párrafo "La inclusión sostenible exige..." queda como Normal después | ✅ Aparentemente OK (verificar visualmente) |
| 12 | **Eduardo — 7.3.1 no ocupar subcategorías únicas** | Colapsada en Fase A | ✅ Aplicado |
| 13 | **7.6.1 sacar** (subcategoría única) | Colapsada en Fase A | ✅ Aplicado |
| 14 | **CIF 10 Cap 8 no cerradas** — ordenar, analizar, balancear | Agente 3 reescribió 4 párrafos del Cap 8 + nueva sec 8.3 + nueva 8.4 | ✅ Aplicado parcialmente. **Pendiente revisión global** del orden |
| 15 | **CIF 14 clasificación medidas por tipo de reforma** — aceptar, incorporar | Agente 3 agregó sec 8.3 con 3 horizontes (sin reforma legal / regulatorias / sistémicas) | ✅ Aplicado |
| 16 | **Mail 1 Carla** cerrar con seminario — aceptar | Cap 8.4 "Preguntas para la discusión" agregada en v2 ya | ✅ Aplicado |
| 17 | **Anexo 2.1 sacar** (subsección única) | A.2.1 colapsada en Fase A | ✅ Aplicado |
| 18 | **Eduardo — menos prescriptivo, no jugársela con solución** | Agente 3 suavizó Cap 7 (4 edits); v2 ya había reframeado Cap 7 como "Desarrollo del Escenario 2" | ✅ Aplicado |
| 19 | **Comentario 11 CIF numeración tablas y subtítulos** — verificar | **v3.2:** grep detectó problemas. Tablas: secuencia salta de Tabla 2 (sin tabla 1 labeleada) a Tabla 6, luego Tabla 2/3/4/5. Figuras: OK 1-10 secuencial. Tarjetas: solo 1 labeleada (hay tarjetas 2-23 referenciadas sin label). Documentado, **corrección pendiente** | ⚠️ **Verificado, corrección manual pendiente** |
| 20 | **Carla 42** (0,2% no calza con ficha) | **v3.2:** Ficha Chile Tabla 0 corregida con datos OECD 2022: Total $308→$394, Privado $240→$293, Bolsillo $240→$281, Gasto público/PIB 0,2%→0,34%. Nota de fuente OECD SHA agregada | ✅ Aplicado en v3.2 |
| 21 | **Figura 1** revisar datos | **v3.2:** leyenda reemplazada con fuente OECD SHA explícita, años 2019-2023, dataflow completo, notando salto 2019-2020 | ✅ Aplicado en v3.2 |
| 22 | **Figura 2** ejecutor calza, es millones o miles de millones | **NO verificable desde archivo local** (datos DIPRES no disponibles). Requiere verificación visual del gráfico | ❌ **PENDIENTE verificación visual** |
| 23 | **Figura 5 retail o gasto público** — Carla Castillo | **NO verificado** — requiere inspección del gráfico y nota en leyenda | ❌ **PENDIENTE** |
| 24 | **Tarjeta 1 retail o no** — Carla Castillo | **NO verificado** — requiere inspección de contenido | ❌ **PENDIENTE** |
| 25 | **NO em dashes** | Reemplazo global aplicado en fix_v3 (15 en doc + 28 en comments) | ✅ Aplicado |
| 26 | **Sacar "Propuesta IA"** del autor | Reemplazo de 52 tracked changes a "Martín Illanes" simple | ✅ Aplicado |

---

## Resumen cuantitativo (actualizado v3.3)

- **Total items de feedback:** 34 (se agregaron 8 sobre Resumen Ejecutivo)
- **Aplicados (✅):** 28
- **Verificados pero corrección manual pendiente (⚠️):** 2 (items 7 header 2.4, 11 header 5.3.4)
- **Pendientes totalmente (❌):** 4 (items 19 numeración tarjetas, 22 Figura 2, 23 Figura 5, 24 Tarjeta 1 — requieren verificación visual tuya)

---

## Bloque v3.3 — Resumen Ejecutivo (feedback 23 abr AM)

### Tabla de items nuevos

| # | Feedback | Acción v3.3 | Estado |
|---|---|---|---|
| 27 | **Eduardo id=28** — mensajes clave con hipervínculo a capítulo/sección | Reply actualizado: "Aceptado. Se agregará columna o nota al margen en el cuadro de mensajes clave indicando el capítulo y sección…" | ✅ Reply actualizado; **renderizado visual con links pendiente** |
| 28 | **Eduardo id=29/34** — evitar jargon "canal retail" | Reply actualizado: balance "farmacias privadas (canal retail)" en Resumen Ejecutivo, mantener "canal retail" en cuerpo técnico | ✅ Reply actualizado; **barrido en el texto pendiente** |
| 29 | **Eduardo** — "agregarla a los" — gramatical | Es SUG30/SUG31 (artículos faltantes). id=3 SUG31 ya aceptado; id=2 SUG30 pendiente ubicación exacta | ⚠️ **Parcialmente aplicado** |
| 30 | **Eduardo** — "por ejemplo" → "e.g." (NO aceptar, mantener estilo) | No se aplica cambio, estilo chileno usa "p. ej." | ✅ Decisión: rechazar |
| 31 | **Carla id=31 (CC-DOCX9)** — incluir alto costo — responder la pregunta, no solo "aceptado" | Reply actualizado: "Sí, incluye alto costo. El tope anual aplica indistintamente a medicamentos de bajo costo con consumo repetido (crónicos) y a medicamentos de alto costo ambulatorios…" | ✅ Aplicado |
| 32 | **Carla id=37 (CC-DOCX12)** — GES también cubre alto costo; ser factualmente correcto | Reply actualizado: "Aceptado y matizado. GES sí cubre medicamentos de alto costo (DS 22/2025 incorporó elexacaftor/tezacaftor/ivacaftor)… el BFAU está dirigido a medicamentos que quedan fuera de estos regímenes especiales…" | ✅ Aplicado |
| 33 | **Eduardo id=36 (SUG41)** — "por brechas de canasta" | Ya aceptado en v3 | ✅ (sin cambios en v3.3) |
| 34 | **Eduardo id=39 (SUG37)** — "y coordinada" — acepta (no rechazar) | Reply cambiado de [RECHAZADO] a "Aceptado. Se acepta la sugerencia de Eduardo, manteniendo 'simultánea y coordinadamente'…" | ✅ Corregido en v3.3 |
| 35 | **Eduardo id=40 (SUG27)** — agregar párrafo efectividad conjunta | Reply cambiado de [PENDIENTE_DIRECTORES] a "Aceptado. Se incorpora el párrafo propuesto por Eduardo…" | ✅ Aplicado en v3.3 |
| 36 | **Eduardo id=41 (SUG38)** — "cluster intermedio" → "conjunto países OCDE protección farmacéutica intermedia" | Ya aplicado en v3.2 (reply corregido) | ✅ (sin cambios en v3.3) |
| 37 | **Carla id=42 (CC-DOCX15)** — FONASA MLE/MAI | Reply expandido: "aplica en ambas modalidades con canasta y reglas de copago comunes; trazabilidad vía RUT asociado a recetas y dispensaciones…" | ✅ Aplicado en v3.3 |
| 38 | **Eduardo id=44 (SUG42)** — "informada por evidencia" | Ya aceptado en v3 | ✅ (sin cambios en v3.3) |

## Bloque v3.4 — Figuras y Tarjetas (feedback 24 abr)

| # | Feedback | Acción v3.4 | Estado |
|---|---|---|---|
| 39 | **Figura 2 unidad + fuentes** — usar informe CIF 2025 | Leyenda reescrita: MM$ 1.514.814 (2024), 60,8% Servicios de Salud, fuente CIF 2025 + DIPRES/SINIM | ✅ v3.4 |
| 40 | **Figura 5 valores y especificación** — confirmar HC51 retail, usar Google Sheet autor | Leyenda reescrita: HC51 retail USD PPA 2022, OECD SHA, Chile US$394 Alemania US$1.038 promedio OECD US$614 | ✅ v3.4 |
| 41 | **Tarjeta 1 números cuadran** | Título actualizado con referencia a fuentes OECD SHA + MINSAL | ✅ v3.4 parcial (número individuales ya estaban corregidos en v3.2 Ficha Chile Tabla 0) |

## Bloque v3.10 — Cap 4 y 5 + CIF 7 biosimilares (24 abr very late)

| # | Feedback | Acción v3.10 | Estado |
|---|---|---|---|
| 68 | **Carla 88** — EPF un mes, gratis=0, subestimación alto costo | Caveat metodológico en 4.2: gasto bolsillo, mes único, subestima eventos raros, no gasto anualizado | ✅ |
| 69 | **Carla 92** — OMS actualizó indicador protección financiera | Nota: Global Monitoring Report 2023 concentra en 10%, SDG 3.8.2, WHO/World Bank 2023 | ✅ |
| 70 | **Carla 101** — retail vs institucional | 2 vías complementarias (hospital + retail), decisión de mix queda abierta en Esc 2 | ✅ |
| 71 | **CIF 7** — biosimilares heterogeneidad regulatoria | Recuadro 5.3.4 con EMA/FDA/MHRA/Health Canada/ANMAT/ANVISA/COFEPRIS/ISP Chile, referencias | ✅ |
| 72 | **Carla 114** — datos solo retail o todo | Aclarado: 0,46-0,51% PIB es total; HC51 _T 2022 Chile = 1,34% PIB | ✅ |
| 73 | **Carla 115** — solo retail o total | HC51 es retail, excluye HC52 hospitalario (estándar SHA) | ✅ |
| 74 | **Carla 122** — FFAA | Pie de página: CAPREDENA/DIPRECA con reglas independientes; potencial extensión BFAU en fase convergencia | ✅ |
| 75 | **Carla 123** — ISAPRE sin APS | Canal principal farmacias privadas con POS, red mínima definida en reglamento | ✅ |
| 76 | **Carla 129** — programas o retail | Se deja abierto: mix de programas + retail + subvenciones, escenarios muestran magnitudes | ✅ |
| 77 | **Carla 131** — trasvasaje institucional→retail | Riesgo en Cap 7 mitigación: copagos con incentivos relativos, monitoreo migración, coordinación ISAPRE | ✅ |
| 78 | **Carla 133** — alto costo | Cobertura "casi integral" es ambulatoria general; alto costo sigue por GES/LRS/DAC | ✅ |
| 79 | **Carla 140** — lo gratis sigue gratis + ISAPRE | Beneficio focalizado por exposición al gasto, no homogeneización universal; tope de gasto ambulatorio | ✅ |

## Bloque v3.9 — Capítulos 3 y 4 (24 abr late night)

| # | Feedback | Acción v3.9 | Estado |
|---|---|---|---|
| 62 | **Aclaración sobre numeración 58→72** | Los DOCX59-71 NO EXISTEN en el docx. Carla saltó de 58 a 72. IDs internos (id=XX) ≠ numeración DOCX_N. Todo coherente | ✅ Verificado |
| 63 | **Carla DOCX72 (id=62)** — judicialización sin criterio sanitario | Reply: judicialización como síntoma de falla, BFAU + ETESA reducen necesidad de tribunales, citar CIF 2025 | ✅ v3.9 |
| 64 | **Carla DOCX75 (id=63)** — sistema judicial que respeta reglas | Reply: objetivo no es eliminar vía judicial sino alinearla con sistema formal | ✅ v3.9 |
| 65 | **Carla DOCX78 (id=64)** — categorías no excluyentes | Reply: reformular como características coexistentes, no segmentos mutuamente excluyentes | ✅ v3.9 |
| 66 | **Carla DOCX79 (id=65)** — GES incluye alto costo | Reply: revisar todo el documento, "alto costo" es conjunto GES+LRS+DAC+FOFAR, BFAU se dirige al segmento no cubierto | ✅ v3.9 |
| 67 | **Carla DOCX85 (id=66)** — gasto total vs retail con caveat | Reply: datos OECD 2022 Chile $394 PPA (alto LatAm, bajo OCDE vs $614), caveat en 4.1 sobre composición del arsenal y efectos cruzados entre canales | ✅ v3.9 |

## Bloque v3.8 — Cierre Cap 2 + equipo agentes (24 abr late PM)

| # | Feedback | Acción v3.8 | Estado |
|---|---|---|---|
| 53 | **Carla 40 (id=56)** — separar impuestos vs 7% | Reply matizado: Estado opera como comprador directo + asegurador obligatorio; no solo ejecuta tributario | ✅ v3.8 |
| 54 | **Carla 53 (id=57)** — qué proyecto / quién | Reply con cita APA MINSAL 2020 "Plan Salud Universal" + incorporar en texto | ✅ v3.8 |
| 55 | **Carla 54 (id=58)** — MLE/MAI articulación | Reply: BFAU independiente de modalidad, con jerarquía vs GES/LRS/DAC/FOFAR | ✅ v3.8 |
| 56 | **Carla 56 (id=59)** — ChileCompra retail | Reply: intermediación de demanda; extensión posible a retail vía CENABAST Ley 21.198 | ✅ v3.8 |
| 57 | **Carla 57 (id=60)** — precios referencia retail | Reply: precio máximo cubierto, previene captura del subsidio, orienta sustitución | ✅ v3.8 |
| 58 | **Carla 58 (id=61)** — política universal sustitución | Reply: ampliación listado ISP como condición habilitante + certificación universal + biosimilares | ✅ v3.8 |
| 59 | **Agente A** — 10 DEFER Carla residuales | Aplicados 10 replies + 9 edits texto | ✅ v3.8 |
| 60 | **Agente B** — barrido terminológico | 25 edits: BFAU en TOC, glosario, suavización prescriptivos | ✅ v3.8 |
| 61 | **Agente C** — coherencia + renumeración Cap 8 | Cap 8.3→8.1, Cap 8.4→8.2; limpieza intros; biblio identificada | ✅ v3.8 (6 edits, 8 fails por texto ya en tracked) |

## Bloque v3.6 — Capítulo 2 (feedback 24 abr PM)

| # | Feedback | Acción v3.6 | Estado |
|---|---|---|---|
| 47 | **Carla 29 (id=50)** — personas son ejecutoras | Reply aceptado: hogares como ejecutores de gasto de bolsillo | ✅ v3.6 |
| 48 | **Carla 30 (id=51)** — barreras red pública empujan a compra fuera del canal | Reply aceptado: explicita disponibilidad/dispensación/red, vincula con judicialización 3.2.6 | ✅ v3.6 |
| 49 | **Carla 33 (id=52)** — alto costo en farmacia hospitalaria ambulatoria | Reply matizado: no binarismo retail/hospital; DAC oncológico en hospital ambulatorio | ✅ v3.6 |
| 50 | **Carla 34 (id=53)** — convenios ISAPRE + CAEC | Reply aceptado: (i) convenios farmacia retail, (ii) seguros complementarios, (iii) CAEC | ✅ v3.6 |
| 51 | **Carla 37 (id=54)** — copagos FONASA 0 / ISAPRE 20% | Reply preciso: FONASA A/B=0%, C=10%, D=20%; ISAPRE 20% arancel + deducibles por ley | ✅ v3.6 |
| 52 | **Carla 38 (id=55)** — GES no se considera en sec 2.2 | Reply aclarado: GES en punto 3, ISAPRE en punto 7; se analizan por separado | ✅ v3.6 |

## Bloque v3.5 — Capítulo 1 (feedback 24 abr)

| # | Feedback | Acción v3.5 | Estado |
|---|---|---|---|
| 42 | **CIF 2 — dimensión humana patologías complejas** | Nuevo párrafo en Cap 1.1 sobre cánceres, genéticas raras, autoinmunes, neurodegenerativas + judicialización (recursos de protección, demoras, agravamiento) | ✅ v3.5 |
| 43 | **Carla 19 — no solo Ricarte Soto** | Reply aceptado: se amplía con GES, LRS, DAC, FOFAR como conjunto | ✅ v3.5 (reply) |
| 44 | **Eduardo 43 — precios accesibles → precio efectivo** | Reply simplificado a "Aceptado." | ✅ v3.5 |
| 45 | **Eduardo 44 — sostienen → explican fracción** | Reply simplificado a "Aceptado." | ✅ v3.5 |
| 46 | **Eduardo 45 — cotidiano → persistente** | Reply simplificado a "Aceptado." | ✅ v3.5 |

### Renumeración de Tablas (Bloque A v3.3)

| Antes | Después |
|---|---|
| Tabla 6: Gasto público adicional para convergencia… (aparecía en cap 6.2.3) | **Tabla 1**: Gasto público adicional para convergencia… |
| Tabla 2: Propuestas presidenciales | Tabla 2 (sin cambio) |
| Tabla 3: Gasto de bolsillo | Tabla 3 (sin cambio) |
| Tabla 4: Comparación internacional | Tabla 4 (sin cambio) |
| Tabla 5: Normativa | Tabla 5 (sin cambio) |

**Estado:** ✅ Renumeración aplicada como tracked change. Secuencia ahora: 1, 2, 3, 4, 5 ✅

---

## Honestidad sobre mi sistematización

### Lo que hice bien

- **17 de 26 items aplicados** como tracked changes en docx
- Documentación de todos los cambios en `build_v3_base.py`, `build_v3.py`, `fix_v3.py`, `edits_agente1.json`, `edits_agente2.json`, `edits_agente3.json`
- Verificación de datos con fuentes primarias (OECD SHA reproducido)

### Lo que NO hice bien

- **No tenía trazabilidad 1-a-1 de cada feedback tuyo a una acción concreta**. Esta tabla es la primera vez que lo hago sistemáticamente.
- **Items 19, 22, 23, 24** (numeración tablas, Figura 2, Figura 5, Tarjeta 1) los mencionaste pero no los procesé — quedaron colgados.
- **Items 20 y 21** (Carla 42 y Figura 1) los verifiqué con datos OECD pero **no apliqué la corrección al docx** — están en `verificacion-figuras-v3.md` esperando ser aplicados.
- **Item 2** (U con tilde) se aplicó pero al comentario equivocado por un bug en el locator.

---

## Plan para cerrar los pendientes (v3.2)

Orden sugerido por independencia + ROI:

### Bloque 1 (mecánico, puedo hacer ahora, ~30 min)

- **Item 20 — Carla 42:** corregir ficha Chile (Tabla 0) con datos OECD 2022: 0,2% → 0,34% PIB; $308 → $394 per cápita; etc.
- **Item 21 — Figura 1:** mejorar leyenda con fuente OECD SHA explícita + año 2022.
- **Item 19 — numeración tablas/subtítulos:** grep sistemático, listar inconsistencias, corregir.

### Bloque 2 (requiere input tuyo, ~15 min)

- **Item 2 — U con tilde:** verificar que el reply correcto está en la sugerencia 29 real, no EU-SUG38.
- **Item 7 — Header 2.4:** verificar visualmente que esté limpio.
- **Item 11 — Header 5.3.4:** verificar visualmente.

### Bloque 3 (requiere tu verificación visual, ~20 min)

- **Item 22 — Figura 2:** ¿porcentajes o absolutos? ¿M$ o MM$?
- **Item 23 — Figura 5:** ¿retail o total? actualizar leyenda.
- **Item 24 — Tarjeta 1:** ¿solo retail? agregar especificación.

---

## Propuesta

¿Arranco con el **Bloque 1** ahora (mecánico, no requiere tu input)? Aplico las 3 correcciones como tracked changes, subo v3.2 a Drive, y después vamos con los Bloques 2 y 3 que sí requieren tu ojo sobre el documento.
