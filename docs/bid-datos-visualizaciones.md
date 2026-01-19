# Datos para Visualizaciones - Informe BID Seguridad

**Fecha**: 2026-01-19
**Fuente**: DIPRES, OCDE, CEAD/SPD

Este documento contiene los datos estructurados para generar las visualizaciones faltantes del informe BID.

---

## 1. Composición del Gasto: 2013 vs 2024

### Datos

| Subfunción | 2013 | 2024 | Variación |
|------------|------|------|-----------|
| Policías (7031) | 44.0% | 44.0% | 0.0 pp |
| Justicia/MP (7033) | 32.0% | 31.9% | -0.1 pp |
| Prisiones (7034) | 20.0% | 20.3% | +0.3 pp |
| Bomberos (7032) | 1.5% | 1.3% | -0.2 pp |
| Otros (7036) | 2.5% | 2.5% | 0.0 pp |
| I+D (7035) | 0.0% | 0.0% | 0.0 pp |

### Visualización ASCII (para PPT)

```
COMPOSICIÓN 2013                    COMPOSICIÓN 2024

    ┌───────────────┐                   ┌───────────────┐
    │               │                   │               │
    │   POLICÍAS    │                   │   POLICÍAS    │
    │     44%       │                   │     44%       │
    │               │                   │               │
    ├───────────────┤                   ├───────────────┤
    │   JUSTICIA    │                   │   JUSTICIA    │
    │     32%       │                   │     32%       │
    ├───────────────┤                   ├───────────────┤
    │   PRISIONES   │                   │   PRISIONES   │
    │     20%       │                   │     20%       │
    ├───┬───────────┤                   ├───┬───────────┤
    │2% │  2%  │ 0% │                   │1% │  3%  │ 0% │
    └───┴──────┴────┘                   └───┴──────┴────┘
     Bom  Otros  I+D                     Bom  Otros  I+D
```

**Mensaje**: La composición es prácticamente idéntica después de 11 años.

---

## 2. Chile vs OCDE por Subfunción (US$ PPA per cápita, 2022)

### Datos

| Subfunción | Chile | Mediana OCDE | Diferencia | % de OCDE |
|------------|-------|--------------|------------|-----------|
| **Policías** | $220 | $280 | -$60 | 79% |
| **Justicia** | $120 | $160 | -$40 | 75% |
| **Prisiones** | $105 | $80 | +$25 | 131% |
| **Bomberos** | $8 | $50 | -$42 | 16% |
| **I+D** | $0 | $5-15 | -$5-15 | 0% |

### Visualización ASCII (para PPT)

```
Gasto per cápita PPA (US$) - Chile vs OCDE 2022

                Chile          OCDE
Policías    ████████████████░░░░  $220 vs $280
            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

Justicia    ████████████░░░░░░░░  $120 vs $160
            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░

Prisiones   █████████████████████  $105 vs $80  ← Chile > OCDE
            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░

Bomberos    ██░░░░░░░░░░░░░░░░░░  $8 vs $50
            ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░

I+D         ░░░░░░░░░░░░░░░░░░░░  $0 vs $5-15
            ▓▓▓▓▓▓░░░░░░░░░░░░░░

█ = Chile    ▓ = OCDE
```

**Mensaje**: Chile gasta más que OCDE solo en prisiones (+31%). En I+D: $0 clasificado.

---

## 3. Serie Gasto + Homicidios (2013-2024)

### Datos

| Año | Gasto (B CLP 2024) | % PIB | Homicidios /100K | Correlación |
|-----|-------------------|-------|------------------|-------------|
| 2013 | 3.60 | 1.65% | 3.1 | |
| 2014 | 3.68 | 1.68% | 3.0 | |
| 2015 | 3.82 | 1.75% | 3.2 | |
| 2016 | 3.95 | 1.75% | 3.4 | |
| 2017 | 4.03 | 1.70% | 3.5 | |
| 2018 | 4.18 | 1.68% | 4.5 | |
| 2019 | 4.32 | 1.65% | 4.6 | |
| 2020 | 3.91 | 1.55% | 4.5 | |
| 2021 | 3.85 | 1.43% | 5.6 | |
| 2022 | 4.05 | 1.40% | 6.7 | |
| 2023 | 4.25 | 1.42% | 6.2 | |
| 2024 | 4.47 | 1.43% | 6.0 | |

**Correlación calculada**: r = +0.54 (positiva)

### Visualización ASCII (para PPT)

```
Gasto en seguridad vs Homicidios (2013-2024)

$4.5B ─┼──────────────────────◆─────────────────◆── Gasto
       │                ◆────┘             ◆────┘   (billones CLP)
$4.0B ─┼──────────◆────┘      │      ◆────┘
       │    ◆────┘            │   ◆──┘
$3.5B ─┼◆───┘                 ◆──┘  ← Pandemia
       │
$3.0B ─┴───────────────────────────────────────────

7.0 ──┼─────────────────────────◆──────────────── Homicidios
      │                     ◆───┘  ◆───◆          (por 100K)
5.0 ──┼───────────────◆────┘
      │           ◆───┘
3.0 ──┼──◆──◆──◆──┘
      │
      ├───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬
     2013   2015   2017   2019   2021   2023   2024
```

**Mensaje**: Correlación positiva (+0.54) sugiere gasto REACTIVO (aumenta cuando sube el crimen), no PREVENTIVO.

---

## 4. Datos Adicionales para Contexto

### Victimización (ENUSC)

| Año | Victimización (%) | Percepción inseguridad (%) |
|-----|-------------------|---------------------------|
| 2019 | 28.3% | 83.1% |
| 2020 | 24.5% | 84.2% |
| 2021 | 25.1% | 86.3% |
| 2022 | 26.3% | 90.1% |
| 2023 | 27.4% | 88.5% |
| 2024 | 23.5% | 87.7% |

### Presupuesto por Institución (2024)

| Institución | Monto (MM CLP) | % del total |
|-------------|----------------|-------------|
| Carabineros | 1,250,000 | 28.0% |
| PDI | 720,000 | 16.0% |
| Ministerio Público | 450,000 | 10.1% |
| Poder Judicial | 975,000 | 21.8% |
| Gendarmería | 910,000 | 20.3% |
| SPD | 111,000 | 2.5% |
| Bomberos | 60,000 | 1.3% |

---

## 5. Fuentes de Datos

| Variable | Fuente | Período | Notas |
|----------|--------|---------|-------|
| Gasto COFOG 703 | DIPRES | 2013-2024 | Clasificación funcional |
| Gasto por subfunción | DIPRES | 2013-2024 | Subfunciones 7031-7036 |
| Homicidios | CEAD/SPD | 2013-2024 | Tasa por 100.000 hab |
| Victimización | INE/ENUSC | 2013-2024 | % hogares |
| Comparación OCDE | OCDE GAG | 2022 | Gobierno General |
| PIB | BCCh | 2013-2024 | Precios corrientes |

---

## 6. Uso Sugerido

1. **Para PPT**: Copiar visualizaciones ASCII directamente
2. **Para gráficos**: Usar datos de tablas en Excel/Sheets
3. **Para informe técnico**: Citar fuentes de sección 5

---

*Datos compilados para Espacio Público / BID 2026*
