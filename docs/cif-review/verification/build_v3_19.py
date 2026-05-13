"""v3.19: limpieza de patrones IA + cambios narrativos prioritarios.

Cambios vs v3.18 (todos como tracked changes con autor "Martín Illanes"):

LIMPIEZA DE PATRONES IA (sobre-correcciones "no es A, sino B"):
1. "no es un fenómeno meramente administrativo, sino un síntoma" → "es un síntoma estructural"
2. "no solo definir beneficios, sino asegurar" → "definir beneficios y asegurar"
3. "no solo precios de lista sino también" → "precios de lista junto con"
4. "no es un fenómeno colateral ni marginal: es un síntoma" → "es un síntoma estructural"
5. "no se explica sólo por 'precio', sino por una arquitectura" → reformular sin antítesis
6. "no depende de una sola medida, sino de un paquete" → "depende de un paquete"
7. "no es un fenómeno homogéneo: responde a dos frentes" → "responde a dos frentes"

CAMBIOS NARRATIVOS PRIORITARIOS:
8. Mensaje 4: "Una opción priorizada para la discusión" → "El informe profundiza uno
   de los tres escenarios" (sacar prescriptividad)
9. Mensaje 6: "los países que han reducido" → "varios países OCDE que han reducido"
10. Cap 7 reframe: "actúa como piso universal" → "actúa como red de protección
    cuando los regímenes específicos no cubren"

Salida: output/informe-final-v3.19.docx + -aceptada.docx
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

# Reusar funciones del build_v3_18
sys.path.insert(0, str(Path(__file__).parent))
from build_v3_18 import (
    AUTHOR,
    DATE,
    W_NS,
    XML_NS,
    qn,
    next_rev,
    find_and_replace_text,
)

BASE = Path("/srv/projects/cochid/cochid-scribe")
SRC = BASE / "docs/cif-review/output/informe-final-v3.18.docx"
V19 = BASE / "docs/cif-review/output/informe-final-v3.19.docx"
V19A = BASE / "docs/cif-review/output/informe-final-v3.19-aceptada.docx"


# Override DATE for v3.19 changes
DATE_V19 = "2026-05-07T14:00:00-04:00"

# Monkey-patch: build_v3_18.DATE is used by find_and_replace_text. We need v3.19 timestamps.
import build_v3_18
build_v3_18.DATE = DATE_V19


CHANGES = [
    # ========== LIMPIEZA PATRONES IA ==========
    (
        "no se explica sólo por “precio”, sino por una arquitectura fragmentada de cobertura y provisión",
        "se explica por una arquitectura fragmentada de cobertura y provisión, más que por el precio unitario",
        "M-Mensajes: 'no se explica sólo, sino por'",
    ),
    (
        "no se explica sólo por \"precio\", sino por una arquitectura fragmentada de cobertura y provisión",
        "se explica por una arquitectura fragmentada de cobertura y provisión, más que por el precio unitario",
        "M-Mensajes: 'no se explica sólo, sino por' (variante quotes)",
    ),
    (
        "no depende de una sola medida, sino de un paquete de políticas",
        "depende de un paquete de políticas",
        "M-RE: 'no depende, sino paquete'",
    ),
    (
        "no es un fenómeno homogéneo: responde a dos frentes con lógicas distintas",
        "responde a dos frentes con lógicas distintas",
        "M-Mensajes: 'no es homogéneo: responde a dos frentes'",
    ),
    (
        "no es un fenómeno meramente administrativo, sino un síntoma estructural de insuficiencia",
        "es un síntoma estructural de insuficiencia",
        "Cap3: 'no es admin, sino síntoma'",
    ),
    (
        "requiere no solo definir beneficios, sino asegurar su materialización efectiva en la dispensación",
        "requiere definir beneficios y asegurar su materialización efectiva en la dispensación",
        "Cap3: 'no solo definir, sino asegurar'",
    ),
    (
        "incorporando no solo precios de lista sino también precios netos",
        "incorporando precios de lista y precios netos",
        "Cap7: 'no solo lista sino netos'",
    ),
    (
        "no es un fenómeno colateral ni marginal: es un síntoma de que los beneficios explícitos del sistema son insuficientes",
        "es un síntoma estructural de que los beneficios explícitos del sistema son insuficientes",
        "Cap3.2.6: 'no es colateral ni marginal: es síntoma'",
    ),

    # ========== CAMBIOS NARRATIVOS ==========
    # Mensaje 4: sacar prescriptividad ("priorizada")
    (
        "Una opción priorizada para la discusión es un escenario intermedio de convergencia OCDE.",
        "El informe profundiza en uno de los tres escenarios analizados, el de convergencia intermedia con el cluster OCDE.",
        "Mensaje 4: sacar 'priorizada'",
    ),

    # Mensaje 6: "varios países" en lugar de "los países"
    (
        "los países que han reducido el gasto de bolsillo en medicamentos combinan",
        "varios países OCDE que han reducido el gasto de bolsillo en medicamentos combinan",
        "Mensaje 6: 'los países' → 'varios países OCDE'",
    ),

    # Mensaje 7: reformular "Una implementación gradual" si menciona prescripción
    # (lo dejamos por ahora — es informativo)

    # Cap 4 / Cifras: aclarar HF3/HC51 en contexto natural si aparecen siglas crípticas
    # (deja que v4.0 lo haga, son demasiados cambios)

    # Cap 7: BFU como red de protección (refuerzo del framing existente)
    # En v3.18 ya dice "actúa como piso universal" — agregamos "red de protección"
    (
        "actúa como piso universal para medicamentos ambulatorios fuera de esos regímenes",
        "actúa como red de protección financiera para medicamentos ambulatorios cuando esos regímenes no cubren",
        "Cap 7: BFU 'piso universal' → 'red de protección'",
    ),
]


def main():
    print(f"=== build_v3_19.py ===")
    print(f"SRC: {SRC.name}")
    print(f"OUT: {V19.name}\n")

    if not SRC.exists():
        raise SystemExit(f"Source not found: {SRC}")

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

        for old, new, label in CHANGES:
            n = find_and_replace_text(body, old, new)
            if n:
                applied.append(f"  ✓ {label} ({n} replacement{'s' if n > 1 else ''})")
            else:
                skipped.append(f"  ✗ {label} (no match)")

        # Save
        tree.write(str(doc_xml), xml_declaration=True, encoding="UTF-8", standalone=True)

        if V19.exists():
            V19.unlink()
        V19.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(V19, "w", zipfile.ZIP_DEFLATED) as z:
            for path in (tmp / "src").rglob("*"):
                if path.is_file():
                    z.write(path, path.relative_to(tmp / "src"))
        size = V19.stat().st_size
        print(f"✓ {V19.name} ({size:,} bytes)\n")

        print("Applied:")
        for line in applied:
            print(line)
        if skipped:
            print("\nSkipped:")
            for line in skipped:
                print(line)
        print(f"\nTotal: {len(applied)} applied, {len(skipped)} skipped")

        # Generate "aceptada"
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmp2 = Path(tmpdir2)
            shutil.copy2(V19, tmp2 / "src.docx")
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
            if V19A.exists():
                V19A.unlink()
            with zipfile.ZipFile(V19A, "w", zipfile.ZIP_DEFLATED) as z:
                for path in (tmp2 / "src").rglob("*"):
                    if path.is_file():
                        z.write(path, path.relative_to(tmp2 / "src"))
            size_a = V19A.stat().st_size
            print(f"\n✓ {V19A.name} ({size_a:,} bytes)")


if __name__ == "__main__":
    main()
