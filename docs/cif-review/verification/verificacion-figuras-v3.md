# Verificación de Figuras 1 y 2 y Ficha Chile

**Fecha:** 2026-04-22 21:15
**Fuente de verdad:** OECD SHA (System of Health Accounts) 2019-2023, función HC51 (retail pharmaceuticals), Chile. Dataset oficial descargado del dataflow `OECD.ELS.HD,DSD_SHA@DF_SHA`.

---

## 1. Ficha Chile (Tabla 0 del informe) — discrepancias detectadas

La ficha Chile actualmente en el docx v3.1 dice:

| Campo | Valor en ficha | Valor correcto OECD 2022 | Estado |
|---|---|---|---|
| Gasto total medicamentos per cápita (US$ 2022) | $308 | **$394.2 USD PPA** (HC51 _T) o **$416.8 USD PPA** (precios corrientes) | ⚠️ incorrecto |
| Gasto privado per cápita | $240 | **$293.4 USD PPA** (HF2+HF3 ≈ $12.1 + $281.3) | ⚠️ incorrecto |
| Gasto de bolsillo (HF3) | $240 | **$281.3 USD PPA** | ⚠️ incorrecto (coincide con privado; error conceptual) |
| % del gasto de bolsillo | 71% | **71.4%** (OECD HF3/HC51 _T) | ✅ correcto |
| **Gasto público en medicamentos: 0.2% del PIB** | 0.2% | **0.342% del PIB** (HF1/PIB 2022) | ⚠️ **incorrecto** — comentario Carla 42 era válido |

### Probable causa del 0,2% en la ficha

La serie OECD muestra que 0,2% podría corresponder al año **2019** (0.218% HF1/PIB). Es posible que la ficha use el dato más antiguo mientras la Figura 1 usa datos 2022-2024. Esto genera la inconsistencia que Carla señaló.

**Corrección propuesta:** actualizar la ficha con el dato OECD 2022 (más reciente disponible con serie completa):
- Gasto público en medicamentos: **0,34% del PIB (2022)** o **0,37% (2023, dato más reciente)**
- Nota metodológica: "Incluye HC51 retail pharmaceuticals financiado por esquemas públicos/obligatorios (HF1), según OECD SHA 2022."

---

## 2. Figura 1 — "Evolución del gasto público en medicamentos 2014-2024"

**Caption actual:** "Serie anual de dos indicadores: (i) gasto público en medicamentos como % del PIB; (ii) gasto público en medicamentos como % del gasto corriente MINSAL. Fuente: Elaboración propia a partir de bases DIPRES/OCDE."

**Datos OECD para HC51 HF1 / PIB (Chile, 2019-2023):**

| Año | % del PIB (HC51 HF1) | % gasto salud total (HC51 HF1 / total health) |
|---|---|---|
| 2019 | 0.218% | 2.346% |
| 2020 | 0.373% | 3.843% |
| 2021 | 0.339% | 3.486% |
| 2022 | 0.342% | 3.422% |
| 2023 | 0.371% | 3.645% |

**Observaciones:**

- La serie muestra un salto en 2020 (0.22% → 0.37%) probablemente asociado a la pandemia y/o a cambios metodológicos SHA.
- La cifra ha estabilizado entre 0,34% y 0,37% del PIB desde 2021.
- La segunda serie del gráfico (% del gasto corriente MINSAL) no se puede reconstruir desde OECD puro — requiere datos DIPRES sobre ejecución presupuestaria MINSAL.

**Recomendación para Figura 1:**

1. Confirmar que los valores graficados para años 2019-2023 coinciden con la serie OECD arriba.
2. Si el gráfico muestra un valor cerca de 0.2% para 2022, eso es incorrecto — debería ser 0.34%.
3. Clarificar en la leyenda si la serie es "gasto público en HC51 (OECD)" o "ejecución presupuestaria DIPRES" — son denominadores distintos.
4. El dato 2024 no está aún en OECD (último año disponible es 2023). Si la figura muestra 2024, su fuente es presupuesto DIPRES, no ejecutado.

---

## 3. Figura 2 — "Composición del gasto público en medicamentos por ejecutor/programa"

**Caption actual:** "Participación porcentual anual de cuatro ejecutores: Servicios de Salud (SS), Programa Nacional de Inmunizaciones (PNI), Ley 20.850–Ricarte Soto (LRS) y Municipios (APS). Gráfico en áreas apiladas."

**Observaciones:**

- La clasificación por ejecutor (SS, PNI, LRS, APS/Municipios) es específica de DIPRES Chile, **no existe en datasets OECD**. Los datos fuente no están en el servidor local (`/srv/projects/archives/illanes00-cif/` no incluye DIPRES crudo).
- La leyenda dice "participación porcentual anual" — si el gráfico muestra **valores absolutos en CLP** (millones o miles de millones) en lugar de porcentajes, hay inconsistencia entre leyenda y gráfico.
- Si la leyenda dice "millones de pesos" (M$) pero los valores absolutos son realmente miles de millones (MM$), es error de unidad y hay que corregir.

**Recomendación para Figura 2:**

1. **Verificar visualmente** el gráfico: ¿muestra porcentajes apilados sumando 100% o valores absolutos? La leyenda dice "porcentual".
2. Si son valores absolutos: verificar unidad (M$ = millones vs MM$ = miles de millones). Para referencia, el presupuesto MINSAL total ronda los 9 billones CLP (= 9.000.000 M$ = 9.000 MM$). Gasto público en medicamentos ~5-7% de eso, es decir ~450.000-650.000 M$ o ~450-650 MM$.
3. Solicitar a Martín (o al autor original) los datos DIPRES fuente para reconstruir y validar.

---

## 4. Propuesta de corrección para la ficha Chile

Reemplazar el contenido del cell 1 de la Tabla 0 con valores OECD 2022 verificados:

> **Estadísticas vitales (2024)**
> - PIB PPA per cápita: US$34.637
> - Población: 19,76 millones
> - Edad mediana: 36,4 años
> - Esperanza de vida: 81,2 años
>
> **Gasto en medicamentos (retail, OECD SHA 2022)**
> - Gasto total per cápita: US$394 PPA
> - Gasto público (HF1) per cápita: US$101 PPA
> - Gasto voluntario (HF2) per cápita: US$12 PPA
> - Gasto de bolsillo (HF3) per cápita: US$281 PPA
> - % del gasto de bolsillo (HF3/total): 71%
>
> **Gasto público como % del PIB (2022)**
> - Gasto público total: 27,0%
> - Gasto público en salud: 5,1%
> - Gasto público en medicamentos retail (HC51): 0,34%
>
> _Fuente: OECD Health Statistics, dataflow OECD.ELS.HD,DSD_SHA@DF_SHA; datos 2022 (último año con serie completa disponible)._

---

## 5. Acciones sugeridas para v3.2

| Acción | Prioridad | Estado |
|---|---|---|
| Corregir ficha Chile (tabla 0) con cifras OECD 2022 | **Alta** | Aplicable como tracked change |
| Añadir nota metodológica a Figura 1 sobre serie OECD vs DIPRES | Alta | Aplicable como tracked change |
| Verificar visualmente Figura 2 (porcentajes vs absolutos, unidad CLP) | Media | Requiere inspección del gráfico por Martín |
| Reconstruir serie Figura 2 desde DIPRES si valores no coinciden | Media | Requiere acceso a datos DIPRES externos |
| Agregar comentario al autor en Figura 2 solicitando verificar unidad | Alta | Aplicable como comment |

---

## 6. Datos OECD Chile disponibles para referencia

Fuente: CSV descargado de carpeta Drive CIF, filtrado sobre:
- REF_AREA = CHL
- FUNCTION = HC51 (retail pharmaceuticals)
- MODE_PROVISION = _T
- PROVIDER = _T
- PRICE_BASE = Q (prices constants)

### Serie completa Chile HC51 (2019-2023)

**USD PPA per cápita:**

| Año | Total (_T) | HF1 Gov | HF2 Vol | HF3 OOP | % HF3/_T |
|---|---|---|---|---|---|
| 2019 | 354.6 | 59.5 | 5.4 | 289.7 | 81.7% |
| 2020 | 345.5 | 95.7 | 8.1 | 241.8 | 70.0% |
| 2021 | 386.7 | 99.9 | 12.2 | 274.6 | 71.0% |
| 2022 | 394.2 | 100.7 | 12.1 | 281.3 | 71.4% |
| 2023 | 397.3 | 108.1 | 10.9 | 278.3 | 70.0% |

**% del PIB:**

| Año | Total (_T) | HF1 Gov | HF3 OOP |
|---|---|---|---|
| 2019 | 1.302% | 0.218% | 1.064% |
| 2020 | 1.346% | 0.373% | 0.942% |
| 2021 | 1.312% | 0.339% | 0.932% |
| 2022 | 1.340% | 0.342% | 0.956% |
| 2023 | 1.364% | 0.371% | 0.955% |
