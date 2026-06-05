import Charts from '../components/Charts'
import IntlBenchmark from '../components/IntlBenchmark'

// Capítulo 6 · Síntesis y comparación internacional: composición y carga
// distributiva (Charts) + Chile vs OCDE en el perímetro retail (IntlBenchmark).
export default function CapSintesis() {
 return (
 <>
 <header style={{ margin: '4px 0 8px' }}>
 <p style={{ margin: 0, fontSize: 12.5, fontWeight: 700, letterSpacing: '.04em', textTransform: 'uppercase', color: '#2b6cb0' }}>
 Capítulo 5
 </p>
 <h1 className="ptitle" style={{ marginTop: 0 }}>
 Síntesis y comparación internacional
 </h1>
 <p className="psub">
 Tres lecturas del gasto en medicamentos en Chile, composición por canal,
 carga distributiva por quintil y reparto del financiamiento, y la posición
 de Chile frente a la OCDE en el perímetro de medicamentos ambulatorios
 (<i>retail</i>).
 </p>
 </header>
 <Charts />
 <IntlBenchmark />
 </>
 )
}
