import { useState } from 'react'
import { comparability, CompCode } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// Las cuatro clasificaciones ICHA del SHA 2011 (ortogonales: el mismo sufijo
// numérico NO significa lo mismo entre familias).
const FAMILIES: { key: string; titulo: string; eje: string; cap: string; capTitle: string }[] = [
 { key: 'HC', titulo: 'ICHA-HC · Funciones', eje: '¿QUÉ se compra?', cap: 'SHA 2011, cap. 5', capTitle: 'Códigos de funciones de salud (ICHA-HC) y su estado de reporte en Chile' },
 { key: 'HP', titulo: 'ICHA-HP · Proveedores', eje: '¿DÓNDE / quién lo entrega?', cap: 'SHA 2011, cap. 6', capTitle: 'Códigos de proveedores de salud (ICHA-HP) y su estado de reporte en Chile' },
 { key: 'HF', titulo: 'ICHA-HF · Esquemas de financiamiento', eje: '¿QUIÉN paga?', cap: 'SHA 2011, cap. 7', capTitle: 'Códigos de esquemas de financiamiento (ICHA-HF) y su estado de reporte en Chile' },
 { key: 'FS', titulo: 'ICHA-FS · Fuentes de ingreso', eje: '¿de DÓNDE viene el recurso?', cap: 'SHA 2011, cap. 8', capTitle: 'Códigos de fuentes de ingreso (ICHA-FS) y su estado de reporte en Chile' },
]
const level = (code: string) => code.split('.').length - 1 // HC.1=0, HC.5.1=1, HC.5.1.1=2
const isMissing = (s: string) => /Missing/i.test(s)
const hasNote = (s: string) => !!s && s.replace(/[.\s…]/g, '').length > 2

function FamilyTable({ fam, codes, showMissing, capN, capTitle }: { fam: typeof FAMILIES[number]; codes: CompCode[]; showMissing: boolean; capN: number; capTitle: string }) {
 const [open, setOpen] = useState<CompCode | null>(null)
 const [collapsed, setCollapsed] = useState(false)
 const reported = codes.filter(c => !isMissing(c.status))
 const missing = codes.filter(c => isMissing(c.status))
 // árbol desplegable: padres (con hijos) se pueden colapsar
 const byCode = new Map(codes.map(c => [c.code, c]))
 // Sólo hay dropdown si existe al menos un hijo VISIBLE bajo el filtro actual:
 // si todas las subfunciones están ocultas (Missing con showMissing=false), no
 // tiene sentido mostrar el desplegable (bug HC.1.3).
 const hasKids = (code: string) => codes.some(c => c.code !== code && c.code.startsWith(code + '.') && (showMissing || !isMissing(c.status)))
 const parentOf = (code: string): string | null => {
 const parts = code.split('.')
 for (let i = parts.length - 1; i >= 1; i--) { const p = parts.slice(0, i).join('.'); if (byCode.has(p)) return p }
 return null
 }
 const [expanded, setExpanded] = useState<Set<string>>(() => new Set(codes.filter(c => hasKids(c.code)).map(c => c.code)))
 const toggleExp = (code: string) => setExpanded(s => { const n = new Set(s); n.has(code) ? n.delete(code) : n.add(code); return n })
 const ancestorsOpen = (code: string) => { let p = parentOf(code); while (p) { if (!expanded.has(p)) return false; p = parentOf(p) } return true }
 const shown = codes.filter(c => (showMissing || !isMissing(c.status)) && ancestorsOpen(c.code))
 return (
 <div className="chartbox" style={{ marginBottom: 14 }}>
 <div className="toggle-h" onClick={() => setCollapsed(c => !c)}>
 <span>{collapsed ? '▸' : '▾'}</span>
 <span>{fam.titulo}</span>
 <span className="pill">{fam.eje}</span>
 <span className="note" style={{ marginLeft: 'auto', fontWeight: 400 }}>
 {fam.cap} · {reported.length} reportados{missing.length ? ` · ${missing.length} no reportados` : ''}
 </span>
 </div>
 {!collapsed && (
 <>
 <Caption ch={1} n={capN} kind="tabla" title={capTitle} />
 <div className="tablewrap">
 <table style={{ marginTop: 8 }}>
 <colgroup>
 <col style={{ width: '26%' }} />
 <col style={{ width: '46%' }} />
 <col style={{ width: '16%' }} />
 <col style={{ width: '12%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Código (▸ desplegar)</th>
 <th style={{ textAlign: 'left' }}>Descripción</th>
 <th>Estado en Chile</th>
 <th></th>
 </tr>
 </thead>
 <tbody>
 {shown.map(c => {
 const lv = level(c.code)
 const kids = hasKids(c.code)
 return (
 <tr key={c.code}>
 <td style={{
 textAlign: 'left', paddingLeft: 8 + lv * 22,
 borderLeft: lv > 0 ? '2px solid #e6edf5' : undefined,
 fontWeight: lv === 0 ? 700 : 500, color: '#1a365d',
 fontSize: lv === 0 ? 13 : 12,
 }}>
 {kids
 ? <span className="expander" onClick={() => toggleExp(c.code)}>{expanded.has(c.code) ? '▾' : '▸'} </span>
 : <span style={{ display: 'inline-block', width: 14 }} />}
 {c.code}
 </td>
 <td style={{ textAlign: 'left', fontSize: lv === 0 ? 12.5 : 12, color: lv === 0 ? '#1d2939' : '#475467' }}>{c.desc}</td>
 <td style={{ textAlign: 'center' }}>
 {isMissing(c.status)
 ? <span className="badge miss">No reportado</span>
 : <span className="badge ok">Reportado</span>}
 </td>
 <td style={{ textAlign: 'center' }}>
 {hasNote(c.expl) && (
 <button className="link" onClick={() => setOpen(c)} title="Ver nota de comparabilidad">ⓘ nota</button>
 )}
 </td>
 </tr>
 )
 })}
 </tbody>
 </table>
 </div>
 </>
 )}
 {open && (
 <div className="modal-backdrop" onClick={() => setOpen(null)}>
 <div className="modal" onClick={e => e.stopPropagation()}>
 <button className="close" onClick={() => setOpen(null)}>×</button>
 <h3>{open.code} · {open.desc}</h3>
 <p className="note">
 {isMissing(open.status) ? <span className="badge miss">No reportado por Chile</span> : <span className="badge ok">Reportado</span>}
 </p>
 <p>{open.expl}</p>
 <p className="note" style={{ marginBottom: 0 }}>Fuente: nota oficial OECD «Sources and comparability, CHL» + JHAQ MINSAL/DEIS.</p>
 </div>
 </div>
 )}
 </div>
 )
}

export default function CodeTaxonomy() {
 const [showMissing, setShowMissing] = useState(false)
 return (
 <section id="codigos">
 <h2 className="ptitle">El sistema de códigos ICHA (HC · HP · HF · FS)</h2>
 <p className="psub">Cuatro clasificaciones ortogonales del SHA 2011. El mismo número significa cosas distintas en cada familia.</p>

 <div className="card warn">
 <b>«Farmacias» (<CodeRef c="HP.5.1" />) no es «medicamentos» (<CodeRef c="HC.5.1" />).</b> El sufijo
 numérico se reusa entre familias y no correlaciona:
 <ul style={{ margin: '8px 0' }}>
 <li><CodeRef c="HC.5.1"><b>Medicamentos</b></CodeRef> = el bien comprado (función, <i>qué</i> se compra)</li>
 <li><CodeRef c="HP.5.1"><b>Farmacias</b></CodeRef> = el establecimiento que dispensa (proveedor, <i>dónde</i> se compra)</li>
 <li><CodeRef c="HF.1.2.2"><b>Cotización obligatoria del 7% canalizada por ISAPRE</b></CodeRef> = quién financia (esquema, <i>quién</i> paga)</li>
 <li><b>Cotización del trabajador (la parte que pone la persona, código FS.3.1)</b> = el origen del recurso (fuente, <i>de dónde</i> sale)</li>
 </ul>
 Un <CodeRef c="HC.5.1">medicamento</CodeRef> puede dispensarse en una <CodeRef c="HP.5.1">farmacia</CodeRef>,
 en un <CodeRef c="HP.1">hospital</CodeRef> o en un consultorio de atención primaria (código HP.3.4);
 pagarse por el <CodeRef c="HF.1.2.1">esquema público obligatorio de FONASA</CodeRef> o de
 <CodeRef c="HF.3"> bolsillo de los hogares (copagos y compra directa)</CodeRef>; y ese esquema
 financiarse con <CodeRef c="FS.3">cotizaciones sociales obligatorias</CodeRef> o
 <CodeRef c="FS.1"> impuestos generales</CodeRef>. Las cuatro preguntas son independientes. Por eso una sola
 garantía como GES cruza dos esquemas de financiamiento a la vez, el
 <CodeRef c="HF.1.2.1"> tramo público obligatorio de FONASA</CodeRef> y la
 <CodeRef c="HF.1.2.2"> cotización obligatoria del 7% vía ISAPRE</CodeRef>, sin tener una categoría de
 financiamiento (HF) propia.
 </div>

 <p className="note">
 <b>ICHA-FS</b> (fuentes de ingreso) describe de dónde vienen los recursos de cada esquema de financiamiento
 , ya sean <CodeRef c="FS.1">impuestos generales del fisco</CodeRef> o
 <CodeRef c="FS.3"> cotizaciones sociales obligatorias</CodeRef>, : es la cuarta dimensión, distinta del gasto
 mismo (qué se compra × dónde se entrega × quién paga, es decir HC × HP × HF). Cada tabla se puede colapsar;
 «ⓘ nota» aparece solo cuando Chile registró una observación de comparabilidad para ese código.
 </p>

 <label className="chk" style={{ margin: '6px 0 12px' }}>
 <input type="checkbox" checked={showMissing} onChange={e => setShowMissing(e.target.checked)} />
 Mostrar también los códigos que Chile NO reporta (Missing)
 </label>

 {FAMILIES.map((fam, i) => (
 <FamilyTable
 key={fam.key}
 fam={fam}
 showMissing={showMissing}
 capN={i + 2}
 capTitle={fam.capTitle}
 codes={comparability.filter(c => c.code.split('.')[0] === fam.key)}
 />
 ))}
 </section>
 )
}
