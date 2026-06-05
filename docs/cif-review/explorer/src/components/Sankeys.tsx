import { useState } from 'react'
import Caption from './Caption'

// Embebe los diagramas de Sankey de viz/ (Plotly standalone) vía iframe.
// sankey-publico: financiación (transferencias FONASA) vs ejecución (Farmacia),
//   y el total público disjunto en banda 1,1-1,2 billones.
// sankey-total: las tres vistas (devengado / compra / bolsillo), NO aditivas.
const BASE = import.meta.env.BASE_URL

const SANKEYS = [
  {
    key: 'publico',
    file: 'viz/sankey-publico.html',
    label: 'Gasto público: financiación vs ejecución',
    height: 560,
    desc: 'El sistema público tiene dos caras de la misma plata: FONASA financia (transferencias) y los Servicios de Salud ejecutan (Farmacia). Sumar ambos lados infla del orden de 500.000 MM$. El total disjunto del lado ejecución se ubica en la banda de 1,1 a 1,2 billones de pesos (0,42% a 0,46% del PIB).',
  },
  {
    key: 'total',
    file: 'viz/sankey-total.html',
    label: 'Las tres vistas del gasto (no aditivas)',
    height: 720,
    desc: 'Tres fotografías del mismo gasto físico desde marcos distintos: el devengado público, la compra (Mercado Público) y el bolsillo de los hogares. NO se suman: hacerlo sería triple conteo. La línea Farmacia (736.761 MM$) es el nodo común que aparece en las tres.',
  },
] as const

export default function Sankeys() {
  const [active, setActive] = useState<'publico' | 'total'>('publico')
  const s = SANKEYS.find(x => x.key === active)!

  return (
    <section id="sankeys">
      <h2 className="ptitle">Cómo fluye la plata: diagramas de Sankey</h2>
      <p className="psub">
        Dos diagramas de flujo trazan de dónde sale el gasto y a dónde va. El primero muestra por qué
        no se pueden sumar la financiación y la ejecución del mismo gasto. El segundo, por qué las tres
        vistas del gasto (devengado, compra y bolsillo) no se suman entre sí.
      </p>

      <div className="filterbox" style={{ display: 'inline-flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        <label style={{ margin: 0 }}>Diagrama</label>
        {SANKEYS.map(x => (
          <button
            key={x.key}
            className="preset"
            style={{
              width: 'auto', margin: 0,
              background: active === x.key ? '#1a365d' : undefined,
              color: active === x.key ? '#fff' : undefined,
              borderColor: active === x.key ? '#1a365d' : undefined,
            }}
            onClick={() => setActive(x.key)}
          >
            {x.label}
          </button>
        ))}
      </div>

      <Caption ch={3} n={3} kind="grafico" title={s.label} />
      <div className="chartbox" style={{ padding: 0, overflow: 'hidden' }}>
        <iframe
          key={s.key}
          title={s.label}
          src={`${BASE}${s.file}`}
          style={{ width: '100%', height: s.height, border: 0, display: 'block' }}
          loading="lazy"
        />
      </div>
      <p className="note">{s.desc}</p>
      <p className="note">
        Fuente: reconstrucción Espacio Público sobre DIPRES, CENABAST, SINIM y la Encuesta de
        Presupuestos Familiares del INE. Diagramas en Plotly; se abren también de forma independiente
        en <code>{s.file}</code>.
      </p>
    </section>
  )
}
