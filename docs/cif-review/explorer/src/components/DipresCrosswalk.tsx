import CodeRef from './CodeRef'
import Caption from './Caption'

// Crosswalk Ley de Presupuestos (DIPRES) ↔ OCDE SHA: cada fila del gasto público canónico
// (1.514.814 MM$ CLP 2024) se mapea a su línea presupuestaria y a su código SHA, declarando
// si es trazable a una glosa, una glosa-embebida, una estimación propia, o vive en otra partida.
// Fuente reproducible: silver.dipres_presupuesto (Ley 2010-2025). Ancla: LRS = 175.672 MM$ exacto.

type Traza = 'trazable' | 'glosa' | 'estimacion' | 'otra-partida'

interface Fila {
 instrumento: string
 mm: number // MM$ CLP 2024 (canónico, Tabla 4.3)
 linea: string // línea de la Ley de Presupuestos
 traza: Traza
 hf: React.ReactNode // quién financia (OCDE), español + código al hover
 funcion: React.ReactNode// qué función (OCDE)
 canal: string // ambulatorio (retail) vs hospitalario
}

const FILAS: Fila[] = [
 {
 instrumento: 'GES / AUGE (porción FONASA)',
 mm: 540000,
 linea: 'Partida 16 · Cap. 02 · FONASA (sin glosa GES segregada)',
 traza: 'glosa',
 hf: <><CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> + <CodeRef c="HF.1.2.2">7% obligatorio de ISAPRE</CodeRef></>,
 funcion: <>según canasta: <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> + <CodeRef c="HC.1">atención hospitalaria</CodeRef></>,
 canal: 'mixto (ambulatorio + hospitalario)',
 },
 {
 instrumento: 'Fármaco intrahospitalario público (punto de cuadre)',
 mm: 246000,
 linea: 'Punto de cuadre algebraico: público total (1.514.814) − ambulatorio público (HC.5.1·HF1 = 804.882) − PNI (30.000) ≈ 246.000. Cifra reportable = banda 250.000–725.000 (central ~485.000)',
 traza: 'estimacion',
 hf: <><CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef></>,
 funcion: <>medicamento embebido en la <CodeRef c="HC.1">atención hospitalaria</CodeRef></>,
 canal: 'hospitalario',
 },
 {
 instrumento: 'APS, FOFAR / arsenal municipal',
 mm: 195000,
 linea: 'Partida 16 · "Atención Primaria, Ley N° 19.378" (aporte per cápita, suma por Servicio de Salud)',
 traza: 'trazable',
 hf: <><CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> (per cápita, gestión municipal)</>,
 funcion: <><CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> para crónicos</>,
 canal: 'ambulatorio (farmacia de CESFAM)',
 },
 {
 instrumento: 'Ley Ricarte Soto',
 mm: 175672,
 linea: 'Partida 16 · Cap. 02 · Prog. 01 · "Fondo para Diagnóstico y Tratamientos de Alto Costo Ley N°20.850"',
 traza: 'trazable',
 hf: <><CodeRef c="HF.1.1">aporte fiscal del gobierno</CodeRef> (impuestos, vía FONASA)</>,
 funcion: <>alto costo: <CodeRef c="HC.5.1">ambulatorio</CodeRef> u <CodeRef c="HC.1">hospitalario</CodeRef></>,
 canal: '≈70% ambulatorio / ≈30% hospitalario (est.)',
 },
 {
 instrumento: 'Judicialización (glosa sub-presupuestada)',
 mm: 93594,
 linea: 'Glosa de sentencias presupuestada en 28.914 (2024); la ejecución FONASA la desborda a 93.594 (DIPRES, Proyecciones de Gasto Público 2025-2050)',
 traza: 'glosa',
 hf: <>el esquema que la sentencia obliga (típicamente <CodeRef c="HF.1.2.1">FONASA</CodeRef>)</>,
 funcion: <>alto costo: <CodeRef c="HC.5.1">ambulatorio</CodeRef> u <CodeRef c="HC.1">hospitalario</CodeRef></>,
 canal: 'mixto',
 },
 {
 instrumento: 'Drogas de Alto Costo (DAC)',
 mm: 70803,
 linea: 'Glosa 11 (Drogas de Alto Costo) dentro de los Servicios de Salud / FONASA',
 traza: 'glosa',
 hf: <><CodeRef c="HF.1.1">aporte fiscal</CodeRef> / <CodeRef c="HF.1.2.1">FONASA</CodeRef></>,
 funcion: <>oncológicos: mayormente <CodeRef c="HC.5.1">ambulatorios</CodeRef></>,
 canal: '≈85% ambulatorio / ≈15% hospitalario (est.)',
 },
 {
 instrumento: 'FF.AA. y de Orden',
 mm: 62339,
 linea: 'Otra partida (Defensa / Seguridad, DIPRECA, CAPREDENA, sanidad institucional). Estimación EP',
 traza: 'otra-partida',
 hf: <><CodeRef c="HF.1.2.1">seguro social institucional</CodeRef></>,
 funcion: <>embebido en la <CodeRef c="HC.1">atención hospitalaria</CodeRef> institucional</>,
 canal: 'hospitalario',
 },
 {
 instrumento: 'PNI, vacunas (biológicos estrictos)',
 mm: 30000,
 linea: 'Partida 16 · "Programa Nacional de Inmunizaciones" (programa total ≈177.000; los biológicos son una asignación interna)',
 traza: 'trazable',
 hf: <><CodeRef c="HF.1.1">aporte fiscal del gobierno</CodeRef></>,
 funcion: <><CodeRef c="HC.6.2">inmunización (función preventiva)</CodeRef>, no es medicamento de tratamiento</>,
 canal: 'preventivo (no retail ni curativo)',
 },
]

const TOTAL = FILAS.reduce((a, f) => a + f.mm, 0)
const fMM = (v: number) => v.toLocaleString('es-CL')

const BADGE: Record<Traza, { txt: string; cls: string }> = {
 'trazable': { txt: 'trazable a la glosa', cls: 'ok' },
 'glosa': { txt: 'glosa no segregada', cls: 'miss' },
 'estimacion': { txt: 'derivado / sin glosa', cls: 'miss' },
 'otra-partida': { txt: 'otra partida', cls: 'miss' },
}

export default function DipresCrosswalk() {
 return (
 <section id="crosswalk-dipres">
 <h2 className="ptitle">De la Ley de Presupuestos a las cuentas OCDE</h2>
 <p className="psub">
 Cómo se compone el gasto público en medicamentos desde la Ley de Presupuestos (DIPRES) y a qué
 categoría OCDE corresponde cada peso. Fuente reproducible: el detalle 2010–2025 está en el lake
 de datos públicos (partida → capítulo → programa → asignación).
 </p>

 <div className="card">
 <p>
 El <b>gasto público en medicamentos se ubica en una banda de 0,42% a 0,46% del PIB</b>{' '}
 (≈1,1 a 1,2 billones de pesos, lado ejecución), que converge con el 0,46% del PIB del estudio
 CIF/UC. La suma de los ocho instrumentos de la vista-programa (que daba 1.514.814 MM$){' '}
 <b>no es aditiva</b>: el GES público y las Drogas de Alto Costo se devengan dentro de la
 Farmacia de los Servicios de Salud, y FONASA financia lo que esa farmacia ejecuta, así que
 sumar las líneas duplica del orden de 400.000 MM$. Esta tabla recorre esas líneas y las mapea
 a su código OCDE; no todas se leen con la misma claridad en la Ley. La columna{' '}
 <b>Trazabilidad</b> lo declara fila por fila: <b>Ricarte Soto, APS y PNI</b> tienen glosa
 propia con nombre y monto; <b>GES y Drogas de Alto Costo</b> existen pero quedan diluidas
 dentro de un programa mayor; la <b>judicialización</b> es una glosa sub-presupuestada que la
 ejecución desborda; y las <b>FF.AA.</b> viven en otra partida, fuera de Salud.
 </p>
 <p style={{ marginBottom: 0 }}>
 El <b>fármaco intrahospitalario público</b> no lo aísla ninguna fuente. El{' '}
 <b>punto de cuadre algebraico</b>, público total (1.514.814) − ambulatorio público
 (<CodeRef c="HC.5.1">HC.5.1</CodeRef>·<CodeRef c="HF.1">HF.1</CodeRef> = 804.882) −{' '}
 <CodeRef c="PNI">PNI</CodeRef> (30.000) ≈ <b>246.000 MM$</b> (0,105% del PIB), es la fila que
 hace cuadrar esta tabla; pero la cifra <em>reportable</em> es una <b>banda de 250.000–725.000 MM$</b>{' '}
 (central ~485.000), porque el cierre es <b>algebraico/casi tautológico</b> (su único ancla
 empírica es que el bolsillo OCDE ≈ bolsillo CIF, ambos de la EPF): es un{' '}
 <b>marco que acota</b>, no una prueba. Por eso las líneas de esta tabla suman{' '}
 <b>{fMM(TOTAL)} MM$</b>: usan el <em>punto de cuadre</em> del intrahospitalario, no la fracción
 bruta de los Servicios de Salud.
 </p>
 </div>

 <Caption
 ch={5}
 n={2}
 kind="tabla"
 title="Crosswalk de la Ley de Presupuestos (DIPRES) a las cuentas OCDE, con trazabilidad por glosa"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '17%' }} />
 <col style={{ width: '8%' }} />
 <col style={{ width: '22%' }} />
 <col style={{ width: '11%' }} />
 <col style={{ width: '15%' }} />
 <col style={{ width: '15%' }} />
 <col style={{ width: '12%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>Instrumento</th>
 <th>MM$ 2024</th>
 <th style={{ textAlign: 'left' }}>Línea de la Ley de Presupuestos</th>
 <th>Trazabilidad</th>
 <th style={{ textAlign: 'left' }}>Quién financia (OCDE)</th>
 <th style={{ textAlign: 'left' }}>Qué función (OCDE)</th>
 <th style={{ textAlign: 'left' }}>Canal</th>
 </tr>
 </thead>
 <tbody>
 {FILAS.map(f => (
 <tr key={f.instrumento}>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>{f.instrumento}</td>
 <td className="num">{fMM(f.mm)}</td>
 <td style={{ textAlign: 'left', fontSize: 12.5 }}>{f.linea}</td>
 <td style={{ textAlign: 'center' }}>
 <span className={'badge ' + BADGE[f.traza].cls}>{BADGE[f.traza].txt}</span>
 </td>
 <td style={{ textAlign: 'left' }}>{f.hf}</td>
 <td style={{ textAlign: 'left' }}>{f.funcion}</td>
 <td style={{ textAlign: 'left', fontSize: 12.5 }}>{f.canal}</td>
 </tr>
 ))}
 <tr className="tot">
 <td style={{ textAlign: 'left' }}>SUMA (vista-programa, NO aditiva)</td>
 <td className="num">{fMM(TOTAL)}</td>
 <td colSpan={5} style={{ textAlign: 'left', fontWeight: 400 }}>
 Esta suma <b>no es un total</b>: las líneas se solapan (el GES público y las Drogas de Alto
 Costo están dentro de la Farmacia de los Servicios de Salud). El gasto público disjunto cae en
 una banda de 0,42% a 0,46% del PIB (≈1,1 a 1,2 billones de pesos), que converge con el 0,46%
 del estudio CIF/UC · Fuente CLP: DIPRES / CIF-UC 2025 ·
 serie reproducible en el lake (silver.dipres_presupuesto)
 </td>
 </tr>
 </tbody>
 </table>
 </div>

 <div className="note">
 <p><b>Las cuatro etiquetas de trazabilidad.</b></p>
 <p>
 <span className="badge ok">trazable a la glosa</span> = el monto coincide con una línea que la
 Ley nombra de forma explícita (Ricarte Soto calza al peso: 175.672 MM$).{' '}
 <span className="badge miss">glosa no segregada</span> = el gasto existe pero no se abre del
 programa que lo contiene (GES diluido en FONASA; DAC apenas como Glosa 11).{' '}
 <span className="badge miss">derivado / sin glosa</span> = ninguna línea lo aísla en la Ley: el
 fármaco intrahospitalario se <em>deriva</em> por identidad contable (no se estima a ojo) y la
 judicialización es un carril de facto.{' '}
 <span className="badge miss">otra partida</span> = está en el presupuesto pero fuera de Salud
 (FF.AA.). El <CodeRef c="HC.5.1">ambulatorio</CodeRef> y el <CodeRef c="HC.1">hospitalario</CodeRef>{' '}
 nunca se separan en la Ley; el «total farmacéutico» se cierra en la sección de medicamentos.
 </p>
 </div>

 <div className="note">
 <p>
 <b>Corroboración de magnitud (CENABAST y CNEP).</b> Dos fuentes distintas del presupuesto
 respaldan el <em>orden de magnitud</em> del arsenal hospitalario público. CENABAST: el gasto
 devengado de farmacia del SNSS 2024 (compra directa por Mercado Público + intermediación,
 incluye fármacos e insumos médicos) suma <b>1.323.645 MM$</b>. CNEP (2024): el arsenal
 hospitalario 2023 (fármacos + dispositivos) es <b>≈1,45 billones</b>, con <b>+23% real
 2018-2023</b> y concentración <b>16/75</b> (16% de los hospitales = 75% del gasto). Ambas{' '}
 <b>mezclan fármacos con dispositivos/insumos</b>, así que corroboran la escala pero{' '}
 <b>no aíslan el fármaco</b>.
 </p>
 <p>
 Por eso el fármaco intrahospitalario público se reporta como <b>banda de 250.000–725.000 MM$</b>{' '}
 (central ~485.000): el <em>punto de cuadre</em> algebraico ≈246.000 (público total −
 ambulatorio público − PNI) hace cuadrar la contabilidad, y la fracción del arsenal CENABAST
 consumida en internación es coherente con él, pero el <b>cierre del modelo es algebraico/casi
 tautológico</b> (su único ancla empírica es bolsillo OCDE ≈ bolsillo CIF, ambos de la EPF). El
 total farmacéutico no se <em>lee</em> (<CodeRef c="HC.RI.1">HC.RI.1</CodeRef> sigue Missing):
 el modelo es un <b>marco que ACOTA</b>, no una prueba. Ver el desarrollo completo en la{' '}
 <a href="#medicine-breakdown">sección del medicamento</a>.
 </p>
 </div>
 </section>
 )
}
