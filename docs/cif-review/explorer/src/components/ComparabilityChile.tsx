import { useMemo, useState } from 'react'
import { comparability, dataSources, CompCode, Source } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

const OECD_NOTE =
 'https://stats.oecd.org/wbos/fileview2.aspx?IDFile=8c9a9676-c5cb-4d37-9fb4-18923ce901c4'
const API = '/api/v1/medicamentos/dev/v6'

const isMissing = (status: string) => /missing/i.test(status)

// ── Nombres en español de los códigos SHA que aparecen en la columna «Variables» ──
// El problema que resuelve: la metadata OECD entrega los códigos pelados (HF.1.1,
// FS.1, HC.1.1…), que son crípticos. Acá cada código se muestra liderando con su
// NOMBRE descriptivo, y el código queda entre paréntesis. Cubre todos los códigos
// presentes en data_sources (verificado contra el JSON).
const SHA_NAMES: Record<string, string> = {
 // HC · funciones (¿qué se compra?)
 'HC.0': 'Gasto no clasificado por función',
 'HC.1.1': 'Atención curativa hospitalaria',
 'HC.1.2': 'Atención curativa de día',
 'HC.1.3': 'Atención curativa ambulatoria',
 'HC.1.4': 'Atención curativa domiciliaria',
 'HC.2.1': 'Rehabilitación hospitalaria',
 'HC.2.3': 'Rehabilitación ambulatoria',
 'HC.3': 'Cuidados de larga duración (salud)',
 'HC.4': 'Servicios auxiliares (laboratorio, imagen, transporte)',
 'HC.5': 'Bienes médicos',
 'HC.5.1': 'Medicamentos ambulatorios',
 'HC.5.2': 'Aparatos terapéuticos y otros bienes médicos',
 'HC.6': 'Atención preventiva',
 'HC.7': 'Gobernanza y administración del sistema',
 'HC.7.1': 'Gobernanza del sistema de salud',
 // HF · esquemas de financiamiento (¿quién paga?)
 'HF.1.1': 'Esquemas de gobierno (aporte fiscal)',
 'HF.1.2.1': 'Seguro social (FONASA, Mutuales, FF.AA.)',
 'HF.1.2.2': 'Cotización obligatoria del 7% vía ISAPRE',
 'HF.2.1.1': 'Seguro voluntario primario (ISAPRE complemento)',
 'HF.2.1.2': 'Seguro voluntario complementario',
 'HF.2.2.1': 'Instituciones sin fines de lucro (NPISH)',
 'HF.3': 'Bolsillo de los hogares (copagos + compra directa)',
 // FS · fuentes de ingreso (¿de dónde sale el recurso?)
 'FS.1': 'Transferencias del gobierno (impuestos)',
 'FS.1.1': 'Transferencias internas del gobierno',
 'FS.1.2': 'Transferencias del gobierno desde otros niveles',
 'FS.3': 'Cotizaciones sociales obligatorias',
 'FS.3.1': 'Cotizaciones de empleados',
 'FS.3.2': 'Cotizaciones de empleadores',
 'FS.4': 'Cotizaciones de seguro voluntario',
 'FS.5.1': 'Recursos de instituciones sin fines de lucro',
 'FS.5.2': 'Recursos de empresas',
 'FS.6.1': 'Pago directo de los hogares',
 'FS.6.3': 'Donaciones y otros ingresos de los hogares',
}

// Convierte la cadena cruda de «Variables SHA» (p. ej. "HF.1.1, FS.1, HC.1.1…")
// en una lista legible: cada código detectado se renderiza con su NOMBRE en
// español liderando y el código entre paréntesis (vía CodeRef si está en el
// glosario). El texto en inglés de la metadata se descarta para no ensuciar.
function ReadableVars({ raw }: { raw: string }) {
 const found: string[] = []
 const re = /[A-Z]{2}\.?\s?\d+(?:\.\d+)*/g
 let m: RegExpExecArray | null
 while ((m = re.exec(raw)) !== null) {
 const code = m[0].replace(/\s/g, '')
 if (!found.includes(code)) found.push(code)
 }
 if (found.length === 0) return <span className="note">{raw}</span>
 return (
 <span style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
 {found.map(code => {
 const name = SHA_NAMES[code]
 return (
 <span key={code} style={{ fontSize: 12.5, lineHeight: 1.35 }}>
 {name ? <CodeRef c={code}>{name}</CodeRef> : name ?? code}{' '}
 <code style={{ fontSize: 11, color: '#667085' }}>{code}</code>
 </span>
 )
 })}
 </span>
 )
}

// Vacíos relevantes a medicamentos: la descripción en español lidera (qué es
// lo que Chile no mide), el código SHA va secundario y al hover vía CodeRef.
// `code` se usa con CodeRef sólo si está en el glosario; si no, va plano.
const MISSING_MEDS: { code?: string; label: string }[] = [
 { code: 'HC.RI.1', label: 'El gasto farmacéutico TOTAL del país: recetado + venta libre, sumando lo ambulatorio y lo hospitalario en una sola cifra' },
 { code: 'HC.5.1.1', label: 'Los medicamentos recetados de uso ambulatorio, separados del resto' },
 { code: 'HC.5.1.2', label: 'Los medicamentos de venta libre (sin receta / OTC)' },
 { code: 'HP.5.1', label: 'Las farmacias como proveedor de dispensación retail, aisladas del agregado de comercios' },
 { label: 'El financiamiento externo (resto del mundo): aportes de fuentes fuera del país' },
]

type ModalState =
 | { kind: 'source'; data: Source }
 | { kind: 'comp'; data: CompCode }
 | null

export default function ComparabilityChile() {
 const [q, setQ] = useState('')
 const [modal, setModal] = useState<ModalState>(null)

 const filtered = useMemo(() => {
 const needle = q.trim().toLowerCase()
 if (!needle) return comparability
 return comparability.filter(c =>
 (c.code + ' ' + c.desc + ' ' + c.status + ' ' + c.expl).toLowerCase().includes(needle))
 }, [q])

 const close = () => setModal(null)

 return (
 <section id="comparabilidad">
 <h2>Fuentes chilenas y vacíos de reporte</h2>
 <p className="psub">
 De qué registros administrativos sale cada celda del System of Health
 Accounts (SHA) y, sobre todo, qué deja de medir Chile cuando se compara
 internacionalmente.
 </p>

 <div className="card">
 <p style={{ marginTop: 0 }}>
 Las cuentas de salud chilenas no nacen de una encuesta única, sino del
 ensamblaje anual de varios registros administrativos heterogéneos:
 la ejecución presupuestaria del Estado (SIGFE y DIPRES), las
 estadísticas del seguro público (FONASA), la información financiera de
 los aseguradores privados (Superintendencia de Salud para ISAPRE,
 Asociación de Aseguradores para los seguros complementarios), las
 estimaciones de las mutuales y del sector sin fines de lucro, y la
 producción asistencial física (REM). El gasto de bolsillo, el mayor
 componente del gasto en medicamentos, no proviene de ningún registro
 contable, sino de la Encuesta de Presupuestos Familiares (EPF) que el
 INE levanta cada cinco años y que MINSAL proyecta entre olas. El equipo
 de MINSAL/DEIS arma con todo ello el cuestionario conjunto OECD–Eurostat–OMS
 (JHAQ) que origina la nota oficial de comparabilidad{' '}
 <a href={OECD_NOTE} target="_blank" rel="noreferrer">
 «Note on data sources and comparability, CHL»
 </a>.
 </p>
 <p>
 ¿Por qué importa todo esto a la hora de comparar? Porque la calidad y la
 cobertura de cada comparación internacional dependen de la fuente que
 alimenta la celda. No todas las cifras valen lo mismo.
 </p>
 <p>
 Una cifra respaldada por ejecución presupuestaria (DIPRES) es un dato
 duro. Tiene un valor muy distinto al de un componente reconstruido por
 residuo, como el{' '}
 <CodeRef c="HF.1.2.2">7% de cotización obligatoria de ISAPRE</CodeRef>{' '}
 que la Superintendencia separa del{' '}
 <CodeRef c="HF.2.1">complemento voluntario</CodeRef>, o al de un
 componente estimado a partir de una encuesta que sólo se levanta cada
 cinco años, como el{' '}
 <CodeRef c="HF.3">gasto de bolsillo de los hogares</CodeRef> vía EPF.
 </p>
 <p style={{ marginBottom: 0 }}>
 La trampa es sutil. Dos países pueden mostrar el mismo valor de{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> y, sin embargo,
 estar contando cosas distintas, si sus fuentes y sus notas de
 comparabilidad difieren. Por eso esta sección antepone el origen del dato
 a la cifra misma.
 </p>
 </div>

 {/* ── (1) Fuentes de datos chilenas ── */}
 <h3>Fuentes de datos chilenas que alimentan las cuentas</h3>
 <p className="note">
 Cada fila identifica el registro de origen, qué cubre y a qué cuentas SHA
 alimenta. La última columna ya no muestra los códigos pelados: cada uno
 aparece con su <b>nombre en español</b> liderando y el código entre
 paréntesis (por ejemplo, «Seguro social FONASA (HF.1.2.1)»). El tipo de
 fuente importa: ejecución presupuestaria (dato duro), estados financieros de
 aseguradores, producción asistencial valorizada o estimación de encuesta.
 Abrir el detalle muestra cómo se inserta en el SHA.
 </p>
 <Caption
 ch={2}
 n={1}
 kind="tabla"
 title="Registros administrativos chilenos que alimentan las cuentas SHA"
 />
 <div className="tablewrap">
 <table style={{ minWidth: 720 }}>
 <colgroup>
 <col style={{ width: '16%' }} />
 <col style={{ width: '32%' }} />
 <col style={{ width: '12%' }} />
 <col style={{ width: '30%' }} />
 <col style={{ width: '10%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Fuente</th>
 <th style={{ textAlign: 'left' }}>Qué cubre</th>
 <th>Tipo</th>
 <th style={{ textAlign: 'left' }}>Cuentas SHA que alimenta (nombre · código)</th>
 <th></th>
 </tr>
 </thead>
 <tbody>
 {dataSources.map(s => (
 <tr key={s.name}>
 <td style={{ fontWeight: 600 }}>{s.name}</td>
 <td style={{ textAlign: 'left' }}>
 {s.desc.length > 120 ? s.desc.slice(0, 117) + '…' : s.desc}
 </td>
 <td style={{ textAlign: 'center' }}>
 <span className="pill">{s.type}</span>
 </td>
 <td style={{ textAlign: 'left' }}>
 <ReadableVars raw={s.vars} />
 </td>
 <td style={{ textAlign: 'center' }}>
 <button
 className="link"
 onClick={() => setModal({ kind: 'source', data: s })}
 >
 Ver detalle
 </button>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {/* ── (2) puntero al árbol de códigos (evita duplicar la tabla de la sección 2) ── */}
 <p className="note" style={{ margin: '6px 0 4px' }}>
 Las {comparability.length} clasificaciones SHA (HC/HP/HF/FS) con su estado de reporte y
 nota de comparabilidad están en la <a href="#codigos">sección «Sistema de códigos
 ICHA»</a> (árbol desplegable). Aquí nos concentramos en las <b>fuentes</b> y en <b>qué no
 reporta Chile</b>.
 </p>

 {/* ── (3) Callout: lo que Chile NO reporta ── */}
 <div className="card warn">
 <h3 style={{ marginTop: 0 }}>Lo que Chile NO reporta a la OECD</h3>
 <p>
 Los vacíos casi nunca son de fuentes que no existan. Son, más bien, de
 desagregaciones que ningún registro chileno llega a producir.
 </p>
 <p>
 Varias clasificaciones que resultan decisivas para entender el gasto en
 medicamentos quedan en estado{' '}
 <span className="badge miss">Missing</span> dentro del SHA chileno:
 </p>
 <ul>
 {MISSING_MEDS.map(m => (
 <li key={m.code ?? m.label}>
 {m.code ? <CodeRef c={m.code}>{m.label}</CodeRef> : m.label}
 </li>
 ))}
 </ul>
 <p>
 La consecuencia práctica es directa: el{' '}
 <strong>«medicamento total»</strong> no existe como dato reportado. El
 fármaco hospitalario va embebido en la{' '}
 <CodeRef c="HC.1">atención curativa de internación</CodeRef> y no se
 separa de ella; el SHA tampoco desagrega recetado vs. venta libre ni
 aísla a las{' '}
 <CodeRef c="HP.5.1">farmacias como subnivel propio</CodeRef> (sólo el
 agregado de <CodeRef c="HP.5">retail</CodeRef>). Se suma que cerca de un
 quinto del gasto corriente{' '}
 <CodeRef c="HC.0">no está clasificado por función</CodeRef>, lo que
 subestima sistemáticamente toda cifra vista por función.
 </p>
 <p>
 <strong>Cifra canónica:</strong> cerca del 71% de gasto de bolsillo. Es trazable
 y se reproduce desde el SHA: el{' '}
 <CodeRef c="HF.3">bolsillo de los hogares (copagos + compra directa)</CodeRef>{' '}
 sobre los{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (2022), el bien
 médico farmacéutico contando todos los canales. Esos mismos ambulatorios
 traen 25,6% de financiamiento público (FOFAR, GES-retail, CENABAST).
 </p>
 <p style={{ marginBottom: 0 }}>
 El <strong>62%</strong> que circula es otra cosa: bolsillo sobre el
 perímetro CIF (que incluye lo hospitalario). Descansa sobre el{' '}
 <CodeRef c="HC.RI.1">gasto farmacéutico total estimado</CodeRef>, así que
 es estimación, no dato SHA (ver{' '}
 <a href="#medicine-breakdown">sección 4</a>). La comparación
 internacional rigurosa se ancla en los{' '}
 <CodeRef c="HC.5.1">ambulatorios</CodeRef>, consistentes entre países;
 todo «total farmacéutico» obliga a declarar método y denominador.
 </p>
 </div>

 {/* ── (4) Descargas ── */}
 <h3>Descargar metadata oficial</h3>
 <div className="dl">
 <a href={`${API}/fuente/oecd-metadata-xls`} target="_blank" rel="noreferrer">
 Metadata oficial OECD (XLS)
 </a>
 <a
 className="alt"
 href={`${API}/fuente/oecd-metadata-md`}
 target="_blank"
 rel="noreferrer"
 >
 Metadata procesada (Markdown)
 </a>
 <a className="alt" href={OECD_NOTE} target="_blank" rel="noreferrer">
 Nota de comparabilidad CHL (OECD.Stat)
 </a>
 </div>

 {/* ── MODAL inline ── */}
 {modal && (
 <div
 className="modal-backdrop"
 onClick={close}
 role="dialog"
 aria-modal="true"
 >
 <div className="modal" onClick={e => e.stopPropagation()}>
 <button className="close" onClick={close} aria-label="Cerrar">
 ×
 </button>
 {modal.kind === 'source' ? (
 <>
 <h3>{modal.data.name}</h3>
 <p>
 <span className="pill">{modal.data.type}</span>
 </p>
 <div className="note" style={{ margin: '8px 0' }}>
 <b>Cuentas SHA que alimenta:</b>
 <div style={{ marginTop: 4 }}>
 <ReadableVars raw={modal.data.vars} />
 </div>
 </div>
 <p style={{ whiteSpace: 'pre-wrap' }}>{modal.data.desc}</p>
 </>
 ) : (
 <>
 <h3>
 {modal.data.desc} <CodeRef c={modal.data.code} />
 </h3>
 <p>
 {isMissing(modal.data.status) ? (
 <span className="badge miss">{modal.data.status}</span>
 ) : (
 <span className="badge ok">Reportado</span>
 )}
 </p>
 <div className="quote" style={{ whiteSpace: 'pre-wrap' }}>
 {modal.data.expl || 'Sin nota de comparabilidad para esta categoría.'}
 </div>
 </>
 )}
 </div>
 </div>
 )}
 </section>
 )
}
