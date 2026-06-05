import { useState } from 'react'
import { cell, hcxhp, hpxhf, HP_LABEL, labelHC, EP, RAINBOW } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// Mosaic / Marimekko: corte 2D del cubo SHA. Cada segmento lidera con su
// descripción en español; el código SHA (glosKey) va al hover vía CodeRef.
type Cut = 'HCxHF' | 'HCxHP' | 'HPxHF'


const HF_SEG = [
 { key: 'HF1', glosKey: 'HF.1', label: 'Público y obligatorio', color: EP.primary },
 { key: 'HF2', glosKey: 'HF.2', label: 'Voluntario', color: RAINBOW[2] },
 { key: 'HF3', glosKey: 'HF.3', label: 'Bolsillo de los hogares', color: EP.red },
]
const HP_SEG = [
 { key: 'HP5', glosKey: 'HP.5', label: 'Farmacias en convenio', color: RAINBOW[2] },
 { key: 'HP1', glosKey: 'HP.1', label: 'Hospitales', color: RAINBOW[6] },
 { key: 'HP3', glosKey: 'HP.3', label: 'Atención primaria (APS)', color: RAINBOW[3] },
]
const HC_COLS = ['HC1', 'HC4', 'HC51', 'HC52', 'HC6', 'HC7', 'HC2', 'HC3']
const HP_COLS = ['HP1', 'HP3', 'HP5', 'HP6', 'HP7']

interface Spec { cols: string[]; colLabel: (c: string) => string; segs: { key: string; glosKey?: string; label: string; color: string }[]; val: (c: string, s: string) => number | null }

function spec(cut: Cut): Spec {
 if (cut === 'HCxHF') return {
 cols: HC_COLS, colLabel: c => `${c} ${labelHC(c).split(' (')[0]}`, segs: HF_SEG,
 val: (c, s) => cell(c, s, 2022, 'usd'),
 }
 if (cut === 'HCxHP') return {
 cols: HC_COLS.filter(c => hcxhp[c]), colLabel: c => `${c} ${labelHC(c).split(' (')[0]}`, segs: HP_SEG,
 val: (c, s) => hcxhp[c]?.[s] ?? null,
 }
 return {
 cols: HP_COLS.filter(c => hpxhf[c]), colLabel: c => `${c} ${(HP_LABEL[c] || c).split(' ')[0]}`, segs: HF_SEG,
 val: (c, s) => hpxhf[c]?.[s] ?? null,
 }
}

const fInt = (v: number) => v.toLocaleString('es-CL', { maximumFractionDigits: 0 })
const FUENTE = 'Fuente: OECD SHA, USD PPA corrientes 2022 (OBS_STATUS=D, definición difiere).'

export default function MosaicCube() {
 const [cut, setCut] = useState<Cut>('HCxHF')
 const [hov, setHov] = useState<{ c: string; s: string; v: number } | null>(null)
 const sp = spec(cut)

 // totales por columna (suma de segmentos) y gran total
 const colTot: Record<string, number> = {}
 sp.cols.forEach(c => { colTot[c] = sp.segs.reduce((a, s) => a + (sp.val(c, s.key) ?? 0), 0) })
 const cols = sp.cols.filter(c => colTot[c] > 0).sort((a, b) => colTot[b] - colTot[a])
 const grand = cols.reduce((a, c) => a + colTot[c], 0)

 const W = 900, H = 380, padB = 46, padT = 8, padR = 4, gap = 3
 const plotW = W - padR, plotH = H - padB - padT
 let x = 0
 const rects: { c: string; s: string; v: number; x: number; y: number; w: number; h: number; color: string }[] = []
 const colMeta: { c: string; x: number; w: number; tot: number }[] = []
 cols.forEach(c => {
 const w = (colTot[c] / grand) * (plotW - gap * (cols.length - 1))
 colMeta.push({ c, x, w, tot: colTot[c] })
 let y = padT
 sp.segs.forEach(s => {
 const v = sp.val(c, s.key) ?? 0
 const h = (v / colTot[c]) * plotH
 if (v > 0) rects.push({ c, s: s.key, v, x, y, w, h, color: s.color })
 y += h
 })
 x += w + gap
 })

 return (
 <section id="mosaico">
 <h2 className="ptitle">Descomposición visual: cortes del cubo SHA</h2>
 <p className="psub">
 Mosaico (Marimekko): el <b>ancho</b> de cada columna ∝ el total de la categoría, el
 <b> alto</b> de cada bloque ∝ su participación y el <b>área</b> ∝ el monto. Elige qué dos
 dimensiones del cubo SHA cruzar.
 </p>

 <div className="filterbox" style={{ display: 'inline-flex', gap: 14, alignItems: 'center', marginBottom: 10 }}>
 <label style={{ margin: 0 }}>Corte del cubo</label>
 <select value={cut} onChange={e => { setCut(e.target.value as Cut); setHov(null) }} style={{ width: 'auto' }}>
 <option value="HCxHF">Tipo de prestación × quién la financia, quién paga qué</option>
 <option value="HCxHP">Tipo de prestación × dónde se entrega, proveedor de cada servicio</option>
 <option value="HPxHF">Dónde se entrega × quién la financia, quién le paga a quién</option>
 </select>
 </div>

 <Caption ch={4} n={1} kind="grafico" title="Mosaico Marimekko: descomposición del cubo SHA por cortes de dos dimensiones" />
 <div className="chartbox">
 <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block', maxWidth: '100%' }} role="img">
 {rects.map((r, i) => {
 const isMed = r.c === 'HC51'
 const isBol = r.s === 'HF3'
 return (
 <g key={i}
 onMouseEnter={() => setHov({ c: r.c, s: r.s, v: r.v })}
 onMouseLeave={() => setHov(null)}>
 <rect x={r.x} y={r.y} width={r.w} height={r.h} fill={r.color}
 stroke={isMed ? '#92400e' : '#fff'} strokeWidth={isMed ? 2 : 1}
 opacity={hov && (hov.c !== r.c || hov.s !== r.s) ? 0.55 : (isBol ? 1 : 0.92)} />
 {r.w > 46 && r.h > 22 && (
 <text x={r.x + r.w / 2} y={r.y + r.h / 2 + 4} textAnchor="middle"
 fontSize={11} fill={r.s === 'HF3' || r.color === EP.primary ? '#fff' : '#1d2939'} fontWeight={600}>
 {Math.round((r.v / colTot[r.c]) * 100)}%
 </text>
 )}
 </g>
 )
 })}
 {colMeta.map((m, i) => (
 <text key={i} x={m.x + m.w / 2} y={H - padB + 16} textAnchor="middle" fontSize={10.5}
 fill="#475467" fontWeight={m.c === 'HC51' ? 700 : 400} transform={m.w < 60 ? `rotate(-25 ${m.x + m.w / 2} ${H - padB + 16})` : undefined}>
 {sp.colLabel(m.c).length > 16 && m.w < 90 ? m.c : sp.colLabel(m.c)}
 </text>
 ))}
 {colMeta.map((m, i) => (
 <text key={'t' + i} x={m.x + m.w / 2} y={H - padB + 30} textAnchor="middle" fontSize={9.5} fill="#98a2b3">
 {fInt(m.tot)}
 </text>
 ))}
 </svg>

 {/* leyenda + tooltip */}
 <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center', marginTop: 8 }}>
 {sp.segs.map(s => (
 <span key={s.key} className="note" style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
 <span style={{ width: 11, height: 11, background: s.color, borderRadius: 2, display: 'inline-block' }} />
 {s.glosKey ? <CodeRef c={s.glosKey}>{s.label}</CodeRef> : s.label}
 </span>
 ))}
 <span className="note" style={{ marginLeft: 'auto' }}>
 {hov
 ? <>{hov.c} × {hov.s}: <b>{fInt(hov.v)}</b> millones de USD PPA · {Math.round((hov.v / colTot[hov.c]) * 100)}% de esa columna</>
 : <>Pasa el cursor sobre un bloque · cifras en millones de USD PPA (2022) · <span style={{ color: EP.amberInk }}>la franja con borde ámbar son los <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef></span></>}
 </span>
 </div>
 </div>
 {cut === 'HCxHF' && (
 <>
 <p className="note">
 La columna más ancha es la <CodeRef c="HC.1">atención curativa</CodeRef> (24.438):
 consultas, procedimientos y fármacos administrados en hospitalización. La franja con borde
 ámbar son los <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (7.815,6), el 13,4%
 del <CodeRef c="CHE">gasto total en salud</CodeRef>. Lo clave es quién paga: el{' '}
 <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> (copagos y compra directa, en rojo)
 cubre el 71% de esa columna; lo <CodeRef c="HF.1">público y obligatorio</CodeRef>, aporte
 fiscal, cotizaciones FONASA y el 7% obligatorio de ISAPRE, apenas el 26%; y lo{' '}
 <CodeRef c="HF.2">voluntario</CodeRef> (ISAPRE complementario y seguros privados), el 3%.
 </p>
 <p className="note">
 Ojo con el denominador: ~23% del gasto queda{' '}
 <CodeRef c="HC.0">sin clasificar por función</CodeRef>. Sobre el gasto sí clasificado, el
 peso de los medicamentos ambulatorios sube de 13,4% a ~17,4%. {FUENTE}
 </p>
 </>
 )}
 {cut === 'HCxHP' && (
 <p className="note">
 Los <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (7.815,6), según dónde se
 entregan: <CodeRef c="HP.5">farmacias de venta al público</CodeRef> 54,5%,{' '}
 <CodeRef c="HP.1">hospitales</CodeRef> 30,6% y <CodeRef c="HP.3">atención primaria (APS)</CodeRef>{' '}
 14,9%. La provisión es mixta: no es solo retail de farmacia, una parte importante se
 dispensa en hospitales y en la red de APS. {FUENTE}
 </p>
 )}
 {cut === 'HPxHF' && (
 <p className="note">
 Las <CodeRef c="HP.5">farmacias de venta al público</CodeRef> (4.502) y quién las financia:
 el <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> pone 3.949 (88%) y lo{' '}
 <CodeRef c="HF.1">público y obligatorio</CodeRef>, vía FONASA y CENABAST, los 552 restantes
 (12%). Quien financia no siempre es quien provee: aquí un financiador público termina
 pagándole a un proveedor privado. {FUENTE}
 </p>
 )}
 </section>
 )
}
