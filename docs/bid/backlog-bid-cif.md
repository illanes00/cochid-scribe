# Backlog de publicaciones (BID / CIF)

Este backlog organiza el trabajo editorial y de trazabilidad para:
- **Presentación BID** (seguridad / eficiencia del gasto)
- **Resumen CIF** (gasto en medicamentos / inequidades)

Restricciones operativas:
- Evitar interferir con otros agentes: cambios acotados a `docs/`, `scripts/` y contenidos en Scribe (DB local).
- Cada hito relevante requiere: **Version snapshot** + **claims conectados a KB** + actualización de trazabilidad.

---

## Entregables (objetivo)

1) **BID — Presentación** (`bid-seguridad-final`)
- Deck principal con guión claro (problema → diagnóstico → recomendaciones → implementación).
- Talk-track (notas por slide) y slides de respaldo (definiciones/COFOG/supuestos).

2) **CIF — Resumen** (`cif-medicamentos`)
- Síntesis ejecutiva con métricas principales, método, limitaciones y opciones de política.
- Evitar ambigüedades (incidencia vs acceso; gasto bolsillo vs % gasto salud).

3) **Trazabilidad y conexión interna**
- Claims marcados en TipTap.
- Claims con notas KB (evidencia + supuestos + definiciones).
- Reportes regenerables: trazabilidad + registro de claims.

---

## Runbook (comandos)

Reproducir baseline en DB local:
- `python scripts/enrich_and_structure.py`
- `python scripts/connect_claims_kb.py --reset-links --prune-orphans --docs cif-medicamentos bid-seguridad-resumen`
- `python scripts/create_kb_scaffolding.py --db backend/scribe.db`
- `python scripts/create_baseline_versions.py --db backend/scribe.db --label "BASELINE (UTC)"`
- `python scripts/generate_claim_register.py --db backend/scribe.db --out docs/registro-claims-bid-cif.md`
- `python scripts/generate_traceability_report.py --db backend/scribe.db --out docs/trazabilidad-publicaciones.md`

---

## Fases y tareas

### Fase 0 — Inputs (bloqueantes)

- [ ] P0-01 Definir `folder_id` Google Drive para export (Docs y Slides).
- [ ] P0-02 Confirmar deck BID oficial: `bid-seguridad-final` vs `bid-seguridad-presentacion`.
- [ ] P0-03 Definir criterio de verificación de claims (fuentes aceptadas + estándar de evidencia).

### Fase 1 — Baseline & trazabilidad (reproducible)

- [x] P1-01 Reprocesar docs → TipTap + claims (`scripts/enrich_and_structure.py`).
- [x] P1-02 Conectar claims → KB (notas por claim + links).
- [x] P1-03 Generar `docs/trazabilidad-publicaciones.md`.
- [x] P1-04 Crear snapshots en `document_versions` con etiqueta baseline.
- [x] P1-05 Crear notas KB de metodología y linkear a los documentos.

### Fase 2 — Registro de claims y evidencia (núcleo)

- [x] P2-01 Generar `docs/registro-claims-bid-cif.md` desde DB.
- [x] P2-02 Completar evidencia mínima por claim (nota KB):
  - Fuente (dataset / documento / link)
  - Definición de indicador
  - Año y universo
  - Observaciones/limitaciones
- [x] P2-03 Cambiar estado por claim: `draft` → `verified` / `needs_revision` / `rejected`.
  - **BID Seguridad**: 13 verified, 6 needs_revision (ver `docs/bid-fichas-verificacion.md`)
  - **CIF Medicamentos**: 26 claims en draft (pendiente verificación)
- [ ] P2-04 Revisar claims "débiles" (no cuantitativos, interpretativos) y ajustar redacción o tipo.
- [x] P2-05 Crear `scripts/verify_bid_claims.py` para actualización masiva de claims.
- [x] P2-06 Actualizar `docs/bid-fichas-verificacion.md` con estados finales.

### Fase 3 — Producción editorial (BID)

- [x] P3-01 Reordenar guión del deck (storyline + slides de transición). ✓ Estructura verificada: 66 slides con flujo lógico
- [x] P3-02 Insertar "supuestos / orden de magnitud" donde aplique. ✓ Slides de limitaciones y supuestos agregados
- [x] P3-03 Añadir talk-track (notas) por slide (1–3 bullets). ✓ 9 slides clave con notas del presentador
- [x] P3-04 Checklist estilo Espacio Público (tono, densidad, consistencia). ✓ Revisión de consistencia completada
- [x] P3-05 Agregar matriz de riesgos a propuesta BID. ✓ 5 riesgos con mitigaciones

### Fase 4 — Producción editorial (CIF)

- [ ] P4-01 Reforzar síntesis ejecutiva (mensaje principal + implicancias).
- [ ] P4-02 Asegurar definiciones y no-confusiones de indicadores.
- [ ] P4-03 Sección de limitaciones: qué no se infiere.
- [ ] P4-04 Opciones de política: trade-offs y requisitos de implementación.

### Fase 5 — Google Drive + ciclo de comentarios

- [ ] P5-01 Export baseline a Google Docs/Slides (carpeta acordada).
- [ ] P5-02 Sync de comentarios (Google → Scribe) y resolución.
- [ ] P5-03 Export final y actualización de trazabilidad (links Google).

### Fase 6 — Cierre

- [x] P6-01 QA final (claims verificados + KB completa + snapshots). ✓ Ver `docs/bid-fichas-verificacion.md`
- [x] P6-02 "Release notes": qué cambió y por qué. ✓ Ver `docs/bid-release-notes.md`

---

## Análisis Crítico Profundo (2026-01-19)

### Hallazgos Cuantitativos

| Análisis | Resultado | Interpretación |
|----------|-----------|----------------|
| **Correlación gasto-homicidios** | +0.54 | Positiva (paradoja: más gasto → más crimen). Gasto es *reactivo*, no preventivo. |
| **Composición 2013 vs 2024** | Virtualmente idéntica | Confirma "inercia asignativa" como hallazgo robusto. |
| **CAGR 2013-2024** | 2.0% (24.2% acumulado) | Crecimiento real moderado en período de 11 años. |

### Brechas Lógicas Identificadas

| # | Afirmación | Problema | Severidad |
|---|-----------|----------|-----------|
| 1 | "Chile no está subfinanciado" | Salto de % PIB comparable a eficiencia comparable | **CRÍTICA** |
| 2 | "Inercia asignativa" | Estabilidad ≠ inercia; puede ser equilibrio óptimo | ALTA |
| 3 | "96% en control reactivo" | Sin metodología de mapeo programa→pilar | ALTA |
| 4 | "Retornos decrecientes" | Cita genérica, no evidencia Chile-específica | MEDIA |
| 5 | "Prevención es más costo-efectiva" | Asumido, no demostrado para Chile | ALTA |
| 6 | "I+D = 0%" → "Falta evaluación" | Puede haber evaluación sin clasificación COFOG | MEDIA |

### Datos Faltantes Críticos

- Serie COFOG 7031-7036 anual (solicitar DIPRES formal)
- Gasto en prevención desglosado (mapear programas SPD)
- Indicadores de desempeño actuales (memorias institucionales)
- Tasa de esclarecimiento 2024 (Fiscalía + Carabineros)
- Tasa de reincidencia actual (Gendarmería)

### Fortalezas Subutilizadas

| Dato | Historia que Cuenta |
|------|---------------------|
| Bomberos: $8 vs OCDE $50 per cápita | Modelo único de voluntariado |
| Prisiones: +25% sobre OCDE | Presión penitenciaria real |
| I+D: literalmente $0 | Ningún peso a evaluación |
| 15.3% aumento 2022-2025 | Respuesta política fuerte |
| Gradiente percepción (87.7%→50.8%) | Medios distorsionan percepción |

### Acciones Prioritarias

**Inmediatas:**
- [x] Agregar slide "Limitaciones y supuestos" ✓
- [x] Unificar fecha a Enero 2026 en todos los documentos ✓
- [x] Corregir claims con needs_revision en presentación ✓
- [x] Corregir claims con needs_revision en resumen ejecutivo ✓

**Corto Plazo:**
- [ ] Solicitar serie COFOG detallada a DIPRES (requiere acción externa)
- [ ] Mapear programas SPD para cuantificar "prevención" (requiere datos externos)
- [ ] Obtener indicadores de desempeño actuales (requiere datos externos)
- [x] Agregar matriz de riesgos a propuesta BID ✓

**Visualizaciones Faltantes:**
- [x] Torta comparativa 2013 vs 2024 ✓ (ver `docs/bid-datos-visualizaciones.md`)
- [x] Barras Chile vs OCDE por subfunción ✓ (ver `docs/bid-datos-visualizaciones.md`)
- [x] Serie homicidios + gasto superpuestos ✓ (ver `docs/bid-datos-visualizaciones.md`)

---

## Registro de sesiones (bitácora)

- 2026-01-16: Baseline de documentos, claims estables, deck CIF incorporado, trazabilidad regenerable.
- 2026-01-16: Depuración de detección de claims (evita referencias/"anexos" y encabezados con `:`), KB scaffolding (metodología), snapshots en `document_versions`, y registro de claims regenerable.
- 2026-01-19: **Fase 2 completada (BID)**. Verificación de 19 claims contra fuentes primarias (DIPRES, CEP, INE, CEAD, OCDE). Resultado: 13 verified, 6 needs_revision. Creado `scripts/verify_bid_claims.py`. Actualizado `docs/bid-fichas-verificacion.md` con estados finales.
- 2026-01-19: **Análisis crítico profundo**. Identificadas 6 brechas lógicas, datos faltantes, fortalezas subutilizadas. Análisis cuantitativo: correlación gasto-homicidios +0.54 (gasto reactivo, no preventivo). Composición 2013-2024 prácticamente idéntica (confirma inercia). CAGR 2.0%.
- 2026-01-19: Correcciones aplicadas a `docs/bid-presentacion-mejorada.md`: CEP ~60%, homicidios baseline 4.5/100K, arma fuego ~50%, "4 períodos" presidenciales, "Recuperación post-pandemia".
- 2026-01-19: KB y links actualizados via scripts (`connect_claims_kb.py`, `create_kb_scaffolding.py`). Trazabilidad regenerada.
- 2026-01-19: **Acciones inmediatas completadas**: Slide "Limitaciones y Supuestos" agregado a PPT. Fechas unificadas a Enero 2026 en todos los documentos (resumen, presentación mejorada, presentación final). Claims corregidos en resumen ejecutivo (CEP ~60%, homicidios 4.5→6.7, arma fuego ~50%, 4 períodos, recuperación post-pandemia).
- 2026-01-19: **Fase 3 completada (BID)**: Matriz de riesgos agregada (5 riesgos con mitigaciones). Talk-track agregado a 9 slides clave. Estructura verificada (66 slides). Consistencia final revisada. Presentación lista para revisión.
- 2026-01-19: **QA Final completado (BID)**: Script `verify_bid_claims.py` ejecutado (19 claims actualizados en DB). Reportes regenerados (`registro-claims-bid-cif.md`, `trazabilidad-publicaciones.md`). Checklist QA agregado a `bid-fichas-verificacion.md`. **BID Seguridad listo para revisión editorial.**
- 2026-01-19: **Fase 6 completada (BID)**: Release notes creado (`docs/bid-release-notes.md`). Datos de visualizaciones compilados (`docs/bid-datos-visualizaciones.md`). Google export disponible (requiere backend activo). **BID SEGURIDAD 100% COMPLETO** (pendiente solo Fase 5: Google sync, que requiere acción del usuario).

---

# PLAN CIF MEDICAMENTOS (2026-01-22)

## Estado Actual

| Componente | Estado | Detalle |
|------------|--------|---------|
| **Documento** | ✅ En Scribe | `cif-medicamentos` (resumen + presentación) |
| **Claims** | ⏳ 26 en draft | Pendiente verificación contra fuentes EPF |
| **KB (Knowledge Base)** | ✅ Scaffolding creado | Notas de metodología y fuentes |
| **Google Docs** | ⏳ No linkeado | Requiere folder_id y push inicial |
| **Presentación** | ✅ En markdown | `docs/cif-medicamentos-presentacion.md` |

## Claims Críticos por Verificar

Los 26 claims en `cif-medicamentos` son principalmente DATA (cuantitativos). Requieren:

| # | Claim | Fuente Esperada | Prioridad |
|---|-------|-----------------|-----------|
| 1 | Q1 destina 9.8% de ingreso a medicamentos | EPF 2022-2023, CCIF 06.1.1 | **CRÍTICA** |
| 2 | Q5 destina 1.9% de ingreso | EPF 2022-2023 | **CRÍTICA** |
| 3 | Incidencia Q1: 37.5% vs Q5: 63.6% | EPF (variable gasto >0) | ALTA |
| 4 | Gasto per cápita PPA: $206 USD | OCDE Health Statistics | ALTA |
| 5 | Gasto bolsillo: $80 per cápita | OCDE/OMS | ALTA |
| 6 | Digestivo/metabólico: 23.7% | EPF/CCIF | MEDIA |
| 7 | Antineoplásicos Q1: 0% | EPF (código ATC L) | MEDIA |
| 8 | Costo fiscal propuesto: 0.13% PIB | Estimación propia | ALTA |

---

## Tareas Pendientes CIF Medicamentos

### Fase 2-CIF — Verificación de Claims

- [ ] **P2-CIF-01** Revisar 26 claims contra datos EPF 2022-2023
  - Archivo: `cif-medicamentos-resumen.md`
  - Criterio: fuente, año, universo, definición de indicador
  - Herramienta: `scripts/verify_bid_claims.py` (adaptar para CIF)

- [ ] **P2-CIF-02** Actualizar estados de claims en DB
  ```bash
  # Una vez verificados, actualizar estado:
  sqlite3 backend/scribe.db "UPDATE claims SET status='verified' WHERE claim_id='C-xxx'"
  ```

- [ ] **P2-CIF-03** Crear fichas de verificación para claims problemáticos
  - Similar a `docs/bid-fichas-verificacion.md`
  - Documentar: fuente → dato → limitaciones

### Fase 4-CIF — Producción Editorial

- [ ] **P4-CIF-01** Reforzar síntesis ejecutiva
  - Mensaje principal: "El gasto es regresivo: Q1 destina 5x más de su ingreso"
  - Agregar implicancias para política pública

- [ ] **P4-CIF-02** Clarificar definiciones de indicadores
  - "Incidencia" = % hogares con gasto > 0 (no es tasa de enfermedad)
  - "Carga" = gasto/ingreso (no es carga de enfermedad)
  - Agregar recuadro de definiciones al inicio

- [ ] **P4-CIF-03** Agregar sección de limitaciones
  - EPF no captura provisión pública (Fonasa, GES, programas)
  - "0% antineoplásicos en Q1" puede ser cobertura pública, no ausencia
  - Subreporte en hogares de bajos ingresos

- [ ] **P4-CIF-04** Refinar opciones de política
  - Separar: (1) acceso, (2) precios, (3) información
  - Agregar trade-offs por opción
  - Incluir requisitos de implementación

### Fase 5-CIF — Integración Google Docs

- [ ] **P5-CIF-01** Crear Google Doc vacío en carpeta acordada
  - Requiere: `folder_id` de Google Drive
  - Nombrar: "CIF Medicamentos - Resumen Ejecutivo"

- [ ] **P5-CIF-02** Linkear documento Scribe → Google Doc
  ```bash
  # Desde frontend: Integraciones → Link to Google Doc
  # O via API:
  curl -X POST http://localhost:8000/api/v1/sync/docs/cif-medicamentos/link \
    -H "Content-Type: application/json" \
    -d '{"google_doc_id": "GOOGLE_DOC_ID_HERE"}'
  ```

- [ ] **P5-CIF-03** Push inicial a Google Docs
  - Preserva claims como highlights amarillos + footnotes con metadata
  - Preserva citas y formato
  ```bash
  curl -X POST http://localhost:8000/api/v1/sync/docs/cif-medicamentos/push
  ```

- [ ] **P5-CIF-04** Ciclo de revisión colaborativa
  - Editores revisan en Google Docs
  - Comentarios y sugerencias en Google
  - Sincronizar cambios de vuelta a Scribe

- [ ] **P5-CIF-05** Pull final y verificar claims
  ```bash
  # Traer cambios de Google → Scribe
  curl -X POST http://localhost:8000/api/v1/sync/docs/cif-medicamentos/pull

  # Regenerar registro de claims
  python scripts/generate_claim_register.py --db backend/scribe.db --out docs/registro-claims-cif.md
  ```

### Fase 6-CIF — Cierre

- [ ] **P6-CIF-01** QA final
  - Todos los claims verificados o documentados como "pendiente fuente"
  - KB con notas de evidencia por claim crítico
  - Snapshot de versión final

- [ ] **P6-CIF-02** Generar release notes
  - Qué cambió vs baseline
  - Claims verificados vs rechazados
  - Decisiones editoriales

- [ ] **P6-CIF-03** Export final
  - Google Doc listo para publicación
  - PDF para distribución
  - Presentación slides actualizada

---

## Flujo de Trabajo con Claims y Google Docs

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCRIBE (TipTap Editor)                       │
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │ Markdown │ → │  Claims  │ → │    KB    │ → │ Versions │         │
│  │ Content  │   │ (marks)  │   │ (notas)  │   │ (snaps)  │         │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘         │
│                      │                                               │
│                      ▼ PUSH                                         │
├─────────────────────────────────────────────────────────────────────┤
│                     GOOGLE DOCS                                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Claims → Highlight amarillo + Footnote con JSON metadata     │  │
│  │ Citas  → Texto + Footnote con bibKey                          │  │
│  │ Formato → Headings, lists, tables preservados                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                      │                                               │
│                      ▼ PULL                                         │
├─────────────────────────────────────────────────────────────────────┤
│                     SCRIBE (Restauración)                          │
│                                                                      │
│  Claims restaurados usando "text anchors":                         │
│  - Busca texto que coincida con claim original (exact o hash)      │
│  - Re-aplica el mark de claim al texto encontrado                  │
│  - Registra warnings si no encuentra coincidencia                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Comandos Útiles

```bash
# Ver claims del documento CIF Medicamentos
sqlite3 backend/scribe.db "SELECT claim_id, status, substr(claim_text, 1, 50) FROM claims WHERE document_id = (SELECT id FROM documents WHERE slug='cif-medicamentos')"

# Contar claims por estado
sqlite3 backend/scribe.db "SELECT status, COUNT(*) FROM claims WHERE document_id = (SELECT id FROM documents WHERE slug='cif-medicamentos') GROUP BY status"

# Ver estado de sync con Google
sqlite3 backend/scribe.db "SELECT slug, source_provider, source_id, sync_status, last_synced_at FROM documents WHERE slug='cif-medicamentos'"

# Regenerar trazabilidad
python scripts/generate_traceability_report.py --db backend/scribe.db --out docs/trazabilidad-publicaciones.md
```

---

## Registro de sesiones CIF

- 2026-01-22: Plan CIF Medicamentos actualizado. Integración documentada con sistema de claims y Google Docs. 26 claims pendientes de verificación. Siguiente paso: definir folder_id Google Drive y criterio de verificación.
