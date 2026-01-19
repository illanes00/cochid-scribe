# Trazabilidad de publicaciones (Scribe)

**Generado**: 2026-01-19 14:27:07 UTC
**DB**: `backend/scribe.db`

## Publicaciones

| Slug | Tipo | Versión | Últ. actualización | Claims (verif/total) | Notas (KB) | Google |
|------|------|--------|-------------------|----------------------|------------|--------|
| `cif-medicamentos-presentacion` | presentation | 1.0.0 | 2026-01-16 21:11:36 | 0/0 | 0 | — |
| `bid-seguridad-final` | presentation | 1.0.0 | 2026-01-16 21:11:36 | 0/0 | 0 | — |
| `bid-seguridad-presentacion` | presentation | 1.0.0 | 2026-01-16 21:11:36 | 0/0 | 0 | — |
| `cif-medicamentos` | policy | 1.0.0 | 2026-01-16 21:11:36 | 0/26 | 27 | — |
| `bid-seguridad-resumen` | policy | 1.0.0 | 2026-01-16 21:11:36 | 13/19 | 20 | — |

## Flujo recomendado (TipTap + Google Drive)

1. Conectar Google en `/integrations` (OAuth).
2. Editar el documento en Scribe (TipTap).
3. Guardar un snapshot en **Versions** antes de cambios mayores.
4. Exportar a Google Docs/Slides desde el editor (menú ⋮).
5. Sincronizar comentarios desde **Comments → Sync** (si está vinculado a Google).
6. Revisar claims en **Claims** y vincularlos a la KB (notas) cuando aplique.

Nota: la API soporta `folder_id` en export (Docs/Slides) para guardar en un folder específico.

## Scripts de soporte

- `python scripts/enrich_and_structure.py` — reestructura presentaciones y (re)detecta claims en policy briefs.
- `python scripts/connect_claims_kb.py` — crea notas por claim y enlaces claim↔nota y documento↔nota.
- `python scripts/fix_documents.py` — actualiza JSON TipTap desde Markdown (útil para reimportar).
- `python scripts/create_kb_scaffolding.py` — crea notas de metodología y enlaces (documento/claim → metodología).
- `python scripts/create_baseline_versions.py` — guarda snapshots en `document_versions` (Versions).
- `python scripts/generate_claim_register.py` — genera `docs/registro-claims-bid-cif.md` desde la DB.
