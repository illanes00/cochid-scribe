#!/usr/bin/env python3
"""
Update Scribe document with slides data for BID presentation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.document import Document

DOCUMENT_SLUG = "bid-seguridad-final"


def build_slides_data():
    """Return slides data structure for Scribe document."""
    slides = [
        # ========== SECCIÓN 1: APERTURA (4 slides) ==========
        {
            "id": "slide-01",
            "slideNumber": 1,
            "layout": "title",
            "title": "Eficiencia y Calidad del Gasto Público en Seguridad Ciudadana en Chile",
            "content": "Espacio Público para BID\nEnero 2026",
            "notes": "Informe Final para reunión BID. Cubre análisis completo del gasto en seguridad 2013-2024."
        },
        {
            "id": "slide-02",
            "slideNumber": 2,
            "layout": "content",
            "title": "Estructura de la Presentación",
            "content": """1. Recordatorio: Informe de avance
2. Marco Conceptual: Calidad del gasto en seguridad
3. Hallazgos Consolidados: Cifras finales 2024
4. Comparación Internacional: Chile en contexto global
5. Hacia la Calidad del Gasto: Síntesis y brechas
6. Recomendaciones: 5 líneas de política pública
7. Cierre y próximos pasos""",
            "notes": "Estructura en 7 secciones para presentación de 1 hora."
        },
        {
            "id": "slide-03",
            "slideNumber": 3,
            "layout": "content",
            "title": "Qué hay de nuevo desde el informe de avance",
            "content": """Lo que ya cubrimos (Noviembre 2025):
• Contexto: seguridad como prioridad ciudadana
• Fenómeno delictual complejo (homicidios, secuestros)
• Contexto institucional (Ministerio de Seguridad)
• Evolución preliminar del gasto 2013-2024

Hoy: Hallazgos consolidados, marco conceptual y recomendaciones""",
            "notes": "Recapitulación del informe de avance previo."
        },
        {
            "id": "slide-04",
            "slideNumber": 4,
            "layout": "content",
            "title": "Mensajes Clave",
            "content": """En 2024, el gasto del Gobierno Central en seguridad alcanzó $4,47 billones CLP (1,43% del PIB y 5,82% del gasto total).

Hallazgo central: El gasto en seguridad pública no aparece como "subfinanciado" en términos agregados.

Implicancia: El margen de mejora no está en aumentar la escala del presupuesto, sino en mejorar el desempeño: cómo se administra la composición interna y qué capacidades de gestión existen.""",
            "notes": "Mensaje principal del informe: el problema no es cuánto sino cómo."
        },

        # ========== SECCIÓN 2: MARCO CONCEPTUAL (5 slides) ==========
        {
            "id": "slide-05",
            "slideNumber": 5,
            "layout": "content",
            "title": "¿Por qué importa la calidad del gasto?",
            "content": """La experiencia comparada del BID muestra que:

"Países con esfuerzos similares presentan resultados muy distintos en homicidios, victimización y percepción de seguridad"

Esto se explica por:
• Rigideces en la asignación
• Debilidades en la gestión
• Ausencia de seguimiento-evaluación""",
            "notes": "Evidencia BID sobre importancia de la calidad del gasto."
        },
        {
            "id": "slide-06",
            "slideNumber": 6,
            "layout": "content",
            "title": "Eficacia, Eficiencia y Calidad",
            "content": """• Eficacia: ¿Logramos los resultados? (reducir victimización, acortar tiempos)

• Eficiencia: ¿Cuántos resultados por peso gastado?

• Calidad: Focalización + equidad territorial + sostenibilidad + transparencia

El giro: De preguntar "¿cuánto?" a preguntar "¿cómo?" """,
            "notes": "Definiciones conceptuales clave."
        },
        {
            "id": "slide-07",
            "slideNumber": 7,
            "layout": "content",
            "title": "Los Tres Pilares Funcionales",
            "content": """CONTROL Y REACCIÓN (~96% del gasto)
• Policías, Fiscalía, Tribunales, Gendarmería

PREVENCIÓN (~3%)
• Situacional, Social, Territorial
• Subsecretaría de Prevención del Delito

REINSERCIÓN SOCIAL (~1%)
• Educación, capacitación, apoyo psicosocial

Mensaje: Los sistemas concentrados solo en control muestran retornos decrecientes""",
            "notes": "Chile concentra gasto en control, con débil inversión en prevención."
        },
        {
            "id": "slide-08",
            "slideNumber": 8,
            "layout": "content",
            "title": "Economía del Crimen (Becker, 1968)",
            "content": """La decisión de delinquir compara:

Beneficio esperado del delito vs. Costo esperado
(Ganancia × P(éxito))  vs.  (Pena × P(detección))

El gasto público incide en:
• P(detección): capacidades policiales
• Pena efectiva: inversión en justicia
• Oportunidades: prevención
• Trayectorias: reinserción""",
            "notes": "Marco teórico económico para entender canales de impacto."
        },
        {
            "id": "slide-09",
            "slideNumber": 9,
            "layout": "content",
            "title": "Eficiencia Asignativa vs. Técnica",
            "content": """ASIGNATIVA: ¿Cómo distribuimos entre funciones?
Ejemplo: ¿Más a prevención o a prisiones?

TÉCNICA: ¿Qué resultados produce cada función?
Ejemplo: Tiempos de respuesta, esclarecimiento

El desafío: Chile tiene información sobre asignación pero limitada sobre resultados""",
            "notes": "Distinción clave para el diagnóstico."
        },

        # ========== SECCIÓN 3: HALLAZGOS CONSOLIDADOS (7 slides) ==========
        {
            "id": "slide-10",
            "slideNumber": 10,
            "layout": "content",
            "title": "Cifra Principal: Gasto en Seguridad 2024",
            "content": """$4,47 billones CLP

• 1,43% del PIB
• 5,82% del gasto del Gobierno Central
• 8,13% excluyendo Protección Social

Fuente: DIPRES, ejecución presupuestaria 2024""",
            "notes": "Cifras oficiales de cierre 2024."
        },
        {
            "id": "slide-11",
            "slideNumber": 11,
            "layout": "content",
            "title": "Composición del Gasto 2024",
            "content": """Distribución por subfunción COFOG:

• Policías (PDI + Carabineros): 44,0% → $1,97 billones
• Justicia + Ministerio Público: 31,9% → $1,43 billones
• Prisiones (Gendarmería): 20,3% → $0,91 billones
• Bomberos: 1,33% → $0,06 billones
• Otros n.e.p.: 2,48% → $0,11 billones
• I+D: 0% → $0""",
            "notes": "Distribución por subfunción COFOG 703."
        },
        {
            "id": "slide-12",
            "slideNumber": 12,
            "layout": "content",
            "title": "Hallazgo: Ausencia de I+D",
            "content": """Subfunción 7035: Investigación y desarrollo en orden público y seguridad

Chile: 0%
OCDE: ~1-2% (US$5-15 PPA per cápita)

No se clasificó gasto en I+D en seguridad durante todo el período 2013-2024.

Esto sugiere énfasis débil en capacidades analíticas, tecnológicas y de evaluación.""",
            "notes": "Hallazgo notable: cero clasificado en I+D."
        },
        {
            "id": "slide-13",
            "slideNumber": 13,
            "layout": "content",
            "title": "Evolución 2013-2024",
            "content": """En pesos reales (CLP 2024):
• Crecimiento sostenido hasta 2018-2019
• Baja en 2020 (pandemia)
• Retroceso adicional 2022
• Rebote 2023-2024 que supera máximos pre-pandemia (2024 > 2019)

Cierre 2024: $4,47 billones CLP

Gráfico: gasto_chile_deflactado.png""",
            "notes": "Normalización post-pandemia, sin salto estructural permanente."
        },
        {
            "id": "slide-14",
            "slideNumber": 14,
            "layout": "content",
            "title": "Evolución como % del PIB",
            "content": """Serie histórica:
• Máximo 2015-2016: 1,75%
• Banda 2013-2019: 1,6-1,75%
• 2024: 1,43% (retorno a rango histórico)

El % del PIB se mantuvo relativamente estable pese a cambios en el fenómeno delictual.""",
            "notes": "Estabilidad macro del esfuerzo fiscal."
        },
        {
            "id": "slide-15",
            "slideNumber": 15,
            "layout": "content",
            "title": "Mensaje Fiscal Clave",
            "content": """No hay "subfinanciamiento" agregado

"El gasto en seguridad pública se mueve dentro de un vecindario normal: crece hasta 2018-2019, cae durante pandemia, luego se normaliza sin saltos estructurales permanentes."

Implicancia directa:
El margen de mejora no está en aumentar escala sino en mejorar desempeño""",
            "notes": "Conclusión principal del diagnóstico fiscal."
        },
        {
            "id": "slide-16",
            "slideNumber": 16,
            "layout": "content",
            "title": "Inercia Asignativa",
            "content": """La mezcla no cambia pese a cambios en el delito:

2013: 44% - 32% - 20% (Policías - Justicia - Prisiones)
2017: 44% - 32% - 20%
2024: 44% - 32% - 20%

La asignación responde a trayectorias históricas más que a evidencia sobre retornos

Gráfico: composicion-evolucion""",
            "notes": "Rigidez asignativa como hallazgo clave."
        },

        # ========== SECCIÓN 4: COMPARACIÓN INTERNACIONAL (6 slides) ==========
        {
            "id": "slide-17",
            "slideNumber": 17,
            "layout": "content",
            "title": "Comparación Internacional: Metodología",
            "content": """Gobierno General (GFSM 2014):

Análisis Nacional → Gobierno Central (DIPRES)
Comparación Internacional → Gobierno General (OCDE, FMI)

Ajuste: CLP 2024 para nacional, US$ PPA 2024 para internacional""",
            "notes": "Metodología de comparación internacional."
        },
        {
            "id": "slide-18",
            "slideNumber": 18,
            "layout": "content",
            "title": "Chile vs OCDE: % del PIB (2023)",
            "content": """Comparación como % del PIB:

• Mediana OCDE: 1,8%
• Promedio Mundial: 1,8%
• Chile: 1,56%
• Promedio LATAM: 1,9%

Chile: posición intermedia, levemente bajo mediana OCDE

Gráfico: grafico_brecha_chile_ocde.png""",
            "notes": "Brecha acotada con OCDE."
        },
        {
            "id": "slide-19",
            "slideNumber": 19,
            "layout": "content",
            "title": "Chile vs OCDE: Per cápita PPA",
            "content": """Gasto per cápita en dólares ajustados:

• Chile 2023: US$511
• Chile 2024: US$509
• Mediana OCDE 2022: US$841

Chile: sobre LATAM, pero bajo Europa y OCDE

Gráfico: ppp_percap_latam.png""",
            "notes": "Chile en posición intermedia en per cápita."
        },
        {
            "id": "slide-20",
            "slideNumber": 20,
            "layout": "content",
            "title": "Por Subfunción: Policías y Justicia",
            "content": """POLICÍAS (7031):
• Chile: $220 PPA
• Mediana OCDE: $280 PPA
• Posición: media internacional

JUSTICIA/MP (7033):
• Chile: $120 PPA
• Mediana OCDE: $160 PPA
• Posición: levemente bajo referencias""",
            "notes": "Posición media en policías, levemente baja en justicia."
        },
        {
            "id": "slide-21",
            "slideNumber": 21,
            "layout": "content",
            "title": "Por Subfunción: Prisiones y Bomberos",
            "content": """PRISIONES (7034) - Chile ALTO:
• Chile: $105 PPA per cápita
• Mediana OCDE: $80 PPA
• Europa: $95 PPA
Refleja presión sobre estándares penitenciarios y ocupación

BOMBEROS (7032) - Chile MUY BAJO:
• Chile: $8 PPA
• Mediana OCDE: $50 PPA
Modelo de voluntariedad explica bajo gasto directo""",
            "notes": "Prisiones alto, bomberos muy bajo por modelo voluntario."
        },
        {
            "id": "slide-22",
            "slideNumber": 22,
            "layout": "content",
            "title": "Síntesis Comparativa",
            "content": """Posición de Chile por subfunción:

• Policías: Media
• Justicia/MP: Levemente baja
• Prisiones: ALTA (+25% sobre OCDE per cápita)
• Bomberos: Muy baja (-85%)
• I+D: NULA (0%)

Gráfico: grafico_ratio_jp_2023.png""",
            "notes": "Resumen de posición internacional por subfunción."
        },

        # ========== SECCIÓN 5: HACIA LA CALIDAD DEL GASTO (5 slides) ==========
        {
            "id": "slide-23",
            "slideNumber": 23,
            "layout": "content",
            "title": "5 Hallazgos Principales",
            "content": """1. Esfuerzo relevante y comparable internacionalmente
2. Mezcla estable y concentrada en control (~96%)
3. Gasto intensivo en personal (~70%)
4. Prisiones alta, I+D nula en comparación
5. Brechas de información limitan evaluación""",
            "notes": "Síntesis de los 5 hallazgos del informe."
        },
        {
            "id": "slide-24",
            "slideNumber": 24,
            "layout": "content",
            "title": "Hallazgo 1: Esfuerzo Comparable",
            "content": """No hay subinversión extrema en el agregado

Chile vs. OCDE (% PIB):
OCDE: 1,8%
Chile: 1,56%
Brecha: acotada (-0,24 pp)

El problema no es cuánto sino cómo""",
            "notes": "Chile gasta nivel comparable a OCDE."
        },
        {
            "id": "slide-25",
            "slideNumber": 25,
            "layout": "content",
            "title": "Hallazgo 2-3: Concentración y Personal",
            "content": """HALLAZGO 2: Concentración en Control
~96% va a policías, justicia y prisiones
Prevención: ~3%
Reinserción: ~1%
Riesgo: retornos decrecientes sin equilibrio

HALLAZGO 3: Intensivo en Personal
Personal: 70%
B&S + Inversión: 28%
Margen de gestión acotado sin tocar dotaciones""",
            "notes": "Concentración en control e intensidad de personal."
        },
        {
            "id": "slide-26",
            "slideNumber": 26,
            "layout": "content",
            "title": "Hallazgo 4-5: Desequilibrios y Brechas",
            "content": """HALLAZGO 4: Desequilibrios en Mezcla
Alto: Prisiones (+25% sobre OCDE per cápita)
Bajo: I+D (0%), Bomberos (-85%)
Privación de libertad es costosa y de última ratio

HALLAZGO 5: Brechas de Información
No se puede vincular gasto con resultados
Presupuesto → ??? → COFOG → ??? → Resultados
Sin mapeo público""",
            "notes": "Desequilibrios comparativos y brecha de información."
        },
        {
            "id": "slide-27",
            "slideNumber": 27,
            "layout": "content",
            "title": "Cuatro Desafíos de Información",
            "content": """1. Trazabilidad: No hay diccionario público programas → COFOG

2. Desagregación: Faltan desgloses por servicio y territorio

3. Interoperabilidad: Registros fragmentados entre instituciones

4. Evaluación: Pocas evaluaciones de impacto rigurosas en seguridad ciudadana""",
            "notes": "Los 4 desafíos de información identificados."
        },

        # ========== SECCIÓN 6: RECOMENDACIONES (6 slides) ==========
        {
            "id": "slide-28",
            "slideNumber": 28,
            "layout": "content",
            "title": "5 Recomendaciones de Política Pública",
            "content": """CALIDAD SOBRE CANTIDAD:

1. Reforzar prevención y reinserción
2. Abrir espacio para I+D
3. Profundizar interoperabilidad y trazabilidad
4. Desarrollar métricas de desempeño
5. Consolidar línea base para evaluación continua""",
            "notes": "Las 5 recomendaciones del informe."
        },
        {
            "id": "slide-29",
            "slideNumber": 29,
            "layout": "content",
            "title": "Rec 1: Reforzar Prevención y Reinserción",
            "content": """Sin disminuir abruptamente el control:

• Recomposición gradual del gasto
• Fortalecer Subsecretaría de Prevención del Delito
• Alinear gasto penitenciario con objetivos de reducción de reincidencia
• Priorizar programas con evidencia de efectividad""",
            "notes": "Recomendación 1: prevención y reinserción."
        },
        {
            "id": "slide-30",
            "slideNumber": 30,
            "layout": "content",
            "title": "Rec 2: Abrir Espacio para I+D",
            "content": """Establecer línea de gasto en subfunción 7035:

• Datos y modelos de gestión
• Evaluación de programas
• Desarrollo tecnológico
• Experimentación y pilotos

Objetivo: Preparar el sistema para enfrentar delito más sofisticado""",
            "notes": "Recomendación 2: crear capacidad de I+D."
        },
        {
            "id": "slide-31",
            "slideNumber": 31,
            "layout": "content",
            "title": "Rec 3: Profundizar Interoperabilidad",
            "content": """Plan de vinculación presupuesto-COFOG-resultados:

• Publicar diccionario de mapeo programas → subfunciones
• Paneles periódicos: gasto + dotaciones + indicadores
• Desagregación por institución y territorio
• Identificadores comunes entre instituciones""",
            "notes": "Recomendación 3: mejorar trazabilidad de datos."
        },
        {
            "id": "slide-32",
            "slideNumber": 32,
            "layout": "content",
            "title": "Rec 4: Desarrollar Métricas de Desempeño",
            "content": """Introducción progresiva de indicadores:

Policías: Tiempos respuesta, esclarecimiento
Justicia: Duración causas, tasa condena
Prisiones: Hacinamiento, reincidencia

Objetivo: Orientar recursos hacia áreas con mejores resultados""",
            "notes": "Recomendación 4: indicadores de desempeño."
        },
        {
            "id": "slide-33",
            "slideNumber": 33,
            "layout": "content",
            "title": "Rec 5: Consolidar Línea Base",
            "content": """Este informe como punto de partida:

• Actualización periódica de series
• Módulos de análisis más sofisticados
• Estudios de eficiencia técnica
• Evaluaciones de impacto específicas

Cerrar brecha entre diagnóstico fiscal y gestión cotidiana""",
            "notes": "Recomendación 5: evaluación continua."
        },

        # ========== SECCIÓN 7: CIERRE (4 slides) ==========
        {
            "id": "slide-34",
            "slideNumber": 34,
            "layout": "content",
            "title": "Mensaje Final",
            "content": """"Dado el nivel de esfuerzo que Chile ya realiza en seguridad, el principal margen de mejora se encuentra en cómo se gastan los recursos y cómo se conectan con resultados."

Avanzar hacia una seguridad con mayor calidad del gasto:
• Es una exigencia fiscal
• Es condición para recuperar confianza ciudadana""",
            "notes": "Mensaje central del informe."
        },
        {
            "id": "slide-35",
            "slideNumber": 35,
            "layout": "content",
            "title": "Próximos Pasos",
            "content": """1. Socialización de hallazgos con autoridades
2. Piloto de interoperabilidad con 2-3 instituciones
3. Diseño de indicadores de desempeño prioritarios
4. Actualización anual de series COFOG
5. Evaluaciones de impacto en programas seleccionados

Oportunidad de colaboración con BID""",
            "notes": "Agenda de implementación propuesta."
        },
        {
            "id": "slide-36",
            "slideNumber": 36,
            "layout": "content",
            "title": "Equipo del Proyecto",
            "content": """Espacio Público:

• Benjamín García (Director Ejecutivo)
• Eleni Kokkidou (Subdirectora Ejecutiva)
• Patricio Domínguez (Director)
• Mauricio Duce (Director)
• Martín Illanes (Investigador)""",
            "notes": "Equipo responsable del estudio."
        },
        {
            "id": "slide-37",
            "slideNumber": 37,
            "layout": "title",
            "title": "¡Gracias!",
            "content": "Eficiencia y Calidad del Gasto Público en Seguridad Ciudadana en Chile\n\nEspacio Público para BID\nEnero 2026",
            "notes": "Cierre de presentación. Abrir a preguntas."
        },
    ]

    return {
        "slides": slides,
        "theme": {
            "primaryColor": "#1a365d",
            "secondaryColor": "#c53030",
            "fontFamily": "Arial, sans-serif"
        }
    }


def main():
    """Update Scribe document with slides data."""
    db = SessionLocal()
    try:
        # Find the document
        doc = db.query(Document).filter(Document.slug == DOCUMENT_SLUG).first()
        if not doc:
            print(f"Document not found: {DOCUMENT_SLUG}")
            # Create the document if it doesn't exist
            doc = Document(
                slug=DOCUMENT_SLUG,
                title="BID Seguridad Final - Presentación",
                doc_type="presentation",
                front_matter={},
                content={},
            )
            db.add(doc)
            print(f"Created new document: {DOCUMENT_SLUG}")

        # Update front_matter with slides_data
        front_matter = doc.front_matter or {}
        front_matter["slides_data"] = build_slides_data()
        doc.front_matter = front_matter
        doc.doc_type = "presentation"

        db.commit()
        db.refresh(doc)

        slides_count = len(front_matter["slides_data"]["slides"])
        print(f"Updated document: {DOCUMENT_SLUG}")
        print(f"Total slides: {slides_count}")
        print(f"View at: https://scribe.illanes00.cl/documents/{DOCUMENT_SLUG}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
