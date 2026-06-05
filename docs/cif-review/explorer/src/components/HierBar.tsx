// Barras horizontales para la jerarquía única. Solo barras, nada más.
// Cada barra muestra el % local (sobre la base del filtro) y, cuando la base
// no es el gasto total, también el % del gasto total. Marca el dato como real
// o estimación con un punto ámbar sobrio, y deja la fuente a mano.

import type { Cert } from '../data/hierarchy'

const fInt = (v: number) => Math.round(v).toLocaleString('es-CL')
const fPct = (v: number) => v.toFixed(1).replace('.', ',') + '%'

export interface BarItem {
  label: string
  sub?: string
  mm: number
  cert: Cert
  fuente: string
  color: string
}

// Pastilla "estimación" sobria (ámbar), o "dato" discreto.
export function CertPill({ cert }: { cert: Cert }) {
  if (cert === 'estimacion') {
    return <span className="hb-cert hb-cert-est" title="Cifra estimada o presentada como banda">estimación</span>
  }
  return <span className="hb-cert hb-cert-real" title="Dato observado en la fuente">dato</span>
}

// Lista de barras sobre una misma base. `gtPct` opcional: si la base local no
// es el gasto total, se entrega una función que da el % del gasto total.
export function BarList({
  items,
  base,
  unidad = 'millones de pesos',
  gtPct,
}: {
  items: BarItem[]
  base: number
  unidad?: string
  gtPct?: (mm: number) => number
}) {
  const max = Math.max(...items.map(i => i.mm))
  return (
    <div className="hb-list">
      {items.map(it => {
        const localPct = base ? (it.mm / base) * 100 : 0
        const w = max ? (it.mm / max) * 100 : 0
        return (
          <div className="hb-row" key={it.label}>
            <div className="hb-head">
              <span className="hb-label">{it.label}</span>
              <span className="hb-vals">
                <b className="hb-pct">{fPct(localPct)}</b>
                <span className="hb-mm">{fInt(it.mm)} {unidad}</span>
              </span>
            </div>
            <div className="hb-track">
              <div className="hb-fill" style={{ width: w + '%', background: it.color }} />
            </div>
            <div className="hb-foot">
              {it.sub && <span className="hb-sub">{it.sub}</span>}
              <span className="hb-meta">
                <CertPill cert={it.cert} />
                {gtPct && <span className="hb-gt">{fPct(gtPct(it.mm))} del gasto total</span>}
                <span className="hb-src">Fuente: {it.fuente}</span>
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Barra única segmentada (apilada al 100%): para el resumen público / privado.
export function StackedBar({
  segs,
  unidad = 'millones de pesos',
}: {
  segs: { label: string; mm: number; pct: number; color: string }[]
  unidad?: string
}) {
  const tot = segs.reduce((a, s) => a + s.mm, 0)
  return (
    <div className="hb-stack-wrap">
      <div className="hb-stack">
        {segs.map(s => (
          <div key={s.label} className="hb-seg" style={{ width: s.pct + '%', background: s.color }} title={`${s.label}: ${fPct(s.pct)}`}>
            {s.pct >= 12 ? fPct(s.pct) : ''}
          </div>
        ))}
      </div>
      <div className="hb-legend">
        {segs.map(s => (
          <span key={s.label} className="hb-leg-item">
            <span className="hb-dot" style={{ background: s.color }} />
            {s.label} <b>{fPct(s.pct)}</b> <span className="note">({fInt(s.mm)} {unidad})</span>
          </span>
        ))}
      </div>
      <p className="note hb-stack-tot">Suma: {fInt(tot)} {unidad} = 100%.</p>
    </div>
  )
}

// Estilos propios (prefijo hb-). No tocan clases compartidas.
export const HIER_BAR_CSS = `
.hb-list{display:flex;flex-direction:column;gap:14px;margin:12px 0}
.hb-row{display:flex;flex-direction:column;gap:5px}
.hb-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.hb-label{font-size:14px;font-weight:700;color:var(--ep)}
.hb-vals{display:flex;align-items:baseline;gap:10px;white-space:nowrap}
.hb-pct{font-size:16px;color:var(--ep);font-variant-numeric:tabular-nums}
.hb-mm{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.hb-track{height:16px;background:#eef2f7;border-radius:5px;overflow:hidden}
.hb-fill{height:100%;border-radius:5px;transition:width .3s ease}
.hb-foot{display:flex;flex-direction:column;gap:3px}
.hb-sub{font-size:12px;color:#475467;line-height:1.45}
.hb-meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:11px;color:var(--muted)}
.hb-cert{display:inline-block;border-radius:5px;padding:0 6px;font-size:10px;font-weight:700;letter-spacing:.2px}
.hb-cert-real{background:#eef2f7;color:#475467}
.hb-cert-est{background:var(--amber);color:var(--amber-ink)}
.hb-gt{background:#eaf2fb;color:var(--ep);border-radius:5px;padding:0 6px;font-weight:600}
.hb-src{font-style:italic}
.hb-stack-wrap{margin:10px 0 4px}
.hb-stack{display:flex;height:30px;border-radius:7px;overflow:hidden;border:1px solid var(--bd)}
.hb-seg{display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700;min-width:0;overflow:hidden}
.hb-legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:9px}
.hb-leg-item{font-size:12.5px;color:#344054}
.hb-dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
.hb-stack-tot{margin:6px 0 0}
`
