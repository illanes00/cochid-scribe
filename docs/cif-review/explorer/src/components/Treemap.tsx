import { useState, useMemo } from 'react'
import { HC51_2022, clp, pct, EP, RAINBOW } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// ── Treemap jerárquico del gasto en medicamentos ambulatorios (HC.5.1, 2022) ──
// Capas CONMUTABLES sobre el MISMO total (3.518.751 MM$): financiador, proveedor
// e intersección financiador × proveedor. El área de cada rectángulo es ∝ su monto.
// La vista "programa" es ilustrativa y NO aditiva (los instrumentos se solapan):
// se rotula explícitamente para no inducir doble conteo.

type Layer = 'financiador' | 'proveedor' | 'cruce' | 'programa'

interface Leaf { name: string; glos?: string; value: number; color: string; sub?: string }
interface Group { name: string; glos?: string; color: string; children: Leaf[] }

const A = HC51_2022

// Colores por dimensión (paleta institucional EP)
const FIN_COLOR: Record<string, string> = {
  'Obligatorio': EP.primary,
  'Voluntario': RAINBOW[2],
  'Bolsillo': EP.red,
}
const PROV_COLOR: Record<string, string> = {
  'Retail': RAINBOW[0],
  'Hospital': RAINBOW[6],
  'APS': RAINBOW[3],
}

// ── Datos por capa ────────────────────────────────────────────────────────────
function layerData(layer: Layer): Group[] {
  if (layer === 'financiador') {
    return [
      { name: 'Bolsillo', glos: 'HF.3', color: EP.red, children: [
        { name: 'Copago + compra directa', value: A.financiador[2].mm, color: EP.red, sub: 'sin reembolso de un tercero' },
      ] },
      { name: 'Obligatorio', glos: 'HF.1', color: EP.primary, children: [
        { name: 'FONASA (cotización)', glos: 'HF.1.2.1', value: A.publicoFino[1].mm, color: EP.primary, sub: 'seguro social' },
        { name: 'ISAPRE 7% obligatorio', glos: 'HF.1.2.2', value: A.publicoFino[2].mm, color: EP.accent, sub: 'cotización obligatoria' },
        { name: 'Aporte fiscal puro', glos: 'HF.1.1', value: A.publicoFino[0].mm, color: '#7aa4cf', sub: 'impuestos generales' },
      ] },
      { name: 'Voluntario', glos: 'HF.2', color: RAINBOW[2], children: [
        { name: 'ISAPRE complementario + seguros', value: A.financiador[1].mm, color: RAINBOW[2], sub: 'sobre el 7% + NPISH' },
      ] },
    ]
  }
  if (layer === 'proveedor') {
    return [
      { name: 'Retail', glos: 'HP.5', color: RAINBOW[0], children: [
        { name: 'Farmacia de venta al público', value: A.canal[0].mm, color: RAINBOW[0], sub: 'Cruz Verde, Salcobrand, Ahumada, populares' },
      ] },
      { name: 'Hospital', glos: 'HP.1', color: RAINBOW[6], children: [
        { name: 'Farmacia hospitalaria a externos', value: A.canal[1].mm, color: RAINBOW[6], sub: 'pacientes ambulatorios' },
      ] },
      { name: 'APS', glos: 'HP.3', color: RAINBOW[3], children: [
        { name: 'CESFAM y consultorios municipales', value: A.canal[2].mm, color: RAINBOW[3], sub: 'reportado vía SINIM' },
      ] },
    ]
  }
  if (layer === 'cruce') {
    // Intersección financiador × proveedor (estimada por marginales OCDE: el cruce
    // celda a celda NO lo publica la OCDE; reparto ilustrativo proporcional).
    const groups: Group[] = []
    for (const p of A.canal) {
      const pName = p.label
      const pColor = PROV_COLOR[pName] ?? '#888'
      const children: Leaf[] = A.financiador.map(f => ({
        name: f.label.replace(' de los hogares', '').replace(' / obligatorio', ''),
        glos: f.code,
        value: Math.round(p.mm * (f.mm / A.total_mm)),
        color: FIN_COLOR[f.label.replace(' de los hogares', '').replace(' / obligatorio', '')] ?? pColor,
        sub: `${pName} financiado por ${f.label}`,
      }))
      groups.push({ name: pName, glos: p.code, color: pColor, children })
    }
    return groups
  }
  // programa: descomposición ilustrativa NO aditiva (se solapan). Montos del gasto
  // PÚBLICO por instrumento (lado ejecución), no fracción del ambulatorio.
  return [
    { name: 'Farmacia de los Servicios de Salud', color: EP.primary, children: [
      { name: 'Farmacia SS (contiene GES público y DAC)', value: 736_761, color: EP.primary, sub: 'línea 22.04.004.001, 2023 · base del gasto' },
    ] },
    { name: 'APS municipal', color: RAINBOW[3], children: [
      { name: 'Gasto comunal en farmacia (incluye FOFAR)', value: 162_613, color: RAINBOW[3], sub: 'SINIM, 2023' },
    ] },
    { name: 'Ley Ricarte Soto', glos: 'LRS', color: RAINBOW[2], children: [
      { name: 'Fondo de alto costo (aditivo)', value: 175_672, color: RAINBOW[2], sub: 'ejecución 2025' },
    ] },
    { name: 'Otros (aditivos)', color: RAINBOW[5], children: [
      { name: 'PNI (vacunas)', glos: 'PNI', value: 30_000, color: RAINBOW[5], sub: 'prevención, HC.6.2' },
      { name: 'FF.AA. y de Orden', value: 62_339, color: RAINBOW[7] ?? '#4B3B7C', sub: 'sanidad militar' },
      { name: 'Judicialización (glosa)', value: 32_679, color: RAINBOW[8] ?? '#764494', sub: 'subt 26.02 público, 2023' },
    ] },
  ]
}

// ── Squarified-ish treemap (algoritmo de slice-and-dice por filas) ────────────
interface Rect { x: number; y: number; w: number; h: number }
function sliceDice(items: number[], rect: Rect, horizontal: boolean): Rect[] {
  const total = items.reduce((a, b) => a + b, 0) || 1
  const out: Rect[] = []
  let off = horizontal ? rect.x : rect.y
  for (const v of items) {
    const frac = v / total
    if (horizontal) {
      const w = rect.w * frac
      out.push({ x: off, y: rect.y, w, h: rect.h }); off += w
    } else {
      const h = rect.h * frac
      out.push({ x: rect.x, y: off, w: rect.w, h }); off += h
    }
  }
  return out
}

const W = 920, H = 460, GAP = 3

export default function Treemap() {
  const [layer, setLayer] = useState<Layer>('financiador')
  const [hov, setHov] = useState<{ name: string; value: number; sub?: string } | null>(null)
  const groups = useMemo(() => layerData(layer), [layer])

  const grand = useMemo(
    () => groups.reduce((a, g) => a + g.children.reduce((s, c) => s + c.value, 0), 0),
    [groups]
  )

  // Nivel 1: columnas por grupo (ancho ∝ total del grupo). Nivel 2: filas dentro.
  const groupTotals = groups.map(g => g.children.reduce((s, c) => s + c.value, 0))
  const groupRects = sliceDice(groupTotals, { x: 0, y: 0, w: W, h: H }, true)

  const tiles: { rect: Rect; leaf: Leaf; gName: string }[] = []
  groups.forEach((g, gi) => {
    const gr = groupRects[gi]
    const inner: Rect = { x: gr.x + GAP, y: gr.y + GAP, w: Math.max(0, gr.w - 2 * GAP), h: Math.max(0, gr.h - 26) }
    const childRects = sliceDice(g.children.map(c => c.value), inner, false)
    g.children.forEach((c, ci) => tiles.push({ rect: childRects[ci], leaf: c, gName: g.name }))
  })

  const isProg = layer === 'programa'

  return (
    <section id="areas">
      <h2 className="ptitle">Áreas del gasto: treemap jerárquico</h2>
      <p className="psub">
        El área de cada rectángulo es proporcional al monto. Conmuta la capa para ver el mismo
        gasto en medicamentos ambulatorios (HC.5.1, 2022) ordenado por <b>quién lo paga</b>
        {' '}(financiador), por <b>dónde se entrega</b> (proveedor), por su <b>intersección</b>, o por
        {' '}<b>instrumento</b> (vista ilustrativa, no aditiva).
      </p>

      <div className="filterbox" style={{ display: 'inline-flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        <label style={{ margin: 0 }}>Capa</label>
        {([
          ['financiador', 'Financiador (quién paga)'],
          ['proveedor', 'Proveedor (dónde se entrega)'],
          ['cruce', 'Intersección financiador × proveedor'],
          ['programa', 'Instrumento (ilustrativo, no aditivo)'],
        ] as [Layer, string][]).map(([k, lbl]) => (
          <button
            key={k}
            className="preset"
            style={{ width: 'auto', margin: 0, background: layer === k ? EP.primary : undefined, color: layer === k ? '#fff' : undefined, borderColor: layer === k ? EP.primary : undefined }}
            onClick={() => { setLayer(k); setHov(null) }}
          >
            {lbl}
          </button>
        ))}
      </div>

      {isProg && (
        <div className="card warn" style={{ marginTop: 0 }}>
          <p style={{ margin: 0 }}>
            <b>Vista ilustrativa, no aditiva.</b> Estos instrumentos se solapan: el GES público y las
            Drogas de Alto Costo se devengan <b>dentro</b> de la Farmacia de los Servicios de Salud, y
            FONASA financia lo que esa farmacia ejecuta. Sumar los rectángulos duplicaría del orden de
            400.000 MM$. El gasto público disjunto se ubica en una banda de 0,42% a 0,46% del PIB
            {' '}(≈1,1 a 1,2 billones de pesos), no en la suma de las cajas.
          </p>
        </div>
      )}

      <Caption ch={3} n={2} kind="grafico"
        title={`Treemap del medicamento ambulatorio (HC.5.1, 2022) por ${layer === 'cruce' ? 'proveedor × financiador' : layer}`} />
      <div className="chartbox">
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }} role="img">
          {/* títulos de grupo */}
          {groups.map((g, gi) => {
            const gr = groupRects[gi]
            return (
              <text key={'g' + gi} x={gr.x + 6} y={gr.y + 16} fontSize={12.5} fontWeight={700} fill="#fff"
                style={{ paintOrder: 'stroke' }} stroke={g.color} strokeWidth={0} >
                {g.name}
              </text>
            )
          })}
          {tiles.map((t, i) => {
            const big = t.rect.w > 70 && t.rect.h > 30
            return (
              <g key={i}
                onMouseEnter={() => setHov({ name: `${t.gName} · ${t.leaf.name}`, value: t.leaf.value, sub: t.leaf.sub })}
                onMouseLeave={() => setHov(null)}>
                <rect x={t.rect.x} y={t.rect.y} width={Math.max(0, t.rect.w)} height={Math.max(0, t.rect.h)}
                  fill={t.leaf.color} stroke="#fff" strokeWidth={1.5}
                  opacity={hov && hov.name !== `${t.gName} · ${t.leaf.name}` ? 0.6 : 0.95} />
                {big && (
                  <>
                    <text x={t.rect.x + 7} y={t.rect.y + 18} fontSize={11.5} fontWeight={600} fill="#fff">
                      {t.leaf.name.length > 26 ? t.leaf.name.slice(0, 25) + '…' : t.leaf.name}
                    </text>
                    <text x={t.rect.x + 7} y={t.rect.y + 34} fontSize={11} fill="#fff" opacity={0.92}>
                      {pct((t.leaf.value / grand) * 100)} · {clp(t.leaf.value)} MM$
                    </text>
                  </>
                )}
              </g>
            )
          })}
        </svg>
        <div className="note" style={{ marginTop: 8, minHeight: 18 }}>
          {hov
            ? <><b>{hov.name}</b>: {clp(hov.value)} MM$ ({pct((hov.value / grand) * 100)} del total{hov.sub ? ` · ${hov.sub}` : ''})</>
            : <>Total del treemap: <b>{clp(grand)} MM$</b>{isProg ? ' (suma ilustrativa, no aditiva)' : ' = HC.5.1 ambulatorio 2022'}. Pasa el cursor sobre un rectángulo para ver su monto y su participación.</>}
        </div>
      </div>

      <p className="note">
        Las capas <b>financiador</b>, <b>proveedor</b> e <b>intersección</b> reparten el mismo total
        (3.518.751 MM$, HC.5.1 ambulatorio 2022, dato OCDE SHA). La intersección financiador × proveedor
        es ilustrativa: la OCDE entrega los marginales, no el cruce celda a celda, así que se reparte de
        forma proporcional. La capa <b>instrumento</b> mide el gasto público por programa y no se suma.
        Fuente: OECD SHA (DSD_SHA@DF_SHA) + DIPRES/SINIM para los instrumentos.
      </p>
    </section>
  )
}
