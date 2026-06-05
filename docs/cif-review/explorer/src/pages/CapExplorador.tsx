import PivotExplorer from '../components/PivotExplorer'
import MosaicCube from '../components/MosaicCube'
import Treemap from '../components/Treemap'
import Sankeys from '../components/Sankeys'

// Capítulo 3 · El cubo OCDE 2023 y las áreas del gasto.
// Mini-informe integrado: el cubo (función × proveedor × financiador, un solo año)
// queda UNIDO a las cifras, y las áreas del gasto se ven como treemap jerárquico
// con capas conmutables (financiador, proveedor, intersección, instrumento).
export default function CapExplorador() {
  return (
    <>
      <header className="chapter-head">
        <p style={{ margin: 0, fontSize: 12.5, fontWeight: 700, letterSpacing: '.04em', textTransform: 'uppercase', color: '#2b6cb0' }}>
          Capítulo 3
        </p>
        <h1 className="ptitle">El cubo OCDE y las áreas del gasto</h1>
        <p className="psub">
          Cada peso gastado en medicamentos se clasifica por tres ejes: en qué se usa (función),
          quién lo entrega (proveedor) y quién lo paga (financiador). El cubo cruza esos tres ejes
          para un solo año. Debajo, el treemap descompone el gasto por áreas, con capas conmutables,
          y los diagramas de Sankey muestran cómo fluye la plata.
        </p>
      </header>

      <div className="card" style={{ borderLeftColor: '#2b6cb0' }}>
        <b>El cubo es un objeto de un solo año.</b> Reúne, en una sola foto, cuánto se gasta en cada
        función de salud, quién lo provee y quién lo financia. No se mezclan años: las cifras de
        compra (2024), de la Ley Ricarte Soto (2025) o del gasto municipal corresponden a sus propios
        años y van en su capítulo. Las celdas con desglose por medicamento están ancladas a 2022 (el
        último año con detalle confirmado en las cuentas de salud); el agregado de salud 2023 está
        disponible y su desglose por medicamento se está incorporando. Las unidades se rotulan en % del
        PIB (principal); entre paréntesis, pesos (MM$ = millones de pesos) y USD PPA (dólar ajustado por
        poder de compra, rotulado, no el dólar de mercado).
      </div>

      {/* El cubo, unido a las cifras: tabla dinámica + descomposición visual */}
      <PivotExplorer />
      <MosaicCube />

      {/* Las áreas del gasto: treemap jerárquico con capas conmutables */}
      <Treemap />

      {/* Los flujos: Sankeys embebidos de viz/ */}
      <Sankeys />
    </>
  )
}
