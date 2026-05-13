# Global issues a resolver en v3.15

## 1. Regresiones / duplicaciones de texto

| Ítem | Dónde | Problema | Acción |
|---|---|---|---|
| Nota 71% duplicada e inconsistente | P0103 (Cap 1, Cap 1.1) vs P0462 (Cap 4.1, nota metodológica) | P0103 dice "cálculo propio sobre EPF + CENABAST + FONASA" (versión vieja, incorrecta). P0462 dice "OECD SHA 2022 HF3/HC51" (versión correcta). | Reemplazar P0103 con la versión correcta (OECD SHA) o eliminarlo y dejar solo la nota en P0462. |
| Caption Figura 2 triplicado | detectado por agente Lectura | tracked changes anterior dejó 3 copias | MI-33 del agente Lectura |
| Resumen Ejec parr 1 duplicado | detectado por agente Lectura | tracked changes anterior dejó 2 copias | MI-30 |
| Cap 1.1 judicialización 2 veces | detectado por agente Lectura | MI-31 |

## 2. Tabla de contenidos corrupto

- P0026-0035 son H1 que deben ser tabla de contenidos auto-generada. Están vacíos o con texto descriptivo completo pegado donde debería ir solo el título.
- Específicamente (según agente Lectura):
  - TOC "2.4 Matriz de coberturas" lleva texto descriptivo completo (debería ser solo el título)
  - TOC "5.3.4 Competencia..." idem
  - "Capítulo 7Capítulo 7" duplicado en TOC
  - TOC Cap 7 dice "Seguro Universal con tope..." pero body dice "Desarrollo del Escenario 2..."
- Acción: regenerar TOC dentro del docx (Word tiene campo TOC automático). O limpiar manualmente los headers del TOC para que solo tengan título.

## 3. Headers corruptos (número+título sin espacio)

Patrón sistemático: "1.Introducción", "1.1.Contexto", "2.Acceso", "2.4Matriz", "4.2Distribución", "5.4Síntesis", "6.2Tres", "7.2Principios", "7.5.2Financiamiento", "7.6Instrumentos", "7.7ETESA", "7.7.1Análisis", "7.8Acuerdos", "7.9Transparencia", "7.10Consideraciones", "7.11Confianza", "7.12Riesgos", "7.13 Síntesis" (tab en vez de espacio), "8.1 Clasificación" (tab), "8.2 Preguntas" (tab), "Anexo 1.Glosario", "Anexo 2.Parámetros", "Anexo 3:Propuestas", "Anexo 4:Detalle", "Anexo 5:Normativa", "Anexo 6:Tarjetas", "A.2.1.1.Población", "A.2.1.2.Servicios", "A.2.1.3.Costos", "A.2.1.4.Otros", "3.2.1.Cobertura", "3.2.2.Cobertura parcial", "3.2.3.Falla", "3.2.4.Precio", "3.2.5.No acceso", "3.2.6.Judicialización", "5.3.1.Sistema", "5.3.2.Cobertura ambulatoria", "5.3.3.Compras", "5.3.4.Competencia", "5.3.6. Trazabilidad" (doble espacio), "6.2.1.Escenario 1", "6.2.2.Escenario 2", "6.2.3. Escenario 3", "7.4.1.Canasta", "7.4.2Copagos" (sin punto), "7.4.3.Sustitución", "7.4.4.Modalidad", "7.5.1.Gobernanza", "7.3.1Análisis..."

Acción: regex global para `^(\d+(?:\.\d+)*)\.([A-ZÁÉÍÓÚÑa-záéíóúñ])` → `$1. $2` + `^(Anexo \d+)[.:](\S)` → `$1. $2` + `^(A\.\d+(?:\.\d+)*)\.([A-ZÁÉÍÓÚÑa-záéíóúñ])` → `$1. $2` + reemplazar tabs por espacios en 7.13, 8.1, 8.2.

## 4. Portada

- Nueva portada descargada a `/srv/projects/cochid/cochid-scribe/docs/cif-review/assets/portada-v3.14.png` (1.4 MB PNG).
- La portada actual del docx es la antigua. Hay que reemplazar la imagen embebida.
- Acción: identificar el image relationship dentro del docx (word/media/image1.png o similar), reemplazar el archivo preservando el relationship. Validar dimensiones.

## 5. Formato / alineación / estilo

- Barrido pendiente: detectar párrafos con alineación incongruente (center donde debería ser justify, left donde debería ser justify), tamaños de fuente inconsistentes en body text, espacios antes/después de párrafo irregulares.
- Acción (tooling): leer `pPr/jc` y `rPr/sz` de cada párrafo del body, detectar outliers por capítulo.

## 6. Fragmentos huérfanos (agente Lectura)

- "farmacias privadas" pegado al inicio de 5-6 párrafos (0150, 0206, 0213, 0599, 0655, 0879) como residuo de un find-replace global.
- ", ,", "ida la ones", "reduccines del precio efectivo", punto aislado en P0811.
- Acción: MI-35 a MI-45 del agente Lectura.

## 7. Redundancias temáticas mayores (agente Lectura)

- Idea "medicamentos no en planes salvo GES/LRS/DAC/FOFAR" repetida 5 veces
- "71% retail" con nota metodológica 4 veces
- "alto costo ≠ baja prevalencia / cáncer" 3 veces
- Cap 7.13 duplica Cap 8 — sugerir eliminar 7.13 o reducirlo a remisión.

## 8. Inconsistencias temporales

- Anexo 5 tabla normativa cortada en "agosto 2025" pero portada mayo 2026.
- Cita P0025 "(2025)" pero portada "Mayo 2026" (LE-001 ya lo arregla).

## 9. Oraciones largas (>80 palabras)

5 casos identificados, partir en 2-3.

## 10. Inconsistencia terminológica Cap 7

- TOC dice "Seguro Universal con tope" (antigua)
- Body dice "Desarrollo del Escenario 2: Beneficio Farmacéutico Ambulatorio Universal" (nueva)
- Tabla Contenidos debe regenerarse tras arreglar.
