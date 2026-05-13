# Anexo 4. Detalle metodológico

Informe v4.0, mayo 2026
Autor: Martín Illanes
Revisión técnica: Carla Castillo (UDD), Eduardo Undurraga (PUC)

Este anexo documenta las fuentes, los supuestos y los procedimientos de cálculo que sostienen las cifras del informe principal. Se organiza en nueve secciones. La sección A4.1 fija el marco contable internacional. Las secciones A4.2 y A4.3 desarrollan el cálculo del gasto público y su descomposición por programa. Las secciones A4.4 y A4.5 documentan el procesamiento de la Encuesta de Presupuestos Familiares y la calibración del tope del Beneficio Farmacéutico Universal simulado. La sección A4.6 valida el modelo OMS sobre la Ley Ricarte Soto. La sección A4.7 presenta el cuadro de doble entrada que articula la totalidad del gasto. Las secciones A4.8 y A4.9 reúnen los datos macro y un glosario.

## A4.1 Marco contable: SHA aplicado a Chile

El informe adopta la clasificación del System of Health Accounts 2011 publicada conjuntamente por OECD, Eurostat y la OMS. Esta clasificación permite la comparación internacional homogénea del gasto en salud y, en particular, del gasto en medicamentos. Tres dimensiones se cruzan en cada flujo monetario: la función del gasto (HC), el esquema de financiamiento (HF) y el proveedor o canal de dispensación (HP). El gasto chileno en medicamentos se reconstruye combinando estas tres dimensiones a partir de los reportes OECD SHA, los cierres presupuestarios de la Dirección de Presupuestos (Dipres), las cuentas públicas de Fonasa y los anuarios de Cenabast.

### Tabla A4.1.1. Dimensión HC, función del gasto

| Código SHA | Función | Aplicación a Chile |
|---|---|---|
| HC1 | Atención curativa | Hospitalización y atención ambulatoria curativa. Incluye medicamentos administrados durante la hospitalización como parte del costo del egreso. |
| HC2 | Rehabilitación | No aplica para medicamentos. |
| HC3 | Cuidados de largo plazo | No aplica. |
| HC4 | Servicios auxiliares | Imagenología, laboratorio. |
| HC5 | Bienes médicos | |
| HC51 | Medicamentos y bienes no durables ambulatorios | Dispensación para uso domiciliario en farmacia retail comercial, APS, ambulatorio hospitalario y Cenabast retail. Es la categoría principal del informe. |
| HC52 | Aparatos terapéuticos durables | Prótesis, equipos médicos. |
| HC53 | Otros bienes médicos no durables | No aplica. |
| HC6 | Prevención | Vacunación PNI, screening. |
| HC7 | Gobernanza | Administración del sistema. |

Cabe señalar que HC51 incluye la dispensación pública gratuita (APS, Arsenal Farmacológico, FOFAR, GES dispensación pública) junto con la venta retail comercial. La distinción entre fuente pública y privada opera en la dimensión HF, no en HC.

### Tabla A4.1.2. Dimensión HF, esquema de financiamiento

| Código SHA | Esquema | Aplicación a Chile |
|---|---|---|
| HF1 | Gobierno y cotización obligatoria | |
| HF1.1 | Gobierno por impuestos generales | Presupuesto MINSAL Partida 16. |
| HF1.2 | Cotización obligatoria | Cotización 7% obligatoria por ley, dirigida a Fonasa o a la fracción obligatoria de Isapre. |
| HF2 | Voluntario | |
| HF2.1 | Seguros voluntarios | Planes premium voluntarios Isapre, complementarios privados. |
| HF2.2 / HF2.3 | NPISH y empresas | No relevante para medicamentos. |
| HF3 | Bolsillo del hogar (OOP) | Compra directa por el hogar. |

Respecto del tratamiento de la cotización obligatoria, conviene precisar lo siguiente. La cotización 7% es obligatoria por ley para todo trabajador formal. Aunque sea recaudada por una aseguradora privada (Isapre), la metodología SHA la clasifica en HF1.2, no en HF2. El criterio aplicable es la naturaleza obligatoria del aporte por mandato legal, no la titularidad pública o privada del operador. En consecuencia, el 26% público del HC51 chileno reportado por OECD comprende Fonasa y la fracción obligatoria Isapre. Lo que se imputa a HF2 (3% del HC51) corresponde solo a planes voluntarios complementarios. El caso análogo en la literatura comparada es Suiza, donde las Krankenkassen privadas con contribución obligatoria también se clasifican en HF1.2.

### Tabla A4.1.3. Dimensión HP, proveedor o canal

| Código SHA | Proveedor |
|---|---|
| HP1 | Atención primaria. |
| HP3 | Hospital. |
| HP52 | Farmacia comunitaria, canal retail comercial. |

Conviene distinguir el canal del producto. El canal retail (Cruz Verde, Salcobrand, Ahumada, farmacia de barrio, Cenabast retail adherido) corresponde a HP52. La función HC51 puede dispensarse en cualquiera de los tres canales: HP52 retail, HP1 APS, HP3 ambulatorio hospitalario. Esta distinción es relevante para entender por qué dos cifras aparentemente comparables del gasto público pueden diferir según qué combinación HC × HP × HF se considere.

## A4.2 Dos cifras de gasto público y su triangulación

El informe utiliza dos cifras válidas del gasto público en medicamentos, con denominadores ligeramente distintos. Ambas son consistentes con la metodología SHA, y la diferencia entre ellas se explica por la cobertura de medicamentos administrados durante la hospitalización.

### A4.2.1 Cifra OECD SHA HF1 sobre HC51

La primera cifra proviene del CSV OECD SHA oecd_sha_raw_from_drive.csv, descargado del portal OECD.Stat en abril de 2026. Cubre medicamentos ambulatorios financiados por el sistema público obligatorio (Fonasa, fracción obligatoria Isapre y presupuesto fiscal directo).

#### Tabla A4.2.1. Serie histórica HF1 sobre HC51 sobre PIB Chile

| Año | HF1 sobre HC51 sobre PIB |
|---|---|
| 2020 | 0,373% |
| 2021 | 0,339% |
| 2022 | 0,342% |
| 2023 | 0,371% |

La cifra redondeada a 0,34% (correspondiente a 2022) fue la utilizada en versiones anteriores del informe. Esta cifra excluye los medicamentos administrados durante la hospitalización interna (que se imputan a HC1, dentro del costo del egreso), los medicamentos hospitalarios oncológicos no separados del tratamiento (también HC1) y la fracción del PNI que SHA imputa a HC6 prevención.

### A4.2.2 Cifra CIF sobre UC 2025

La segunda edición del estudio "Caracterización del Gasto Público en Medicamentos en Chile" (Centro de Innovación Farmacéutica de la Universidad Católica y Escuela de Gobierno UC, octubre 2025) reporta el gasto público total en medicamentos para el año 2024 en MM$ 1.514.814 chilenos, equivalente a USD 1.583 millones al tipo de cambio promedio del período. Esta cifra representa el 0,46% del PIB y el 8,79% de la Partida 16 del MINSAL. Como antecedente, el estudio reporta una variación real interanual de −5,57% entre 2023 y 2024.

A diferencia de la cifra OECD HC51, la metodología CIF agrega componentes adicionales: los medicamentos hospitalarios reasignados desde HC1, las transferencias a los Servicios de Salud, las transferencias a APS, las vacunas del PNI y el gasto judicial vía recursos de protección.

### A4.2.3 Triangulación con suma de programas

Cuando el gasto se desglosa por programa con datos Dipres y CIF sobre UC 2025, la suma de programas con presupuesto verificable triangula con la cifra agregada CIF.

#### Tabla A4.2.3. Programas con presupuesto verificable

| Programa | Presupuesto 2024-2025 (MM$) | % del total |
|---|---|---|
| Servicios de Salud (29 SS y hospitales) | ~920.000 (2024) | 60,8% |
| APS y municipios (FOFAR + Arsenal) | ~240.000 (2024) | 15-18% |
| Programa Nacional de Inmunizaciones (PNI) | 176.876 (2025) | 11,7% |
| Ley Ricarte Soto | 175.672 (2025) | 11,5% |
| Drogas Alto Costo (DAC, Glosa 11) | 70.803 (2025) | 4,7% |
| Vía judicial (recursos de protección) | 81.000 (2024) | 5,3% |
| GES Fonasa medicamentos | n/d (sin glosa segregada) | (no consolidado) |
| CAEC Isapres porción medicamentos | n/d (no publicado) | (no consolidado) |
| Total verificable (CIF sobre UC 2025) | 1.514.814 (2024) | 100% |

La decisión editorial de la versión 4.0 fue utilizar 0,46% como cifra principal y mencionar 0,34% como referencia comparativa retail-only OECD SHA HC51. Ambas son válidas y reflejan denominadores con cobertura distinta.

## A4.3 Cubo OMS aplicado a Chile

El cubo OMS estructura el aporte de cada programa al gasto agregado mediante una identidad multiplicativa. La fórmula es:

> Aporte HF1 sobre HC51 del programa = Población elegible × Cobertura efectiva × Beneficio promedio × Precio anual promedio

Donde la población elegible representa el número de personas con la condición clínica que el programa podría cubrir; la cobertura efectiva, el porcentaje de elegibles que efectivamente acceden, sujeto a restricciones de presupuesto, listas cerradas y brechas geográficas; el beneficio, el porcentaje del costo del tratamiento financiado por el programa; y el precio anual, el costo promedio del tratamiento por persona-año.

### Tabla A4.3. Aporte por programa, datos verificados 2024-2025

| Programa | Pob. elegible (% pob CL 20,1M) | Cobertura efectiva | Beneficio | Patologías | Presupuesto verificable (MM$) | Fuente |
|---|---|---|---|---|---|---|
| Servicios de Salud (red secundaria y terciaria) | toda Fonasa atendida en red, ~80% | parcial, depende de dispensación local | 100% (gratuito en red pública) | toda red | ~920.000 (2024) | CIF sobre UC 2025; SINIM |
| APS, FOFAR y Arsenal | ~30% pob (crónicos en APS Fonasa) | 50-60% (acceso APS efectivo) | 100% (gratuito) | HTA, DM2, dislipidemia, esenciales | ~240.000 (2024) [verificar glosa precisa] | MINSAL APS / CIF |
| PNI (vacunas) | universal | 95-98% calendario | 100% | ~16 vacunas | 176.876 (2025) | Dipres Cap. 09 asig. 002 |
| Ley Ricarte Soto | ~0,33% pob (65.351 acumulado a 2024) | 100% en elegibles | 100% | 27 patologías (Decreto 4° / 2019) | 175.672 (2025) | Dipres Cap. 02 asig. 410 |
| DAC Glosa 11 | ~0,1% pob (oncológicos no GES no LRS) | 85% solicitantes | 100% | drogas oncológicas no GES | hasta 70.803 (2025) | Dipres Glosa 11 |
| Recursos de protección (vía judicial) | huecos del sistema | 100% en sentencias favorables | variable | medicamentos huérfanos | 81.000 (2024) | Fonasa cuenta pública |
| GES Fonasa medicamentos | 87 problemas, incidencia anual ~30% pob | 70% diagnósticos confirmados | 80-100% según copago | 87 problemas | sin glosa segregada [verificar] | Decreto MINSAL 2025-2028 |
| GES Isapre medicamentos (HF1.2) | 87 problemas, afiliados Isapre ~16% pob | 70% diagnósticos | 80% (copago) | ídem | no publicado [verificar] | Superintendencia de Salud |
| CAEC Isapre porción meds | ~16% pob Isapre | 10% (criterio catastrófico activo) | 80-100% post-deducible | sin lista cerrada | no publicado [verificar] | Reglamento Sup. Salud 11 / 2008 |
| Cenabast Ley 21.198 (retail) | hogares en farmacias adheridas | voluntaria por farmacia | subsidio cruzado vía precio | catálogo CEM | $17.640 facturado y $26.824 ahorro hogares (2024) | Anuario Cenabast 2024 |
| Bonificación complementarios privados | ~25% pob con seguro complementario | varía por plan | 30-70% reembolso | ambulatorio según plan | HF2 SHA = 0,04% PIB | Superintendencia de Salud |

Sin embargo, tres componentes no admiten una cifra agregada pública. GES Fonasa medicamentos no dispone de glosa presupuestaria segregada que permita aislar el componente farmacéutico de las prestaciones. GES Isapre medicamentos no es publicado. La porción farmacéutica del CAEC Isapre tampoco. Estos tres vacíos constituyen un problema de transparencia presupuestaria que el informe levanta como hallazgo independiente y como condición previa para la calibración fina de cualquier escenario de reforma.

## A4.4 Encuesta de Presupuestos Familiares (EPF IX 2021-2022)

### A4.4.1 Fuente y procesamiento

La fuente de gasto del bolsillo del hogar es la novena Encuesta de Presupuestos Familiares (EPF IX), levantada por el Instituto Nacional de Estadísticas entre 2021 y 2022. La muestra incluye 14.961 hogares con factor de expansión fe que pondera a 4.374.477 hogares totales. El gasto en medicamentos se aísla mediante el filtro CCIF 06.1.1 (productos farmacéuticos), que captura la compra directa en farmacia comercial y excluye la dispensación gratuita en establecimientos públicos.

### A4.4.2 Quintilización ponderada

Los quintiles se construyen sobre el ingreso disponible per cápita del hogar (ing_disp_hog_hd_pc), ponderado por fe, mediante el método del cumsum:

`python
df_sorted = df.sort_values("ing_disp_hog_hd_pc")
df_sorted["share"] = df_sorted["fe"].cumsum() / df_sorted["fe"].sum()
df_sorted["quintil"] = np.searchsorted([0.2, 0.4, 0.6, 0.8, 1.0], df_sorted["share"]) + 1


Este procedimiento garantiza que cada quintil concentre el 20% de los hogares ponderados, no el 20% de la muestra simple. La diferencia es relevante porque la muestra EPF sobre-representa hogares urbanos del Gran Santiago.

### A4.4.3 Resultados por quintil

#### Tabla A4.4.3. Gasto medio en medicamentos por quintil de ingreso per cápita

| Quintil pc | Hogares ponderados | Ingreso pc medio (CLP/mes) | Gasto medio en meds (CLP/mes) | % sin gasto |
|---|---|---|---|---|
| Q1 | 874.629 | $183.504 | $16.526 | 80% |
| Q2 | 874.620 | $307.868 | $21.942 | 65% |
| Q3 | 875.364 | $411.502 | $27.681 | 55% |
| Q4 | 874.936 | $592.399 | $36.882 | 35% |
| Q5 | 874.929 | $1.286.208 | $61.290 | 20% |

### A4.4.4 Distribución de la carga relativa al ingreso

La distribución de la carga del gasto en medicamentos respecto del ingreso per cápita se reporta para seis umbrales.

#### Tabla A4.4.4. Hogares con gasto en medicamentos sobre ingreso pc por umbral

| Umbral gasto / ingreso pc | % hogares | Hogares ponderados |
|---|---|---|
| > 0% (cualquier gasto) | 53,1% | 2.323.000 |
| > 1% | 41,2% | 1.802.000 |
| > 2,5% | 30,5% | 1.334.000 |
| > 5% | 23,4% | 1.024.000 |
| > 10% | 21,8% | 953.000 |
| > 20% | 18,5% | 809.000 |

El indicador clave del informe es el 21,8% de hogares con gasto en medicamentos superior al 10% de su ingreso per cápita, equivalente a 953.000 hogares en términos ponderados.

### A4.4.5 Gasto OOP retail anualizado

La extrapolación a 12 meses del gasto medio mensual ponderado da $143,8 mil millones CLP/mes, esto es $1.725 mil millones CLP/año. Al tipo de cambio promedio 2024 de USD/CLP 945,22 (SII), corresponde a USD 1.917 millones/año. Como porcentaje del PIB Chile 2024 (USD 330,3 mil millones, Banco Mundial), el gasto OOP retail anualizado representa 0,58% del PIB. Esta cifra es comparable, sin coincidir, con la imputación SHA HF3 sobre HC51 sobre PIB de 2022 (0,956%). La diferencia se explica porque la EPF capta solo el gasto declarado en farmacia retail, mientras que SHA suma estimaciones más amplias que incluyen copagos hospitalarios ambulatorios y compra de medicamentos sin receta no siempre reportados.

## A4.5 Calibración del tope BFU

### A4.5.1 Política simulada

El Beneficio Farmacéutico Universal (BFU) se simula como un subsidio que cubre el exceso del gasto del hogar sobre un tope. La regla operativa es:

> subsidio_hogar = max(0, gasto_meds − tope)

El tope admite tres formas funcionales: proporcional al ingreso per cápita (tope_pct × ingreso_pc), proporcional al ingreso total del hogar (tope_pct × ingreso_total_hogar) o monto fijo en pesos (tope_clp). El informe principal utiliza la formulación proporcional al ingreso per cápita por dos razones. La primera es comparabilidad internacional con el Belastungsgrenze alemán. La segunda es equidad horizontal en un país con dispersión amplia de ingresos.

### A4.5.2 Búsqueda inversa, qué tope para qué presupuesto

Asumiendo USD/CLP de 945, una búsqueda binaria sobre la EPF produce el siguiente mapa de equivalencias entre presupuesto fiscal anual y nivel del tope.

#### Tabla A4.5.2. Equivalencias presupuesto-tope BFU

| Presupuesto USD/año | Presup. CLP MMM/mes | Tope % ingreso pc | Tope % ingreso total | Tope monto fijo CLP/mes |
|---|---|---|---|---|
| 400 M | 31,5 | 31,3% | 6,8% | $144.066 |
| 600 M | 47,3 | 20,2% | 4,4% | $98.851 |
| 800 M | 63,0 | 13,6% | 3,0% | $70.160 |
| 1.080 M | 85,1 | 8,0% | 1,7% | $43.130 |
| 1.500 M | 118,1 | 3,0% | 0,6% | $16.967 |
| 2.000 M | 157,5 | 0% (subsidio total) | 0% | $0 |

### A4.5.3 Lectura de la tabla

Para un presupuesto de USD 800-900 millones anuales (escenario 2 BFU del capítulo 6), el tope corresponde a 13-15% del ingreso per cápita o aproximadamente $70.000 CLP/mes por persona. Para el escenario 3 OECD plena (USD 2.500 millones o más), el tope tiende a cero y el sistema cubre el grueso del gasto retail. Respecto de la comparación con el Belastungsgrenze alemán (2% del ingreso bruto anual del hogar), Chile partiría con un tope mayor (13-15%) por menor base fiscal disponible y convergería a 5-7% en horizonte mediano si se materializa el aumento de carga tributaria comprometido en la Estrategia Fiscal 2024-2028.

Cabe señalar que esta sección documenta una metodología de calibración. La defensa de la propuesta BFU como tal corresponde al capítulo 6 del informe principal.

## A4.6 Modelo OMS aplicado a LRS, validación parcial

### A4.6.1 Lista actual

La Ley Ricarte Soto (Decreto 4° de 2019, vigente) cubre 27 patologías de alto costo. La población acumulada hasta 2024 alcanza a 65.351 personas, según cuenta pública Fonasa.

### A4.6.2 Datos disponibles

La validación parcial se realizó sobre el proyecto archivado archives/illanes00-cif/`, que contiene un technology master con 1.601 entradas. De las 27 patologías LRS, 10 cuentan con prevalencia documentada en literatura chilena o internacional (37%). De las 1.363 tecnologías únicas, 125 cuentan con precio referencial, utilizando NADAC (Estados Unidos) como proxy a falta de un registro nacional consolidado de precios de medicamentos de alto costo (9% de cobertura).

### A4.6.3 Patologías con prevalencia documentada

#### Tabla A4.6.3. Patologías LRS con prevalencia disponible

| Patología | Prevalencia | Personas estimadas | Elegibles |
|---|---|---|---|
| Artritis reumatoide | 0,46% pob | 92.396 | 13.524 |
| Enfermedad inflamatoria intestinal | 102/100k | 20.488 | 5.998 |
| Leucemia mieloide crónica | 15/100k | 3.013 | 3.013 |
| Fibrosis quística | 22/100k | 4.419 | 4.419 |
| Atrofia muscular espinal | 2/100k | 402 | 402 |
| Colitis ulcerosa | 72/100k | 14.462 | 4.339 |
| Psoriasis (severa) | 1,11% pob | 222.959 | 114.601 |
| Espondilitis anquilosante | 0,5% pob | 100.432 | 40.173 |
| Asma (severa) | 10,2% pob | 2.048.810 | 102.441 |
| Esclerosis múltiple | 12/100k | 2.410 | 2.410 |

El total de elegibles para estas 10 patologías asciende a 291.320 personas, equivalentes al 1,45% de la población chilena.

### A4.6.4 Brecha pendiente

Para validar de forma plena el cubo OMS contra el presupuesto LRS de MM$ 175.672 de 2025 falta documentar la prevalencia de las 17 patologías restantes, levantar precios chilenos reales (en lugar del proxy NADAC) y modelar la distribución de pacientes por tratamiento, considerando que no toda la prevalencia accede al tratamiento subsidiado. La recomendación operativa es completar el technology master en una segunda iteración del proyecto archivado y publicar el cálculo como anexo verificable en una versión posterior del informe.

## A4.7 Cuadro de doble entrada, desagregación completa del gasto en medicamentos

Esta sección presenta la pieza articuladora del anexo. La tabla A4.7 reúne en filas cada origen del gasto y en columnas las dimensiones SHA pertinentes (esquema de financiamiento HF, función HC, canal HP), los beneficiarios, el monto verificable en MM$ 2024 y la fuente. Las celdas no documentadas se marcan con n/d, acompañadas de una nota explicativa al pie. La tabla permite leer simultáneamente cómo se suman el gasto del Estado, el gasto privado obligatorio, el gasto voluntario privado y el gasto del bolsillo, a la vez que evidencia los vacíos de transparencia que el informe ya levantó en A4.3.

#### Tabla A4.7. Desagregación cruzada del gasto en medicamentos en Chile, 2024

| # | Origen del gasto | Esquema HF | Función HC | Canal HP | Beneficiarios | MM$ 2024 | Fuente |
|---|---|---|---|---|---|---|---|
| 1 | Servicios de Salud (red secundaria y terciaria) | HF1.1 | HC1 + HC51 | HP3 hospital + HP1 APS | Fonasa atendido en red pública | ~920.000 | CIF sobre UC 2025; SINIM |
| 2 | APS y FOFAR + Arsenal Farmacológico | HF1.1 | HC51 | HP1 APS municipal | Fonasa con condición crónica en APS | ~240.000 | CIF sobre UC 2025; MINSAL APS |
| 3 | PNI (vacunas) | HF1.1 | HC6 | HP1 APS y vacunatorios públicos | universal (toda la población) | 176.876 | Dipres Cap. 09 asig. 002 |
| 4 | Ley Ricarte Soto | HF1.1 | HC51 (alto costo) | HP3 hospital y HP1 APS | Fonasa e Isapre con patología LRS | 175.672 | Dipres Cap. 02 asig. 410 |
| 5 | DAC Glosa 11 | HF1.1 | HC51 (alto costo no LRS) | HP3 hospital | Fonasa con patología oncológica no GES no LRS | 70.803 | Dipres Glosa 11 |
| 6 | Vía judicial (recursos de protección) | HF1.1 | HC51 (huérfanos) | HP3 hospital | Fonasa e Isapre con sentencia favorable | 81.000 | Fonasa cuenta pública 2024 |
| 7 | GES Fonasa medicamentos | HF1.1 + HF1.2 | HC51 (canasta GES) | HP3 hospital y HP1 APS | Fonasa con dx GES confirmado | n/d (a) | Decreto MINSAL 2025-2028 |
| 8 | GES Isapre medicamentos | HF1.2 | HC51 (canasta GES) | HP3 prestadores Isapre | Isapre con dx GES confirmado | n/d (b) | Superintendencia de Salud |
| 9 | CAEC Isapre, porción farmacéutica | HF1.2 | HC51 (catastrófico) | HP3 hospital | Isapre con CAEC activado | n/d (c) | Reglamento Sup. Salud 11 / 2008 |
| 10 | Cenabast Ley 21.198 (retail) | HF1.1 (subsidio cruzado) + HF3 (precio final) | HC51 | HP52 farmacia retail adherida | hogares en farmacias adheridas (1.580 puntos) | 17.640 facturado; 26.824 ahorro hogares | Anuario Cenabast 2024 |
| 11 | Complementarios privados (reembolsos) | HF2.1 | HC51 | HP52 farmacia retail | ~25% pob con seguro complementario | n/d (d), HF2 SHA = 0,04% PIB | Superintendencia de Salud |
| 12 | OOP retail (gasto del bolsillo en farmacia) | HF3 | HC51 | HP52 farmacia retail comercial | toda la población (excluye dispensación pública) | 1.725.000 | EPF IX 2021-2022, anualizado |
| 13 | OOP hospitalario ambulatorio | HF3 | HC1 + HC51 | HP3 hospital | toda la población con copago hospitalario | n/d (e) | OECD SHA HF3 sobre HC51 |
| | Total verificable agregado público (filas 1-10) | | | | | ~2.681.991 | suma de filas verificables |
| | Total OOP retail (fila 12) | | | | | 1.725.000 | EPF IX |

Notas al pie de la tabla A4.7.

[p] • (a) GES Fonasa medicamentos. La canasta GES integra prestaciones, medicamentos y dispositivos en un único arancel por problema de salud. La glosa presupuestaria de Fonasa no segrega el componente farmacéutico, lo que impide aislar la cifra. El informe utiliza estimaciones indirectas (capítulo 4) con un rango de incertidumbre de ±20%.
[p] • (b) GES Isapre medicamentos. Isapre reporta la cobertura GES en agregado a la Superintendencia de Salud, sin desagregar el componente farmacéutico. La cifra no se publica. La estimación indirecta usada en el informe se basa en la proporción de afiliación (~16% Isapre) y el patrón GES Fonasa (capítulo 4).
[p] • (c) CAEC Isapre, porción farmacéutica. El CAEC se activa sobre el deducible en función del costo total del tratamiento catastrófico. La porción farmacéutica no se publica. Existen estimaciones basadas en case mix CAEC, con rango amplio.
[p] • (d) Complementarios privados. La Superintendencia de Salud reporta primas y siniestros agregados de seguros complementarios, sin desagregación por categoría de prestación. El SHA imputa HF2 sobre HC51 = 0,04% del PIB para 2022.
[p] • (e) OOP hospitalario ambulatorio. El gasto del bolsillo en medicamentos administrados durante atención ambulatoria hospitalaria se imputa parcialmente a HC1 y parcialmente a HC51 según SHA. La EPF no captura este flujo de forma directa.

Sin embargo, el agregado público verificable de la tabla A4.7 (sumando filas 1 a 10) excede la cifra CIF sobre UC 2025 reportada en A4.2.2 (MM$ 1.514.814) porque la fila 1 (Servicios de Salud) incluye gasto HC1 hospitalario que CIF reasigna y porque las filas 4 y 5 contabilizan compromiso presupuestario 2025, no ejecución 2024. El cuadro debe leerse como inventario completo de orígenes, con la advertencia de que la consolidación final a un solo año fiscal requiere la depuración HC1 sobre HC51 documentada en A4.1.

## A4.8 Datos macro Chile 2022-2025

#### Tabla A4.8. Datos macro de referencia

| Indicador | Valor | Año | Fuente |
|---|---|---|---|
| PIB Chile (CLP nominal) | $307,5 billones | 2024 | Dipres IFP 4T 2024 |
| PIB Chile (USD corrientes) | USD 330,27 mil millones | 2024 | Banco Mundial |
| Población Chile | 20.086.377 | 2024 | INE proyección base 2024 |
| Presupuesto Gobierno Central | $76,16 billones | 2024 | Dipres |
| Presupuesto MINSAL Partida 16 | $14,46 billones | 2024 | IPSUSS / Dipres |
| Presupuesto MINSAL Partida 16 | $16,03 billones (oficial) / $28,15 billones (suma capítulos) | 2025 | Senado / Dipres |
| Tipo de cambio promedio USD/CLP | 945,22 | 2024 | SII |
| Tipo de cambio promedio USD/CLP | 880,52 | 2022 | SII |

## A4.9 Glosario

[p] • HC51. Función SHA, medicamentos y bienes médicos no durables ambulatorios.
[p] • HC1. Función SHA, atención curativa, incluye medicamentos administrados durante hospitalización.
[p] • HF1. Esquema SHA, gobierno y cotización obligatoria.
[p] • HF1.1. Subset HF1, gobierno por impuestos generales.
[p] • HF1.2. Subset HF1, cotización obligatoria por mandato legal.
[p] • HF2. Esquema SHA, voluntario adicional (planes premium, complementarios).
[p] • HF3. Esquema SHA, bolsillo del hogar.
[p] • OOP. Out of pocket, gasto del bolsillo del hogar.
[p] • Retail. Canal de dispensación, farmacia comunitaria comercial (Cruz Verde, Salcobrand, Ahumada y similares).
[p] • APS. Atención primaria de salud, pública y gratuita.
[p] • CCIF 06.1.1. Clasificación de Consumo Individual por Finalidad, productos farmacéuticos.
[p] • fe. Factor de expansión EPF, pondera la muestra a hogares totales.
[p] • NADAC. National Average Drug Acquisition Cost, registro de precios de Estados Unidos utilizado como proxy a falta de registro chileno consolidado.
[p] • SHA. System of Health Accounts 2011 (OECD/Eurostat/WHO).
