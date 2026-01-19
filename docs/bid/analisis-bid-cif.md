# Análisis editorial y de trazabilidad — BID Seguridad + CIF Medicamentos

**Fecha**: 2026-01-16  
**Objetivo**: dejar los documentos *publicables* (claros, consistentes, verificables) y que el trabajo quede trazable dentro de Scribe (TipTap + claims + KB + export Google).

---

## Criterios de “bien hecho” (para este repo / Espacio Público)

1. **Mensaje central inequívoco** (en 1 frase) + “implicancia” operacional (qué se hace distinto).
2. **Cifras clave consistentes** entre resumen y presentación (mismos años, mismos denominadores, mismas unidades).
3. **Claims atómicos**: cada cifra relevante debe vivir en un enunciado breve (ideal: 1 claim = 1 idea verificable).
4. **Evidencia asociable**: para cada claim crítico, indicar qué fuente lo respalda (aunque sea como “pendiente”).
5. **Lectura BID** (seguridad): foco en capacidad de gestión, trazabilidad, métricas y roadmap accionable.
6. **Lectura política pública** (medicamentos): foco en regresividad, barreras de acceso, instrumentos concretos y orden de magnitud fiscal.
7. **Trazabilidad interna**: versiones, comentarios (si se usa Google), y vínculos claim↔nota (KB) para sostener discusión editorial.

---

## BID Seguridad

### Entregables
- `docs/bid-resumen-ejecutivo.md` (policy brief / resumen ejecutivo)
- `docs/bid-presentacion-mejorada.md` (slide deck recomendado como principal)
- `docs/bid-presentacion-final.md` (slide deck alternativo, más “informe”)

### Mensaje central (actual)
“No es un problema de cuánto se gasta, sino de **cómo** se gasta: composición, ejecución, capacidades y medición”.

### Fortalezas
- Marco conceptual claro (eficacia/eficiencia/calidad; asignativa vs técnica).
- Hallazgos muy “BID”: inercia asignativa, rigidez por personal, brecha de I+D, falta de mapeo programa→COFOG.
- Recomendaciones accionables con indicadores sugeridos (en deck mejorada).
- Hoja de ruta 2026–2028 y propuesta de asistencia técnica (muy alineado a cliente).

### Riesgos / puntos a blindar (para publicación)
- “I+D = 0%”: mejor formular como “**no aparece clasificado** en COFOG 7035” (puede existir gasto disperso).
- “Subfinanciamiento”: matizar (“en agregado”, “según COFOG Gobierno Central/General”), evitando lectura binaria.
- Comparaciones internacionales: exigir consistencia de año y fuente (OCDE vs FMI vs DIPRES; Gobierno Central vs General).

### Mejoras concretas sugeridas
1. En el resumen ejecutivo: agregar una **tabla final** “recomendación → output → indicador → data requerida”.
2. En la presentación: reducir slides “placeholder” si el objetivo es *comité técnico* (si el objetivo es *storytelling*, mantener).
3. Alinear fecha de presentación vs informe (Diciembre 2025 / Enero 2026) en portada o subtítulo para que no parezca inconsistencia.

### Claims críticos (lista mínima) y evidencia esperada
- Gasto 2024: $4,47 billones; 1,43% PIB; 5,82% gasto total → DIPRES/COFOG + serie usada.
- Mix 2024: 44,0% policías; 31,9% justicia/MP; 20,3% prisiones → DIPRES/COFOG.
- Inercia 2013–2024 (mix estable) → serie por subfunción.
- “70% personal” (si se mantiene) → clasificación económica DIPRES / definición.
- Comparación internacional %PIB / per cápita PPA → OCDE GAG / IMF GFS (explicitar).

---

## CIF Medicamentos

### Entregables
- `docs/cif-medicamentos-resumen.md` (resumen ejecutivo ampliado + anexo)
- `docs/cif-medicamentos-presentacion.md` (slide deck; actualmente fuera de DB, conviene publicarlo en Scribe)

### Mensaje central (actual)
“El gasto es **regresivo**: Q1 destina 9,8% de su ingreso vs Q5 1,9%”.

### Fortalezas
- Mensajes clave con tabla comparativa (muy buena entrada).
- Metodología bien especificada (EPF 2022–2023; CCIF 06.1.1; limitaciones).
- Resultados por quintil y por subgrupo terapéutico bien ordenados.
- Presentación incluye propuesta de programa + costo (aporta “policy”).

### Riesgos / puntos a blindar
- Interpretación de incidencia (37,5% vs 63,6%): puede ser **barrera de acceso** *o* **provisión pública** no observada. Conviene explicitar “no observable con EPF”.
- Comparación OCDE: asegurar consistencia de unidad (per cápita PPA vs %PIB vs % bolsillo) y año.
- “Antineoplásicos 0% en Q1”: aclarar si es *en EPF* (gasto reportado) y que puede estar cubierto vía programas o no capturado.

### Mejoras concretas sugeridas
1. En el resumen: incorporar un **recuadro de orden de magnitud fiscal** (si se mantiene la propuesta del deck: 0,13% PIB) como “estimación preliminar”.
2. En recomendaciones: separar “instrumentos de acceso” vs “regulación de precios” vs “información/monitoreo” y asociar indicadores.
3. En anexos: explicitar qué significa “no identificado” (problema de codificación) y su relevancia para monitoreo.

### Claims críticos (lista mínima) y evidencia esperada
- Carga Q1 9,8% vs Q5 1,9% → EPF (definición de ingreso y mensualización).
- Incidencia 37,5% vs 63,6% → EPF (variable de gasto positivo).
- Per cápita PPA 206 y bolsillo 80 → fuente internacional (OCDE/OMS) + año.
- Participación subgrupos (digestivo 23,7% etc.) → EPF/CCIF.
- Propuesta de programa y costo (si se incorpora al resumen) → supuestos y cálculo (documentar).

---

## Conexión profunda dentro de Scribe (TipTap + claims + KB)

### Qué significa “profundizar” acá
No basta con “generar claims”: hay que **hacerlos navegables y discutibles**:
- claim ↔ texto (selección/scroll),
- claim ↔ evidencia (bibliografía/dataset),
- claim ↔ nota (KB) para discusión editorial.

### Propuesta mínima operativa (sin ensuciar el PDF final)
1. Mantener las piezas publicables limpias (sin `[[wiki-links]]` visibles).
2. En KB, crear notas de apoyo para conceptos y fuentes (“EPF”, “CCIF 06.1.1”, “COFOG 703”, “GFS/OCDE”).
3. Vincular esas notas desde los claims (nota por claim) y desde el documento.

---

## Trazabilidad

Ver `docs/trazabilidad-publicaciones.md` para el estado (claims, KB, Google) y los scripts de sincronización.

---

# ANÁLISIS CRÍTICO PROFUNDO (2026-01-19)

## 1. BRECHAS LÓGICAS Y ARGUMENTALES

### 1.1 Saltos Lógicos Identificados

| # | Afirmación | Problema | Evidencia Faltante | Severidad |
|---|-----------|----------|-------------------|-----------|
| 1 | "Chile no está subfinanciado" | Salto de % PIB comparable a eficiencia comparable | No hay vínculo gasto → resultados | **CRÍTICA** |
| 2 | "Inercia asignativa" | Estabilidad ≠ inercia; puede ser equilibrio óptimo | Análisis de procesos presupuestarios | ALTA |
| 3 | "96% en control reactivo" | Sin metodología de mapeo programa→pilar | Clasificación detallada de programas | ALTA |
| 4 | "Retornos decrecientes" | Cita genérica, no evidencia Chile-específica | Estudios elasticidad gasto-crimen Chile | MEDIA |
| 5 | "Prevención es más costo-efectiva" | Asumido, no demostrado para Chile | Evaluaciones de impacto programas preventivos | ALTA |
| 6 | "I+D = 0%" → "Falta evaluación" | Puede haber evaluación sin clasificación COFOG | Inventario evaluaciones existentes | MEDIA |

### 1.2 Contrafactuales No Explorados

| Pregunta | Por qué importa | Cómo abordar |
|----------|-----------------|--------------|
| ¿Qué pasaría si se aumentara 20% prevención? | Justifica recomendación 1 | Simulación / meta-análisis |
| ¿Cuál es el costo de no hacer nada? | Fortalece propuesta BID | Proyección tendencial |
| ¿Por qué la composición es estable? | Distingue inercia vs equilibrio | Análisis institucional |

---

## 2. BRECHAS DE DATOS CRÍTICAS

### 2.1 Datos Inexistentes

| Dato Faltante | Afecta a | Alternativa |
|---------------|----------|-------------|
| **Serie COFOG 7031-7036 anual** | Composición por subfunción | Solicitar DIPRES formal |
| **Gasto en prevención desglosado** | Recomendación 1 | Mapear programas SPD |
| **Indicadores desempeño actuales** | Recomendación 4 | Memorias institucionales |
| **Tasa esclarecimiento 2024** | Eficiencia policial | Fiscalía + Carabineros |
| **Tasa reincidencia actual** | Eficacia prisiones | Gendarmería |

### 2.2 Datos Existentes No Utilizados

| Dato Disponible | Fuente | Uso Potencial |
|-----------------|--------|---------------|
| **Hacinamiento carcelario** | Gendarmería/INDH | Justifica "alto gasto en prisiones" |
| **Dotación policial per cápita** | Carabineros | Comparación internacional |
| **Presupuesto SPD detallado** | DIPRES | Cuantifica "prevención" |
| **ENUSC por región** | INE | Inequidades territoriales |

---

## 3. ANÁLISIS CUANTITATIVOS PROPUESTOS

### 3.1 Correlación Gasto-Crimen

**Pregunta**: ¿Más gasto está asociado a menos crimen?

**Datos necesarios**:
- Serie gasto COFOG 703 2013-2024
- Serie homicidios 2013-2024
- Serie victimización ENUSC 2013-2024

**Hipótesis**: Correlación débil o nula (gasto reactivo, no preventivo)

### 3.2 Descomposición del Cambio

**Pregunta**: ¿Qué subfunción creció más 2013-2024?

**Método**: Calcular CAGR por subfunción

**Relevancia**: Identifica dónde está el "dinamismo" presupuestario

### 3.3 Brecha Chile-OCDE en el Tiempo

**Pregunta**: ¿Chile converge o diverge de OCDE?

**Método**: Serie de diferencia % PIB Chile - Mediana OCDE

**Relevancia**: Narrativa de largo plazo

---

## 4. VISUALIZACIONES FALTANTES

| Gráfico | Mensaje |
|---------|---------|
| **Torta comparativa 2013 vs 2024** | "Estabilidad" visual |
| **Barras Chile vs OCDE por subfunción** | Dónde estamos alto/bajo |
| **Mapa calor regional** | Inequidades territoriales |
| **Serie homicidios + gasto superpuestos** | ¿Correlación? |

---

## 5. FORTALEZAS SUBUTILIZADAS

| Dato | Historia que Cuenta | Uso Sugerido |
|------|---------------------|--------------|
| **Bomberos: $8 vs OCDE $50 per cápita** | Modelo único voluntariado | Slide diferenciador |
| **Prisiones: +25% sobre OCDE** | Presión penitenciaria real | Justifica costo |
| **I+D: literalmente $0** | Ningún peso a evaluación | Slide de impacto |
| **15.3% aumento 2022-2025** | Respuesta política fuerte | Contexto compromiso |
| **Gradiente percepción** | 87.7% país vs 50.8% barrio | Medios distorsionan |

---

## 6. RECOMENDACIONES FALTANTES

| Área | Recomendación No Incluida |
|------|---------------------------|
| **Territorial** | Redistribución regional del gasto |
| **Personal** | Eficiencia en uso de dotaciones |
| **Coordinación** | Protocolos Carabineros-PDI-Fiscalía |
| **Tecnología** | Inversión en tecnología policial |

---

## 7. ESTADO DE VERIFICACIÓN (Actualizado 2026-01-19)

### Claims BID Seguridad

| Estado | Cantidad | % |
|--------|----------|---|
| **Verified** | 13 | 68% |
| **Needs revision** | 6 | 32% |
| **Draft** | 0 | 0% |

### Claims que Requieren Revisión

1. **C-302878240d13**: "Normalización" → Usar "recuperación parcial"
2. **C-40eca44ec973**: CEP 61% → Confirmar ~60%
3. **C-0dba6577f0f0**: Arma fuego >50% → 2024 es 49.5%
4. **C-90bc0f1ec73f**: 3 ciclos → 4 períodos
5. **C-881aa0f931cf**: "Comparable" → 2024 supera pre-COVID
6. **C-dabf4b56573e**: Mediana OCDE $841 → Verificar fuente primaria

---

## 8. ACCIONES PRIORITARIAS

### Inmediatas
- [ ] Calcular correlación gasto-homicidios (simple)
- [ ] Generar tabla comparativa composición 2013 vs 2024
- [ ] Agregar slide "Limitaciones y supuestos"
- [ ] Unificar fecha a Enero 2026 en todos los documentos

### Corto Plazo
- [ ] Solicitar serie COFOG detallada a DIPRES
- [ ] Mapear programas SPD para cuantificar "prevención"
- [ ] Obtener indicadores de desempeño actuales
- [ ] Agregar matriz de riesgos a propuesta BID

---

*Análisis profundo generado 2026-01-19*

