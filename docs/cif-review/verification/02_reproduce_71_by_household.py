"""Use the processed per-household dataset to compute the 71% ratio."""

import csv
from pathlib import Path
from collections import defaultdict

FILE = Path("/srv/projects/archives/illanes00-cif/data/processed/dataset_hogares_meds.csv")


def pnum(v: str) -> float:
    if not v or v.strip() == "":
        return 0.0
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return 0.0


def main():
    print(f"Loading: {FILE}")

    total_fe = 0.0
    total_meds_weighted = 0.0
    total_health_weighted = 0.0
    total_ingreso_weighted = 0.0
    n_hogares = 0
    n_con_meds = 0

    # Also by quintil
    by_quintil: dict[str, dict[str, float]] = defaultdict(lambda: {"meds": 0.0, "health": 0.0, "ingreso": 0.0, "n": 0.0})

    with open(FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_hogares += 1
            fe = pnum(row.get("fe", "0"))
            meds = pnum(row.get("gasto_meds", "0"))
            health = pnum(row.get("gastot_d06_hd", "0"))
            ingreso = pnum(row.get("ing_disp_hog_hd", "0"))
            quintil = row.get("quintil", "?")

            total_fe += fe
            total_meds_weighted += meds * fe
            total_health_weighted += health * fe
            total_ingreso_weighted += ingreso * fe

            if meds > 0:
                n_con_meds += 1

            by_quintil[quintil]["meds"] += meds * fe
            by_quintil[quintil]["health"] += health * fe
            by_quintil[quintil]["ingreso"] += ingreso * fe
            by_quintil[quintil]["n"] += fe

    print(f"\nTotal hogares muestra: {n_hogares:,}")
    print(f"Total hogares ponderado (fe): {total_fe:,.0f}")
    print(f"Hogares con gasto meds > 0: {n_con_meds:,} ({n_con_meds/n_hogares*100:.1f}%)")

    print("\n" + "=" * 70)
    print("GASTO AGREGADO PONDERADO (millones CLP)")
    print("=" * 70)
    print(f"  Gasto en medicamentos: ${total_meds_weighted/1_000_000:>15,.0f}M")
    print(f"  Gasto en salud total:  ${total_health_weighted/1_000_000:>15,.0f}M")
    print(f"  Ingreso disponible:    ${total_ingreso_weighted/1_000_000:>15,.0f}M")

    print("\n" + "=" * 70)
    print("RATIO CLAVE: Meds / Gasto salud del hogar")
    print("=" * 70)

    if total_health_weighted > 0:
        ratio = total_meds_weighted / total_health_weighted * 100
        print(f"\n  Ratio agregado: {ratio:.2f}%")
        print(f"  ${total_meds_weighted:,.0f} / ${total_health_weighted:,.0f}")

    print("\n" + "=" * 70)
    print("POR QUINTIL")
    print("=" * 70)
    print(f"  {'Quintil':10s} {'Meds/Salud':>12s} {'Meds/Ingreso':>14s} {'# hogares':>14s}")
    for q in sorted(by_quintil.keys()):
        d = by_quintil[q]
        meds_over_health = d["meds"] / d["health"] * 100 if d["health"] > 0 else 0
        meds_over_ing = d["meds"] / d["ingreso"] * 100 if d["ingreso"] > 0 else 0
        print(f"  Q{q:<9s} {meds_over_health:>11.2f}% {meds_over_ing:>13.2f}% {d['n']:>14,.0f}")

    print("\n" + "=" * 70)
    print("ANÁLISIS ALTERNATIVO: solo hogares con gasto meds > 0")
    print("=" * 70)

    # Restrict to households that actually report medicine spending
    total_fe_c = 0.0
    total_meds_c = 0.0
    total_health_c = 0.0

    with open(FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            meds = pnum(row.get("gasto_meds", "0"))
            if meds <= 0:
                continue
            fe = pnum(row.get("fe", "0"))
            health = pnum(row.get("gastot_d06_hd", "0"))
            total_fe_c += fe
            total_meds_c += meds * fe
            total_health_c += health * fe

    if total_health_c > 0:
        ratio_c = total_meds_c / total_health_c * 100
        print(f"\n  Ratio (solo hogares con gasto meds): {ratio_c:.2f}%")
        print(f"  ${total_meds_c:,.0f} / ${total_health_c:,.0f}")

    print("\n" + "=" * 70)
    print("INTERPRETACIÓN")
    print("=" * 70)
    print("""
Si el ratio agregado (total meds / total salud) es ~71%, el dato del informe
viene de ese cálculo: la proporción del gasto total en salud de los hogares
que se dirige a medicamentos.

Si solo es ~29% (agregado) o cercano, significa que el informe lo calculó
con otra fórmula (probablemente sobre un subconjunto específico).
""")


if __name__ == "__main__":
    main()
