"""v4.3: cambios finales + brief extraído del informe.

Sobre v4.2:
1. Aplica cambios puntuales pendientes flagged por Martín (antítesis residuales, "opción priorizada")
2. Genera v4.3 .docx (informe completo)
3. Genera brief.docx extraído del v4.2 (mantiene figuras, tablas, formato del informe)

Salidas:
- informe-final-v4.3.docx (con tracked changes vs v3.18)
- informe-final-v4.3-aceptada.docx (limpia)
- brief-medicamentos-v4.3.docx (extracto del informe con figuras)
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).parent))
from build_v3_18 import (
    AUTHOR,
    W_NS,
    XML_NS,
    qn,
    next_rev,
    find_and_replace_text,
    get_para_text,
    normalize,
)

BASE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review")
SRC = BASE / "output/informe-final-v4.2.docx"
SRC_ACC = BASE / "output/informe-final-v4.2-aceptada.docx"
V43 = BASE / "output/informe-final-v4.3.docx"
V43A = BASE / "output/informe-final-v4.3-aceptada.docx"
BRIEF = BASE / "output/brief/brief-medicamentos-v4.3.docx"

DATE_V43 = "2026-05-07T20:00:00-04:00"

import build_v3_18
build_v3_18.DATE = DATE_V43


# ============================================================
# Cambios finales sobre v4.2 → v4.3
# ============================================================
FINAL_CHANGES = [
    # Antítesis "no como mecanismo ordinario de acceso"
    (
        "Conviene leerla como síntoma de vacíos del beneficio explícito, no como mecanismo ordinario de acceso.",
        "Conviene leerla como síntoma de vacíos del beneficio explícito; su crecimiento sostenido sugiere un problema estructural de diseño antes que un canal regular de acceso.",
        "v4.3: 'no como mecanismo ordinario'",
    ),
    # "Una opción priorizada para la discusión" residual
    (
        "Una opción priorizada para la discusión es un escenario intermedio de convergencia OCDE",
        "El informe profundiza en uno de los tres escenarios analizados, el de convergencia intermedia con el cluster OCDE",
        "v4.3: 'opción priorizada' residual",
    ),
    # Frase IA-flagged "El cierre del informe entrega preguntas filosófico-políticas..."
    (
        "El cierre del informe entrega preguntas filosófico-políticas que el debate público y el seminario buscan ordenar. Su resolución corresponde a la deliberación entre actores con preferencias y diagnósticos distintos.",
        "El cierre del informe deja planteadas preguntas que el debate público y el seminario buscan ordenar.",
        "v4.3: frase IA-flagged sobre cierre",
    ),
]


def apply_final_changes():
    """Aplica los cambios finales sobre v4.2 SUGERENCIAS y produce v4.3."""
    print("=== v4.3: cambios finales sobre v4.2 ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        root = tree.getroot()
        body = root.find(qn("body"))

        applied = []
        skipped = []
        for old, new, label in FINAL_CHANGES:
            n = find_and_replace_text(body, old, new)
            if n:
                applied.append(f"  ✓ {label} ({n})")
            else:
                skipped.append(f"  ✗ {label} (no match)")

        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V43.exists():
            V43.unlink()
        V43.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V43, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))

        print(f"\nApplied: {len(applied)}")
        for line in applied:
            print(line)
        if skipped:
            print(f"\nSkipped: {len(skipped)}")
            for line in skipped:
                print(line)
        print(f"\n✓ {V43.name} ({V43.stat().st_size:,} bytes)")

        # Generar aceptada
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmp2 = Path(tmpdir2)
            shutil.copy2(V43, tmp2 / "src.docx")
            with zipfile.ZipFile(tmp2 / "src.docx") as z:
                z.extractall(tmp2 / "src")

            doc_xml_a = tmp2 / "src/word/document.xml"
            tree_a = etree.parse(str(doc_xml_a))
            root_a = tree_a.getroot()

            for ins in list(root_a.iter(qn("ins"))):
                parent = ins.getparent()
                idx = list(parent).index(ins)
                for child in list(ins):
                    ins.remove(child)
                    parent.insert(idx, child)
                    idx += 1
                parent.remove(ins)

            for d in list(root_a.iter(qn("del"))):
                d.getparent().remove(d)

            tree_a.write(str(doc_xml_a), xml_declaration=True, encoding="UTF-8", standalone=True)
            if V43A.exists():
                V43A.unlink()
            with zipfile.ZipFile(V43A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            print(f"✓ {V43A.name} ({V43A.stat().st_size:,} bytes)")


def extract_brief_from_informe():
    """Extrae el brief desde v4.3-aceptada.docx manteniendo estilos, figuras y tablas.
    Estrategia: copia el .docx completo, luego elimina las secciones que no van al brief,
    deja la portada original + Mensajes clave + Resumen ejecutivo + Anexo seleccionado.
    Eso preserva 100% el formato, los estilos y todas las figuras del informe.
    """
    print("\n=== Brief v4.3: extracto del informe ===\n")

    SRC_BRIEF_BASE = V43A  # base es v4.3 limpia
    if not SRC_BRIEF_BASE.exists():
        print(f"⚠ Falta {SRC_BRIEF_BASE}")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copy2(SRC_BRIEF_BASE, tmp / "src.docx")
        with zipfile.ZipFile(tmp / "src.docx") as z:
            z.extractall(tmp / "src")

        doc_xml = tmp / "src/word/document.xml"
        tree = etree.parse(str(doc_xml))
        root = tree.getroot()
        body = root.find(qn("body"))

        # Identificar las secciones (Heading1) y decidir cuáles MANTENER
        # Brief 8pp = portada + Mensajes clave + RE expandido + nota corta sobre cómo leer el informe
        # Si el informe tiene esas dos secciones al inicio, mantenemos
        # eliminamos: 1. Introducción, 2. Acceso..., 3. Ruta..., 4. Diagnóstico..., 5. Comparado, 6. Escenarios, 7. BFU, 8. Conclusiones, Bibliografía, Anexos
        # Mantenemos: Tabla de contenidos (puede quedar pequeña), Mensajes clave, Resumen ejecutivo
        # Plus: agregar al final una página de nota metodológica corta

        keep_h1 = {
            "Tabla de contenidos",  # Mantener para mostrar estructura del informe extenso
            "Mensajes clave",
            "Resumen ejecutivo",
        }
        # Cualquier otro Heading1 → eliminar contenido hasta el siguiente Heading1

        children = list(body)
        # Buscar índices de los Heading1 a mantener y a eliminar
        h1_indices = []
        for i, elem in enumerate(children):
            if elem.tag != qn("p"):
                continue
            pStyle = elem.find(f".//{qn('pPr')}/{qn('pStyle')}")
            style = pStyle.get(qn("val"), "") if pStyle is not None else ""
            if style == "Heading1":
                text = normalize(get_para_text(elem))
                h1_indices.append((i, text, elem))

        # Determinar rangos a borrar
        to_delete_ranges = []  # list of (start_idx, end_idx)
        for j, (idx, text, _) in enumerate(h1_indices):
            keep = any(k.lower() in text.lower() for k in keep_h1)
            if not keep:
                # Determinar el rango: desde idx hasta el próximo h1
                next_idx = h1_indices[j+1][0] if j + 1 < len(h1_indices) else len(children)
                to_delete_ranges.append((idx, next_idx, text))

        print(f"  H1 detectados: {len(h1_indices)}")
        for idx, text, _ in h1_indices:
            keep = any(k.lower() in text.lower() for k in keep_h1)
            mark = "MANTENER" if keep else "ELIMINAR"
            print(f"    [{mark}] {text[:70]}")

        # Aplicar borrado de atrás hacia adelante
        # Pero borramos por elemento, no por índice (porque body se modifica)
        # Sacamos los elementos por referencia
        elements_to_remove = []
        for start, end, _ in to_delete_ranges:
            for k in range(start, end):
                if k < len(children):
                    elements_to_remove.append(children[k])

        print(f"\n  Eliminando {len(elements_to_remove)} elementos...")

        for elem in elements_to_remove:
            try:
                body.remove(elem)
            except Exception:
                pass

        # Save
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if BRIEF.exists():
            BRIEF.unlink()
        BRIEF.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(BRIEF, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))

        size = BRIEF.stat().st_size
        print(f"\n✓ {BRIEF.name} ({size:,} bytes)")
        print(f"  Hereda 100% formato del informe: estilos, fuentes, tablas, figuras embebidas.")


def main():
    apply_final_changes()
    extract_brief_from_informe()


if __name__ == "__main__":
    main()
