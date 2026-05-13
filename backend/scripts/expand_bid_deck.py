#!/usr/bin/env python3
"""
Expand BID Deck - Add missing slides per ChatGPT/BID feedback

Target expanded structure (~17 slides main deck):
0. Portada
1. Objetivo del estudio (NEW)
2. Qué cambia vs avance
3. 5 mensajes clave
4. El giro: tesis central
5. Contexto: por qué mirar calidad del gasto (NEW)
6. Evolución del gasto (tendencia)
7. Composición del gasto (estructura)
8. Comparación internacional
9. Metodología y límites COFOG (NEW)
10. Marco conceptual: inputs → outputs → outcomes (NEW)
11. Diagnóstico de brechas (cuello de botella)
12. Riesgos de interpretación (NEW)
13. Agenda información/interoperabilidad
14. 5 recomendaciones oficiales (UPDATE)
15. Cómo usar esto (NEW)
16. Próximos pasos / cierre
17. APÉNDICE
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"
EMU_PER_INCH = 914400


def get_slides_service():
    """Get Google Slides service."""
    db = SessionLocal()
    slides_service = build_slides_service(db)
    if not slides_service:
        print("ERROR: Google integration not connected")
        sys.exit(1)
    return slides_service, db


def generate_unique_id():
    return f"exp_{uuid.uuid4().hex[:12]}"


def create_slide_with_content(slide_id, title, body, insertion_index=None):
    """Create requests for a new slide with title and body."""
    title_id = f"{slide_id}_title"
    body_id = f"{slide_id}_body"

    requests = [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
                **({"insertionIndex": insertion_index} if insertion_index is not None else {})
            }
        },
        # Title
        {
            "createShape": {
                "objectId": title_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": int(9 * EMU_PER_INCH), "unit": "EMU"},
                        "height": {"magnitude": int(0.7 * EMU_PER_INCH), "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": int(0.5 * EMU_PER_INCH),
                        "translateY": int(0.25 * EMU_PER_INCH),
                        "unit": "EMU"
                    }
                }
            }
        },
        {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
        {
            "updateTextStyle": {
                "objectId": title_id,
                "style": {"fontSize": {"magnitude": 28, "unit": "PT"}, "bold": True, "fontFamily": "Arial"},
                "textRange": {"type": "ALL"},
                "fields": "fontSize,bold,fontFamily"
            }
        },
        # Body
        {
            "createShape": {
                "objectId": body_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": int(9 * EMU_PER_INCH), "unit": "EMU"},
                        "height": {"magnitude": int(4.3 * EMU_PER_INCH), "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": int(0.5 * EMU_PER_INCH),
                        "translateY": int(1.0 * EMU_PER_INCH),
                        "unit": "EMU"
                    }
                }
            }
        },
        {"insertText": {"objectId": body_id, "insertionIndex": 0, "text": body}},
        {
            "updateTextStyle": {
                "objectId": body_id,
                "style": {"fontSize": {"magnitude": 16, "unit": "PT"}, "fontFamily": "Arial"},
                "textRange": {"type": "ALL"},
                "fields": "fontSize,fontFamily"
            }
        }
    ]
    return requests


# ============================================================================
# NEW SLIDES TO ADD
# ============================================================================

EXPANDED_SLIDES = [
    {
        "id": "exp_objetivo",
        "title": "Objetivo del estudio",
        "body": """PREGUNTA CENTRAL
¿Cómo ha evolucionado el gasto público en seguridad ciudadana en Chile y qué tan bien se puede vincular con resultados?

ALCANCE
• Período: 2013-2024
• Cobertura: Gobierno Central (COFOG 703)
• Enfoque: Eficiencia y calidad del gasto, no solo nivel

ENTREGABLES
• Línea base de gasto público en seguridad
• Diagnóstico de brechas de información
• Agenda para mejorar calidad del gasto
• 5 recomendaciones de política implementables

Fuente: Términos de Referencia BID / Espacio Público"""
    },
    {
        "id": "exp_contexto_calidad",
        "title": "Por qué mirar calidad del gasto, no solo nivel",
        "body": """EL DEBATE TRADICIONAL
"Chile necesita gastar más en seguridad"

EL PROBLEMA CON ESE ENFOQUE
• No hay evidencia de que más gasto = mejores resultados
• La composición del gasto está congelada hace una década
• No existen evaluaciones sistemáticas de programas de seguridad
• Los datos no permiten conectar presupuesto → resultados

EL GIRO NECESARIO
De "¿cuánto gastamos?" a "¿qué tan bien gastamos?"

IMPLICANCIA PARA POLÍTICA PÚBLICA
Las decisiones presupuestarias deben basarse en evidencia de efectividad, no en demanda política por "más recursos".

Fuente: Análisis Espacio Público 2024"""
    },
    {
        "id": "exp_metodologia_cofog",
        "title": "Metodología y límites: qué podemos (y qué no) comparar",
        "body": """COFOG 703: ORDEN PÚBLICO Y SEGURIDAD
Clasificación funcional ONU que permite comparabilidad internacional

QUÉ INCLUYE (Chile)
✓ Carabineros y PDI (policías)
✓ Poder Judicial y Ministerio Público (justicia)
✓ Gendarmería y SENAME/Mejor Niñez (prisiones/menores)

QUÉ NO CAPTURA BIEN
✗ Gasto en prevención del delito
✗ Transferencias a municipios (seguridad comunal)
✗ Inversión en I+D de seguridad
✗ Diferencias de clasificación entre países

COMPARABILIDAD
• Gobierno Central Chile vs Gobierno General OCDE (cuidado)
• Datos comparables 2013-2024 dentro de Chile

Fuente: DIPRES, OCDE, Clasificador COFOG"""
    },
    {
        "id": "exp_marco_conceptual",
        "title": "Marco conceptual: de insumos a resultados",
        "body": """CADENA DE VALOR DEL GASTO EN SEGURIDAD

INSUMOS (Inputs)          →    PRODUCTOS (Outputs)    →    RESULTADOS (Outcomes)
─────────────────────────────────────────────────────────────────────────────────
• Remuneraciones              • Patrullajes               • Tasa de victimización
• Bienes y servicios          • Causas tramitadas         • Tasa de homicidios
• Inversión                   • Plazas penitenciarias     • Tiempo de respuesta
• Transferencias              • Atención a víctimas       • Tasa de condenas
                              • Programas prevención      • Reincidencia

BRECHA ACTUAL EN CHILE
Tenemos datos de INSUMOS (presupuesto).
Faltan datos integrados de PRODUCTOS y RESULTADOS.

CONSECUENCIA
Sin trazabilidad completa, no se puede optimizar la asignación.

Fuente: Marco de Calidad del Gasto (BID/OCDE)"""
    },
    {
        "id": "exp_riesgos",
        "title": "Riesgos de interpretación: más gasto ≠ más seguridad",
        "body": """⚠️ ADVERTENCIAS PARA LECTURA DE ESTOS DATOS

1. PERCEPCIÓN ≠ REALIDAD
   Mayor gasto no garantiza menor percepción de inseguridad.
   Los factores de percepción son múltiples y mediáticos.

2. INDICADORES ENGAÑOSOS
   "Más cárceles" puede subir indicadores de "gestión"
   pero empeorar resultados de bienestar (reincidencia).

3. KPIs ÚNICOS SON PELIGROSOS
   Un solo indicador incentiva gaming.
   Ejemplo: metas de detenciones → detenciones sin condena.

4. GASTO MUNICIPAL NO ESTÁ INCLUIDO
   Seguridad comunal (cámaras, alarmas, patrullaje local)
   no aparece en COFOG 703 central.

REGLA DE ORO
Cualquier conclusión de política debe triangular datos de gasto
con indicadores de resultados verificables.

Fuente: Buenas prácticas OCDE / BID en evaluación de gasto"""
    },
    {
        "id": "exp_como_usar",
        "title": "Cómo usar este estudio",
        "body": """PARA CONVERSACIONES CON GOBIERNO / CANDIDATOS
• "No solo subir presupuesto" → primero evaluar qué funciona
• Usar como argumento para gobernanza basada en evidencia

PARA PRIORIZAR INVERSIÓN
• Identificar dónde hay evidencia de efectividad
• Detectar dónde faltan datos para decidir

PARA DISEÑO DE POLÍTICA PÚBLICA
• Rediseñar clasificadores para capturar prevención
• Construir sistema de indicadores integrado
• Implementar evaluaciones de impacto

PARA APOYO BID / COOPERACIÓN INTERNACIONAL
• Asistencia técnica en interoperabilidad de datos
• Metodologías de evaluación de impacto
• Presupuesto por resultados
• Gobernanza del sistema de seguridad

Fuente: Recomendaciones Espacio Público para uso del estudio"""
    }
]

# Updated official recommendations (from final report)
UPDATED_RECOMMENDATIONS = {
    "id": "exp_recs_oficial",
    "title": "5 recomendaciones de política (Informe Final)",
    "body": """1. ARTICULACIÓN INSTITUCIONAL
   Establecer responsabilidades claras y coordinación entre instituciones
   → Crear instancia de gobernanza del gasto en seguridad

2. MEDICIÓN Y CALIDAD DEL GASTO
   Mejorar granularidad de datos (territorial, programática)
   → Diccionario de datos común entre instituciones

3. TRANSPARENCIA Y RENDICIÓN DE CUENTAS
   Publicar datos comparables en el tiempo, replicables
   → Portal de datos abiertos de gasto en seguridad

4. PLAN NACIONAL DE EVALUACIÓN
   Evaluaciones de impacto sistemáticas con métricas claras
   → Unidad de evaluación en DIPRES o SPD

5. PRESUPUESTOS POR RESULTADOS
   Vincular partidas presupuestarias con indicadores verificables
   → Piloto en programas de prevención 2027

Fuente: Informe Final Espacio Público, Recomendaciones Cap. 5"""
}


def expand_deck(slides_service, dry_run=True):
    """Add the expanded slides to the deck."""

    print("=" * 80)
    print("EXPANDING BID DECK")
    print("=" * 80)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("    Run with --execute to apply changes\n")

    # Phase 1: Create new slides (they'll be added at the end)
    print("\n[PHASE 1] Creating new slides...")

    all_requests = []
    for slide in EXPANDED_SLIDES:
        print(f"  Preparing: {slide['title'][:50]}...")
        requests = create_slide_with_content(
            slide_id=slide["id"],
            title=slide["title"],
            body=slide["body"]
        )
        all_requests.extend(requests)

    # Also create updated recommendations slide
    print(f"  Preparing: {UPDATED_RECOMMENDATIONS['title'][:50]}...")
    requests = create_slide_with_content(
        slide_id=UPDATED_RECOMMENDATIONS["id"],
        title=UPDATED_RECOMMENDATIONS["title"],
        body=UPDATED_RECOMMENDATIONS["body"]
    )
    all_requests.extend(requests)

    print(f"\nTotal requests: {len(all_requests)}")

    if dry_run:
        print("\n[DRY RUN] Would create these slides:")
        for slide in EXPANDED_SLIDES:
            print(f"  • {slide['title']}")
        print(f"  • {UPDATED_RECOMMENDATIONS['title']}")
        return True

    # Execute creation
    try:
        body = {"requests": all_requests}
        slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"\n✓ Created {len(EXPANDED_SLIDES) + 1} new slides")
    except Exception as e:
        print(f"\n✗ ERROR creating slides: {e}")
        return False

    return True


def reorder_expanded_deck(slides_service, dry_run=True):
    """
    Reorder the deck to final target structure.

    Target order:
    0: Portada (keep)
    1: Objetivo del estudio (exp_objetivo)
    2: Qué hay de nuevo (exec_slide_02)
    3: 5 mensajes clave (exec_slide_03)
    4: El giro (exec_slide_04)
    5: Contexto calidad (exp_contexto_calidad)
    6: Evolución/Tendencia (existing)
    7: Composición/Estructura (existing)
    8: Comparación internacional (existing)
    9: Metodología COFOG (exp_metodologia_cofog)
    10: Marco conceptual (exp_marco_conceptual)
    11: Diagnóstico brechas (exec_slide_09)
    12: Riesgos interpretación (exp_riesgos)
    13: Agenda información (exec_slide_10)
    14: 5 recomendaciones oficial (exp_recs_oficial)
    15: Cómo usar esto (exp_como_usar)
    16: Próximos pasos (exec_slide_12)
    17: APÉNDICE
    """

    print("\n[PHASE 2] Reordering to target structure...")

    if dry_run:
        print("\n[DRY RUN] Would reorder slides to:")
        target_order = [
            "0: Portada",
            "1: Objetivo del estudio",
            "2: Qué hay de nuevo",
            "3: 5 mensajes clave",
            "4: El giro",
            "5: Contexto calidad",
            "6: Evolución/Tendencia",
            "7: Composición/Estructura",
            "8: Comparación internacional",
            "9: Metodología COFOG",
            "10: Marco conceptual",
            "11: Diagnóstico brechas",
            "12: Riesgos interpretación",
            "13: Agenda información",
            "14: 5 recomendaciones oficial",
            "15: Cómo usar esto",
            "16: Próximos pasos",
            "17+: APÉNDICE"
        ]
        for item in target_order:
            print(f"    {item}")
        return True

    # Move new slides to their positions
    # Strategy: Move one at a time, from first to last position

    moves = [
        ("exp_objetivo", 1, "Objetivo del estudio"),
        ("exp_contexto_calidad", 5, "Contexto calidad"),
        ("exp_metodologia_cofog", 9, "Metodología COFOG"),
        ("exp_marco_conceptual", 10, "Marco conceptual"),
        ("exp_riesgos", 12, "Riesgos interpretación"),
        ("exp_recs_oficial", 14, "5 recomendaciones oficial"),
        ("exp_como_usar", 15, "Cómo usar esto"),
    ]

    for slide_id, target_pos, description in moves:
        print(f"  Moving {description} to position {target_pos}...")
        body = {
            "requests": [{
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": target_pos
                }
            }]
        }
        try:
            slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=body
            ).execute()
            print(f"    ✓ Success")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    return True


def show_structure(slides_service):
    """Show current structure."""
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slides = presentation.get("slides", [])
    print(f"\nTotal slides: {len(slides)}")
    print("-" * 80)

    for i, slide in enumerate(slides):
        slide_id = slide.get("objectId", "")
        title = "(no title)"
        for elem in slide.get("pageElements", []):
            shape = elem.get("shape", {})
            placeholder = shape.get("placeholder", {})
            if placeholder.get("type") in ("TITLE", "CENTERED_TITLE"):
                for te in shape.get("text", {}).get("textElements", []):
                    if "textRun" in te:
                        content = te["textRun"].get("content", "").strip()
                        if content:
                            title = content[:60]
                            break
        if title == "(no title)":
            for elem in slide.get("pageElements", []):
                shape = elem.get("shape", {})
                for te in shape.get("text", {}).get("textElements", []):
                    if "textRun" in te:
                        content = te["textRun"].get("content", "").strip()
                        if content and len(content) > 3:
                            title = content[:60]
                            break

        marker = " [MAIN]" if i < 17 else " [APPENDIX]"
        print(f"{i:3d}. {title}{marker}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Expand BID Deck")
    parser.add_argument("command", choices=["expand", "reorder", "show", "full"],
                        help="Command to execute")
    parser.add_argument("--execute", action="store_true", help="Execute changes")

    args = parser.parse_args()
    dry_run = not args.execute

    slides_service, db = get_slides_service()

    try:
        if args.command == "show":
            show_structure(slides_service)

        elif args.command == "expand":
            expand_deck(slides_service, dry_run)

        elif args.command == "reorder":
            reorder_expanded_deck(slides_service, dry_run)

        elif args.command == "full":
            print("FULL EXPANSION SEQUENCE")
            print("=" * 80)

            # Step 1: Create new slides
            if not expand_deck(slides_service, dry_run):
                return

            # Step 2: Reorder
            if not reorder_expanded_deck(slides_service, dry_run):
                return

            if not dry_run:
                print("\n" + "=" * 80)
                print("EXPANSION COMPLETE!")
                show_structure(slides_service)

    finally:
        db.close()


if __name__ == "__main__":
    main()
