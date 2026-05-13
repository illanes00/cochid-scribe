"""Reproduce the 71% figure cited in the medicamentos report.

Tests several methodologies to figure out which one yields ~71%:
- Participation of medicines over total household health expenditure
- Participation of OOP medicine spending over total OOP health spending
- Private channel share of medicine expenditure
- Other plausible ratios

Uses the raw EPF files from the archived illanes00-cif project.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from decimal import Decimal

EPF_BASE = Path("/srv/projects/archives/illanes00-cif/data/raw/epf")
GASTOS_FILE = EPF_BASE / "base-gastos-ix-epf-(formato-csv).csv"
CCIF_FILE = EPF_BASE / "ccif-ix-epf-(formato-csv).csv"


def parse_number(value: str) -> float:
    """Parse numbers that use comma as decimal separator (Spanish/European format)."""
    if not value or value.strip() == "":
        return 0.0
    # Handle scientific notation: "2,39142857142857e+04"
    # The comma is the decimal separator
    cleaned = value.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_ccif_dictionary() -> dict[str, str]:
    """Load the CCIF dictionary mapping code → description."""
    ccif_map = {}
    with open(CCIF_FILE, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader)
        # Find the ccif and glosa columns
        print(f"CCIF columns: {header}")
        for row in reader:
            if len(row) >= 2:
                code = row[0].strip()
                desc = row[1].strip() if len(row) > 1 else ""
                ccif_map[code] = desc
    return ccif_map


def categorize_ccif(code: str) -> str:
    """Return a high-level category based on CCIF code prefix."""
    if not code:
        return "otros"
    # 06 = Salud
    # 06.1 = Productos, artefactos y equipos médicos
    # 06.1.1 = Productos farmacéuticos (medicamentos)
    # 06.1.2 = Otros productos médicos
    # 06.1.3 = Artefactos y equipos terapéuticos
    # 06.2 = Servicios médicos y paramédicos para pacientes ambulatorios
    # 06.3 = Servicios hospitalarios
    if code.startswith("06.1.1"):
        return "medicamentos"
    if code.startswith("06.1.2"):
        return "otros_productos_medicos"
    if code.startswith("06.1.3"):
        return "aparatos_terapeuticos"
    if code.startswith("06.2"):
        return "servicios_ambulatorios"
    if code.startswith("06.3"):
        return "servicios_hospitalarios"
    if code.startswith("06"):
        return "salud_otro"
    return "no_salud"


def main():
    print(f"Loading EPF gastos from: {GASTOS_FILE}")
    print(f"Total lines in file: (computing)")

    # Aggregate expenditure by category, weighted by fe (expansion factor)
    totals: dict[str, float] = defaultdict(float)
    n_records: dict[str, int] = defaultdict(int)
    unique_establecimientos: set[str] = set()
    medicine_by_estab: dict[str, float] = defaultdict(float)

    # Read header first
    with open(GASTOS_FILE, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        header = next(reader)
        print(f"GASTOS columns: {header}")

        # Map column indices
        idx_fe = header.index("fe") if "fe" in header else None
        idx_ccif = header.index("ccif") if "ccif" in header else None
        idx_gasto = header.index("gasto") if "gasto" in header else None
        idx_glosa = header.index("glosa_ccif") if "glosa_ccif" in header else None

        print(f"Column indices: fe={idx_fe}, ccif={idx_ccif}, gasto={idx_gasto}")
        print("\nProcessing rows...")

        count = 0
        for row in reader:
            count += 1
            if count % 100_000 == 0:
                print(f"  {count:,} rows processed")

            if len(row) <= max(idx_ccif or 0, idx_gasto or 0, idx_fe or 0):
                continue

            ccif = row[idx_ccif].strip() if idx_ccif is not None else ""
            gasto = parse_number(row[idx_gasto]) if idx_gasto is not None else 0.0
            fe = parse_number(row[idx_fe]) if idx_fe is not None else 1.0

            # Weighted expenditure
            weighted = gasto * fe

            category = categorize_ccif(ccif)
            totals[category] += weighted
            n_records[category] += 1

    print(f"\nTotal rows processed: {count:,}")

    # Compute totals for salud (06.x)
    print("\n" + "=" * 70)
    print("GASTO TOTAL EN SALUD (ponderado por fe), categoría 06.x")
    print("=" * 70)

    salud_categories = [
        "medicamentos",
        "otros_productos_medicos",
        "aparatos_terapeuticos",
        "servicios_ambulatorios",
        "servicios_hospitalarios",
        "salud_otro",
    ]
    total_salud = sum(totals[c] for c in salud_categories)

    for cat in salud_categories:
        amount = totals[cat]
        share = amount / total_salud * 100 if total_salud > 0 else 0
        n = n_records[cat]
        print(f"  {cat:30s}  ${amount:>18,.0f}  {share:>6.2f}%  ({n:>6,} registros)")

    print(f"  {'TOTAL SALUD (06.x)':30s}  ${total_salud:>18,.0f}  100.00%")

    print("\n" + "=" * 70)
    print("RATIOS CANDIDATOS PARA EL '71%' CITADO EN EL INFORME")
    print("=" * 70)

    meds = totals["medicamentos"]
    otros_prod = totals["otros_productos_medicos"]
    aparatos = totals["aparatos_terapeuticos"]
    prod_meds_total = meds + otros_prod + aparatos  # "productos medicos"

    ambulatorio = totals["servicios_ambulatorios"]
    hospitalario = totals["servicios_hospitalarios"]

    # Candidate 1: Medicamentos / Gasto total en salud
    if total_salud > 0:
        r1 = meds / total_salud * 100
        print(f"\nCandidato 1: Medicamentos / Gasto total salud = {r1:.2f}%")
        print(f"   ${meds:,.0f} / ${total_salud:,.0f}")

    # Candidate 2: Medicamentos / (productos + aparatos médicos)
    if prod_meds_total > 0:
        r2 = meds / prod_meds_total * 100
        print(f"\nCandidato 2: Medicamentos / Productos médicos (06.1) = {r2:.2f}%")
        print(f"   ${meds:,.0f} / ${prod_meds_total:,.0f}")

    # Candidate 3: (Medicamentos + ambulatorio) / gasto salud
    r3 = (meds + ambulatorio) / total_salud * 100
    print(f"\nCandidato 3: (Meds + ambulatorio) / total salud = {r3:.2f}%")

    # Candidate 4: Medicamentos / (medicamentos + servicios ambulatorios)
    denom4 = meds + ambulatorio
    r4 = meds / denom4 * 100 if denom4 > 0 else 0
    print(f"\nCandidato 4: Meds / (Meds + ambulatorio) = {r4:.2f}%")

    # Candidate 5: Medicamentos / (salud ex hospital)
    denom5 = meds + otros_prod + aparatos + ambulatorio
    r5 = meds / denom5 * 100 if denom5 > 0 else 0
    print(f"\nCandidato 5: Meds / (salud ex hospitalario) = {r5:.2f}%")

    # Candidate 6: (Meds + otros productos) / salud
    r6 = (meds + otros_prod) / total_salud * 100
    print(f"\nCandidato 6: (Meds + otros prod) / salud total = {r6:.2f}%")

    print("\n" + "=" * 70)
    print("INTERPRETACIÓN")
    print("=" * 70)
    print(
        "Si alguno de los candidatos anteriores está cerca de 71%, "
        "ese es probablemente el cálculo usado en el informe."
    )
    print(
        "Si ninguno está cerca, el 71% puede venir de un subconjunto "
        "más específico (ej: solo hogares que reportan gasto, solo EPF urbana, "
        "o dividiendo por tipo de establecimiento)."
    )


if __name__ == "__main__":
    main()
