# Contexto compartido — Revisión integral v3.14a

## Objetivo

Revisión integral del informe "Inclusión sostenible de medicamentos en los planes de salud en Chile" (Espacio Público / CIF, mayo 2026). Cada agente produce un JSON con `edits` que un consolidador aplicará como tracked changes sobre v3.14a → v3.14 final.

## Archivos clave

| Path | Qué es |
|---|---|
| `/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-v3.14a.docx` | Versión actual del informe |
| `/tmp/v314a_extract/word/document.xml` | Texto del informe (extraído, XML OOXML) |
| `/tmp/v314a_extract/word/comments.xml` | Comentarios existentes |
| `/srv/projects/cochid/cochid-scribe/docs/cif-review/data/oecd/oecd_sha_raw_from_drive.csv` | OECD SHA bruto 26 MB (HC51, HF1/HF2/HF3, todos países, 2010-2022) |
| `/srv/projects/cochid/cochid-scribe/docs/cif-review/data/oecd/sheet_autor_main.csv` | Google Sheet del autor (18 países consolidados) |
| `/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/minuta-cif-analisis.md` | Análisis de minuta CIF de sept 2025 |

## Principios editoriales (Espacio Público / CIF)

1. **No prescriptivo**: "recomienda" → "plantea como opción", "debe" → "podría" o "convendría", "es necesario" → "sería necesario".
2. **No em dashes (—)**. Usar coma, paréntesis, dos puntos o guion simple `-`.
3. **"Planes de salud"** no "seguros de salud" para Chile (FONASA/ISAPRE).
4. **No citar a CIF como fuente académica**. Usar fuentes primarias (NEJM, Lancet, NICE, FDA, EMA, MINSAL, OECD).
5. **Primera persona editorial evitada**: "este informe desarrolla" en vez de "recomendamos".
6. **Fecha del informe**: mayo 2026.
7. **Replies a comentarios simples**: "Aceptado." sin justificación larga.
8. **Cero neologismos innecesarios**.
9. **Cifras OECD siempre citar** como "OECD SHA 2022, HC51 HF3" o similar, con dataset identificado.

## Datos verificados

- **Chile 2022 HC51 (OECD SHA)**: HF1+HF2=29%, HF3=71%, total per cápita US$ 394 PPA.
- **CIF 2025 (Caracterización gasto público en medicamentos, 2da ed.)**: MM$ 1.514.814 gasto público 2024 (8,79% presupuesto MINSAL). Ejecutores: Servicios de Salud 60,8%, PNI, LRS, Municipios.
- **Costa Rica CCSS**: 86,4% afiliación (UCR 2024), ~53% uso efectivo medicamentos.
- **Figura 2 eje Y**: está en miles de millones de pesos (MM$). El valor máximo ~1.500 corresponde a MM$ 1.500 (CLP 1,5 billones).
- **Tablas en v3.14a**: 6 tablas (Tabla 0 Ficha Chile + Tabla 1-6) y 9 figuras + 1 tarjeta.

## Formato de edits.json

```json
{
  "agent": "nombre",
  "generated_at": "2026-01-01T00:00:00Z",
  "edits": [
    {
      "id": "FICHA-01",
      "type": "replace_paragraph",
      "locator": {
        "strategy": "contains",
        "text": "Privado per cápita (US$ PPA 2022): US$ 293"
      },
      "old": "...",
      "new": "...",
      "rationale": "Dato incorrecto según OECD SHA 2022 HC51 (datos reales: X)"
    },
    {
      "id": "NEW-01",
      "type": "insert_paragraph_after",
      "anchor": { "strategy": "contains", "text": "header identificador" },
      "new": "texto nuevo",
      "rationale": "..."
    },
    {
      "id": "MI-20",
      "type": "add_comment",
      "anchor": { "strategy": "contains", "text": "párrafo a comentar" },
      "comment": "[MI-20] Comentario aclaratorio...",
      "rationale": "..."
    }
  ]
}
```

Tipos soportados: `replace_paragraph`, `insert_paragraph_after`, `insert_paragraph_before`, `add_comment`, `replace_text_in_paragraph`.

## Normas de trazabilidad

- Todos los comentarios nuevos del autor llevan prefijo `[MI-NN]` con N secuencial (último usado: MI-15).
- Autor siempre "Martín Illanes", fecha "2026-01-01T00:00:00Z".
