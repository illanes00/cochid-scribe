import { PieChart, Pie, Cell as PieCell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { clp, pct, EP, RAINBOW, HC51_2022, HOSP_BANDA, CNEP_2024 } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// ── Colores por dimensión ──────────────────────────────────────────────────
const CANAL_COLORS = [RAINBOW[0], RAINBOW[4], RAINBOW[2]] // retail · hospital · APS
const FIN_COLORS = [RAINBOW[5], RAINBOW[2], EP.red] // público · voluntario · bolsillo

// ── Sub-componente: tabla de magnitudes en CLP MM$ ──────────────────────────
interface BreakRow { code: string; label: string; sub: string; mm: number; pctv: number; salud?: number }

function MoneyTable({
 rows,
 total,
 totalLabel,
 capN,
 capTitle,
 headFirst,
 highlightCode,
 showSalud,
}: {
 rows: readonly BreakRow[]
 total: number
 totalLabel: string
 capN: number
 capTitle: string
 headFirst: string
 highlightCode?: string
 showSalud?: boolean
}) {
 return (
 <>
 <Caption ch={3} n={capN} kind="tabla" title={capTitle} />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: showSalud ? '46%' : '58%' }} />
 <col style={{ width: showSalud ? '24%' : '26%' }} />
 <col style={{ width: '16%' }} />
 {showSalud && <col style={{ width: '14%' }} />}
 </colgroup>
 <thead>
 <tr>
 <th>{headFirst}</th>
 <th>MM$ CLP (2022)</th>
 <th>% de HC.5.1</th>
 {showSalud && <th>% gasto salud</th>}
 </tr>
 </thead>
 <tbody>
 {rows.map(r => {
 const hl = r.code === highlightCode
 return (
 <tr key={r.code} className={hl ? 'row-meds' : undefined}>
 <td>
 <CodeRef c={r.code}>{r.label}</CodeRef>{' '}
 <span className="note">· {r.sub}</span>
 </td>
 <td className="num">{clp(r.mm)}</td>
 <td className={hl ? 'pct' : 'num'}>{pct(r.pctv)}</td>
 {showSalud && <td className="num">{r.salud != null ? pct(r.salud) : '·'}</td>}
 </tr>
 )
 })}
 <tr className="tot">
 <td>{totalLabel}</td>
 <td className="num">{clp(total)}</td>
 <td className="num">100,0%</td>
 {showSalud && <td className="num">13,4%</td>}
 </tr>
 </tbody>
 </table>
 </div>
 </>
 )
}

// ── Sub-componente: torta de participación ──────────────────────────────────
function PieCard({
 rows,
 colors,
 capN,
 capTitle,
 foot,
}: {
 rows: readonly BreakRow[]
 colors: string[]
 capN: number
 capTitle: string
 foot: string
}) {
 const data = rows.map((r, i) => ({ name: r.label, value: r.mm, color: colors[i] }))
 return (
 <div className="chartbox" style={{ margin: '8px 0', maxWidth: '100%' }}>
 <Caption ch={3} n={capN} kind="grafico" title={capTitle} />
 <ResponsiveContainer width="100%" height={240}>
 <PieChart>
 <Pie
 data={data}
 dataKey="value"
 nameKey="name"
 cx="50%"
 cy="50%"
 outerRadius={72}
 innerRadius={34}
 paddingAngle={1}
 labelLine={false}
 label={(e: { value: number }) => pct((e.value / HC51_2022.total_mm) * 100)}
 >
 {data.map((d, i) => <PieCell key={i} fill={d.color} />)}
 </Pie>
 <Tooltip
 wrapperStyle={{ zIndex: 20, maxWidth: 240 }}
 formatter={(v: number) => [clp(v) + ' MM$ CLP', '']}
 />
 <Legend wrapperStyle={{ fontSize: 11 }} />
 </PieChart>
 </ResponsiveContainer>
 <div className="note" style={{ textAlign: 'center' }}>{foot}</div>
 </div>
 )
}

// ── Programas de cobertura: qué captura HC.5.1 de cada uno ───────────────────
interface ProgRow { prog: string; tipo: 'línea' | 'etiqueta'; mapa: string; capturado: 'sí' | 'parcial' | 'no'; nota: string }
const PROGRAMAS: ProgRow[] = [
 { prog: 'GES', tipo: 'etiqueta', mapa: 'HC.5.1 (ambulatorio) + HC.1 (EV)', capturado: 'parcial', nota: 'GES-ambulatorio sí entra en HC.5.1; GES-intrahospitalario cae en HC.1.' },
 { prog: 'FOFAR', tipo: 'etiqueta', mapa: 'HC.5.1 · canal APS', capturado: 'sí', nota: 'Crónicos en APS; reportado vía SINIM. Está entero dentro de HC.5.1.' },
 { prog: 'DAC', tipo: 'etiqueta', mapa: 'HC.1', capturado: 'no', nota: 'Alto costo oncológico EV en los Servicios de Salud → cae en HC.1, NO en HC.5.1.' },
 { prog: 'LRS', tipo: 'línea', mapa: 'HC.1', capturado: 'no', nota: 'Ley Ricarte Soto, 175.672 MM$ (2024). Alto costo EV → HC.1. Línea propia, no etiqueta.' },
 { prog: 'PNI', tipo: 'línea', mapa: 'HC.6.2', capturado: 'no', nota: 'Vacunas, ~30.000 MM$ (2024). Prevención (HC.6.2), no medicamento de tratamiento.' },
]

// ── Gasto catastrófico: 3 métodos, distintos denominadores ───────────────────
interface CatRow { metodo: string; numerador: string; denominador: string; umbral: string; chile: string; nota: string }
const CATASTROFICO: CatRow[] = [
 { metodo: 'Per cápita (variante informe)', numerador: 'gasto de bolsillo en salud', denominador: 'ingreso PER CÁPITA del hogar', umbral: '10%', chile: '22,0%', nota: 'El más sensible; NO es el estándar internacional.' },
 { metodo: 'ODS 3.8.2 (WHO–Banco Mundial)', numerador: 'gasto de bolsillo en salud', denominador: 'gasto/ingreso TOTAL del hogar', umbral: '10%', chile: '8,2%', nota: 'Estándar ODS. A umbral 25% → 2,2%.' },
 { metodo: 'Capacidad de pago / medicamentos (WHO, Xu)', numerador: 'gasto de bolsillo', denominador: 'gasto neto de subsistencia (> alimentos)', umbral: '40%', chile: '1,1%', nota: 'Solo medicamentos (salud total = 6,0%). Método Xu 2003/2005.' },
]

// ── El modelo que cierra: el medicamento COMPLETO ─────────────────────────────
// Identidad de cierre (fuente-de-verdad v10 §3 · modelo-contable-medicamento.md):
// ambulatorio (HC.5.1, dato OCDE) + lo que cae FUERA de HC.5.1 (intrahospitalario
// embebido en HC.1 + vacunas en HC.6). Cada pieza fuera del ambulatorio se DERIVA
// como (cifra CIF todas-funciones) − (celda OCDE HC.5.1). Base 2022, en % PIB para
// tolerar el desfase de años; los MM$ escalan con el PIB implícito.
interface ModelRow {
 code?: string
 pieza: string
 formula: string
 pib: string
 mm: string
 derivado: boolean
}
const MODELO: ModelRow[] = [
 {
 code: 'HC.5.1',
 pieza: 'Ambulatorio (todos los pagadores)',
 formula: 'dato OCDE SHA',
 pib: '1,340%',
 mm: '3.518.751',
 derivado: false,
 },
 {
 code: 'HC.1',
 pieza: 'Intrahospitalario público (embebido en HC.1)',
 formula: 'punto de cuadre: CIF público 0,46 − HC.5.1 público 0,342 − PNI 0,013 · banda honesta 250.000–725.000 (central ~485.000)',
 pib: '0,11–0,31%',
 mm: '250–725k (≈485.000)',
 derivado: true,
 },
 {
 pieza: 'Privado intramural',
 formula: 'CIF privado 0,13 − HC.5.1 voluntario 0,041',
 pib: '0,089%',
 mm: '≈208.539',
 derivado: true,
 },
 {
 code: 'HC.6.2',
 pieza: 'PNI (vacunas, prevención)',
 formula: 'dato (línea presupuestaria)',
 pib: '0,013%',
 mm: '30.000',
 derivado: false,
 },
]

// ── Componente principal ─────────────────────────────────────────────────────
export default function MedicineBreakdown() {
 const A = HC51_2022
 return (
 <section id="medicine-breakdown">
 <h2>
 El medicamento ambulatorio (<CodeRef c="HC.5.1">HC.5.1</CodeRef>): por canal y por quién paga
 </h2>
 <p className="lead">
 El gasto en <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> de Chile fue de{' '}
 <strong>{clp(A.total_mm)} MM$</strong> en 2022 (dato duro OECD SHA, en CLP) ={' '}
 <strong>{pct(A.pib)} del PIB</strong> = <strong>{pct(A.salud)} del gasto en salud</strong>{' '}
 (equivale a {clp(A.usd_ppa)} USD PPA millones). Es lo dispensado para uso ambulatorio por{' '}
 <em>cualquier</em> canal: farmacia retail, farmacia hospitalaria a pacientes externos y APS.
 </p>

 {/* Caveat de perímetro: HC.5.1 NO es todos los medicamentos */}
 <div className="card warn">
 <h3 style={{ marginTop: 0 }}>HC.5.1 NO es «todos los medicamentos»</h3>
 <p style={{ marginTop: 4, marginBottom: 0 }}>
 <CodeRef c="HC.5.1">HC.5.1</CodeRef> cuenta el medicamento <strong>ambulatorio</strong>
 {' '}(el que el paciente retira para consumir fuera del recinto). Quedan{' '}
 <strong>fuera</strong> de esta cuenta:
 {' '}(a) el fármaco administrado <strong>en internación</strong> (suero EV, quimioterapia de
 pabellón), que va embebido en la <CodeRef c="HC.1">atención curativa</CodeRef> y no es
 separable; y (b) las <strong>vacunas</strong> del <CodeRef c="PNI">PNI</CodeRef>, que son{' '}
 <CodeRef c="HC.6.2">prevención (HC.6.2)</CodeRef>. Por eso HC.5.1{' '}
 <strong>subcuenta</strong> el medicamento total, sobre todo el alto costo
 intrahospitalario. Aquí reportamos lo duro (HC.5.1) y dejamos explícito el perímetro; NO
 afirmamos una cifra hospitalaria precisa porque <CodeRef c="HC.RI.1">HC.RI.1</CodeRef>{' '}
 (farmacéutico total) figura como <span className="badge miss">Missing</span> en SHA.
 </p>
 </div>

 <div className="grid2">
 {/* Panel A, POR CANAL */}
 <div>
 <h3>
 <span className="pill">Panel A</span> Por canal de dispensación
 </h3>
 <p className="note">
 Quién <em>dispensa</em> el medicamento ambulatorio (el proveedor). El{' '}
 <CodeRef c="HP.5">retail</CodeRef> es el canal mayor con {pct(A.canal[0].pctv)}, pero{' '}
 <strong>es menos de la mitad</strong> si se mira el medicamento total: el{' '}
 <CodeRef c="HP.1">hospital a externos</CodeRef> ({pct(A.canal[1].pctv)}) y la{' '}
 <CodeRef c="HP.3">APS</CodeRef> ({pct(A.canal[2].pctv)}) aportan el resto.
 </p>
 <MoneyTable
 rows={A.canal}
 total={A.total_mm}
 totalLabel="Total HC.5.1 (ambulatorio)"
 capN={1}
 capTitle="Medicamentos ambulatorios (HC.5.1) por canal de dispensación, 2022 (MM$ CLP)"
 headFirst="Canal"
 highlightCode="HP.5"
 />
 <PieCard
 rows={A.canal}
 colors={CANAL_COLORS}
 capN={1}
 capTitle="Composición del medicamento ambulatorio por canal, 2022"
 foot="Por canal · 2022 · MM$ CLP · Σ = total (dato duro OECD SHA)"
 />
 </div>

 {/* Panel B, POR FINANCIADOR */}
 <div>
 <h3>
 <span className="pill">Panel B</span> Por financiador (quién paga)
 </h3>
 <p className="note">
 Quién <em>paga</em> el medicamento ambulatorio. El{' '}
 <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> concentra cerca del{' '}
 {pct(A.financiador[2].pctv)}; el <CodeRef c="HF.1">financiamiento obligatorio</CodeRef>{' '}
 (cotizaciones + aporte fiscal) aporta {pct(A.financiador[0].pctv)} y el{' '}
 <CodeRef c="HF.2">voluntario</CodeRef> {pct(A.financiador[1].pctv)}.
 </p>
 <MoneyTable
 rows={A.financiador}
 total={A.total_mm}
 totalLabel="Total HC.5.1 (ambulatorio)"
 capN={2}
 capTitle="Medicamentos ambulatorios (HC.5.1) por financiador, 2022 (MM$ CLP)"
 headFirst="Quién paga"
 highlightCode="HF.3"
 showSalud
 />
 <PieCard
 rows={A.financiador}
 colors={FIN_COLORS}
 capN={2}
 capTitle="Composición del financiamiento del medicamento ambulatorio, 2022"
 foot="Por financiador · 2022 · MM$ CLP · Σ = total (dato duro OECD SHA)"
 />
 </div>
 </div>

 <p className="note">
 El cruce canal × financiador <strong>no lo reporta la OCDE</strong> (solo entrega los
 marginales), así que «público por canal» NO es dato duro. Validación fuerte: el bolsillo
 OECD de HC.5.1 ({pct(A.financiador[2].salud!)} del gasto en salud) cuadra con el bolsillo CIF
 construido desde la EPF (INE) → las dos fuentes cruzan por construcción.
 </p>

 {/* ── DESGLOSE FINO DEL OBLIGATORIO (HF.1): por fuente de financiamiento ─── */}
 <h2>Adentro del financiamiento obligatorio (HF.1): por fuente</h2>
 <p className="psub">
 El <CodeRef c="HF.1">25,5% obligatorio</CodeRef> no es un bloque homogéneo. Abierto por fuente,
 el <strong>aporte fiscal puro</strong> (impuestos generales, <CodeRef c="HF.1.1">HF.1.1</CodeRef>)
 al medicamento ambulatorio es <strong>0,4%</strong>; el resto es contributivo: cotización{' '}
 <CodeRef c="HF.1.2.1">FONASA</CodeRef> (14,9%) y el{' '}
 <CodeRef c="HF.1.2.2">7% obligatorio de ISAPRE</CodeRef> (10,2%). Es decir, el financiamiento
 del medicamento ambulatorio es mayoritariamente por cotizaciones, no por impuestos generales.
 </p>
 <Caption
 ch={3}
 n={3}
 kind="tabla"
 title="Desglose fino del financiamiento público (HF.1) del medicamento ambulatorio, 2022 (MM$ CLP)"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '54%' }} />
 <col style={{ width: '28%' }} />
 <col style={{ width: '18%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Componente del público (HF.1)</th>
 <th>MM$ CLP (2022)</th>
 <th>% de HC.5.1</th>
 </tr>
 </thead>
 <tbody>
 {A.publicoFino.map(r => {
 const fiscal = r.code === 'HF.1.1'
 return (
 <tr key={r.code} className={fiscal ? 'row-meds' : undefined}>
 <td>
 <CodeRef c={r.code}>{r.label}</CodeRef>{' '}
 <span className="note">· {r.sub}</span>
 </td>
 <td className="num">{clp(r.mm)}</td>
 <td className={fiscal ? 'ratio' : 'num'}>{pct(r.pctv)}</td>
 </tr>
 )
 })}
 <tr className="tot">
 <td>Total público / obligatorio (HF.1)</td>
 <td className="num">{clp(A.financiador[0].mm)}</td>
 <td className="num">{pct(A.financiador[0].pctv)}</td>
 </tr>
 </tbody>
 </table>
 </div>
 <p className="note">
 Una aclaración de perímetros: el <strong>25,5%</strong> es el <CodeRef c="HF.1">HF.1</CodeRef>{' '}
 completo por financiador (incluye el 7% obligatorio de ISAPRE); el <strong>≈15,3%</strong> es
 gobierno + FONASA <em>sin</em> el 7% de ISAPRE; y el <strong>≈30%</strong> es el devengado
 público sobre el ambulatorio, lectura presupuestaria de otro perímetro. No se deben confundir.
 Fuente: OCDE SHA, HC.5.1, 2022, CLP.
 </p>

 {/* ── PROGRAMAS DE COBERTURA Y EL VACÍO ───────────────────────────────── */}
 <h2>Programas de cobertura y el vacío</h2>
 <p className="psub">
 Chile financia medicamentos por <strong>listas cerradas</strong>. Pero el gasto público se
 mide <strong>por objeto/ejecución, no por programa</strong>: GES, DAC, FOFAR y CEM son{' '}
 <em>etiquetas de cobertura</em> sobre medicamentos <strong>ya contados</strong>;{' '}
 <CodeRef c="LRS">LRS</CodeRef> y <CodeRef c="PNI">PNI</CodeRef> son <em>líneas
 presupuestarias propias</em>. Sumar GES + SS + DAC + FOFAR por separado es{' '}
 <strong>doble conteo</strong> (era el error de versiones anteriores).
 </p>

 <Caption
 ch={3}
 n={4}
 kind="tabla"
 title="Programas de medicamentos: tipo, a qué función SHA mapean y qué captura HC.5.1 de cada uno"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '12%' }} />
 <col style={{ width: '14%' }} />
 <col style={{ width: '22%' }} />
 <col style={{ width: '14%' }} />
 <col style={{ width: '38%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Programa</th>
 <th>Tipo</th>
 <th>Mapea a (SHA)</th>
 <th>¿En HC.5.1?</th>
 <th>Detalle</th>
 </tr>
 </thead>
 <tbody>
 {PROGRAMAS.map(p => (
 <tr key={p.prog} className={p.capturado === 'sí' ? 'row-meds' : undefined}>
 <td><CodeRef c={p.prog}>{p.prog}</CodeRef></td>
 <td>
 {p.tipo === 'línea'
 ? <span className="badge ok">línea propia</span>
 : <span className="badge miss">etiqueta</span>}
 </td>
 <td className="note">{p.mapa}</td>
 <td className={p.capturado === 'sí' ? 'pct' : p.capturado === 'no' ? 'ratio' : undefined}>
 {p.capturado === 'sí' ? 'Sí' : p.capturado === 'no' ? 'No' : 'Parcial'}
 </td>
 <td className="note">{p.nota}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 <p className="note">
 Regla de oro (no doble conteo): <strong>GES / DAC / FOFAR / CEM son etiquetas</strong>, no
 se suman entre sí ni al gasto de los Servicios de Salud, ; <strong>LRS y PNI sí son líneas
 propias</strong>. <CodeRef c="CENABAST">CENABAST</CodeRef> es aprovisionamiento intermedio
 (~79% del gasto), tampoco una línea aparte. Captura neta de HC.5.1: entra{' '}
 <CodeRef c="FOFAR">FOFAR</CodeRef> entero y el <CodeRef c="GES">GES</CodeRef>-ambulatorio;
 quedan fuera GES-intrahospitalario, <CodeRef c="DAC">DAC</CodeRef>,{' '}
 <CodeRef c="LRS">LRS</CodeRef> y <CodeRef c="PNI">PNI</CodeRef>.
 </p>

 {/* El vacío + judicialización */}
 <div className="card warn">
 <h3 style={{ marginTop: 0 }}>El vacío: lo que no entra en ninguna lista</h3>
 <p style={{ marginTop: 4 }}>
 El alto costo y lo crónico que cae fuera de GES (~90 problemas), LRS (~27 patologías) y DAC
 no tiene cobertura garantizada. Se financia por tres vías, todas señales del mismo vacío:
 </p>
 <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
 <li>
 <strong>Bolsillo</strong>, el {pct(A.financiador[2].pctv)} de HC.5.1 lo pagan los
 hogares; es la raíz del gasto catastrófico (abajo).
 </li>
 <li>
 <strong>Judicialización</strong> (glosa sub-presupuestada): recursos de protección para
 obtener fármacos no cubiertos. La Ley de Presupuestos contempla una glosa para sentencias
 de <strong>28.914 MM$ (2024)</strong>, pero la ejecución la desborda año a año: FONASA
 ejecutó <strong>93.594 MM$ en 2024</strong> (DIPRES, Proyecciones de Gasto Público
 2025-2050), casi todo en medicamentos. La brecha entre lo presupuestado y lo ejecutado es
 una señal del tamaño del vacío de cobertura.
 </li>
 <li>
 <strong>Postergación de tratamiento</strong>: cerca de un tercio de las personas declara
 haber dejado de tomar dosis por costo (Ipsos-Espacio Público, 2025).
 </li>
 </ul>
 <p style={{ marginBottom: 0 }} className="note">
 La <CodeRef c="LRS">Ley Ricarte Soto</CodeRef> y el GES cubren por listas cerradas de
 patologías o tratamientos; el medicamento crónico ambulatorio de uso masivo se cubre
 principalmente vía el Fondo de Farmacia de la atención primaria y el gasto de bolsillo del hogar.
 </p>
 </div>

 {/* ── GASTO CATASTRÓFICO: 3 MÉTODOS ───────────────────────────────────── */}
 <h2>Gasto catastrófico: tres métodos, tres denominadores</h2>
 <p className="psub">
 Un hogar es «catastrófico» si su gasto de bolsillo supera un umbral de su capacidad de pago.
 La cifra cambia mucho según el <strong>denominador</strong> y el umbral. Todas se construyen
 del microdato de la <strong>EPF IX (INE, 2021-2022)</strong>, la misma fuente con que el
 bolsillo de HC.5.1 (<CodeRef c="HF.3">HF.3</CodeRef> = {clp(A.financiador[2].mm)} MM$) entra
 al SHA → EPF y OCDE cruzan por construcción.
 </p>
 <Caption
 ch={3}
 n={5}
 kind="tabla"
 title="Gasto catastrófico en Chile por método: numerador, denominador, umbral y resultado"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '24%' }} />
 <col style={{ width: '17%' }} />
 <col style={{ width: '23%' }} />
 <col style={{ width: '9%' }} />
 <col style={{ width: '11%' }} />
 <col style={{ width: '16%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Método</th>
 <th>Numerador</th>
 <th>Denominador</th>
 <th>Umbral</th>
 <th>Chile</th>
 <th>Nota</th>
 </tr>
 </thead>
 <tbody>
 {CATASTROFICO.map((c, i) => (
 <tr key={c.metodo}>
 <td>{c.metodo}</td>
 <td className="note">{c.numerador}</td>
 <td className="note">{c.denominador}</td>
 <td className="num">{c.umbral}</td>
 <td className={i === 0 ? 'ratio' : 'pct'}>{c.chile}</td>
 <td className="note">{c.nota}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 <p className="note">
 Los tres son válidos pero no comparables: <strong>22,0%</strong> usa ingreso per cápita (el
 más alto, no estándar); <strong>8,2%</strong> es el ODS 3.8.2 oficial (gasto/ingreso total
 del hogar); <strong>1,1%</strong> es la variante WHO acotada a medicamentos sobre la
 capacidad de pago neta de subsistencia. Citas: Xu et al. (2003), <em>Household catastrophic
 health expenditure</em>, Lancet; WHO &amp; Banco Mundial, protección financiera / ODS 3.8.2;
 INE, EPF IX (2021-2022).
 </p>

 {/* ── EL MEDICAMENTO COMPLETO: EL MODELO QUE CIERRA ───────────────────── */}
 <h2>El medicamento completo: el modelo que cierra</h2>
 <p className="psub">
 El <strong>medicamento ambulatorio</strong> (<CodeRef c="HC.5.1">HC.5.1</CodeRef>) es solo
 una parte. El <strong>medicamento completo</strong> suma además lo que cae <em>fuera</em> de
 HC.5.1: el fármaco administrado en internación, embebido en{' '}
 <CodeRef c="HC.1">atención curativa (HC.1)</CodeRef>, no etiquetado, y las vacunas del{' '}
 <CodeRef c="PNI">PNI</CodeRef> (<CodeRef c="HC.6.2">HC.6.2</CodeRef>). No existe UN total
 publicado: <CodeRef c="HC.RI.1">HC.RI.1</CodeRef> (farmacéutico total) figura como{' '}
 <span className="badge miss">Missing</span>. Por eso el total no se <em>lee</em>: se{' '}
 <strong>demuestra</strong> como suma de celdas. Trabajamos en <strong>% del PIB</strong>{' '}
 (base 2022) para tolerar el desfase de años; los MM$ escalan con el PIB implícito.
 </p>
 <p className="psub" style={{ marginTop: 0 }}>
 Cada pieza fuera del ambulatorio se <strong>deriva</strong> como{' '}
 <em>(cifra CIF de todas las funciones) − (celda OCDE HC.5.1)</em>, no como un supuesto libre.
 Ahora bien: el fármaco intrahospitalario público <strong>no es un punto</strong>, es una{' '}
 <strong>banda de {HOSP_BANDA.rango} MM$</strong> (central <strong>{HOSP_BANDA.centralStr}</strong>).
 El punto de cuadre algebraico (<strong>≈246.000</strong> = público total − ambulatorio público −
 PNI) sirve sólo para cerrar la contabilidad contra el total público; la cifra{' '}
 <em>reportable</em> es la banda. Reemplaza el viejo «360.000 estimación EP» y el «2.650 USD PPA
 triangulado», pero <strong>sin pretender una precisión que el dato no tiene</strong>.
 </p>

 {/* Honestidad: el cierre es algebraico, no es prueba ──────────────────── */}
 <div className="card warn">
 <h3 style={{ marginTop: 0 }}>El cierre es algebraico, no una prueba</h3>
 <p style={{ marginTop: 4, marginBottom: 0 }}>
 Ninguna de las cinco fuentes <strong>aísla</strong> el fármaco intrahospitalario: la OCDE lo
 embebe en <CodeRef c="HC.1">HC.1</CodeRef>, el CIF no lo separa, y la CNEP lo mezcla con
 dispositivos. El modelo «cierra» en el extremo bajo de la banda (1,546% ≈ 1,54% del PIB), pero ese cierre es{' '}
 <strong>casi tautológico</strong>: su único ancla empírica es que el{' '}
 <CodeRef c="HF.3">bolsillo</CodeRef> OCDE (0,956% PIB) ≈ bolsillo CIF (0,95%), y{' '}
 <em>ambos vienen de la misma EPF</em>. Por eso esto es un{' '}
 <strong>marco que ACOTA</strong> el fármaco hospitalario a una banda de{' '}
 {HOSP_BANDA.rango} MM$, no una demostración de un valor exacto. Sólo{' '}
 <strong>WinSIG/PERC (DEIS) o CENABAST por destino</strong> lo convertirían en una medición.
 </p>
 </div>

 <Caption
 ch={3}
 n={6}
 kind="tabla"
 title="El medicamento completo como identidad de cierre algebraico: HC.5.1 + intrahospitalario público (banda) + privado intramural + PNI (base 2022)"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '30%' }} />
 <col style={{ width: '36%' }} />
 <col style={{ width: '12%' }} />
 <col style={{ width: '22%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Pieza</th>
 <th>Fórmula</th>
 <th>% PIB</th>
 <th>MM$ CLP</th>
 </tr>
 </thead>
 <tbody>
 {MODELO.map(r => (
 <tr key={r.pieza} className={r.derivado ? undefined : 'row-meds'}>
 <td>
 {r.code ? <CodeRef c={r.code}>{r.pieza}</CodeRef> : r.pieza}{' '}
 {r.derivado && <span className="badge miss">derivado</span>}
 </td>
 <td style={{ textAlign: 'left' }} className="note">{r.formula}</td>
 <td className="num">{r.pib}</td>
 <td className={r.derivado ? 'est num' : 'num'}>{r.mm}</td>
 </tr>
 ))}
 <tr className="tot">
 <td>Medicamento completo</td>
 <td style={{ textAlign: 'left' }}>suma de las cuatro piezas (banda por el intrahospitalario)</td>
 <td className="num">~1,55–1,75%</td>
 <td className="num">~3,6–4,1 bill (≈3.873.060)</td>
 </tr>
 </tbody>
 </table>
 </div>
 <p className="note">
 El bolsillo intrahospitalario sale ≈0 (CIF bolsillo 0,95 − HC.5.1 bolsillo 0,956 = −0,006):
 consistente con que el paciente internado no paga el remedio, pero, como ambos vienen de la
 EPF, es el <em>único</em> chequeo empírico del cierre, no una confirmación independiente.
 CENABAST, Mercado Público y DIPRES <strong>no se suman entre sí</strong> (misma plata, distinta
 fuente): son los tres ángulos de triangulación del lado compra.
 </p>

 <div className="card">
 <h3 style={{ marginTop: 0 }}>La lectura: un marco que acota, no un total que se «lee»</h3>
 <p style={{ marginTop: 4, marginBottom: 0 }}>
 En el <strong>extremo bajo</strong> de la banda (≈246.000, el residuo que iguala
 público_total − ambulatorio_público − PNI) la suma recupera <em>exactamente</em> el{' '}
 <strong>CIF total de 1,54% del PIB</strong>, por eso ese punto «cierra», ; en el{' '}
 <strong>central (≈485.000)</strong> el total sube a <strong>~1,65% del PIB</strong>
 {' '}(≈3.873.060 MM$). El cierre, entonces, no demuestra un valor exacto sino la{' '}
 <strong>coherencia</strong> del fármaco intrahospitalario con el resto de las cuentas; el
 valor real es la <strong>banda {HOSP_BANDA.rango} MM$</strong> (central {HOSP_BANDA.centralStr}),
 corroborada en magnitud por el arsenal <CodeRef c="CENABAST">CENABAST</CodeRef> (1.119.073)
 consumido en internación. Por eso el <strong>gasto público en medicamentos de todas las
 funciones</strong>, HC.5.1 público (804.882) + intrahospitalario (banda) + PNI (30.000), 
 es del orden del <strong>0,46% del PIB</strong> del estudio CIF/UC (≈1,2 billones de pesos,
 cuentas disjuntas) en el extremo bajo, y mayor hacia el central. Conviene no confundir ese 0,46%
 (un total disjunto) con la vista-programa de ocho instrumentos, que se solapan y no se suman.
 </p>
 </div>

 {/* ── CNEP: corroboración de MAGNITUD del hospitalario ─────────────────── */}
 <h2>CNEP: corroboración independiente de la magnitud hospitalaria</h2>
 <p className="psub">
 El <strong>Informe de Gasto Hospitalario de la CNEP (2024)</strong> mira el arsenal de los
 hospitales públicos desde la <em>eficiencia de compra</em>, una fuente distinta de la OCDE y del
 CIF. Corrobora el <strong>orden de magnitud</strong> del arsenal hospitalario, pero{' '}
 <strong>no aísla el fármaco</strong>: trata fármacos y dispositivos médicos juntos.
 </p>
 <Caption
 ch={3}
 n={7}
 kind="tabla"
 title="CNEP 2024: arsenal hospitalario (fármacos + dispositivos), corrobora la magnitud, no aísla el fármaco"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '34%' }} />
 <col style={{ width: '30%' }} />
 <col style={{ width: '36%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Dimensión</th>
 <th style={{ textAlign: 'left' }}>Dato CNEP (2023)</th>
 <th style={{ textAlign: 'left' }}>Lectura</th>
 </tr>
 </thead>
 <tbody>
 <tr>
 <td style={{ textAlign: 'left' }}>Arsenal hospitalario (fármacos + dispositivos)</td>
 <td style={{ textAlign: 'left' }} className="num">≈1,45 billones</td>
 <td style={{ textAlign: 'left' }} className="note">
 2% del gasto operacional del Gobierno Central; 25% de su gasto en bienes y servicios.
 </td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left' }}>Crecimiento</td>
 <td style={{ textAlign: 'left' }} className="ratio">{CNEP_2024.creceReal}</td>
 <td style={{ textAlign: 'left' }} className="note">
 Presión de gasto real sostenida, consistente con la judicialización al alza.
 </td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left' }}>Concentración</td>
 <td style={{ textAlign: 'left' }}>{CNEP_2024.concentracion}</td>
 <td style={{ textAlign: 'left' }} className="note">
 El gasto se concentra en pocos hospitales de alta complejidad.
 </td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left' }}>Mecanismos de compra</td>
 <td style={{ textAlign: 'left' }} className="note">{CNEP_2024.compra}</td>
 <td style={{ textAlign: 'left' }} className="note">
 Convergente con CENABAST (arsenal 2024 ≈ 1,32 billones).
 </td>
 </tr>
 </tbody>
 </table>
 </div>
 <div className="card warn">
 <p style={{ margin: 0 }}>
 <strong>Caveat CNEP.</strong> {CNEP_2024.caveat[0].toUpperCase() + CNEP_2024.caveat.slice(1)}.
 La cifra de 1,45 billones <em>incluye dispositivos</em>, así que no es comparable directa con
 la banda del fármaco solo ({HOSP_BANDA.rango} MM$). Lo que aporta es{' '}
 <strong>confianza en el orden de magnitud</strong>: hay un arsenal hospitalario público de
 escala billonaria, creciente, concentrado, exactamente el terreno donde vive el fármaco
 intrahospitalario que las cuentas no etiquetan.
 </p>
 </div>

 {/* ── PERSPECTIVAS: cómo mira cada informe los mismos datos ────────────── */}
 <h2>Cómo mira cada informe los datos</h2>
 <p className="psub">
 Los números «no cuadran» entre fuentes porque <strong>no miden lo mismo</strong>: cada informe
 usa un lente, un perímetro y un año distintos. El <strong>puente fuerte</strong> es que el
 bolsillo OCDE ≈ CIF ≈ EPF (comparten la raíz EPF/INE). La <strong>diferencia</strong> entre el
 consumo ambulatorio OCDE y la compra de todas las funciones del CIF es, justamente, el fármaco
 intrahospitalario que nadie aísla.
 </p>
 <Caption
 ch={3}
 n={8}
 kind="tabla"
 title="Perspectivas: cómo mira cada informe el gasto en medicamentos (lente, perímetro, año, cifra)"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '14%' }} />
 <col style={{ width: '20%' }} />
 <col style={{ width: '20%' }} />
 <col style={{ width: '8%' }} />
 <col style={{ width: '38%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Fuente</th>
 <th style={{ textAlign: 'left' }}>Lente · qué mide</th>
 <th style={{ textAlign: 'left' }}>Perímetro</th>
 <th>Año</th>
 <th style={{ textAlign: 'left' }}>Cifra</th>
 </tr>
 </thead>
 <tbody>
 <tr>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>OCDE SHA</td>
 <td style={{ textAlign: 'left' }} className="note">consumo · función · <CodeRef c="HC.5.1">HC.5.1</CodeRef> ambulatorio (todos los canales)</td>
 <td style={{ textAlign: 'left' }} className="note">excl. internación</td>
 <td className="num">2022</td>
 <td style={{ textAlign: 'left' }} className="note">3.518.751 MM$ · bolsillo ≈71% · obligatorio 25,5%</td>
 </tr>
 <tr className="row-meds">
 <td style={{ textAlign: 'left', fontWeight: 600 }}>CIF/UC (2º informe)</td>
 <td style={{ textAlign: 'left' }} className="note">ejecución · gasto público en fármacos (cuentas disjuntas)</td>
 <td style={{ textAlign: 'left' }} className="note">todas las funciones</td>
 <td className="num">2023-24</td>
 <td style={{ textAlign: 'left' }} className="note">0,46% del PIB (≈1,2 billones), referencia externa convergente</td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>CNEP</td>
 <td style={{ textAlign: 'left' }} className="note">compra · eficiencia hospitalaria · fármacos + dispositivos</td>
 <td style={{ textAlign: 'left' }} className="note">arsenal hospitalario</td>
 <td className="num">2023</td>
 <td style={{ textAlign: 'left' }} className="note">≈1,45 billones (mezcla dispositivos)</td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>EPF / INE</td>
 <td style={{ textAlign: 'left' }} className="note">encuesta de hogares · <CodeRef c="HF.3">bolsillo</CodeRef></td>
 <td style={{ textAlign: 'left' }} className="note">bolsillo</td>
 <td className="num">2021-22</td>
 <td style={{ textAlign: 'left' }} className="note">fuente del ≈71% / 62% y del gasto catastrófico</td>
 </tr>
 <tr>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>DIPRES y registros públicos</td>
 <td style={{ textAlign: 'left' }} className="note">presupuesto y ejecución · SINIM (APS) · CENABAST · Mercado Público</td>
 <td style={{ textAlign: 'left' }} className="note">público granular</td>
 <td className="num">2010-25</td>
 <td style={{ textAlign: 'left' }} className="note">cara en pesos del gasto público, por institución e instrumento</td>
 </tr>
 </tbody>
 </table>
 </div>
 <p className="note">
 <strong>Puente fuerte:</strong> bolsillo OCDE ≈ CIF ≈ EPF (misma raíz EPF/INE).{' '}
 <strong>No miden lo mismo:</strong> OCDE = ambulatorio (consumo), CIF = compra de todas las
 funciones; la diferencia entre ambos ≈ el intrahospitalario. Por eso ninguna fila «contradice» a
 otra: son cinco lentes sobre el mismo objeto, y el fármaco hospitalario vive en la costura que
 ninguna etiqueta.
 </p>
 </section>
 )
}
