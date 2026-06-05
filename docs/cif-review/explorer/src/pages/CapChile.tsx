import ComparabilityChile from '../components/ComparabilityChile'

// Capítulo 1 · El gasto en salud total y su descomposición (apertura top-down):
// cuánto gasta Chile en salud, qué fracción es medicamento y qué deja invisible.
export default function CapChile() {
  return (
    <>
      <p className="psub" style={{ textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 700, color: '#2b6cb0', margin: '36px 0 0' }}>
        Referencia
      </p>
      <h1 className="ptitle" style={{ marginTop: 2 }}>El gasto en salud total y su descomposición</h1>
      <p className="psub">
        El punto de partida es el gasto en salud total: cuánto gasta Chile (en % del PIB), cómo se
        ordena en tres ejes (en qué se gasta, quién lo provee, quién lo paga) y qué fracción es
        medicamento. Después, qué registros alimentan cada celda de las cuentas de salud y qué deja
        de medir Chile cuando se compara internacionalmente.
      </p>
      <ComparabilityChile />
    </>
  )
}
