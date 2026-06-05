import MedicineBreakdown from '../components/MedicineBreakdown'

// Capítulo 3 · El medicamento ambulatorio (HC.5.1): el dato duro OCDE SHA en CLP,
// por canal y por financiador, su perímetro (NO es todos los medicamentos), los
// programas de cobertura y el vacío, y el gasto catastrófico.
export default function CapMedicamento() {
  return (
    <article>
      <header>
        <p className="psub" style={{ textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 700, color: '#2b6cb0', margin: 0 }}>
          Capítulo 2
        </p>
        <h1 className="ptitle" style={{ marginTop: 2 }}>
          El medicamento dentro de la salud
        </h1>
        <p className="psub">
          Del gasto en salud total se hace zoom al medicamento. El medicamento total (ambulatorio más
          hospitalario) no se publica como una cifra única: la pieza medible es el ambulatorio
          (HC.5.1, OCDE SHA 2022). Aquí va por canal de dispensación y por quién lo paga, qué deja
          fuera (el fármaco de internación, en HC.1, y las vacunas del PNI), los programas de cobertura
          y el vacío, y la carga del gasto catastrófico sobre los hogares.
        </p>
      </header>
      <MedicineBreakdown />
    </article>
  )
}
