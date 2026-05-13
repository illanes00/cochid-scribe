#!/usr/bin/env python3
"""
Add BID Proposal slides to the presentation.
Content from docs/bid/bid-presentacion-mejorada.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"


def get_bid_proposal_slides():
    """Return the BID proposal slides to add."""
    return [
        # New slide: Section header for BID Proposal
        {
            "layout": "title",
            "title": "PROPUESTA AL BID",
            "content": "Líneas de trabajo futuro 2026-2028",
            "notes": "Sección de propuesta concreta al BID."
        },
        # Oportunidades de colaboración
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

Total portafolio potencial: US$ 1,8 millones""",
            "notes": "El programa base (US$700K) es el mínimo. Las líneas adicionales son oportunidades de expansión."
        },
        # Inversión requerida
        {
            "layout": "content",
            "title": "Inversión: Programa de Asistencia Técnica",
            "content": """Desglose US$ 700.000 (3 años):

• Trazabilidad y datos: US$ 150.000
  Diccionario programa→COFOG, panel de indicadores

• Evaluaciones de impacto: US$ 300.000
  Metodologías rigurosas para programas clave

• Capacitación institucional: US$ 100.000
  DIPRES, Carabineros, PDI, Gendarmería

• Benchmarking regional: US$ 80.000
  Comparación continua con LATAM y OCDE

• Coordinación y gestión: US$ 70.000
  Project management y reporting BID""",
            "notes": "Presupuesto detallado del programa de asistencia técnica."
        },
        # Cronograma
        {
            "layout": "content",
            "title": "Cronograma 2026-2028",
            "content": """AÑO 2026:
Q1: Trazabilidad (diccionario)
Q2: Fondo I+D (diseño)
Q3: Panel de indicadores

AÑO 2027:
Q1: Evaluaciones de impacto
Q2: Benchmarking regional
Q3: Meta 5% prevención
Q4: Fondo I+D operativo

AÑO 2028:
Q1: Indicadores de desempeño
Q2: Actualización anual
Q3: Informe final""",
            "notes": "Cronograma de 3 años con hitos trimestrales."
        },
        # Retorno esperado
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
            "notes": "Beneficios cuantificables y estratégicos del programa."
        },
        # ¿Por qué Espacio Público?
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
            "notes": "Credenciales y valor agregado de Espacio Público."
        },
        # Riesgos y mitigaciones
        {
            "layout": "content",
            "title": "Riesgos y Mitigaciones",
            "content": """• Cambio de gobierno 2026 (Alta prob., Alto impacto)
  → Diseño institucional no partidista; anclar en DIPRES

• Resistencia institucional (Media prob.)
  → Involucrar contrapartes desde diseño; quick wins

• Datos no disponibles (Media prob.)
  → Plan B con fuentes alternativas

• Rotación de equipos (Media prob.)
  → Documentación exhaustiva; transferencia conocimiento

Estrategia: Diseño modular con avances independientes""",
            "notes": "Gestión de riesgos del programa."
        },
        # Mensaje final - slide inspiracional
        {
            "layout": "content",
            "title": "El desafío no es gastar más",
            "content": """Es gastar mejor.

Chile tiene los recursos.
Falta la gestión por resultados.

Con este informe, tenemos la línea base.
Con el BID, podemos transformar el sistema.""",
            "notes": "Cerrar con energía. Este es el llamado a la acción."
        },
    ]


def add_slides_after_position(slides_service, position, new_slides):
    """Add new slides after the specified position."""
    # Create slides
    for i, slide_data in enumerate(new_slides):
        slide_id = f"bid_proposal_{i:02d}"
        insert_pos = position + i + 1
        layout_id = "p13" if slide_data["layout"] == "title" else "p14"

        # Create slide
        create_request = {
            "requests": [{
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": insert_pos,
                    "slideLayoutReference": {
                        "layoutId": layout_id
                    }
                }
            }]
        }

        try:
            slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=create_request
            ).execute()
            print(f"Created slide {insert_pos + 1}: {slide_data['title'][:40]}")

            # Populate content
            populate_slide(slides_service, slide_id, slide_data)

        except Exception as e:
            print(f"Error creating slide: {e}")


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
            print(f"Error populating slide: {e}")


def find_slide_position(slides_service, title_contains):
    """Find the position of a slide by title substring."""
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    for i, slide in enumerate(presentation.get("slides", [])):
        for element in slide.get("pageElements", []):
            shape = element.get("shape", {})
            text_elements = shape.get("text", {}).get("textElements", [])
            for te in text_elements:
                if "textRun" in te:
                    content = te["textRun"].get("content", "")
                    if title_contains.lower() in content.lower():
                        return i
    return -1


def main():
    """Add BID proposal slides to the presentation."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return 1

        # Find the position of "Próximos Pasos" slide
        position = find_slide_position(slides_service, "Próximos Pasos")
        if position < 0:
            # Try alternative
            position = find_slide_position(slides_service, "Equipo del Proyecto")
        if position < 0:
            # Default to before last slide
            presentation = slides_service.presentations().get(
                presentationId=PRESENTATION_ID
            ).execute()
            position = len(presentation.get("slides", [])) - 2

        print(f"Adding BID proposal slides after position {position}")
        new_slides = get_bid_proposal_slides()
        add_slides_after_position(slides_service, position, new_slides)

        print(f"\nAdded {len(new_slides)} BID proposal slides!")
        print(f"View at: https://docs.google.com/presentation/d/{PRESENTATION_ID}")
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
