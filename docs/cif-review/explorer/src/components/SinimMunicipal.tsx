import CodeRef from './CodeRef'
import Caption from './Caption'

// Gasto municipal (APS) en productos farmacéuticos, cuenta 22.04.004 del clasificador
// presupuestario, reportada por las municipalidades a SINIM, por comuna 2020-2024.
// Encuadre SHA: financiamiento PÚBLICO (HF.1), función MEDICAMENTOS AMBULATORIOS (HC.5.1),
// proveedor ATENCIÓN PRIMARIA / farmacia comunal (HP.3). Es la ejecución municipal vista
// "desde abajo"; se SOLAPA con la transferencia FONASA per cápita a la APS, por lo que NO
// se suma al total público canónico (1.514.814 MM$), sirve para descomponer/validar el
// componente ambulatorio público.
// Cifras verificadas contra data/sinim/sinim_medicamentos_salud_TODOS.csv (suma por año,
// M$ ÷ 1000 = MM$). Ver data/sinim/sinim_resumen.md.

interface AnioFila {
 year: number
 mm: number // MM$ CLP corrientes (suma nacional de la cuenta 22.04.004)
 conServicio: number // comunas con salud municipal que reportan gasto
 sinServicio: number // comunas "Sin Servicio" / sin reporte (valor NULL)
}

// Sumas nacionales de medicamentos_miles_pesos por año (verificado: csv → ÷1000).
const ANIOS: AnioFila[] = [
 { year: 2020, mm: 116541.7, conServicio: 318, sinServicio: 27 },
 { year: 2021, mm: 121667.2, conServicio: 317, sinServicio: 28 },
 { year: 2022, mm: 142357.5, conServicio: 320, sinServicio: 25 },
 { year: 2023, mm: 162613.2, conServicio: 319, sinServicio: 26 },
 { year: 2024, mm: 182580.8, conServicio: 320, sinServicio: 25 },
]

// Top comunas 2024 (MM$ y % del gasto municipal-APS nacional 2024). Verificado contra csv.
const TOP_COMUNAS_2024: { comuna: string; region: string; mm: number; pct: number }[] = [
 { comuna: 'Puente Alto', region: 'Metropolitana', mm: 7252.1, pct: 4.0 },
 { comuna: 'Temuco', region: 'Araucanía', mm: 4605.2, pct: 2.5 },
 { comuna: 'Chillán', region: 'Ñuble', mm: 4310.8, pct: 2.4 },
 { comuna: 'Viña del Mar', region: 'Valparaíso', mm: 3475.8, pct: 1.9 },
 { comuna: 'Osorno', region: 'Los Lagos', mm: 3355.2, pct: 1.8 },
]

// Concentración regional 2024 (MM$ y % nacional). Verificado contra csv.
const TOP_REGIONES_2024: { region: string; mm: number; pct: number }[] = [
 { region: 'Metropolitana', mm: 61859.5, pct: 33.9 },
 { region: 'Valparaíso', mm: 19654.9, pct: 10.8 },
 { region: 'Biobío', mm: 18083.0, pct: 9.9 },
 { region: 'Maule', mm: 13332.7, pct: 7.3 },
 { region: 'Araucanía', mm: 13125.3, pct: 7.2 },
]

const TOTAL_2024 = ANIOS[ANIOS.length - 1].mm
const TOTAL_2020 = ANIOS[0].mm
const CREC = ((TOTAL_2024 / TOTAL_2020 - 1) * 100) // +56,7%
const fMM = (v: number) => Math.round(v).toLocaleString('es-CL')
const f1 = (v: number) => v.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

export default function SinimMunicipal() {
 return (
 <section id="sinim-municipal">
 <h2 className="ptitle">Gasto municipal en medicamentos (APS)</h2>
 <p className="psub">
 Lo que las municipalidades ejecutan en productos farmacéuticos para la atención primaria,
 comuna a comuna (2020–2024). Fuente: SINIM (SubDere), cuenta presupuestaria 22.04.004
 «Productos Farmacéuticos».
 </p>

 <div className="card">
 <p style={{ marginTop: 0 }}>
 Es el componente más concreto y trazable del gasto público{' '}
 <b>ambulatorio</b> en medicamentos: el arsenal de la <CodeRef c="HP.3">farmacia
 comunal y los CESFAM (atención primaria)</CodeRef>, financiado con{' '}
 <CodeRef c="HF.1">recursos públicos (aporte fiscal y cotizaciones, vía la
 transferencia FONASA per cápita)</CodeRef> y destinado a los{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> de los pacientes crónicos.
 Lo reporta cada municipio en su ejecución presupuestaria, la cuenta{' '}
 <code>22.04.004</code> del clasificador, y SINIM lo consolida por comuna. En 2024 sumó{' '}
 <b>{fMM(TOTAL_2024)} MM$</b>, tras crecer <b>+{f1(CREC)}%</b> nominal desde 2020.
 </p>
 </div>

 <div className="card">
 <p style={{ marginTop: 0 }}>
 <b>Es una de las líneas aditivas del gasto público disjunto.</b> El gasto municipal en
 farmacia de la atención primaria (ejecución comunal, {fMM(TOTAL_2024)} MM$ en 2024) es
 disjunto de la Farmacia de los Servicios de Salud: se suma como componente propio del total
 público (banda de 0,42% a 0,46% del PIB, ≈1,1 a 1,2 billones de pesos). Lo que <b>no</b> se
 hace es sumar a la vez la financiación FONASA (transferencias) y la ejecución municipal: serían
 las dos caras de la misma plata. Visto «desde abajo» (ejecución municipal real) converge con el
 aporte per cápita declarado «desde arriba» en la línea de atención primaria del presupuesto, lo
 que da una cota independiente del orden de magnitud.
 </p>
 </div>

 <h3>Serie nacional 2020–2024</h3>
 <p className="note">
 Suma de la cuenta 22.04.004 sobre las ≈318–320 comunas con salud municipal. «Sin servicio»
 agrupa las comunas cuya APS no es de gestión municipal (valor NULL en SINIM).
 </p>
 <Caption
 ch={5}
 n={3}
 kind="tabla"
 title="Gasto municipal en medicamentos (APS), serie nacional 2020–2024 (cuenta 22.04.004)"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '16%' }} />
 <col style={{ width: '21%' }} />
 <col style={{ width: '21%' }} />
 <col style={{ width: '21%' }} />
 <col style={{ width: '21%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Año</th>
 <th>MM$ corrientes</th>
 <th>Var. vs. año previo</th>
 <th>Comunas con servicio</th>
 <th>Sin servicio (NULL)</th>
 </tr>
 </thead>
 <tbody>
 {ANIOS.map((a, i) => {
 const prev = i > 0 ? ANIOS[i - 1].mm : null
 const varPct = prev != null ? (a.mm / prev - 1) * 100 : null
 return (
 <tr key={a.year}>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>{a.year}</td>
 <td className="num">{fMM(a.mm)}</td>
 <td className="num">{varPct == null ? ', ' : '+' + f1(varPct) + '%'}</td>
 <td className="num">{a.conServicio}</td>
 <td className="num">{a.sinServicio}</td>
 </tr>
 )
 })}
 <tr className="tot">
 <td style={{ textAlign: 'left' }}>2020 → 2024</td>
 <td className="num">+{fMM(TOTAL_2024 - TOTAL_2020)}</td>
 <td className="num">+{f1(CREC)}%</td>
 <td colSpan={2} style={{ textAlign: 'left', fontWeight: 400 }}>
 Fuente: SINIM (SubDere), cuenta 22.04.004 · M$ → MM$ (÷1000)
 </td>
 </tr>
 </tbody>
 </table>
 </div>

 <div className="grid2">
 <div>
 <h3 style={{ marginBottom: 4 }}>Top comunas 2024</h3>
 <p className="note" style={{ marginTop: 0 }}>
 Por monto ejecutado. % sobre el gasto municipal-APS nacional de 2024.
 </p>
 <Caption
 ch={5}
 n={4}
 kind="tabla"
 title="Top 5 comunas por gasto municipal en medicamentos, 2024"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '34%' }} />
 <col style={{ width: '30%' }} />
 <col style={{ width: '20%' }} />
 <col style={{ width: '16%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Comuna</th>
 <th style={{ textAlign: 'left' }}>Región</th>
 <th>MM$ 2024</th>
 <th>% nac.</th>
 </tr>
 </thead>
 <tbody>
 {TOP_COMUNAS_2024.map(c => (
 <tr key={c.comuna}>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>{c.comuna}</td>
 <td style={{ textAlign: 'left' }}>{c.region}</td>
 <td className="num">{fMM(c.mm)}</td>
 <td className="num">{f1(c.pct)}%</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 <div>
 <h3 style={{ marginBottom: 4 }}>Concentración regional 2024</h3>
 <p className="note" style={{ marginTop: 0 }}>
 Top 5 regiones. La Metropolitana sola concentra un tercio del gasto.
 </p>
 <Caption
 ch={5}
 n={5}
 kind="tabla"
 title="Concentración regional del gasto municipal en medicamentos, top 5 regiones 2024"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '52%' }} />
 <col style={{ width: '28%' }} />
 <col style={{ width: '20%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Región</th>
 <th>MM$ 2024</th>
 <th>% nac.</th>
 </tr>
 </thead>
 <tbody>
 {TOP_REGIONES_2024.map(r => (
 <tr key={r.region}>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>{r.region}</td>
 <td className="num">{fMM(r.mm)}</td>
 <td className="num">{f1(r.pct)}%</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>
 </div>

 <div className="note">
 <p>
 <b>Cómo mapea al marco OCDE (SHA).</b> Financia (<b>HF</b>):{' '}
 <CodeRef c="HF.1">público / obligatorio</CodeRef>, es la transferencia FONASA per cápita
 gestionada por el municipio. Función (<b>HC</b>):{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef>. Proveedor (<b>HP</b>):{' '}
 <CodeRef c="HP.3">atención primaria (CESFAM / farmacia comunal)</CodeRef>. Es uno de los
 registros que alimentan la celda chilena de <CodeRef c="HC.5.1" /> en el SHA, junto a
 SIGFE (SNSS) y la Superintendencia (ISAPRE).
 </p>
 <p>
 <b>Tres hallazgos.</b> (1) <b>Crecimiento sostenido:</b> +{f1(CREC)}% nominal en cinco
 años, con el salto mayor en 2022 (+{f1((ANIOS[2].mm / ANIOS[1].mm - 1) * 100)}%). (2){' '}
 <b>Alta concentración geográfica:</b> la Región Metropolitana absorbe el{' '}
 {f1(TOP_REGIONES_2024[0].pct)}% del total y las cinco primeras comunas, el 12,6%; Puente
 Alto sola gasta tanto como toda la Región de Magallanes y Aysén juntas. (3){' '}
 <b>Comunas «sin servicio»:</b> ≈25 comunas reportan NULL porque su APS no es de gestión
 municipal, toda la Región de Aysén (sus 10 comunas) tiene gasto municipal cero, porque su
 atención primaria la opera directamente el Servicio de Salud.
 </p>
 </div>
 </section>
 )
}
