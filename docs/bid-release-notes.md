# Release Notes - Informe BID Seguridad

**Versión**: 1.1.0 (Post-verificación)
**Fecha**: 2026-01-19
**Autor**: Equipo Espacio Público

---

## Resumen Ejecutivo

Esta versión incorpora la verificación completa de claims contra fuentes primarias, correcciones de precisión, y mejoras de producción editorial para la presentación al BID.

**Estado**: Listo para revisión editorial final.

---

## Cambios por Documento

### `bid-presentacion-mejorada.md` (PPT Principal)

#### Nuevos Slides Agregados

| Slide | Contenido | Ubicación |
|-------|-----------|-----------|
| **Limitaciones y Supuestos** | 4 limitaciones metodológicas, 4 supuestos clave, contrafactuales no explorados | Después de Síntesis, antes de Recomendaciones |
| **Riesgos y Mitigaciones** | Matriz de 5 riesgos con probabilidad, impacto y mitigación | Después de "¿Por qué Espacio Público?", antes de Conclusión |

#### Talk-Track Agregado (Notas del Presentador)

| Slide | Notas |
|-------|-------|
| "La pregunta está mal planteada" | Mensaje central, pausa, contexto de debate público |
| "Seguridad: Primera Preocupación" | Justificación del estudio, presión política |
| "El problema de la inercia" | Hallazgo clave, pregunta retórica sobre cambio |
| "Sin clasificación de I+D" | Dato sorprendente, matiz, oportunidad BID |
| "El mensaje central" | Repetir con convicción, mensaje políticamente viable |
| "Recomendación 1" | Anticipar objeciones, literatura, orden de magnitud |
| "Oportunidades de colaboración" | Programa base vs expansión, atractivo regional |
| "Con el BID, podemos transformar" | Cierre con energía, llamado a la acción |

#### Correcciones de Claims

| Claim | Antes | Ahora | Razón |
|-------|-------|-------|-------|
| CEP delincuencia | 61% | ~60%* | CEP N°95 no confirma 61% exacto |
| Homicidios baseline | 4,7/100K | 4,5/100K (2018) | Dato CEAD/SPD más preciso |
| Arma de fuego | >50% | ~50% (49,5% en 2024) | 2024 bajó de 50%, superó solo en 2022-23 |
| Períodos presidenciales | 3 ciclos | 4 períodos | Piñera I, Bachelet II, Piñera II, Boric |
| Recuperación post-pandemia | "nivel comparable" | "supera máximos pre-COVID" | 2024 > 2019 en términos reales |

#### Fecha Unificada

- Portada: Enero 2026
- Pie de página: Enero 2026
- Consistente en todo el documento

---

### `bid-resumen-ejecutivo.md` (Policy Brief)

#### Correcciones Aplicadas

| Sección | Cambio |
|---------|--------|
| Portada | Diciembre 2025 → **Enero 2026** |
| Contexto | CEP 61% → **~60% (CEP N°95)** |
| Datos objetivos | Homicidios 4,7 → **4,5** (2018 baseline) |
| Datos objetivos | Arma fuego ">50%" → **~50% (49,5% en 2024)** |
| Metodología | "tres ciclos" → **cuatro períodos presidenciales** |
| Evolución | "nivel comparable" → **supera máximos pre-pandemia** |
| Hallazgo central | "normalización" → **recuperación post-pandemia** |
| Pie de página | Diciembre 2025 → **Enero 2026** |

---

### `bid-presentacion-final.md` (PPT Alternativo)

#### Correcciones Aplicadas

- Fecha portada: Diciembre 2025 → **Enero 2026**
- Fecha slide título: Diciembre 2025 → **Enero 2026**
- Fecha pie: Diciembre 2025 → **Enero 2026**

---

## Verificación de Claims

### Metodología

- **Fuentes consultadas**: DIPRES, CEP, INE (ENUSC 2024), CEAD/SPD, OCDE
- **Fecha de verificación**: 2026-01-19
- **Script utilizado**: `scripts/verify_bid_claims.py`

### Resultados

| Estado | Cantidad | % |
|--------|----------|---|
| **Verified** | 13 | 68% |
| **Needs revision** | 6 | 32% |
| **Draft** | 0 | 0% |
| **Rejected** | 0 | 0% |

### Claims Verificados (13)

| ID | Contenido |
|----|-----------|
| C-feaf0084d28b | Gasto 2024: $4,47 billones CLP (1,43% PIB) |
| C-545f220c9fb6 | 23,5% hogares víctima de delito |
| C-1f7d9e27bb02 | Percepción: 87,7% nacional, 74,5% comunal, 50,8% barrial |
| C-1433a5c5cab5 | Homicidios 4,5→6,7→6,0 por 100.000 |
| C-8d8b9fb31d98 | Presupuesto 2025: +15% acumulado |
| C-7d35f3cf980c | Metodología COFOG 703 |
| C-42ee55752c66 | Crecimiento hasta 2018-2019 |
| C-3214ef1c90ae | Baja en 2020 (pandemia) |
| C-c65c0115678a | Cierre 2024: $4,47 billones |
| C-09eb92448c73 | Máximo 2015-2016: 1,75% PIB |
| C-7396cfb88be7 | Banda 2013-2019: 1,6-1,75% |
| C-4104493635f6 | 2024: 5,82% del gasto total |
| C-4dda20102338 | Mínimo 2021: 4,57% |

### Claims con Revisión Pendiente (6)

| ID | Issue | Corrección en documento |
|----|-------|------------------------|
| C-302878240d13 | "Normalización" impreciso | ✓ Cambiado a "recuperación" |
| C-40eca44ec973 | CEP 61% no confirmado | ✓ Cambiado a "~60%" |
| C-0dba6577f0f0 | Arma fuego 2024 es 49,5% | ✓ Cambiado a "~50%" |
| C-90bc0f1ec73f | "3 ciclos" incorrecto | ✓ Cambiado a "4 períodos" |
| C-881aa0f931cf | "nivel comparable" incorrecto | ✓ Cambiado a "supera máximos" |
| C-dabf4b56573e | Mediana OCDE US$841 sin verificar | Pendiente verificación primaria |

---

## Análisis Crítico Agregado

### Hallazgos Cuantitativos Nuevos

| Análisis | Resultado | Interpretación |
|----------|-----------|----------------|
| Correlación gasto-homicidios | **+0.54** | Gasto es reactivo, no preventivo |
| Composición 2013 vs 2024 | Idéntica (44/32/20%) | Confirma "inercia asignativa" |
| CAGR 2013-2024 | 2.0% | Crecimiento real moderado |

### Brechas Lógicas Documentadas

1. "Chile no está subfinanciado" → Salto lógico gasto→eficiencia
2. "Inercia asignativa" → Estabilidad ≠ inercia necesariamente
3. "96% en control reactivo" → Sin metodología de mapeo
4. "Retornos decrecientes" → Cita genérica, no Chile-específica
5. "Prevención más costo-efectiva" → Asumido, no demostrado
6. "I+D = 0%" → Puede haber evaluación no clasificada

---

## Archivos de Soporte Actualizados

| Archivo | Estado |
|---------|--------|
| `docs/bid-fichas-verificacion.md` | +QA checklist, historial actualizado |
| `docs/registro-claims-bid-cif.md` | Regenerado con estados finales |
| `docs/trazabilidad-publicaciones.md` | Regenerado |
| `docs/backlog-bid-cif.md` | Tareas Fase 2-3 completadas |
| `docs/analisis-bid-cif.md` | +Sección análisis crítico profundo |

---

## Scripts Disponibles

```bash
# Regenerar claims en DB con evidencia
python scripts/verify_bid_claims.py

# Regenerar registro de claims
python scripts/generate_claim_register.py --db backend/scribe.db --out docs/registro-claims-bid-cif.md

# Regenerar trazabilidad
python scripts/generate_traceability_report.py --db backend/scribe.db --out docs/trazabilidad-publicaciones.md
```

---

## Próximos Pasos Recomendados

1. **Revisión editorial**: Validar cambios con equipo antes de presentar
2. **Export a Google**: Sincronizar con Google Slides para comentarios
3. **Validación BID**: Compartir con contraparte para feedback
4. **CIF Medicamentos**: Iniciar verificación de 26 claims pendientes

---

## Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2026-01-16 | Versión inicial con claims detectados |
| 1.1.0 | 2026-01-19 | Verificación completa, correcciones, mejoras editoriales |

---

*Release notes generado automáticamente*
*Espacio Público / BID 2026*
