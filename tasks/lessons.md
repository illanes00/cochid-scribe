# Lecciones del proyecto CIF-EP Medicamentos

Reglas operacionales aprendidas de los errores reales en esta sesión. Aplicar en futuras ediciones del informe y en proyectos similares de revisión editorial sobre docx con tracked changes.

---

## 1. Tracked changes y autoría

**Regla 1.1:** Todos los cambios editoriales sobre el informe se aplican como `<w:ins>` y `<w:del>` (tracked changes), nunca como replace directo del texto.
- **Razón:** el workflow de Google Docs permite toggle "Ver con cambios / Ver sin cambios" solo si los cambios son sugerencias.
- **Cómo aplicar:** usar las funciones `make_ins_run()`, `replace_paragraph_content_tracked()`, `make_new_paragraph_tracked()` de `verification/build_v2.py` y siguientes.

**Regla 1.2:** El autor de los tracked changes SIEMPRE es "Martín Illanes" sin sufijos como "(Propuesta IA)", "(Corrector)" ni "(Agente X)".
- **Razón:** el informe se firma como Martín; Eduardo/Carla/CIF no necesitan ver ruido sobre el origen AI de las sugerencias.
- **Cómo evitar regresión:** constantes del script `AUTHOR = "Martín Illanes"`. Al fusionar con contenido heredado, **siempre hacer un pass de limpieza** reemplazando `w:author="Martín Illanes (Propuesta IA)"` → `w:author="Martín Illanes"`. Ver `fix_v3.py`.

---

## 2. Estilos de párrafo al insertar

**Regla 2.1:** Los párrafos nuevos insertados como tracked changes NO deben heredar estilo `Heading1`/`Heading2` del anchor, salvo que sean efectivamente títulos.
- **Causa del bug v3:** `make_new_paragraph_tracked()` copiaba el `<w:pStyle>` del anchor, y como los insertamos cerca de títulos, heredaron el estilo Heading. Resultado: 16 párrafos de cuerpo (contenido de Cap 7.13, 8.3, 8.4) aparecieron en el índice.
- **Fix aplicado en v3.1:** detectar párrafos insertados (tienen `<w:ins>` dentro de `pPr/rPr`) y remover `pStyle` si el contenido es largo (>80 chars) o no parece título.
- **Prevención futura:** al generar nuevos párrafos de **cuerpo**, pasar explícitamente `style_from=None` y `is_heading=False`; solo pasar `is_heading=True` si es título real.

**Regla 2.2:** Los títulos legítimos del documento (Heading1, Heading2, Heading3) no deben tocarse con scripts de limpieza masiva.
- **Criterio para distinguir:** un título legítimo empieza con número de sección (`7.13`, `8.3`) o palabra clave (`Anexo`, `Bibliografía`), es corto (<80 chars), y no termina en punto.

---

## 3. Ortotipografía

**Regla 3.1:** NO usar em dashes (—) en el informe.
- **Reemplazos:**
  - Pares `—texto—` → `(texto)`
  - Individuales ` — ` → `, ` (coma con espacio)
  - A veces ` — ` → `; ` si separa cláusulas independientes
- **Razón:** preferencia editorial del autor (Martín). Consistente con regla global de entregables formales (`.claude/rules/coding-style.md`).
- **Cómo aplicar:** pass regex sobre todos los `<w:t>` fuera de `<w:del>` en document.xml Y comments.xml. Ver `fix_v3.py`.

**Regla 3.2:** Terminología chilena: usar "planes de salud" (no "seguros de salud") cuando se refiere al sistema chileno.
- **Excepción:** citas textuales de leyes, referencias a sistemas de salud de otros países (ahí puede ser "sistemas de salud" o "seguros" según contexto).
- **Fuente de la regla:** Mariela Formas (CIF) 26 sept 2025 + Eduardo Undurraga 7 nov 2025.

---

## 4. Comentarios y replies

**Regla 4.1:** Los replies a comentarios simples (typos, una palabra, una coma) se acortan a "Aceptado." o "Aceptado. Se corrige [X]."
- **NO:** justificación académica de por qué se acepta un cambio menor. Ejemplo malo: "La sugerencia de cambiar 'de' por 'del' mejora la concordancia gramatical y alinea con la norma RAE, por lo que se acepta..."
- **SÍ:** "Aceptado."
- **Ver ejemplos:** Eduardo 30, 31, 32 en v3.1 — todos reemplazados con "Aceptado.".

**Regla 4.2:** Los comentarios de fondo de CIF (por ejemplo, "parece borrador avanzado", "mezcla diagnóstico y propuesta") NO se rebaten académicamente; se responden en tono de recepción.
- **NO:** "Sostenemos que el informe no mezcla diagnóstico con propuesta porque en las secciones 4, 5 y 6 se separa claramente la evidencia de la interpretación..."
- **SÍ:** "Gracias por la observación. Esta versión consolida los comentarios recibidos y se presenta como insumo para la discusión del seminario. Los ajustes estructurales señalados se incorporan en los Capítulos 6-8."
- **Ver ejemplo:** reply a CIF 12 en v3-base.

**Regla 4.3:** Nunca citar a CIF como fuente académica en el informe. Usar fuentes primarias.
- **Preferidas:** NEJM, Lancet, Nature Medicine, NICE, FDA, EMA, OECD, OMS, MINSAL.
- **Razón:** CIF es el cliente; citarlo sería autoreferencial y genera fricción institucional.

---

## 5. Datos y cifras

**Regla 5.1:** El 71% de gasto de bolsillo en retail es un dato OECD SHA directo (HF3/HC51), no "cálculo propio".
- Serie Chile: 2019=81.7%, 2020=70.0%, 2021=71.0%, 2022=71.4%, 2023=70.0%.
- Fuente citable: OECD Health Statistics, dataflow `OECD.ELS.HD,DSD_SHA@DF_SHA`.
- Nota metodológica correcta en Resumen Ejecutivo v3.1.

**Regla 5.2:** El API SDMX OECD es public y operativa. No necesita auth.
- **Endpoint:** `https://sdmx.oecd.org/public/rest/data/OECD.ELS.HD,DSD_SHA@DF_SHA/...`
- **Header:** `Accept: application/vnd.sdmx.data+csv;version=2.0.0`
- **Para Chile HC51:** filtrar por REF_AREA=CHL, FUNCTION=HC51, MODE_PROVISION=_T, PROVIDER=_T.

**Regla 5.3:** Al citar una cifra en la ficha país, verificar el año de referencia. Errores frecuentes: mezclar OECD 2019 con DIPRES 2022, reportar USD corrientes como USD PPA.
- **Ver ejemplo:** la ficha Chile del informe dice "0.2% del PIB" para gasto público, que es el valor 2019 de OECD. Para 2022 el valor correcto es 0,34%.

---

## 6. Nombres de cliente y firmantes

**Regla 6.1:** Martín Illanes es el autor firmante, NO Vergara.
- Nombre completo: Martín Alexis Illanes Vindzanova.
- Ver `/home/illanes00/.claude/projects/-srv-projects/memory/user-martin-profile.md` (ya existe).

**Regla 6.2:** Interlocutores CIF en orden jerárquico (sept 2025 - abr 2026):
- Mariela Formas (coordinadora general CIF)
- Francisca Rodríguez (técnica, comentarios de fondo)
- Carlos Portales (técnico)

**Regla 6.3:** Interlocutores Espacio Público:
- Benjamín García (Director Ejecutivo, interlocutor directo con Martín)
- Eleni Kokkidou (equipo salud)
- Eduardo Undurraga (director, comentarios en Google Doc)
- Carla Castillo (directora, 47 comentarios en docx track changes)

---

## 7. Workflow de versiones

**Regla 7.1:** El informe se versiona por vueltas de revisión. Cada versión preserva la anterior.
- **v1 (17 abr 2026):** 91 comentarios procesados, 26 sugerencias. `informe-final-revisado.docx`
- **v2 (22 abr AM):** Reframing editorial + 8 preguntas seminario. Google Doc `1eoTuv6aN6zaf6KqXPqi1OUI2KXIbuDvuGc6iiCWFbKA`
- **v3 (22 abr PM):** Curación editorial con 3 agentes. Google Doc `1BOKKWQ6amXctKhkgZW-Ksjn9w1BkC_0bNQUZmwcuN08`
- **v3.1 (22 abr late):** Fixes de índice, em dashes, Propuesta IA. Google Doc `1__o8gIwZ_2KVCqk-kA9ChoZZxO03iNeEHUQNeFPC5e4`

**Regla 7.2:** Cada versión sube a Drive como Google Doc convertido (no como docx). Eso preserva los tracked changes y permite el toggle "Ver con cambios".
- Upload via `curl + Drive API + rclone token`. Ver `build_v3.py` Fase F.

**Regla 7.3:** Los scripts de generación viven en `/srv/projects/cochid/cochid-scribe/docs/cif-review/verification/`.
- `build_v2.py` — base reutilizable de todos los posteriores.
- `build_v3_base.py` — cambios estructurales (fecha, colapsar subcategorías).
- `build_v3.py` — consolida los 3 JSONs de agentes editoriales.
- `fix_v3.py` — limpieza (Propuesta IA, em dashes, índice).

---

## 8. Patrones en el informe a monitorear

**Regla 8.1:** Revisar que el informe responda los 10 puntos centrales de CIF (ver `/verification/minuta-cif-analisis.md`). En particular:
- C1: "planes" vs "seguros" — barrido pendiente
- C4: diagnóstico dual (ambulatorio + alto costo) — parcialmente resuelto
- C8: foco europeo explícito — resuelto en v3
- C9: ETESA por valor, no contención — parcialmente resuelto

**Regla 8.2:** Cifras que requieren verificación contra OECD SHA antes de cada versión final:
- 71% gasto bolsillo retail
- Gasto público medicamentos / PIB (0.34% 2022, NO 0.2%)
- Per cápita OECD (US$614 promedio 2021)
- GES 90 patologías (Decreto GES 2025-2028)

**Regla 8.3:** Secciones propensas a tono prescriptivo residual que requieren barrido periódico:
- Resumen Ejecutivo (especialmente sub-bloque "Recomendación")
- Cap 7 título e intro
- Cap 8 conclusiones
- Mensajes Clave (#4 especialmente)
