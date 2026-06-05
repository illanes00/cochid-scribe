import InstrumentsDimensions from '../components/InstrumentsDimensions'
import DipresCrosswalk from '../components/DipresCrosswalk'
import SinimMunicipal from '../components/SinimMunicipal'
import SerieFarmacia from '../components/SerieFarmacia'
import FarmaciaServicio from '../components/FarmaciaServicio'
import MercadoPublico from '../components/MercadoPublico'

// Capítulo 5 · Instrumentos y presupuesto: cada instrumento chileno ubicado en
// los ejes SHA; el crosswalk DIPRES→OCDE; y el gasto municipal-APS (SINIM).
export default function CapInstrumentos() {
  return (
    <>
      <header>
        <p className="psub" style={{ textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 700, color: '#2b6cb0', margin: 0 }}>
          Capítulo 4
        </p>
        <h1 className="ptitle" style={{ marginTop: 2 }}>Instrumentos y presupuesto</h1>
        <p className="psub">
          Cada instrumento de la política chilena de medicamentos ubicado en los ejes de las cuentas
          de salud, el cruce de la Ley de Presupuestos (DIPRES) a las cuentas OCDE, y el gasto
          municipal en farmacia de la atención primaria (SINIM).
        </p>
      </header>

      <InstrumentsDimensions />
      <DipresCrosswalk />
      <SinimMunicipal />

      {/* Cómo evoluciona, dónde se ejecuta y qué se compra: las vistas de detalle
          de la ejecución pública (DIPRES + Mercado Público). */}
      <SerieFarmacia />
      <FarmaciaServicio />
      <MercadoPublico />
    </>
  )
}
