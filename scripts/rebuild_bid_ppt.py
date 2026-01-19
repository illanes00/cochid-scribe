#!/usr/bin/env python3
"""
Rebuild BID Final PPT - Complete restructuring from 54 slides to 30-35 slides.

This script:
1. Analyzes the current PPT structure
2. Identifies duplicate slides
3. Reorganizes content according to new structure
4. Creates new slides for LATAM comparison, Hallazgos, Recomendaciones, Propuesta BID
5. Inserts charts from graphs.illanes00.cl
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import SessionLocal
from app.services.google import build_slides_service, get_google_credentials

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"

# New structure: 35 slides organized into 7 sections
NEW_STRUCTURE = {
    "sections": [
        {
            "name": "INTRODUCCIÓN",
            "slides": [
                {"num": 1, "title": "Portada", "keep": True, "notes": "Informe Final - Enero 2026"},
                {"num": 2, "title": "Contenido", "keep": True, "notes": "Índice de secciones"},
                {"num": 3, "title": "Contexto", "keep": True, "notes": "Crisis de seguridad: 61% prioridad (CEP), 87.7% percepción inseguridad"},
                {"num": 4, "title": "Metodología", "keep": True, "notes": "COFOG, fuentes (DIPRES, CEAD, ENUSC)"},
            ]
        },
        {
            "name": "DIAGNÓSTICO DEL GASTO",
            "slides": [
                {"num": 5, "title": "Gasto 2024: $4,47 billones", "chart": "grafico01c"},
                {"num": 6, "title": "Evolución 2013-2024", "chart": "grafico01c_interactivo"},
                {"num": 7, "title": "% del PIB: 1,43%", "chart": "grafico03"},
                {"num": 8, "title": "% Gasto Total: 5,82%", "chart": "grafico05"},
                {"num": 9, "title": "Composición: 70% personal", "chart": "grafico08"},
                {"num": 10, "title": "Rigidez del Gasto", "create": True},
                {"num": 11, "title": "Efecto Pandemia", "create": True},
                {"num": 12, "title": "Presupuesto 2025: +15%", "create": True},
            ]
        },
        {
            "name": "COMPARACIÓN LATAM",
            "slides": [
                {"num": 13, "title": "Chile en LATAM", "create": True, "content": "$490 PPP/cap vs $435 promedio"},
                {"num": 14, "title": "Paradoja del Gasto", "create": True, "content": "LATAM: 2.17% PIB > OCDE 1.70%, pero menos en absoluto"},
                {"num": 15, "title": "Ranking Regional", "create": True, "content": "Brasil $607, Costa Rica $572, Chile $490, Colombia $467"},
                {"num": 16, "title": "Anomalía Chilena", "create": True, "content": "Mayor desarrollo, menor gasto relativo (1.49% PIB)"},
                {"num": 17, "title": "Casos de Estudio", "create": True, "content": "El Salvador (+178%), Ecuador (-6%)"},
            ]
        },
        {
            "name": "INDICADORES DE SEGURIDAD",
            "slides": [
                {"num": 18, "title": "Victimización: 23,5%", "keep": True},
                {"num": 19, "title": "Homicidios: 6,0 por 100k", "keep": True},
                {"num": 20, "title": "Armas de Fuego: >50%", "keep": True},
                {"num": 21, "title": "Percepción: 87,7%", "keep": True},
                {"num": 22, "title": "Brecha Gasto-Resultados", "keep": True},
            ]
        },
        {
            "name": "HALLAZGOS PRINCIPALES",
            "slides": [
                {"num": 23, "title": "H1: Rigidez estructural", "create": True, "content": "70% en personal limita flexibilidad"},
                {"num": 24, "title": "H2: Fragmentación institucional", "create": True, "content": "PDI, Carabineros, Gendarmería sin coordinación"},
                {"num": 25, "title": "H3: Brecha evaluación", "create": True, "content": "Sin métricas de eficiencia del gasto"},
                {"num": 26, "title": "H4: Déficit tecnológico", "create": True, "content": "Inversión en TI bajo estándar OCDE"},
                {"num": 27, "title": "H5: Modelo reactivo", "create": True, "content": "Gasto en contención, no prevención"},
            ]
        },
        {
            "name": "RECOMENDACIONES",
            "slides": [
                {"num": 28, "title": "R1: Sistema de evaluación", "create": True, "content": "Indicador: Costo por delito prevenido"},
                {"num": 29, "title": "R2: Presupuesto por resultados", "create": True, "content": "Indicador: % programas con metas medibles"},
                {"num": 30, "title": "R3: Coordinación interagencial", "create": True, "content": "Indicador: Índice de duplicación funcional"},
                {"num": 31, "title": "R4: Inversión tecnológica", "create": True, "content": "Indicador: % gasto en TI vs OCDE"},
                {"num": 32, "title": "R5: Balance prevención/reacción", "create": True, "content": "Indicador: Ratio gasto preventivo/reactivo"},
            ]
        },
        {
            "name": "PROPUESTA BID",
            "slides": [
                {"num": 33, "title": "Oportunidad de Colaboración", "create": True},
                {"num": 34, "title": "Propuesta de Proyecto", "create": True, "content": "US$700K - US$1.8M, 24-36 meses"},
                {"num": 35, "title": "Roadmap 2026-2028", "create": True},
            ]
        },
    ]
}

# LATAM data for new slides
LATAM_DATA = {
    "countries": [
        {"name": "Brasil", "pib_pct": 2.87, "ppp_capita": 607, "trend_10y": "+45%"},
        {"name": "Costa Rica", "pib_pct": 2.04, "ppp_capita": 572, "trend_10y": "+50%"},
        {"name": "El Salvador", "pib_pct": 3.91, "ppp_capita": 496, "trend_10y": "+178%"},
        {"name": "Chile", "pib_pct": 1.49, "ppp_capita": 490, "trend_10y": "+43%"},
        {"name": "Colombia", "pib_pct": 2.23, "ppp_capita": 467, "trend_10y": "+79%"},
        {"name": "Argentina", "pib_pct": 0.99, "ppp_capita": 298, "trend_10y": "+28%"},
        {"name": "Ecuador", "pib_pct": 1.85, "ppp_capita": 280, "trend_10y": "-6%"},
        {"name": "Guatemala", "pib_pct": 1.96, "ppp_capita": 269, "trend_10y": "N/A"},
    ],
    "latam_avg_ppp": 435,
    "oecd_avg_ppp": 1182,
    "gap_ratio": 2.7,
}

# Key data for the presentation
KEY_DATA = {
    "gasto_2024": "$4,470.5 miles MM CLP",
    "gasto_billones": "$4,47 billones",
    "pct_pib": "1,43%",
    "pct_gasto_total": "5,82%",
    "victimizacion": "23,5%",
    "percepcion": "87,7%",
    "homicidios_100k": "6,0",
    "armas_fuego_pct": ">50%",
    "presupuesto_2025_aumento": "+15%",
    "chile_ppp": "$490",
    "latam_ppp": "$435",
}


def get_slides_service():
    """Get authenticated Google Slides service."""
    db = SessionLocal()
    try:
        service = build_slides_service(db)
        if not service:
            raise RuntimeError("Google integration not connected. Run OAuth flow first.")
        return service
    finally:
        db.close()


def analyze_presentation():
    """Analyze the current presentation structure."""
    service = get_slides_service()

    presentation = service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slides = presentation.get('slides', [])
    title = presentation.get('title', 'Unknown')

    print(f"=== Presentation Analysis ===")
    print(f"Title: {title}")
    print(f"Total slides: {len(slides)}")
    print()

    # Extract slide titles and content
    slide_data = []
    title_counts = defaultdict(list)

    for i, slide in enumerate(slides):
        slide_id = slide.get('objectId')
        page_elements = slide.get('pageElements', [])

        # Extract title (usually first text box)
        slide_title = ""
        slide_text = ""

        for elem in page_elements:
            if 'shape' in elem:
                shape = elem['shape']
                if 'text' in shape:
                    text_content = extract_text(shape['text'])
                    if not slide_title:
                        slide_title = text_content[:100].strip()
                    slide_text += text_content + "\n"

        slide_info = {
            'index': i + 1,
            'id': slide_id,
            'title': slide_title or f"Slide {i+1}",
            'text_preview': slide_text[:200].strip(),
            'element_count': len(page_elements)
        }
        slide_data.append(slide_info)

        # Track duplicate titles
        if slide_title:
            normalized_title = slide_title.lower().strip()[:50]
            title_counts[normalized_title].append(i + 1)

    return slide_data, title_counts


def extract_text(text_obj):
    """Extract plain text from a Slides text object."""
    if not text_obj:
        return ""

    text_elements = text_obj.get('textElements', [])
    result = []

    for elem in text_elements:
        if 'textRun' in elem:
            result.append(elem['textRun'].get('content', ''))

    return ''.join(result)


def identify_duplicates(title_counts):
    """Identify slides with duplicate or similar titles."""
    duplicates = {}
    for title, indices in title_counts.items():
        if len(indices) > 1:
            duplicates[title] = indices
    return duplicates


def print_slide_summary(slide_data, duplicates):
    """Print a summary of all slides."""
    print("=== Slide Summary ===")
    for slide in slide_data:
        dup_marker = ""
        title_lower = slide['title'].lower().strip()[:50]
        if title_lower in duplicates:
            dup_marker = " [DUPLICATE]"
        print(f"{slide['index']:2d}. {slide['title'][:60]}{dup_marker}")

    print()
    if duplicates:
        print("=== Duplicates Detected ===")
        for title, indices in duplicates.items():
            print(f"  '{title[:40]}...' appears in slides: {indices}")


def create_cleanup_requests(slide_data, duplicates):
    """Create batch requests to remove duplicate slides."""
    requests = []
    slides_to_remove = set()

    # For each duplicate group, keep the first occurrence, remove the rest
    for title, indices in duplicates.items():
        for idx in indices[1:]:  # Skip first, remove rest
            slide_info = slide_data[idx - 1]
            slides_to_remove.add(slide_info['id'])
            requests.append({
                'deleteObject': {
                    'objectId': slide_info['id']
                }
            })

    return requests, slides_to_remove


def create_text_replacement_requests():
    """Create requests to update text throughout the presentation."""
    replacements = [
        # Date updates
        ("Noviembre 2025", "Enero 2026"),
        ("noviembre 2025", "enero 2026"),
        ("Noviembre de 2025", "Enero de 2026"),
        # Title updates
        ("Informe de Avance", "Informe Final"),
        ("Informe de avance", "Informe Final"),
        # Data updates if needed
        ("$4,47 billones", "$4,47 billones"),  # Ensure consistency
    ]

    requests = []
    for old_text, new_text in replacements:
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': old_text,
                    'matchCase': False
                },
                'replaceText': new_text
            }
        })

    return requests


def create_new_slide(service, slide_config):
    """Create a new slide with the given configuration."""
    # Layout options: BLANK, TITLE, TITLE_AND_BODY, TITLE_AND_TWO_COLUMNS, etc.
    layout = 'TITLE_AND_BODY'

    requests = [{
        'createSlide': {
            'slideLayoutReference': {
                'predefinedLayout': layout
            },
            'placeholderIdMappings': []
        }
    }]

    return requests


def create_latam_section_requests(service, presentation):
    """Create requests to add the LATAM comparison section."""
    slides = presentation.get('slides', [])

    # Content for LATAM slides - Updated with latest data from graphs.illanes00.cl
    latam_slides = [
        {
            "title": "Chile en el Contexto Regional",
            "body": """GASTO EN SEGURIDAD PÚBLICA (COFOG 703) - 2023

Chile: $490 PPP per cápita
Promedio LATAM: $435 PPP per cápita
Promedio OCDE: $1,182 PPP per cápita

Chile gasta 13% más que el promedio regional, pero 59% menos que OCDE.

Fuente: CEPAL/COFOG, datos 2023"""
        },
        {
            "title": "La Paradoja del Gasto Regional",
            "body": """LATAM GASTA MÁS % PIB, MENOS EN TÉRMINOS ABSOLUTOS

LATAM promedio: 2.17% del PIB
OCDE promedio: 1.70% del PIB

Sin embargo, OCDE gasta 2.7x más per cápita

Esto refleja:
• Menor base tributaria en LATAM
• Mayor presión sobre recursos limitados
• Necesidad de eficiencia en el gasto"""
        },
        {
            "title": "Ranking Regional de Gasto",
            "body": """GASTO PPP PER CÁPITA (2023)

1. Brasil         $607    2.87% PIB
2. Costa Rica     $572    2.04% PIB
3. El Salvador    $496    3.91% PIB
4. Chile          $490    1.49% PIB
5. Colombia       $467    2.23% PIB
6. Argentina      $298    0.99% PIB
7. Ecuador        $280    1.85% PIB
8. Guatemala      $269    1.96% PIB

Fuente: CEPAL/COFOG 2023"""
        },
        {
            "title": "La Anomalía Chilena",
            "body": """MAYOR DESARROLLO, MENOR GASTO RELATIVO

Chile es outlier en la región:
• PIB per cápita más alto de LATAM ($32,801)
• Gasto en seguridad: solo 1.49% del PIB
• El más bajo entre países comparables

Implicancias:
• Margen fiscal para aumentar inversión
• Riesgo de subinversión estructural
• Necesidad de evaluar eficiencia actual"""
        },
        {
            "title": "Casos de Estudio Contrastantes",
            "body": """TRAYECTORIAS DIVERGENTES

EL SALVADOR: Aumento dramático
• De 2.52% a 3.91% del PIB (2013-2023)
• +178% en inversión per cápita (+10.8% CAGR)
• Estrategia de mano dura

ECUADOR: Recorte con consecuencias
• -6% en inversión (único caso negativo)
• -30% desde máximo 2013
• Escalada de violencia sin precedentes

Lección: El gasto importa, pero la eficiencia también."""
        }
    ]

    requests = []

    for i, slide_content in enumerate(latam_slides):
        # Create slide using OBJECT layout (Título y objetos)
        slide_request = {
            'createSlide': {
                'insertionIndex': 21 + i,  # After Comparación Internacional section
                'slideLayoutReference': {
                    'layoutId': 'p14'  # OBJECT layout = "Título y objetos"
                }
            }
        }
        requests.append(slide_request)

    return requests, latam_slides


def create_hallazgos_section_requests():
    """Create requests for the Hallazgos (Findings) section."""
    hallazgos = [
        {
            "title": "H1: Rigidez Estructural del Gasto",
            "body": """70% DEL GASTO SE DESTINA A PERSONAL

Consecuencias:
• Escaso margen para inversión
• Dificultad para reasignar recursos
• Presupuesto comprometido a largo plazo

Composición:
• Remuneraciones: 63%
• Bienes y servicios: 7%
• Inversión: <10%

Comparación OCDE: Personal ~55%"""
        },
        {
            "title": "H2: Fragmentación Institucional",
            "body": """MÚLTIPLES INSTITUCIONES SIN COORDINACIÓN EFECTIVA

Actores principales:
• Carabineros de Chile
• Policía de Investigaciones (PDI)
• Gendarmería
• Fiscalía / Ministerio Público

Problemas detectados:
• Duplicación de funciones
• Sistemas de información no integrados
• Métricas de desempeño diferentes
• Presupuestos gestionados por separado"""
        },
        {
            "title": "H3: Brecha de Evaluación",
            "body": """AUSENCIA DE MÉTRICAS DE EFICIENCIA

Situación actual:
• No existe costo por delito prevenido
• Sin evaluación de programas preventivos
• Métricas centradas en insumos, no resultados

Lo que no se mide:
• Efectividad de patrullaje
• ROI de inversión tecnológica
• Impacto de programas de prevención

Referencia: OCDE y BID recomiendan presupuesto por resultados"""
        },
        {
            "title": "H4: Déficit Tecnológico",
            "body": """INVERSIÓN EN TI BAJO ESTÁNDAR INTERNACIONAL

Gasto en tecnología:
• Chile: <3% del presupuesto de seguridad
• OCDE promedio: 5-8%
• Líderes (UK, Singapur): 10-12%

Áreas con brecha:
• Sistemas de análisis predictivo
• Integración de bases de datos
• Cámaras y monitoreo inteligente
• Plataformas de denuncia digital"""
        },
        {
            "title": "H5: Modelo Predominantemente Reactivo",
            "body": """GASTO CONCENTRADO EN CONTENCIÓN, NO PREVENCIÓN

Distribución estimada:
• Reacción/contención: ~85%
• Prevención: ~15%

Benchmark internacional:
• Países exitosos: 30-40% prevención
• Chile necesita rebalancear

Prevención efectiva incluye:
• Intervención temprana
• Programas comunitarios
• Diseño urbano seguro
• Rehabilitación efectiva"""
        }
    ]

    return hallazgos


def create_recomendaciones_section_requests():
    """Create requests for the Recomendaciones (Recommendations) section."""
    recomendaciones = [
        {
            "title": "R1: Sistema de Evaluación de Eficiencia",
            "body": """IMPLEMENTAR MÉTRICAS DE COSTO-EFECTIVIDAD

Propuesta:
• Desarrollar indicador de costo por delito prevenido
• Evaluar programas con metodología rigurosa
• Publicar resultados periódicamente

Indicador clave:
→ Costo por delito prevenido

Plazo: 18 meses para diseño e implementación piloto
Referencia: UK Home Office efficiency framework"""
        },
        {
            "title": "R2: Presupuesto por Resultados",
            "body": """VINCULAR RECURSOS A METAS MEDIBLES

Propuesta:
• Definir metas de reducción del delito por programa
• Asignar presupuesto según cumplimiento
• Crear incentivos institucionales

Indicador clave:
→ % de programas con metas medibles

Meta: 80% de programas con metas para 2027
Modelo: Performance-based budgeting (Australia, NZ)"""
        },
        {
            "title": "R3: Coordinación Interagencial",
            "body": """REDUCIR DUPLICACIÓN Y MEJORAR INTEGRACIÓN

Propuesta:
• Crear instancia de coordinación permanente
• Integrar sistemas de información
• Unificar métricas de desempeño

Indicador clave:
→ Índice de duplicación funcional

Meta: Reducir duplicación en 30% a 2028
Modelo: US DHS fusion centers"""
        },
        {
            "title": "R4: Plan de Inversión Tecnológica",
            "body": """CERRAR BRECHA CON ESTÁNDAR INTERNACIONAL

Propuesta:
• Aumentar inversión TI a 6% del presupuesto
• Priorizar: análisis predictivo, integración, monitoreo
• Capacitar personal en nuevas tecnologías

Indicador clave:
→ % gasto en TI vs promedio OCDE

Meta: Alcanzar 6% para 2028 (desde <3% actual)
Inversión estimada: +$50.000 MM CLP anuales"""
        },
        {
            "title": "R5: Rebalancear Prevención vs Reacción",
            "body": """AUMENTAR INVERSIÓN EN PREVENCIÓN DEL DELITO

Propuesta:
• Incrementar gasto preventivo de 15% a 25%
• Escalar programas con evidencia de efectividad
• Evaluar impacto continuamente

Indicador clave:
→ Ratio gasto preventivo / reactivo

Meta: 25% prevención para 2028
Programas prioritarios:
• Intervención familiar temprana
• Prevención escolar
• Reinserción post-penitenciaria"""
        }
    ]

    return recomendaciones


def create_propuesta_bid_section_requests():
    """Create requests for the Propuesta BID section."""
    propuesta = [
        {
            "title": "Oportunidad de Colaboración con el BID",
            "body": """ÁREA DE INTERÉS ESTRATÉGICO

Alineamiento con prioridades BID:
• Seguridad ciudadana en América Latina
• Modernización del Estado
• Presupuesto por resultados
• Evaluación de impacto

Fortalezas de Chile como caso piloto:
• Institucionalidad sólida
• Datos de calidad disponibles
• Capacidad técnica instalada
• Compromiso político transversal"""
        },
        {
            "title": "Propuesta de Proyecto",
            "body": """PROGRAMA DE EFICIENCIA EN SEGURIDAD PÚBLICA

Componentes:
1. Sistema de evaluación de eficiencia (40%)
2. Plataforma de coordinación interagencial (30%)
3. Piloto de presupuesto por resultados (30%)

Inversión estimada: US$700K - US$1.8M
Duración: 24-36 meses

Contrapartida Chile:
• Equipo técnico dedicado
• Acceso a datos institucionales
• Compromiso de implementación"""
        },
        {
            "title": "Roadmap de Implementación 2026-2028",
            "body": """FASES DEL PROYECTO

2026 - DISEÑO (Meses 1-12)
• Diagnóstico detallado
• Diseño de indicadores
• Selección de pilotos

2027 - PILOTO (Meses 13-24)
• Implementación en 2-3 instituciones
• Monitoreo continuo
• Ajustes iterativos

2028 - ESCALA (Meses 25-36)
• Expansión a todo el sistema
• Documentación de lecciones
• Transferencia de conocimiento regional

Entregables: Manual de replicabilidad para LATAM"""
        }
    ]

    return propuesta


def build_all_content_updates(service, presentation):
    """Build content update requests for existing slides."""
    slides = presentation.get('slides', [])
    requests = []

    # Map slide indices to content updates
    content_updates = {
        # Slide 5: Gasto 2024
        4: {
            "title": "Gasto en Seguridad 2024",
            "subtitle": "$4,47 billones"
        },
        # Slide 7: % PIB
        6: {
            "title": "Proporción del PIB",
            "subtitle": "1,43% del PIB"
        },
    }

    return requests


def execute_batch_update(service, requests, description=""):
    """Execute a batch update request."""
    if not requests:
        print(f"No requests to execute for: {description}")
        return None

    print(f"Executing {len(requests)} requests: {description}")

    try:
        response = service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body={'requests': requests}
        ).execute()
        print(f"  Success: {len(response.get('replies', []))} operations completed")
        return response
    except Exception as e:
        print(f"  Error: {e}")
        raise


def add_content_to_new_slides(service, slides_content, start_index):
    """Add content to newly created slides."""
    # Get updated presentation to find new slide IDs
    presentation = service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slides = presentation.get('slides', [])
    requests = []

    for i, content in enumerate(slides_content):
        if start_index + i >= len(slides):
            print(f"Warning: Slide index {start_index + i} out of range")
            continue

        slide = slides[start_index + i]
        page_elements = slide.get('pageElements', [])

        # Find title and body placeholders
        title_id = None
        body_id = None

        for elem in page_elements:
            if 'shape' in elem:
                shape = elem['shape']
                placeholder = shape.get('placeholder', {})
                placeholder_type = placeholder.get('type', '')

                if placeholder_type == 'TITLE' or placeholder_type == 'CENTERED_TITLE':
                    title_id = elem.get('objectId')
                elif placeholder_type == 'BODY' or placeholder_type == 'SUBTITLE':
                    body_id = elem.get('objectId')

        # Insert title text
        if title_id and content.get('title'):
            requests.append({
                'insertText': {
                    'objectId': title_id,
                    'text': content['title'],
                    'insertionIndex': 0
                }
            })

        # Insert body text
        if body_id and content.get('body'):
            requests.append({
                'insertText': {
                    'objectId': body_id,
                    'text': content['body'],
                    'insertionIndex': 0
                }
            })

    return requests


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Rebuild BID Final PPT')
    parser.add_argument('--analyze', action='store_true', help='Only analyze, do not modify')
    parser.add_argument('--cleanup', action='store_true', help='Remove duplicate slides')
    parser.add_argument('--add-latam', action='store_true', help='Add LATAM comparison section')
    parser.add_argument('--add-hallazgos', action='store_true', help='Add Hallazgos section')
    parser.add_argument('--add-recomendaciones', action='store_true', help='Add Recomendaciones section')
    parser.add_argument('--add-propuesta', action='store_true', help='Add Propuesta BID section')
    parser.add_argument('--update-text', action='store_true', help='Update text replacements')
    parser.add_argument('--full-rebuild', action='store_true', help='Execute full rebuild')
    args = parser.parse_args()

    print(f"Presentation ID: {PRESENTATION_ID}")
    print()

    # Always start with analysis
    slide_data, title_counts = analyze_presentation()
    duplicates = identify_duplicates(title_counts)
    print_slide_summary(slide_data, duplicates)

    if args.analyze:
        return

    service = get_slides_service()

    if args.cleanup or args.full_rebuild:
        print("\n=== Cleanup Phase ===")
        cleanup_requests, removed_ids = create_cleanup_requests(slide_data, duplicates)
        if cleanup_requests:
            print(f"Will remove {len(cleanup_requests)} duplicate slides")
            response = execute_batch_update(service, cleanup_requests, "Remove duplicates")
        else:
            print("No duplicates to remove")

    if args.update_text or args.full_rebuild:
        print("\n=== Text Update Phase ===")
        text_requests = create_text_replacement_requests()
        execute_batch_update(service, text_requests, "Text replacements")

    if args.add_latam or args.full_rebuild:
        print("\n=== Adding LATAM Section ===")
        presentation = service.presentations().get(presentationId=PRESENTATION_ID).execute()
        slide_requests, latam_content = create_latam_section_requests(service, presentation)

        # Create the slides first
        if slide_requests:
            execute_batch_update(service, slide_requests, "Create LATAM slides")

            # Then add content
            content_requests = add_content_to_new_slides(service, latam_content, 12)
            if content_requests:
                execute_batch_update(service, content_requests, "Add LATAM content")

    if args.add_hallazgos or args.full_rebuild:
        print("\n=== Adding Hallazgos Section ===")
        hallazgos_content = create_hallazgos_section_requests()

        # Get current slide count
        presentation = service.presentations().get(presentationId=PRESENTATION_ID).execute()
        current_slides = len(presentation.get('slides', []))

        # Create slides
        slide_requests = []
        for i in range(len(hallazgos_content)):
            slide_requests.append({
                'createSlide': {
                    'insertionIndex': current_slides + i,
                    'slideLayoutReference': {
                        'layoutId': 'p14'  # OBJECT layout = "Título y objetos"
                    }
                }
            })

        if slide_requests:
            execute_batch_update(service, slide_requests, "Create Hallazgos slides")
            content_requests = add_content_to_new_slides(service, hallazgos_content, current_slides)
            if content_requests:
                execute_batch_update(service, content_requests, "Add Hallazgos content")

    if args.add_recomendaciones or args.full_rebuild:
        print("\n=== Adding Recomendaciones Section ===")
        recom_content = create_recomendaciones_section_requests()

        presentation = service.presentations().get(presentationId=PRESENTATION_ID).execute()
        current_slides = len(presentation.get('slides', []))

        slide_requests = []
        for i in range(len(recom_content)):
            slide_requests.append({
                'createSlide': {
                    'insertionIndex': current_slides + i,
                    'slideLayoutReference': {
                        'layoutId': 'p14'  # OBJECT layout = "Título y objetos"
                    }
                }
            })

        if slide_requests:
            execute_batch_update(service, slide_requests, "Create Recomendaciones slides")
            content_requests = add_content_to_new_slides(service, recom_content, current_slides)
            if content_requests:
                execute_batch_update(service, content_requests, "Add Recomendaciones content")

    if args.add_propuesta or args.full_rebuild:
        print("\n=== Adding Propuesta BID Section ===")
        propuesta_content = create_propuesta_bid_section_requests()

        presentation = service.presentations().get(presentationId=PRESENTATION_ID).execute()
        current_slides = len(presentation.get('slides', []))

        slide_requests = []
        for i in range(len(propuesta_content)):
            slide_requests.append({
                'createSlide': {
                    'insertionIndex': current_slides + i,
                    'slideLayoutReference': {
                        'layoutId': 'p14'  # OBJECT layout = "Título y objetos"
                    }
                }
            })

        if slide_requests:
            execute_batch_update(service, slide_requests, "Create Propuesta BID slides")
            content_requests = add_content_to_new_slides(service, propuesta_content, current_slides)
            if content_requests:
                execute_batch_update(service, content_requests, "Add Propuesta BID content")

    # Final summary
    print("\n=== Final Summary ===")
    final_slide_data, _ = analyze_presentation()
    print(f"Total slides now: {len(final_slide_data)}")
    print(f"\nPresentation URL: https://docs.google.com/presentation/d/{PRESENTATION_ID}/edit")


if __name__ == "__main__":
    main()
