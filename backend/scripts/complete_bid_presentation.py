#!/usr/bin/env python3
"""
Complete BID Presentation with all detailed content.
Sources: bid-presentacion-mejorada.md, bid-latam-data.html
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"


def build_complete_presentation():
    """Return complete presentation with all detailed content."""
    return [
        # ========== PORTADA ==========
        {
            "layout": "title",
            "title": "EFICIENCIA Y CALIDAD DEL GASTO PÚBLICO EN SEGURIDAD CIUDADANA",
            "content": "Chile 2013-2024\n\nEspacio Público para el BID\nEnero 2026",
            "notes": "Presentación de 1 hora. Cubre diagnóstico completo y propuesta BID.",
            "graph": None
        },

        # ========== QUÉ AVANZAMOS ==========
        {
            "layout": "content",
            "title": "Qué Avanzamos desde Noviembre",
            "content": """Informe de Avance → Informe Final

• Marco conceptual: Preliminar → Eficacia/Eficiencia/Calidad consolidado
• Datos: 2013-2023 → 2013-2024 (cierre fiscal)
• Comparación: OCDE agregado → OCDE + LATAM por subfunción
• Recomendaciones: 3 generales → 5 con indicadores específicos
• Propuesta BID: Mención general → US$700K-1.8M detallado

Valor agregado: Marco analítico robusto + Operacionalización""",
            "notes": "Mostrar evolución desde el informe de avance.",
            "graph": None
        },

        # ========== MENSAJE CENTRAL ==========
        {
            "layout": "content",
            "title": "La Pregunta Central",
            "content": """¿Chile gasta poco o mucho en seguridad?

LA RESPUESTA:
La pregunta está mal planteada.

El problema NO es cuánto gastamos.
El problema es CÓMO gastamos.

El debate público se centra en "más recursos", pero la evidencia
muestra que Chile ya gasta comparable a OCDE.
La oportunidad está en la calidad: composición, ejecución, medición.""",
            "notes": "Este es el mensaje central del informe. Pausa antes de pasar.",
            "graph": None
        },

        # ========== CONTEXTO ==========
        {
            "layout": "content",
            "title": "Seguridad: Primera Preocupación Nacional",
            "content": """Prioridad ciudadana (CEP Octubre 2025):

Delincuencia:    ~60%
Salud:           32%
Economía:        28%
Educación:       21%
Pensiones:       18%

La seguridad domina la agenda pública desde 2017.
Ningún gobierno puede ignorar este dato.
Pero: ¿sabemos si lo que estamos haciendo funciona?""",
            "notes": "CEP N°95 (Sept-Oct 2025). Justifica por qué el estudio importa ahora.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "La Paradoja Chilena",
            "content": """Indicadores complejos:

• Victimización: 23,5% hogares (relativamente estable)
• Homicidios: 6,0 por 100K (↑ desde 4,5 en 2018)
• Percepción inseguridad: 87,7% (muy alta vs. datos)
• Homicidios con arma de fuego: ~50% (↑ desde 42% en 2018)

Violencia más letal + percepción desacoplada de realidad

Fuente: CEAD/SPD, ENUSC 2024""",
            "notes": "Datos que muestran la complejidad del fenómeno.",
            "graph": "https://graphs.illanes00.cl/homicidios-latam"
        },

        {
            "layout": "content",
            "title": "Respuesta Institucional 2022-2025",
            "content": """Medidas implementadas:

✓ Política Nacional contra Crimen Organizado
✓ Ministerio de Seguridad Pública (Ley 21.730)
✓ Fiscalía Supraterritorial
✓ Presupuesto 2025: +15% vs. post-pandemia

Pero: ¿sabemos si el gasto está siendo efectivo?
Ahí entra este informe.""",
            "notes": "Contexto institucional reciente.",
            "graph": None
        },

        # ========== METODOLOGÍA ==========
        {
            "layout": "content",
            "title": "Clasificación COFOG",
            "content": """Estándar internacional del FMI (GFSM 2014):

703 - ORDEN PÚBLICO Y SEGURIDAD
├── 7031 - Servicios de policía (Carabineros, PDI)
├── 7032 - Protección contra incendios (Bomberos)
├── 7033 - Tribunales de justicia (PJ, MP)
├── 7034 - Prisiones (Gendarmería)
├── 7035 - I+D en seguridad (no clasificado en Chile)
└── 7036 - Otros servicios n.e.p. (SPD, otros)

Permite comparación internacional rigurosa""",
            "notes": "Base metodológica del estudio.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Alcance del Estudio",
            "content": """Dimensiones cubiertas:

• Temporal: 2013-2024 (4 períodos presidenciales)
  Piñera I, Bachelet II, Piñera II, Boric
• Institucional: Gobierno Central (análisis nacional)
• Comparativo: Gobierno General (OCDE, LATAM)
• Fuentes: DIPRES, OCDE, FMI, OMS, CEAD/SPD

Nivel de detalle: Por subfunción COFOG y clasificación económica""",
            "notes": "Metodología y fuentes del estudio.",
            "graph": None
        },

        # ========== HALLAZGO 1: ESFUERZO AGREGADO ==========
        {
            "layout": "content",
            "title": "HALLAZGO 1: Esfuerzo Agregado",
            "content": """Gasto en Seguridad 2024:

$4,47 billones CLP

• 1,43% del PIB
• 5,82% del gasto del Gobierno Central
• 8,13% excluyendo Protección Social

Fuente: DIPRES, Ejecución Presupuestaria 2024""",
            "notes": "Cifra principal del estudio.",
            "graph": "gasto_chile_deflactado.png"
        },

        {
            "layout": "content",
            "title": "Evolución 2013-2024",
            "content": """Trayectoria del gasto (billones CLP 2024):

2013: $3,60 → 2015: $3,82 → 2017: $4,03 → 2019: $4,32
2020: $3,91 (pandemia) → 2021: $3,85 → 2022: $3,91
2023: $4,25 → 2024: $4,47

Recuperación post-pandemia: 2024 supera máximos pre-COVID
Sin cambio estructural en composición""",
            "notes": "Serie temporal del gasto en seguridad.",
            "graph": "gasto_chile_deflactado.png - INSERTAR GRÁFICO"
        },

        {
            "layout": "content",
            "title": "Chile vs OCDE: % del PIB",
            "content": """Gasto como % del PIB (Gobierno General, 2022-2023):

Mediana LATAM:     1,9%
Mediana OCDE:      1,8%
Chile (ajustado):  ~1,6%
                   ↑ Brecha acotada

Hallazgo: Chile NO aparece subfinanciado en términos agregados.
La brecha es de solo 0,2 puntos porcentuales.

Fuente: OCDE Government at a Glance 2023""",
            "notes": "Comparación internacional clave.",
            "graph": "grafico_brecha_chile_ocde.png - INSERTAR GRÁFICO"
        },

        {
            "layout": "content",
            "title": "Chile en Contexto LATAM",
            "content": """Gasto per cápita PPA (US$, 2022-2023):

Brasil:         $607
Costa Rica:     $572
El Salvador:    $496
Chile:          $490
Colombia:       $467
Mediana LATAM:  $434

La anomalía chilena: Alto desarrollo (PIB per cápita $32.801)
pero gasto en seguridad similar a países con menor ingreso.""",
            "notes": "Chile tiene mayor PIB per cápita pero gasto similar a El Salvador.",
            "graph": "ppp_percap_latam.png - INSERTAR GRÁFICO\nURL: https://graphs.illanes00.cl/static/bid-latam-data.html"
        },

        # ========== HALLAZGO 2: COMPOSICIÓN ==========
        {
            "layout": "content",
            "title": "HALLAZGO 2: Composición del Gasto",
            "content": """Distribución 2024 por subfunción:

Policías (7031):      44,0%   →   $1,97 billones
Justicia/MP (7033):   31,9%   →   $1,43 billones
Prisiones (7034):     20,3%   →   $0,91 billones
Bomberos (7032):       1,3%   →   $0,06 billones
Otros (7036):          2,5%   →   $0,11 billones
I+D (7035):            0,0%   →   $0,00 (sin clasificación)""",
            "notes": "Distribución por subfunción COFOG 703.",
            "graph": "composicion-chile (graphs.illanes00.cl)"
        },

        {
            "layout": "content",
            "title": "El Problema de la Inercia",
            "content": """La mezcla NO cambia en 11 años:

      Policías    Justicia    Prisiones
2013:   44%        32%         20%
2017:   44%        32%         20%
2024:   44%        32%         20%

La asignación responde a trayectorias históricas,
NO a evidencia sobre efectividad.

Pregunta: ¿El delito de 2024 es igual al de 2013?
No. Pero el presupuesto sí.""",
            "notes": "Uno de los hallazgos más importantes.",
            "graph": "composicion-evolucion (graphs.illanes00.cl)"
        },

        {
            "layout": "content",
            "title": "Hallazgo Crítico: Sin I+D Clasificado",
            "content": """Subfunción 7035 - I+D en seguridad:

Países OCDE con I+D:    $5-15 USD PPA per cápita
Chile:                  $0 USD clasificado

Chile no clasifica gasto en I+D en seguridad.
Esto NO significa ausencia total de investigación, sino que
el gasto existente no se clasifica en la subfunción correspondiente.

Consecuencias:
• Sin línea presupuestaria dedicada
• Evaluaciones de impacto dispersas o ausentes
• Desarrollo tecnológico sin priorización""",
            "notes": "Este dato suele sorprender. Oportunidad para el BID.",
            "graph": None
        },

        # ========== HALLAZGO 3: COMPARACIÓN POR SUBFUNCIÓN ==========
        {
            "layout": "content",
            "title": "HALLAZGO 3: Policías - Posición Media",
            "content": """Gasto per cápita PPA (US$) en Policías (7031):

Europa Occidental:  $350+
Mediana OCDE:       $280
Chile:              $220
Promedio LATAM:     $210

Posición: Alineado con la región, bajo vs. OCDE""",
            "notes": "Chile en posición intermedia en gasto policial.",
            "graph": "subfuncion-policia (graphs.illanes00.cl)"
        },

        {
            "layout": "content",
            "title": "Justicia: Levemente Bajo",
            "content": """Gasto per cápita PPA (US$) en Justicia (7033):

Mediana OCDE:       $160
Promedio LATAM:     $140
Chile:              $120

Posición: Levemente bajo referencia LATAM y OCDE
Tendencia: Decreciente en la última década""",
            "notes": "Chile gasta menos que OCDE en justicia.",
            "graph": "subfuncion-justicia (graphs.illanes00.cl)"
        },

        {
            "layout": "content",
            "title": "Prisiones: COMPARATIVAMENTE ALTO",
            "content": """Gasto per cápita PPA (US$) en Prisiones (7034):

Chile:              $105  ← +25% sobre OCDE
Europa Occidental:  $95
Mediana OCDE:       $80
Promedio LATAM:     $55

Señal de presión sobre sistema penitenciario.
La privación de libertad es costosa y de última ratio.""",
            "notes": "Chile gasta significativamente más que OCDE en prisiones.",
            "graph": "subfuncion-prisiones (graphs.illanes00.cl)"
        },

        {
            "layout": "content",
            "title": "Ratio Justicia/Policía Internacional",
            "content": """Ratio de gasto Justicia vs Policía:

Mediana OCDE:       0,85
Promedio LATAM:     0,70
Chile:              0,73

Chile tiene mayor gasto relativo en policía.
Menor inversión relativa en justicia y persecución penal.

Fuente: OCDE, FMI GFSM 2014""",
            "notes": "El ratio sugiere posible desbalance hacia función policial.",
            "graph": "grafico_ratio_jp_2023.png - INSERTAR GRÁFICO"
        },

        # ========== HALLAZGO 4: INTENSIDAD EN PERSONAL ==========
        {
            "layout": "content",
            "title": "HALLAZGO 4: Gasto Rígido en Personal",
            "content": """Clasificación económica del gasto:

Personal:              ~70%
Bienes y Servicios:    ~20%
Inversión:             ~8%
Otros:                 ~2%

Sin tocar dotaciones, el margen de gestión está en:
• Equipamiento
• Tecnología
• Infraestructura

Gráfico: composicion_economica.png""",
            "notes": "La alta proporción de personal limita flexibilidad.",
            "graph": "composicion_economica.png - INSERTAR GRÁFICO"
        },

        # ========== HALLAZGO 5: BRECHAS DE INFORMACIÓN ==========
        {
            "layout": "content",
            "title": "HALLAZGO 5: No Podemos Evaluar Eficiencia",
            "content": """Cuatro problemas críticos:

1. Sin mapeo programa→COFOG
   → No sabemos qué financia cada peso

2. Sin desagregación territorial
   → No identificamos inequidades

3. Registros no interoperables
   → No podemos seguir casos

4. Pocas evaluaciones de impacto
   → No sabemos qué funciona

SIN INFORMACIÓN, NO HAY GESTIÓN POR RESULTADOS""",
            "notes": "La brecha de información es el principal obstáculo.",
            "graph": None
        },

        # ========== SÍNTESIS ==========
        {
            "layout": "content",
            "title": "Síntesis: 5 Hallazgos",
            "content": """Resumen de hallazgos:

1. Esfuerzo comparable a OCDE
   → No hay evidencia de subfinanciamiento agregado

2. Composición con inercia
   → Asignación no responde a evidencia

3. Alto en prisiones, nulo en I+D
   → Desequilibrio funcional

4. 70% en personal
   → Rigidez presupuestaria

5. Brechas de información
   → Imposible evaluar eficiencia""",
            "notes": "Los 5 hallazgos en una slide.",
            "graph": None
        },

        # ========== RECOMENDACIONES ==========
        {
            "layout": "content",
            "title": "5 Recomendaciones de Política Pública",
            "content": """CALIDAD SOBRE CANTIDAD:

1. Reforzar Prevención y Reinserción
   Meta: 5% del gasto a prevención en 5 años

2. Abrir Espacio para I+D
   Meta: 0,5% del gasto en I+D al 2028

3. Profundizar Interoperabilidad
   Output: Diccionario programa→COFOG público

4. Desarrollar Métricas de Desempeño
   Output: Indicadores por institución

5. Consolidar Línea Base
   Output: Actualización anual de series""",
            "notes": "Las 5 recomendaciones con metas específicas.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Rec 1: Reequilibrar hacia Prevención",
            "content": """Sin disminuir abruptamente el control:

• Meta: 5% del gasto a prevención en 5 años
  (~$90 mil millones CLP/año)

• Priorizar: Intervenciones con evidencia internacional

• Responsable: Subsecretaría de Prevención del Delito

• Indicador: % gasto en subfunción 7036 y programas mapeados

Referencia: BID, "Citizen Security Economics" (2019)""",
            "notes": "Recomendación 1 con meta cuantificable.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Rec 2: Crear Línea de I+D en Seguridad",
            "content": """Establecer subfunción 7035 activa:

• Establecer: Fondo de Innovación en Seguridad
  con línea presupuestaria específica

• Financiar: Evaluaciones de impacto de programas existentes

• Desarrollar: Capacidad analítica institucional
  (datos, modelos predictivos)

• Meta: 0,5% del gasto en seguridad clasificado en I+D al 2028

Esto permitiría aprovechar mejor los recursos existentes.""",
            "notes": "Recomendación 2: crear capacidad de I+D.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Rec 3: Trazabilidad Presupuesto-Resultados",
            "content": """Plan de vinculación:

• Publicar: Diccionario de correspondencia programa→COFOG

• Panel: Trimestral con gasto + dotaciones + indicadores

• Desagregación: Territorial obligatoria

• Indicador: % de programas con mapeo COFOG publicado

Modelo: UK Crime Statistics Hub""",
            "notes": "Recomendación 3: mejorar trazabilidad.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Rec 4: Métricas de Desempeño por Institución",
            "content": """Indicadores propuestos:

CARABINEROS:
• Tiempo de respuesta promedio a llamadas

PDI:
• Tasa de esclarecimiento de delitos

FISCALÍA:
• Duración de causas, tasa de condena

GENDARMERÍA:
• Hacinamiento carcelario, tasa de reincidencia

Objetivo: Orientar incrementos hacia áreas con mejores resultados.""",
            "notes": "Recomendación 4: indicadores específicos por institución.",
            "graph": None
        },

        # ========== PROPUESTA BID ==========
        {
            "layout": "title",
            "title": "PROPUESTA AL BID",
            "content": "Líneas de Trabajo Futuro 2026-2028",
            "notes": "Sección de propuesta concreta al BID.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Oportunidades de Colaboración",
            "content": """Portafolio de colaboración propuesto:

• Programa de asistencia técnica: US$ 700K
  Implementación de recomendaciones (2026-2028)

• Estudio regional comparado: US$ 400K
  Extender análisis a 5 países LATAM

• Laboratorio de innovación: US$ 500K
  Piloto de intervenciones basadas en evidencia

• Capacitación: US$ 200K
  Diplomado en gestión de seguridad basada en evidencia

TOTAL PORTAFOLIO POTENCIAL: US$ 1,8 MILLONES""",
            "notes": "El programa base (US$700K) es el mínimo. Las líneas adicionales son expansión.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Inversión: Programa de Asistencia Técnica",
            "content": """Desglose US$ 700.000 (3 años):

• Trazabilidad y datos:          US$ 150.000
  Diccionario programa→COFOG, panel de indicadores

• Evaluaciones de impacto:       US$ 300.000
  Metodologías rigurosas para programas clave

• Capacitación institucional:    US$ 100.000
  DIPRES, Carabineros, PDI, Gendarmería

• Benchmarking regional:         US$ 80.000
  Comparación continua con LATAM y OCDE

• Coordinación y gestión:        US$ 70.000
  Project management y reporting BID""",
            "notes": "Presupuesto detallado del programa base.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Cronograma 2026-2028",
            "content": """AÑO 2026:
• Q1: Trazabilidad (diccionario)
• Q2: Fondo I+D (diseño)
• Q3: Panel de indicadores

AÑO 2027:
• Q1: Evaluaciones de impacto
• Q2: Benchmarking regional
• Q3: Meta 5% prevención
• Q4: Fondo I+D operativo

AÑO 2028:
• Q1: Indicadores de desempeño
• Q2: Actualización anual
• Q3: Informe final""",
            "notes": "Cronograma de 3 años con hitos trimestrales.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Retorno Esperado",
            "content": """CUANTIFICABLES:
• Reasignación 2% hacia programas efectivos
  → ~$90 mil millones CLP/año mejor asignados
• Reducción 10% reincidencia
  → Ahorro carcelario significativo

ESTRATÉGICOS:
• Chile como referente regional en gestión de seguridad
• Modelo replicable para otros países BID
• Fortalecimiento institucional sostenible
• Chile como piloto, luego escalar a LATAM""",
            "notes": "Beneficios cuantificables y estratégicos.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "¿Por qué Espacio Público?",
            "content": """Nuestra propuesta de valor:

✓ 10+ años de investigación en políticas públicas
✓ Acceso institucional a DIPRES, Ministerios, Fiscalía
✓ Track record con BID, Banco Mundial, PNUD
✓ Equipo multidisciplinario
  (economistas, abogados, data scientists)
✓ Independencia y credibilidad técnica""",
            "notes": "Credenciales y valor agregado de Espacio Público.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Riesgos y Mitigaciones",
            "content": """• Cambio de gobierno 2026 (Alta prob., Alto impacto)
  → Diseño institucional no partidista; anclar en DIPRES

• Resistencia institucional (Media prob., Alto impacto)
  → Involucrar contrapartes desde diseño; quick wins

• Datos no disponibles (Media prob., Medio impacto)
  → Plan B con fuentes alternativas

• Rotación de equipos (Media prob., Medio impacto)
  → Documentación exhaustiva; transferencia conocimiento

Estrategia: Diseño modular con avances independientes""",
            "notes": "Gestión de riesgos del programa.",
            "graph": None
        },

        # ========== CIERRE ==========
        {
            "layout": "content",
            "title": "El Desafío No Es Gastar Más",
            "content": """ES GASTAR MEJOR.

Chile tiene los recursos.
Falta la gestión por resultados.

Con este informe, tenemos la línea base.
Con el BID, podemos transformar el sistema.""",
            "notes": "Cerrar con energía. Este es el llamado a la acción.",
            "graph": None
        },

        {
            "layout": "content",
            "title": "Equipo del Proyecto",
            "content": """Espacio Público:

• Benjamín García (Director Ejecutivo)
• Eleni Kokkidou (Subdirectora Ejecutiva)
• Patricio Domínguez (Director)
• Mauricio Duce (Director)
• Martín Illanes (Investigador Principal)

Contacto: www.espaciopublico.cl""",
            "notes": "Equipo responsable del estudio.",
            "graph": None
        },

        {
            "layout": "title",
            "title": "¡Gracias!",
            "content": "Eficiencia y Calidad del Gasto Público\nen Seguridad Ciudadana\n\nEspacio Público para BID\nEnero 2026",
            "notes": "Cierre. Abrir a preguntas.",
            "graph": None
        },
    ]


def clear_and_rebuild(slides_service, slides_content):
    """Clear all slides and rebuild from scratch."""
    # Delete all existing slides
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slides = presentation.get("slides", [])
    if slides:
        slide_ids = [s["objectId"] for s in slides]
        requests = [{"deleteObject": {"objectId": sid}} for sid in slide_ids]
        slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body={"requests": requests}
        ).execute()
        print(f"Deleted {len(slides)} existing slides")

    # Create all new slides
    print(f"Creating {len(slides_content)} slides...")
    create_requests = []
    for i, slide_data in enumerate(slides_content):
        slide_id = f"complete_{i:02d}"
        layout_id = "p13" if slide_data["layout"] == "title" else "p14"
        create_requests.append({
            "createSlide": {
                "objectId": slide_id,
                "insertionIndex": i,
                "slideLayoutReference": {"layoutId": layout_id}
            }
        })

    slides_service.presentations().batchUpdate(
        presentationId=PRESENTATION_ID,
        body={"requests": create_requests}
    ).execute()
    print(f"Created {len(create_requests)} slides")

    # Populate each slide
    for i, slide_data in enumerate(slides_content):
        populate_slide(slides_service, f"complete_{i:02d}", slide_data)
        print(f"  {i+1}. {slide_data['title'][:45]}")


def populate_slide(slides_service, slide_id, slide_data):
    """Populate a slide with content."""
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slide = None
    for s in presentation.get("slides", []):
        if s["objectId"] == slide_id:
            slide = s
            break

    if not slide:
        return

    title_shape_id = None
    body_shape_id = None

    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        placeholder = shape.get("placeholder", {})
        ptype = placeholder.get("type", "")
        if ptype in ("TITLE", "CENTERED_TITLE"):
            title_shape_id = element["objectId"]
        elif ptype in ("BODY", "SUBTITLE"):
            body_shape_id = element["objectId"]

    requests = []
    if title_shape_id and slide_data.get("title"):
        requests.append({
            "insertText": {
                "objectId": title_shape_id,
                "text": slide_data["title"],
                "insertionIndex": 0
            }
        })

    if body_shape_id and slide_data.get("content"):
        requests.append({
            "insertText": {
                "objectId": body_shape_id,
                "text": slide_data["content"],
                "insertionIndex": 0
            }
        })

    if requests:
        try:
            slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body={"requests": requests}
            ).execute()
        except Exception as e:
            print(f"Error: {e}")


def print_graph_guide(slides_content):
    """Print guide for which graphs to insert where."""
    print("\n" + "=" * 70)
    print("GUÍA DE GRÁFICOS PARA INSERTAR")
    print("=" * 70)
    print("\nInsertar manualmente los siguientes gráficos:\n")

    for i, slide in enumerate(slides_content):
        if slide.get("graph"):
            print(f"Slide {i+1}: {slide['title'][:50]}")
            print(f"   → {slide['graph']}")
            print()

    print("\nFuentes de gráficos:")
    print("1. PNGs locales: /srv/projects/illanes00-graphs/static/screenshots/")
    print("2. Interactivos: https://graphs.illanes00.cl/figures")
    print("3. LATAM data: https://graphs.illanes00.cl/static/bid-latam-data.html")
    print("=" * 70)


def main():
    """Main entry point."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return 1

        slides_content = build_complete_presentation()
        print("=" * 60)
        print("COMPLETE BID PRESENTATION GENERATOR")
        print("=" * 60)
        print(f"Total slides: {len(slides_content)}")
        print("-" * 60)

        clear_and_rebuild(slides_service, slides_content)

        print(f"\nDONE! View at: https://docs.google.com/presentation/d/{PRESENTATION_ID}")

        print_graph_guide(slides_content)

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
