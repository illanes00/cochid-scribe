# Sistema de comentarios trazables MI-NN

**Autor:** Martín Illanes
**Fecha inicial:** 2026-04-24
**Versión docx:** v3.12+

## Propósito

Los comentarios MI-NN ancan decisiones editoriales del autor al texto del documento, de forma que cada razonamiento queda trazable con:
- ID único (`MI-NN`)
- Ubicación anclada (párrafo específico del documento)
- Referencia al feedback original que lo motivó (CIF, Carla, Eduardo + código DOCX-NN)
- Acción editorial aplicada

Esto permite que directores y financista (CIF) puedan entender el razonamiento del autor al leer el documento, no solo el resultado final.

---

## Registro MI-01 a MI-11 (v3.12)

| ID | Tema | Ancla en texto | Feedback origen | Acción editorial |
|---|---|---|---|---|
| **MI-01** | Arquitectura BFAU como capa adicional | "Beneficio Farmacéutico Ambulatorio Universal" (Resumen Ejecutivo / Cap 7) | Carla DOCX142 + CIF + Eduardo | El BFAU no reemplaza GES/LRS/DAC/FOFAR sino que opera como capa de continuidad que cubre los hoyos de la fragmentación |
| **MI-02** | Estado dual: comprador + asegurador | "2.3 Financiamiento y ejecutores" | Carla DOCX40 | Estado opera simultáneamente como comprador directo (Servicios de Salud, PNI, Ricarte Soto, DAC) y asegurador obligatorio (cotizaciones 7%) |
| **MI-03** | Judicialización como síntoma estructural | Sección sobre judicialización (3.2.6) | CIF sept 2025 + Carla DOCX72, DOCX75 | Marco Vargas-Pelaez et al. (2019): no es problema independiente sino síntoma de insuficiencia del beneficio explícito |
| **MI-04** | Caveats metodológicos EPF | Primera mención gasto de bolsillo en Cap 4 | Carla DOCX88 | EPF captura un mes, no anualizado; subestima alto costo ocasional; no captura gratuidad APS |
| **MI-05** | Foco retail es decisión analítica | Primera mención "canal retail" | Carla DOCX101, DOCX145 | Foco retail porque allí está 71% OOP (HF3/HC51); expansión institucional es vía complementaria con trade-offs distintos |
| **MI-06** | Heterogeneidad regulatoria biosimilares | Recuadro biosimilares (5.3.4) | CIF-7 | EMA/FDA/MHRA/ANMAT tienen estándares distintos; Chile no puede importar un estándar único |
| **MI-07** | Escenarios calibrados sobre protección, no mix | "escenarios alternativos" (Cap 6) | Carla DOCX129, DOCX131, DOCX145 | Los rangos fiscales son compatibles con distintas combinaciones institución+retail; informe no prescribe mix |
| **MI-08** | Unidad de acumulación del tope | Primera mención "tope" (Cap 7) | Carla DOCX151 | 4 alternativas: persona / hogar / núcleo FONASA-ISAPRE / sistema tributario. Recomendación: hogar (unidad económica). |
| **MI-09** | Alcance BFAU: ambulatorio + apertura alto costo | "piso para lo ambulatorio" (Cap 7) | Carla DOCX149 | BFAU primordialmente ambulatorio pero sin excluir alto costo con evidencia ISP; convergencia en tercera fase |
| **MI-10** | Riesgo trasvasaje institucional→retail | "Riesgos de implementación" (Cap 7) | Carla DOCX131 | Mitigaciones: copagos con incentivo relativo, monitoreo migración, coordinación ISAPRE |
| **MI-11** | Principio "lo gratis sigue gratis" | "Lo gratis sigue gratis" (Cap 7) | Carla DOCX140 | BFAU no quita beneficios actuales; agrega capa focalizada por exposición al gasto, no homogeneiza canastas |

---

## Esqueleto de temas futuros MI-12+

A medida que llegan nuevos feedbacks del usuario, se agregan con el siguiente patrón:

```
MI-NN | Tema editorial | Ancla en texto | Feedback origen | Acción
```

Todos con formato estandarizado del cuerpo del comentario:

```
[MI-NN] <Título corto del tema>. <Razonamiento explicativo de 2-4 líneas>.
Responde a <nombre del autor del feedback> (<código DOCX-NN o email>).
```

---

## Cómo ubicar los comentarios en Google Docs

1. Abrir el Google Doc v3.12+
2. Todos los comentarios MI-NN aparecen al margen con autor "Martín Illanes"
3. Buscar por texto: `[MI-` (Ctrl+F dentro del panel de comentarios)
4. Cada comentario tiene ancla visible al texto específico que razona

---

## Convenciones

- **Prefijo**: siempre `[MI-NN]` en mayúsculas
- **Numeración**: secuencial global (no se reinicia por capítulo)
- **Autor**: "Martín Illanes" (nunca sufijos como "Propuesta IA")
- **Fecha**: al momento de creación
- **Anclaje**: a párrafo específico, no a rango general
- **Referencia**: siempre explicita qué feedback original responde
