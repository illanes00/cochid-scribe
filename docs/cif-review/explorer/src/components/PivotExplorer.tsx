import { useMemo, useState } from 'react'
import { cube, cell, HC_TREE, HF_TREE, UNITS, YEARS, Unit, TreeNode, fmt, pct, Preset, PRESETS, labelHC, labelHF } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

type Dim = 'HC' | 'HF'
const TREES: Record<Dim, TreeNode[]> = { HC: HC_TREE, HF: HF_TREE }

// padre de cada nodo nivel-1 = último nivel-0 previo
function parents(tree: TreeNode[]): Record<string, string | null> {
 const p: Record<string, string | null> = {}; let last = ''
 for (const n of tree) { if (n.level === 0) { last = n.code; p[n.code] = null } else p[n.code] = last }
 return p
}
function visibleNodes(tree: TreeNode[], expanded: Set<string>): TreeNode[] {
 const par = parents(tree)
 return tree.filter(n => n.level === 0 || expanded.has(par[n.code] ?? ''))
}

type Mode = 'val' | 'rowpct' | 'colpct'

export default function PivotExplorer() {
 const [rowDim, setRowDim] = useState<Dim>('HC')
 const [unit, setUnit] = useState<Unit>('pib')
 const [year, setYear] = useState<number>(2022)
 const [mode, setMode] = useState<Mode>('val')
 const [expHC, setExpHC] = useState<Set<string>>(new Set(['HC5']))
 const [expHF, setExpHF] = useState<Set<string>>(new Set(['HF1', 'HF2', 'HF3']))
 const [focus, setFocus] = useState<{ hc?: string; hf?: string }>({ hc: 'HC51', hf: 'HF3' })

 const colDim: Dim = rowDim === 'HC' ? 'HF' : 'HC'
 const expanded = (d: Dim) => (d === 'HC' ? expHC : expHF)
 const setExpanded = (d: Dim) => (d === 'HC' ? setExpHC : setExpHF)
 const toggle = (d: Dim, code: string) => {
 const s = new Set(expanded(d)); s.has(code) ? s.delete(code) : s.add(code); setExpanded(d)(s)
 }
 const rows = useMemo(() => visibleNodes(TREES[rowDim], expanded(rowDim)), [rowDim, expHC, expHF])
 const cols = useMemo(() => visibleNodes(TREES[colDim], expanded(colDim)).filter(c => c.code !== '_T'), [colDim, expHC, expHF])
 const par = parents(TREES[rowDim])
 const hasChildren = (d: Dim, code: string) => TREES[d].some(n => parents(TREES[d])[n.code] === code)

 const get = (r: string, c: string) => rowDim === 'HC' ? cell(r, c, year, unit) : cell(c, r, year, unit)
 // marginales: total de fila = celda × _T; total de columna = _T × celda; gran total = _T×_T
 const grand = get('_T', '_T')
 // texto de una celda según el modo (valor absoluto / % de su fila / % de su columna)
 const disp = (r: string, c: string): string => {
 const v = get(r, c)
 if (v == null) return '·'
 if (mode === 'val') return fmt(v, unit)
 const t = mode === 'rowpct' ? get(r, '_T') : get('_T', c)
 return t ? pct((100 * v) / t) : '·'
 }
 // texto de la columna TOTAL (margen derecho) para la fila r
 const dispRowTot = (r: string): string => {
 const rt = get(r, '_T')
 if (rt == null) return '·'
 if (mode === 'val') return fmt(rt, unit)
 if (mode === 'rowpct') return '100,0%'
 return grand ? pct((100 * rt) / grand) : '·' // colpct: share del gran total
 }

 const applyPreset = (p: Preset) => {
 setRowDim(p.rowDim); setUnit(p.unit); setYear(p.year)
 setFocus({ hc: p.focusHC, hf: p.focusHF })
 if (p.focusHF && ['HF11', 'HF121', 'HF122', 'HF21', 'HF22', 'HF31', 'HF32'].includes(p.focusHF)) { /* ya expandido */ }
 setExpHF(new Set(['HF1', 'HF2', 'HF3'])); if (p.focusHC === 'HC5' || p.focusHC === 'HC51') setExpHC(new Set(['HC5']))
 }

 const isFocus = (r: string, c: string) => {
 const hc = rowDim === 'HC' ? r : c, hf = rowDim === 'HC' ? c : r
 return focus.hc === hc && focus.hf === hf
 }
 const filterStr = focus.hc && focus.hf
 ? `Gasto en ${labelHC(focus.hc)} pagado por ${labelHF(focus.hf)} · ${year} · ${UNITS.find(u => u.key === unit)?.label} · Fuente: OECD SHA (códigos OECD ${focus.hc} × ${focus.hf})`
 : 'Selecciona una celda para leer en lenguaje claro qué representa ese cruce'

 return (
 <section id="explorador">
 <h2 className="ptitle">El explorador del dataset: en qué se gasta (función) × quién lo paga (financiamiento)</h2>
 <p className="note">Cada celda cruza una <b>función</b> de salud, en qué se gasta, con un <b>financiador</b>, quién pone la plata. Elige qué dimensión va en filas, la unidad, el año y si mostrar <b>monto</b>, <b>composición por financiador (% de fila)</b> o <b>composición por función (% de columna)</b>; expande los subesquemas: el <CodeRef c="HF.1">gasto público y obligatorio</CodeRef> se abre en <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> y <CodeRef c="HF.1.2.2">el 7% obligatorio de ISAPRE</CodeRef>, y los <CodeRef c="HC.5">bienes médicos</CodeRef> se abren en <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> y aparatos terapéuticos. La columna <b>TOTAL</b> (derecha) y la fila <b>total</b> (abajo) son los márgenes: viendo composición por financiador cada fila suma 100%, viendo composición por función cada columna suma 100%. Los presets «nuestros datos» te llevan al filtro exacto que produce cada cifra del informe; al clickear una celda ves en lenguaje claro qué cruce representa y sus dos denominadores.</p>
 <div className="grid2" style={{ gridTemplateColumns: 'minmax(0,1fr) 280px', alignItems: 'start' }}>
 <div style={{ minWidth: 0 }}>
 <Caption ch={4} n={1} kind="tabla" title="Tabla dinámica función × financiamiento del gasto en salud (cubo SHA)" />
 <div className="tablewrap" style={{ maxHeight: '74vh', overflowY: 'auto' }}>
 <table>
 <thead>
 <tr>
 <th style={{ minWidth: 220 }}>{rowDim === 'HC' ? 'En qué se gasta (función)' : 'Quién paga (financiamiento)'}<span style={{ opacity: .5, margin: '0 6px' }}>×</span>{colDim === 'HC' ? 'En qué se gasta' : 'Quién paga'}</th>
 {cols.map(c => (
 <th key={c.code} style={c.level === 1 ? { fontWeight: 400, opacity: .9 } : {}}>
 {hasChildren(colDim, c.code) && (
 <span className="expander" onClick={() => toggle(colDim, c.code)}>{expanded(colDim).has(c.code) ? '▾' : '▸'} </span>
 )}{c.code}
 </th>
 ))}
 <th className="tot" title="Total de la fila: suma de todos los financiadores para esa función">TOTAL</th>
 </tr>
 </thead>
 <tbody>
 {rows.map(r => {
 const meds = r.code === 'HC51' || r.code === 'HF3'
 const cls = r.code === '_T' ? 'tot' : (r.code === 'HC51' ? 'row-meds' : (r.level === 1 ? 'row-l1' : ''))
 return (
 <tr key={r.code} className={cls}>
 <td title={r.es}>
 {hasChildren(rowDim, r.code) && (
 <span className="expander" onClick={() => toggle(rowDim, r.code)}>{expanded(rowDim).has(r.code) ? '▾' : '▸'} </span>
 )}
 <b>{r.code}</b> · {r.es}
 </td>
 {cols.map(c => {
 const f = isFocus(r.code, c.code)
 return (
 <td key={c.code} className={'num' + (f ? ' focus' : '') + (((rowDim === 'HC' ? c.code : r.code) === 'HF3') ? ' hf3' : '')}
 onClick={() => setFocus(rowDim === 'HC' ? { hc: r.code, hf: c.code } : { hc: c.code, hf: r.code })}
 style={{ cursor: 'pointer' }}>
 {disp(r.code, c.code)}
 </td>
 )
 })}
 <td className="num tot">{dispRowTot(r.code)}</td>
 </tr>
 )
 })}
 </tbody>
 </table>
 </div>
 </div>

 <div className="filterbox">
 <label>Filas</label>
 <select value={rowDim} onChange={e => setRowDim(e.target.value as Dim)}>
 <option value="HC">En qué se gasta (función) en filas</option>
 <option value="HF">Quién paga (financiamiento) en filas</option>
 </select>
 <label>Unidad</label>
 <select value={unit} onChange={e => setUnit(e.target.value as Unit)}>{UNITS.map(u => <option key={u.key} value={u.key}>{u.label}</option>)}</select>
 <label>Año</label>
 <select value={year} onChange={e => setYear(+e.target.value)}>{YEARS.map(y => <option key={y} value={y}>{y}</option>)}</select>
 <label>Mostrar</label>
 <select value={mode} onChange={e => setMode(e.target.value as Mode)}>
 <option value="val">Monto ({UNITS.find(u => u.key === unit)?.short})</option>
 <option value="rowpct">Composición por financiador (% de la fila)</option>
 <option value="colpct">Composición por función (% de la columna)</option>
 </select>
 <div className="note" style={{ marginTop: 4 }}>
 {mode === 'val' ? 'Cada celda = monto gastado; la columna TOTAL suma toda la fila.'
 : mode === 'rowpct' ? 'Cada celda = qué fracción de esa función pone cada financiador (cada fila suma 100% → TOTAL).'
 : 'Cada celda = qué fracción de lo que paga ese financiador va a cada función (cada columna suma 100%; la fila total es el agregado).'}
 </div>

 <div className="lbl" style={{ marginTop: 14, fontSize: 11, textTransform: 'uppercase', letterSpacing: '.5px', color: '#98a2b3' }}>Presets, «nuestros datos»</div>
 {PRESETS.map(p => <button key={p.id} className="preset" onClick={() => applyPreset(p)}>{p.label}</button>)}

 <div className="card" style={{ marginTop: 12, fontSize: 12.5 }}>
 <div className="note">Celda seleccionada, qué representa:</div>
 <code>{filterStr}</code>
 {focus.hc && focus.hf && (
 <div style={{ marginTop: 6 }}>
 Valor: <b>{fmt(cell(focus.hc!, focus.hf!, year, unit), unit)}</b>
 {(() => {
 const v = cell(focus.hc!, focus.hf!, year, unit)
 const tFunc = cell(focus.hc!, '_T', year, unit) // total de la función (denominador de fila si HC en filas)
 const tFin = cell('_T', focus.hf!, year, unit) // total del financiador (denominador de columna)
 if (v == null) return null
 return (
 <div style={{ marginTop: 4 }} className="note">
 {focus.hc !== '_T' && tFunc ? <>· {pct(100 * v / tFunc)} de todo lo gastado en {labelHC(focus.hc!)} (denominador: {fmt(tFunc, unit)})<br /></> : null}
 {focus.hf !== '_T' && tFin ? <>· {pct(100 * v / tFin)} de todo lo que paga {labelHF(focus.hf!)} (denominador: {fmt(tFin, unit)})</> : null}
 </div>
 )
 })()}
 </div>
 )}
 </div>
 <a className="note" href="https://data-explorer.oecd.org/vis?df[id]=DSD_SHA@DF_SHA&df[ag]=OECD.ELS.HD" target="_blank" rel="noreferrer">Abrir en OECD Data Explorer ↗</a>
 </div>
 </div>
 <p className="note">Click en cualquier celda para leer en lenguaje claro qué cruce función × financiamiento representa. Click en ▸/▾ para expandir o colapsar subesquemas (por ejemplo abrir <CodeRef c="HC.5">bienes médicos</CodeRef> en <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> y aparatos). Fuente verificada contra el SDMX de la OECD; el total de cada margen coincide con la suma de sus subesquemas.</p>
 </section>
 )
}
