import { BarList, type BarItem } from './HierBar'
import { RAINBOW } from '../data'
import { FARMACIA_SERVICIO_2024 } from '../data/gaps'
import Caption from './Caption'

// Reparto territorial de la línea Farmacia entre los Servicios de Salud, 2024.
// El gasto se concentra en los Servicios metropolitanos y las regiones más
// pobladas; los porcentajes son sobre el total devengado de la red.
const TOTAL = FARMACIA_SERVICIO_2024.reduce((a, s) => a + s.mm, 0)

export default function FarmaciaServicio() {
  const items: BarItem[] = FARMACIA_SERVICIO_2024.map((s, i) => ({
    label: s.servicio,
    mm: s.mm,
    cert: 'real',
    fuente: 'Ejecución por Servicio de Salud (DIPRES)',
    color: RAINBOW[i % RAINBOW.length],
  }))

  return (
    <section id="farmacia-servicio">
      <h2 className="ptitle">Dónde se ejecuta: la Farmacia por Servicio de Salud</h2>
      <p className="psub">
        La línea Farmacia se reparte entre los 29 Servicios de Salud y dos Centros de Referencia.
        El gasto se concentra en los Servicios metropolitanos y en las regiones más pobladas. El total
        devengado de la red en 2024 es de {TOTAL.toLocaleString('es-CL')} MM$.
      </p>

      <Caption ch={4} n={5} kind="grafico" title="Farmacia por Servicio de Salud, 2024 (MM$ y % de la red)" />
      <BarList items={items} base={TOTAL} unidad="MM$" />
      <p className="note">
        Fuente: ejecución presupuestaria de la línea Farmacia por capítulo/Servicio de Salud (DIPRES),
        <code> cochid_datos.meds.farmacia_servicio</code>. Los porcentajes son sobre el total de la red.
      </p>
    </section>
  )
}
