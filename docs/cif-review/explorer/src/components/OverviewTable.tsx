import { cell, fmt, pct, labelHC } from '../data'
import CodeRef from './CodeRef'

// Tabla-resumen del intro: TODO el gasto en salud (funciones HC) × financiador
// (HF1/HF2/HF3), con medicamentos ambulatorios (HC.5.1) destacado y los márgenes, total de
// fila, total de columna y % de fila (sobre el CHE) y de columna (composición).
// Año base 2022 (canónico de la reconciliación SHA), USD PPA millones.
// Estándar de redacción: el encabezado LIDERA con la descripción en español
// (qué es cada cosa); el código SHA queda secundario y en el hover (CodeRef).
const Y = 2022
const HF = [
 { code: 'HF1', glos: 'HF.1', desc: 'Aporte fiscal + cotizaciones obligatorias', sub: 'impuestos + FONASA + 7% ISAPRE' },
 { code: 'HF2', glos: 'HF.2', desc: 'Voluntario y privado', sub: 'ISAPRE complementario + seguros privados + sin fines de lucro' },
 { code: 'HF3', glos: 'HF.3', desc: 'Bolsillo de los hogares', sub: 'copagos + compra directa del hogar' },
]
// funciones HC en orden de magnitud aproximado; HC51 va resaltada como sub-fila de HC5
const ROWS = ['HC1', 'HC2', 'HC4', 'HC5', 'HC51', 'HC6', 'HC7', 'HC3', 'HC0']

export default function OverviewTable() {
 const v = (hc: string, hf: string) => cell(hc, hf, Y, 'usd')
 const grand = cell('_T', '_T', Y, 'usd') ?? 0
 const colTot = (hf: string) => cell('_T', hf, Y, 'usd') ?? 0

 return (
 <div className="chartbox" style={{ marginTop: 14, overflow: 'auto' }}>
 <table>
 <thead>
 <tr>
 <th style={{ textAlign: 'left', minWidth: 220 }}>Función de salud (qué se compra)</th>
 {HF.map(h => (
 <th key={h.code}>
 <CodeRef c={h.glos}>{h.desc}</CodeRef>
 <br /><span className="note" style={{ fontWeight: 400 }}>{h.sub}</span>
 </th>
 ))}
 <th className="tot">TOTAL gasto en salud</th>
 <th className="tot">% del gasto en salud</th>
 </tr>
 </thead>
 <tbody>
 {ROWS.map(hc => {
 const rt = cell(hc, '_T', Y, 'usd')
 if (rt == null) return null
 const isMed = hc === 'HC51'
 return (
 <tr key={hc} className={isMed ? 'row-meds' : ''}>
 <td style={{ textAlign: 'left', paddingLeft: isMed ? 26 : 8, fontWeight: isMed ? 700 : 500, borderLeft: isMed ? '2px solid #92400e' : undefined }}>
 {isMed && <span className="note" style={{ fontWeight: 400 }}>↳ de la cual </span>}
 {isMed
 ? <CodeRef c="HC.5.1"><b>{labelHC(hc)}</b></CodeRef>
 : <><b>{labelHC(hc)}</b> <span className="note" style={{ fontWeight: 400 }}>({hc.replace('HC51', 'HC5.1')})</span></>}
 </td>
 {HF.map(h => (
 <td key={h.code} className={'num' + (isMed && h.code === 'HF3' ? ' hf3' : '')}>{fmt(v(hc, h.code), 'usd')}</td>
 ))}
 <td className="num tot">{fmt(rt, 'usd')}</td>
 <td className="num pct">{grand ? pct(100 * rt / grand) : '·'}</td>
 </tr>
 )
 })}
 <tr className="tot">
 <td style={{ textAlign: 'left' }}>TOTAL <CodeRef c="CHE">gasto en salud</CodeRef></td>
 {HF.map(h => (
 <td key={h.code} className="num">
 {fmt(colTot(h.code), 'usd')}<br />
 <span className="note" style={{ fontWeight: 400 }}>{grand ? pct(100 * colTot(h.code) / grand) : '·'}</span>
 </td>
 ))}
 <td className="num">{fmt(grand, 'usd')}</td>
 <td className="num">100,0%</td>
 </tr>
 </tbody>
 </table>
 <p className="note" style={{ marginTop: 6 }}>
 Esta tabla muestra todo el <CodeRef c="CHE">gasto corriente en salud</CodeRef> de Chile, en USD PPA
 millones del año 2022. Cada fila dice <b>qué se compra</b> (la función); cada columna,
 <b> quién lo paga</b> (el financiador).
 </p>
 <p className="note" style={{ marginTop: 2 }}>
 La fila resaltada son los <b><CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef></b>: los que el hogar
 retira en la farmacia, el consultorio o el hospital, ya sean recetados o de venta libre. Pesan el
 {' '}{grand ? pct(100 * (cell('HC51', '_T', Y, 'usd') ?? 0) / grand) : '·'} del gasto en salud. Y de ese
 monto, el <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> pone cerca del 71%.
 </p>
 <p className="note" style={{ marginTop: 2 }}>
 Los márgenes resumen el cuadro. La última fila reparte cada función entre sus financiadores: cuánto pone el
 dinero <CodeRef c="HF.1">público y obligatorio</CodeRef> (impuestos, cotizaciones FONASA y el 7% de ISAPRE),
 cuánto el <CodeRef c="HF.2">voluntario y privado</CodeRef> y cuánto el <CodeRef c="HF.3">bolsillo</CodeRef>.
 La última columna mide el <b>peso de cada función</b> sobre el total de salud.
 </p>
 <p className="note" style={{ marginTop: 2 }}>
 Puedes explorar el detalle celda a celda, con subesquemas, otras unidades y otros años, en la
 {' '}<a href="#explorador">sección 5 · Explorador</a>. Fuente: OECD SHA (DSD_SHA@DF_SHA), verificado vs SDMX.
 </p>
 <p className="note" style={{ marginTop: 6 }}>
 <b>Una aclaración sobre los denominadores.</b> El <b>≈71%</b> compara el
 {' '}<CodeRef c="HF.3">bolsillo de los hogares</CodeRef> contra los
 {' '}<CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> de todos los canales: es la celda directa de SHA.
 </p>
 <p className="note" style={{ marginTop: 2 }}>
 El <b>62%</b> que suele circular en el debate es otra cosa. Mide el bolsillo contra el
 {' '}<CodeRef c="HC.RI.1">gasto farmacéutico total</CodeRef>, que además suma el fármaco administrado durante
 una hospitalización (ese va embebido en la <CodeRef c="HC.1">atención hospitalaria</CodeRef>). Esa cifra es
 de perímetro más amplio: su componente intrahospitalario no se lee directo de SHA (HC.RI.1 figura como
 no disponible), sino que se <b>deriva</b> por identidad contable (ver el capítulo del medicamento).
 En resumen: son denominadores distintos, y por eso dan números distintos.
 </p>
 </div>
 )
}
