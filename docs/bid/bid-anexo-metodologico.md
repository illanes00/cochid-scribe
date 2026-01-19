# Anexo Metodológico - Estudio de Gasto Público en Seguridad

**Documento complementario al Informe BID Seguridad Ciudadana**
**Espacio Público | Enero 2026**

---

## Tabla de Contenidos

1. [Clasificación Funcional COFOG](#1-clasificación-funcional-cofog)
2. [Niveles de Gobierno](#2-niveles-de-gobierno)
3. [Metodología de Conversión a US$ PPA](#3-metodología-de-conversión-a-us-ppa)
4. [Fuentes de Datos](#4-fuentes-de-datos)
5. [Limitaciones del Análisis](#5-limitaciones-del-análisis)
6. [Glosario de Términos](#6-glosario-de-términos)
7. [Referencias Metodológicas](#7-referencias-metodológicas)

---

## 1. Clasificación Funcional COFOG

### 1.1 Origen y Estándar Internacional

La **Clasificación de las Funciones del Gobierno** (COFOG, por sus siglas en inglés: *Classification of Functions of Government*) es un estándar internacional desarrollado por las Naciones Unidas y adoptado por el Fondo Monetario Internacional en el *Government Finance Statistics Manual* (GFSM).

**Objetivo**: Permitir la comparación internacional del gasto público clasificado por propósito o función, independientemente de la estructura administrativa de cada país.

**Versión utilizada**: COFOG 1999, actualizada en GFSM 2014.

### 1.2 Estructura de COFOG

COFOG tiene tres niveles jerárquicos:

| Nivel | Dígitos | Ejemplo | Descripción |
|-------|---------|---------|-------------|
| División | 2 | 03 | Orden público y seguridad |
| Grupo | 3 | 031 | Servicios de policía |
| Clase | 4 | 0311 | Administración policial |

### 1.3 División 703: Orden Público y Seguridad

El presente estudio se centra en la **División 703** (o 03 en notación de 2 dígitos), que comprende:

| Código | Subfunción | Descripción | Instituciones típicas Chile |
|--------|------------|-------------|---------------------------|
| **7031** | Servicios de policía | Operaciones policiales, patrullaje, control de fronteras, investigación criminal, formación policial | Carabineros de Chile, PDI |
| **7032** | Protección contra incendios | Prevención y extinción de incendios, operaciones de rescate, protección civil | Bomberos de Chile (subsidio estatal) |
| **7033** | Tribunales de justicia | Administración de justicia, operación de tribunales, fiscalías, defensoría | Poder Judicial, Ministerio Público, DPP |
| **7034** | Prisiones | Operación del sistema penitenciario, custodia de reclusos, programas de reinserción | Gendarmería de Chile |
| **7035** | I+D en orden público | Investigación aplicada, desarrollo tecnológico, evaluación de políticas | (No clasificado en Chile) |
| **7036** | N.E.P.* | Gasto no clasificable en anteriores | Varios programas menores |

*N.E.P.: No Especificado Previamente

### 1.4 COFOG-Chile: Adaptación Nacional

Chile implementa COFOG a través de DIPRES, con algunas particularidades:

#### Mapeo institucional

| Institución | Subfunción COFOG principal | Observaciones |
|-------------|---------------------------|---------------|
| Carabineros de Chile | 7031 | Incluye funciones preventivas |
| Policía de Investigaciones (PDI) | 7031 | Policía civil investigativa |
| Ministerio Público | 7033 | Fiscales y persecución penal |
| Poder Judicial | 7033 | Tribunales (no solo penales) |
| Defensoría Penal Pública | 7033 | Defensa pública |
| Gendarmería de Chile | 7034 | Sistema penitenciario |
| Bomberos de Chile | 7032 | Transferencia al Cuerpo de Bomberos |
| Subsecretaría Prevención del Delito | 7036 | Programas de prevención |

#### Limitaciones del mapeo chileno

1. **No publicidad del diccionario**: DIPRES no publica la tabla de correspondencia entre partidas/ítems presupuestarios y códigos COFOG
2. **Programas transversales**: Algunos programas de prevención pueden estar en otras funciones (educación, salud)
3. **Subfunción 7035 vacía**: Chile no clasifica gasto en I+D en seguridad, aunque pueda existir disperso en otras categorías

### 1.5 Qué NO incluye COFOG 703

Para interpretar correctamente las cifras, es importante notar que COFOG 703 **no incluye**:

| Excluido | Clasificación COFOG | Razón |
|----------|---------------------|-------|
| Fuerzas Armadas | 702 (Defensa) | Seguridad externa, no ciudadana |
| Seguridad privada | No es gasto público | Gasto de hogares y empresas |
| Seguridad municipal | Gobierno subnacional* | No en Gobierno Central |
| Programas de salud mental | 707 (Salud) | Aunque vinculados a reinserción |
| Educación en recintos penales | 709 (Educación) | Aunque ejecutada en cárceles |

*En análisis de Gobierno General sí se incluye.

---

## 2. Niveles de Gobierno

### 2.1 Definiciones según GFSM 2014

El análisis del gasto público requiere especificar el nivel institucional:

| Nivel | Definición | Incluye | Excluye |
|-------|------------|---------|---------|
| **Gobierno Central** | Unidades institucionales que ejercen autoridad sobre todo el territorio | Ministerios, servicios públicos centrales | Municipios, empresas públicas |
| **Gobierno General** | Gobierno Central + Gobiernos locales + Fondos de seguridad social | Todo lo anterior + municipios + fondos | Empresas públicas, Banco Central |
| **Sector Público** | Gobierno General + Empresas públicas | Todo lo anterior + empresas estatales | Sector privado |

### 2.2 Aplicación en el Estudio

| Análisis | Nivel usado | Justificación |
|----------|-------------|---------------|
| **Chile (serie 2013-2024)** | Gobierno Central | Datos disponibles, consistencia temporal |
| **Comparación OCDE** | Gobierno General | Estándar internacional OCDE |
| **Comparación LATAM** | Gobierno General (cuando disponible) | Comparabilidad |

### 2.3 Implicancias para la Interpretación

#### Diferencia entre niveles en Chile

| Subfunción | Gobierno Central | Gobierno General |
|------------|------------------|------------------|
| Policías | Carabineros, PDI | + Seguridad municipal |
| Bomberos | Transferencia central | + Aportes municipales |
| Justicia | Poder Judicial, MP, DPP | Similar |
| Prisiones | Gendarmería | Similar |

**Implicancia**: Las cifras de Gobierno Central **subestiman** levemente el esfuerzo total en seguridad, especialmente en municipios con inversión propia en seguridad ciudadana.

### 2.4 Ajuste para Comparación Internacional

Para comparar Chile con la mediana OCDE:

1. **OCDE reporta**: Gobierno General
2. **Chile reporta**: Gobierno Central (dato primario)
3. **Ajuste sugerido**: Factor +5-10% para aproximar GG desde GC

Este ajuste es una aproximación; la diferencia real depende de la estructura fiscal de cada país.

---

## 3. Metodología de Conversión a US$ PPA

### 3.1 ¿Por qué usar PPA?

La **Paridad del Poder Adquisitivo** (PPA) ajusta las cifras monetarias para reflejar diferencias en el costo de vida entre países.

| Método | Definición | Uso |
|--------|------------|-----|
| **Tipo de cambio de mercado** | Conversión a tasa corriente (USD/CLP) | Comercio internacional |
| **PPA** | Conversión usando canasta de bienes equivalente | Comparación de bienestar |

**Ejemplo**: Si US$1 compra una canasta en EE.UU., ¿cuántos CLP compran la misma canasta en Chile?

### 3.2 Fuentes de factores PPA

| Fuente | Cobertura | Actualización | URL |
|--------|-----------|---------------|-----|
| **FMI (WEO)** | 190+ países | Semestral | imf.org/weo |
| **Banco Mundial (ICP)** | 170+ países | Irregular | worldbank.org |
| **OCDE** | Países miembros | Anual | stats.oecd.org |

### 3.3 Fórmula de conversión

```
Gasto en US$ PPA = Gasto en CLP / Factor PPA (CLP por US$ PPA)
```

#### Ejemplo 2024

| Variable | Valor | Fuente |
|----------|-------|--------|
| Gasto seguridad Chile 2024 | CLP 4.470.000 millones | DIPRES |
| Factor PPA 2024 | ~440 CLP/US$ PPA | FMI WEO (estimar) |
| Gasto en US$ PPA | ~US$ 10.159 millones | Cálculo |
| Población Chile 2024 | ~19,9 millones | INE |
| **Gasto per cápita PPA** | **~US$ 511** | Cálculo |

### 3.4 Consideraciones importantes

1. **Año del factor PPA**: Usar el mismo año que el dato de gasto
2. **Fuente consistente**: No mezclar PPA de FMI con OCDE en misma comparación
3. **PPA de consumo vs. gobierno**: Idealmente usar PPA específico para consumo de gobierno, no general

### 3.5 Limitaciones de PPA

| Limitación | Implicancia |
|------------|-------------|
| Canasta de referencia genérica | No captura costos específicos de seguridad |
| Actualización irregular | Datos pueden estar desactualizados |
| Diferencias metodológicas | FMI y OCDE pueden diferir |

---

## 4. Fuentes de Datos

### 4.1 Fuentes Primarias Chile

| Fuente | Institución | Variables | Acceso |
|--------|-------------|-----------|--------|
| **Estadísticas de Finanzas Públicas** | DIPRES | Gasto por función COFOG | dipres.gob.cl |
| **Ley de Presupuestos** | DIPRES | Presupuesto inicial por partida | bcn.cl |
| **ENUSC** | INE/SPD | Victimización, percepción | ine.gob.cl |
| **CEAD** | Min. Interior | Estadísticas delictuales | cead.spd.gov.cl |
| **Boletín Estadístico** | Ministerio Público | Causas, formalizaciones | fiscaliadechile.cl |
| **Encuestas CEP** | CEP | Percepción, prioridades | cepchile.cl |
| **Cuentas Nacionales** | Banco Central | PIB | bcentral.cl |

### 4.2 Fuentes Internacionales

| Fuente | Organismo | Variables | Acceso |
|--------|-----------|-----------|--------|
| **Government at a Glance** | OCDE | Gasto por función, comparado | oecd.org |
| **Government Finance Statistics** | FMI | Gasto por función | data.imf.org |
| **World Economic Outlook** | FMI | PIB, PPA | imf.org/weo |
| **UNODC** | Naciones Unidas | Homicidios internacionales | unodc.org |

### 4.3 Período de Datos

| Variable | Período | Frecuencia | Última actualización |
|----------|---------|------------|---------------------|
| Gasto COFOG Chile | 2013-2024 | Anual | 2025 (dato 2024) |
| Comparación OCDE | 2015-2023 | Anual | GAG 2025 |
| Victimización | 2013-2024 | Anual | ENUSC 2024 |
| Homicidios | 2013-2024 | Anual | CEAD 2024 |

### 4.4 Panel de Visualización

El estudio se apoya en visualizaciones disponibles en:

**graphs.illanes00.cl** - Panel de Gasto Público
- Versión de datos: `output/version_20251230_200135`
- Figuras relevantes: 7-22 (seguridad), 38-49 (comparación internacional)

---

## 5. Limitaciones del Análisis

### 5.1 Limitaciones de Datos

| Limitación | Descripción | Impacto | Mitigación |
|------------|-------------|---------|------------|
| **No publicidad del mapeo COFOG** | DIPRES no publica correspondencia programa→COFOG | No se puede desagregar por programa | Usar agregados disponibles |
| **Datos de ejecución vs. presupuesto** | Serie usa ejecución; presupuesto inicial difiere | Comparación intertemporal afectada | Mantener criterio consistente |
| **Gobierno Central vs. General** | Excluye gasto municipal | Subestima esfuerzo total | Ajustar para comparación internacional |
| **Rezago de publicación** | Datos OCDE con 1-2 años de rezago | Comparación no es contemporánea | Usar último año disponible |

### 5.2 Limitaciones Metodológicas

| Limitación | Descripción | Impacto |
|------------|-------------|---------|
| **Clasificación funcional ≠ efectividad** | COFOG mide insumos, no resultados | No indica si gasto es eficiente |
| **Heterogeneidad institucional** | "Policía" incluye funciones diversas | Agregación oculta diferencias |
| **Comparación internacional** | Países clasifican distinto | Comparación es aproximada |
| **Enfoque descriptivo** | Sin identificación causal | No concluye sobre efectos |

### 5.3 Limitaciones de Alcance

| Aspecto | Incluido | Excluido |
|---------|----------|----------|
| **Temporal** | 2013-2024 | Pre-2013, proyecciones post-2024 |
| **Territorial** | Nacional (GC) | Desagregación regional |
| **Funcional** | COFOG 703 | Otras funciones con componente de seguridad |
| **Análisis** | Descriptivo | Evaluación de impacto, análisis causal |

### 5.4 Supuestos del Análisis

1. **Consistencia metodológica**: DIPRES mantiene criterios de clasificación constantes en el período
2. **Calidad de registros**: Datos oficiales reflejan gasto efectivo
3. **Comparabilidad internacional**: Países OCDE aplican COFOG de manera comparable
4. **Estabilidad de PPA**: Factores PPA son aproximaciones razonables del poder adquisitivo

---

## 6. Glosario de Términos

### Términos Presupuestarios

| Término | Definición |
|---------|------------|
| **Gasto devengado** | Obligación de pago legalmente exigible, independiente del pago efectivo |
| **Gasto ejecutado** | Gasto efectivamente pagado en el período |
| **Presupuesto inicial** | Asignación aprobada en Ley de Presupuestos |
| **Presupuesto vigente** | Presupuesto inicial + modificaciones del año |

### Términos COFOG

| Término | Definición |
|---------|------------|
| **División** | Primer nivel de clasificación (2 dígitos) |
| **Grupo** | Segundo nivel de clasificación (3 dígitos) |
| **Subfunción** | Tercer nivel de clasificación (4 dígitos) |
| **N.E.P.** | No Especificado Previamente |

### Términos Económicos

| Término | Definición |
|---------|------------|
| **PPA** | Paridad del Poder Adquisitivo |
| **Per cápita** | Dividido por población |
| **Términos reales** | Ajustado por inflación |
| **Términos nominales** | Sin ajuste por inflación |

### Términos de Seguridad

| Término | Definición |
|---------|------------|
| **DMCS** | Delitos de Mayor Connotación Social |
| **Tasa de victimización** | % de hogares/personas víctimas de delito |
| **Tasa de denuncia** | % de delitos que se denuncian |
| **Cifra negra** | Delitos no denunciados |

---

## 7. Referencias Metodológicas

### Manuales y Estándares

1. **FMI (2014)**. *Government Finance Statistics Manual 2014*. Washington, DC: International Monetary Fund.
   - Capítulo 6: Classification of Expense
   - Anexo: COFOG codes

2. **Naciones Unidas (1999)**. *Classification of the Functions of Government (COFOG)*. Series M, No. 84.

3. **OCDE (2023)**. *Government at a Glance 2023*. Paris: OECD Publishing.
   - Metodología de comparación internacional

### Fuentes de Datos Chile

4. **DIPRES**. *Estadísticas de las Finanzas Públicas*. Ministerio de Hacienda.
   - Series históricas de gasto por función

5. **INE/SPD**. *Encuesta Nacional Urbana de Seguridad Ciudadana (ENUSC)*. Metodología 2024.

6. **Ministerio Público**. *Boletín Estadístico Anual 2024*. Fiscalía de Chile.

### Literatura Académica de Referencia

7. **Becker, G.S. (1968)**. "Crime and Punishment: An Economic Approach". *Journal of Political Economy*, 76(2), 169-217.

8. **Chalfin, A., & McCrary, J. (2018)**. "Are U.S. Cities Underpoliced? Theory and Evidence". *Review of Economics and Statistics*, 100(1), 167-186.

9. **Sherman, L.W., et al. (1997)**. *Preventing Crime: What Works, What Doesn't, What's Promising*. Washington, DC: National Institute of Justice.

10. **BID (2023)**. *El Costo del Crimen en América Latina y el Caribe*. Washington, DC: Banco Interamericano de Desarrollo.

---

## Anexo: Checklist de Verificación Metodológica

Para cada cifra publicada, verificar:

- [ ] Fuente primaria identificada
- [ ] Año/período especificado
- [ ] Nivel de gobierno (GC/GG) indicado
- [ ] Unidad de medida clara (CLP/USD/PPA)
- [ ] Términos (nominal/real) especificados
- [ ] Limitaciones reconocidas
- [ ] Comparable con otras cifras del documento

---

*Documento preparado por Espacio Público*
*Metodología sujeta a revisión y actualización*
*Última actualización: Enero 2026*
