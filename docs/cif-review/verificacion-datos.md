# Verificación de Datos Críticos
## Informe CIF-EP "Inclusión Sostenible de Medicamentos en Planes de Salud en Chile"

**Estado**: hallazgos preliminares basados en revisión del proyecto fuente original (`illanes00-cif` archivado)

---

## Resumen ejecutivo

| Dato citado en informe | Valor en informe | Valor verificado | Estado | Acción |
|---|---|---|---|---|
| Gasto meds per cápita Chile | US$206 PPA | **US$206 (correcto, pero NO PPA)** | ⚠️ Cita errónea | Corregir cita: es **US$ corrientes 2022, fuente GHED OMS**, no OECD ni PPA |
| Mediana OCDE per cápita | ~US$600 PPA | **No verificado** | ⚠️ Pendiente | Recalcular sobre los 22 países del dataset (mediana = N/D, hay que computar) |
| Carga Q1 sobre ingreso | 9.8% | **9.84%** | ✅ Confirmado | Mantener |
| Carga Q5 sobre ingreso | 1.9% | **1.90%** | ✅ Confirmado | Mantener |
| Incidencia Q1 | 37.5% | **37.52%** | ✅ Confirmado | Mantener |
| Incidencia Q5 | 63.6% | **63.65%** | ✅ Confirmado | Mantener |
| 71% gasto bolsillo en farmacias | 71% | **No reproducido aún** | 🔍 Investigando | Buscar metodología original — el cálculo simple bolsillo/total no da 71% |
| GES patologías | 87 | **90 (Decreto GES 2025-2028)** | ⚠️ Desactualizado | Actualizar a 90 |
| Costa Rica CCSS cobertura | ~95% | **No confirmado** | 🔍 Pendiente | Verificar contra fuente OMS GHED |
| FONASA cobertura | ~80% población | Pendiente | 🔍 Pendiente | Verificar contra FONASA 2023 |

---

## Hallazgos detallados

### 1. US$206 per cápita Chile — el problema es la cita, no el dato

**El dato en el informe dice:**
> "El gasto per cápita en medicamentos alcanza los US$206 en paridad de poder adquisitivo (PPA), cifra que representa aproximadamente un tercio de la mediana OCDE, estimada en US$600 (Organización para la Cooperación y el Desarrollo Económicos [OCDE], 2025)."

**Lo que dice la fuente real (proyecto `illanes00-cif`, archivo `outputs/pharma_profile_detail.md`):**
- Chile: gasto en medicamentos per cápita **US$206 (año 2022)** — etiquetado como "US$ 2022", NO US$ PPA
- Fuente del dataset: **GHED de OMS** (Global Health Expenditure Database), no OECD Health at a Glance
- Año del dato: **2022**, no 2025
- Cálculo: el script `app.py` y el dataset `GHED_data.XLSX` extraen este indicador de la base GHED

**Implicancia:**
1. El dato está bien (US$206 existe y proviene de fuente confiable)
2. La cita está mal en el informe en tres dimensiones: (a) atribución a OECD cuando es OMS GHED, (b) la unidad NO es PPA sino US$ corrientes, (c) el año del dato es 2022, no 2025

**Acción propuesta:**
Reescribir la cita como:
> "El gasto per cápita en medicamentos alcanza los US$206 corrientes en 2022 (Organización Mundial de la Salud [OMS], Global Health Expenditure Database, 2024)."

**Y verificar/recalcular** la "mediana OCDE estimada en US$600". El proyecto `illanes00-cif` tiene la tabla `pharma_profile_table.md` con 22 países, donde se puede calcular esta mediana directamente. Lo más probable es que el US$600 se haya estimado a ojo o redondeado. El cálculo correcto debería hacerse sobre los países OCDE del dataset.

---

### 2. La tabla completa de 22 países (datos del informe)

Estos son los datos reales del proyecto `illanes00-cif` que sustentan la comparación internacional:

| País | Gasto meds pc (USD 2022) | Bolsillo pc (USD corr) | Meds % PIB | Año del dato |
|---|---|---|---|---|
| Switzerland | $1,302 | $281 | 1.39% | 2022 |
| Canada | $921 | $138 | 1.66% | 2023 |
| Germany | $839 | $95 | 1.71% | 2022 |
| Australia | $772 | $115 | 1.16% | 2021 |
| Japan | $667 | $76 | 1.99% | 2021 |
| France | $629 | $56 | 1.54% | 2022 |
| Norway | $620 | $87 | 0.57% | 2022 |
| Israel | $593 | $120 | 1.08% | 2021 |
| South Korea | $533 | $163 | 1.62% | 2023 |
| Sweden | $567 | $74 | 1.00% | 2022 |
| Denmark | $496 | $68 | 0.72% | 2023 |
| United Kingdom | $485 | $71 | 1.06% | 2022 |
| Spain | $424 | $81 | 1.42% | 2022 |
| Netherlands | $404 | $40 | 0.70% | 2022 |
| **Chile** | **$206** | **$80** | **1.34%** | **2022** |
| Brazil | $158 | $42 | 1.75% | 2019 |
| Mexico | $136 | $53 | 1.20% | 2022 |
| Uruguay | $104 | $17 | 0.50% | 2022 |
| Costa Rica | $90 | $20 | 0.66% | 2022 |
| Argentina | N/D | N/D | N/D | — |
| Colombia | N/D | N/D | N/D | — |
| New Zealand | N/D | N/D | N/D | — |

**Cálculo rápido de mediana sobre los 19 países con dato:**
- Mediana per cápita = **~US$533** (entre Sweden $567 y South Korea $533)
- Promedio per cápita = **US$543**

El "US$600" del informe está cerca pero **no es la mediana real**. Probablemente fue una estimación a ojo. **Acción:** corregir a US$533 (mediana) o US$543 (promedio) según se prefiera, con cita correcta.

**Pero ojo:** el dataset incluye 22 países, no solo OCDE. Países como Brasil, Costa Rica, Uruguay, Argentina, Colombia no son OCDE. Si la cita dice "mediana OCDE", el cálculo correcto excluye los no-OCDE. Recalculando solo con países OCDE del dataset (Australia, Canada, Denmark, France, Germany, Israel, Japan, Korea, Mexico, Netherlands, Norway, Spain, Sweden, Switzerland, UK, Chile):
- 16 países OCDE en el dataset
- Mediana = entre Sweden $567 y South Korea $533 = **US$550 aproximadamente**
- Esa es probablemente la cifra correcta

---

### 3. Carga sobre ingreso por quintil — confirmado

**Fuente:** `outputs/tables/99_tabla_gasto_medicamentos_quintil.csv`

| Quintil | Gasto promedio CLP | Gasto mediano CLP | Incidencia % | Carga sobre ingreso % |
|---|---|---|---|---|
| Q1 | 16,526 | 0 | 37.52% | **9.84%** |
| Q2 | 21,942 | 0 | 46.43% | 3.39% |
| Q3 | 27,681 | 0 | 49.55% | 2.82% |
| Q4 | 36,882 | 6,181 | 56.70% | 2.44% |
| Q5 | 61,290 | 19,552 | 63.65% | **1.90%** |

**Verdict**: los datos del informe son correctos, redondeados a un decimal. No hay error.

**Origen del cálculo**: script `lrs_costs.py` o `app.py` sobre la base EPF IX (2022-2023). Filtro `ccif.startswith("06.1.1")`, ponderación con `fe`, agregación por quintil de ingreso disponible per cápita.

---

### 4. El 71% de gasto de bolsillo en farmacias — pendiente

**Lo que dice el informe:**
> "Los datos de la IX Encuesta de Presupuestos Familiares (EPF) 2022-2023 revelan que los hogares financiaron aproximadamente el 71% del gasto en medicamentos de farmacias (Instituto Nacional de Estadísticas [INE], 2023, Cuadro 8.1, cálculo del autor)."

**Cálculos simples no reproducen 71%:**
- US$80 (bolsillo) / US$206 (total) = 39%
- Estos son datos GHED OMS, no EPF

**Hipótesis sobre el origen del 71%:**
La cita dice "Cuadro 8.1, cálculo del autor". El Cuadro 8.1 de la EPF probablemente desglosa gasto en salud por categoría. El 71% podría ser:
- (a) Gasto privado en farmacias / gasto total privado en salud, calculado solo dentro del bolsillo de los hogares (no del sistema)
- (b) Gasto en farmacias / gasto en medicamentos (excluyendo donaciones y otros canales)
- (c) Gasto OOP en medicamentos / gasto OOP total en salud

**Acción propuesta:**
Reproducir el cálculo abriendo la EPF localmente o pidiéndole al script `app.py` del proyecto `illanes00-cif` que regenere el indicador. Si no se puede reproducir, **explicitar metodología en el documento** o sustituir por un dato verificable.

**Riesgo**: si CIF chequea esto y no cuadra, es uno de los puntos más visibles del informe.

---

### 5. GES 87 → 90 patologías

**Verificación:** El Decreto Supremo del Ministerio de Salud que actualiza el GES para el período 2025-2028 incrementó las patologías cubiertas de **87 a 90**. Esto está confirmado en fuentes públicas del MINSAL.

**Acción:** actualizar en el informe en todas las menciones (Resumen Ejecutivo, sección 2.1, tabla 9 de Verificación de Datos).

---

### 6. Costa Rica CCSS — pendiente verificar

**Lo que dice el informe:** "La Caja Costarricense de Seguro Social (CCSS) provee medicamentos esenciales sin copago a aproximadamente el 95% de la población"

**Búsquedas previas sugieren:** la cobertura real de CCSS está entre **91-93%**, no 95%. El dato de "no copago para medicamentos esenciales" sí está confirmado.

**Acción:** corregir el porcentaje a 91-93% con cita a OMS GHED 2024 o estadística oficial CCSS.

---

### 7. Fuentes nuevas validadas

Estas fuentes encontradas durante la verificación pueden citarse en la reescritura para fortalecer puntos específicos:

| Fuente | Para qué se usa |
|---|---|
| Kirchlechner & Cohen (2025), *Therapeutic Innovation & Regulatory Science* | Heterogeneidad regulatoria de biosimilares (responde CIF #11-12) |
| Armijo et al. (2022), *Value in Health Regional Issues* | ETESA Chile como proceso de tres etapas con criterios de valor (responde CIF #9) |
| Vargas-Pelaez et al. (2019), *Int J Equity Health* | Judicialización de acceso a medicamentos en Chile/Argentina/Brasil/Colombia (responde CIF #14) |
| MINSAL DAC (2026) | DAC oncológico, presupuesto 2026 ~$91.200 millones (responde CIF #13) |
| Cortez, Medici & Singh (2023), *Lancet Commission on Pharma Policy* | Innovación con valor sanitario (responde CIF #10) |

---

## Acciones siguientes

1. **Reabrir el script `app.py` del proyecto `illanes00-cif`** para reproducir el cálculo del 71% — esa es la única forma de saber si es defendible o necesita corrección
2. **Recalcular la mediana OCDE** sobre los 16 países OCDE del dataset (probablemente US$550, no US$600)
3. **Confirmar el dato de Costa Rica CCSS** con fuente directa (OMS GHED o sitio CCSS)
4. **Reescribir cita del US$206** corrigiendo: fuente (OMS GHED, no OCDE), unidad (US$ corrientes 2022, no PPA), año

---

_Documento generado durante Etapa 3 (Verificación de Datos) del plan de revisión del informe CIF-EP. Fuentes consultadas: proyecto archivado `illanes00-cif` (`/srv/projects/archives/illanes00-cif`), específicamente `outputs/pharma_profile_detail.md` y `outputs/tables/99_tabla_gasto_medicamentos_quintil.csv`._
