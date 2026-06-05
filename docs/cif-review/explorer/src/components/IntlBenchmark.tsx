import { useMemo } from 'react'
import CodeRef from './CodeRef'
import Caption from './Caption'

// ISO 3166-1 alpha-2 (MAYÚSCULA) por país. Las banderas se sirven LOCALMENTE
// desde public/flags/{ISO2}.png (self-hosted, sin dependencia de un servicio
// externo en runtime). Los emoji de bandera no renderizan en Linux, por eso PNG.
const ISO2: Record<string, string> = {
 'Estados Unidos': 'US',
 Alemania: 'DE',
 Suiza: 'CH',
 Francia: 'FR',
 Canadá: 'CA',
 Japón: 'JP',
 España: 'ES',
 'Reino Unido': 'GB',
 Polonia: 'PL',
 Dinamarca: 'DK',
 Chile: 'CL',
}

// URL local de la bandera, relativa al base de Vite ('./') → resuelve a
// /api/medicamentos-datos/flags/{ISO2}.png bajo el HashRouter de producción.
const flagSrc = (iso: string) => `${import.meta.env.BASE_URL}flags/${iso}.png`

// <img> de bandera self-hosted. `alt` lleva el nombre del país. Cae a nada si el
// país no está mapeado. `w` permite ajustar el tamaño (tabla vs eje per cápita).
function Flag({ pais, w = 24 }: { pais: string; w?: number }) {
 const iso = ISO2[pais]
 if (!iso) return null
 return (
 <img
 src={flagSrc(iso)}
 width={w}
 height={Math.round((w * 2) / 3)}
 alt={pais}
 loading="lazy"
 style={{ borderRadius: 2, boxShadow: '0 0 0 1px rgba(0,0,0,0.08)', flex: '0 0 auto' }}
 />
 )
}

// ─────────────────────────────────────────────────────────────────────────
// Comparación internacional OCDE · gasto en medicamentos (retail / ambulatorio)
//
// Perímetro de TODAS las cifras de esta sección: gasto FARMACÉUTICO RETAIL =
// medicamentos dispensados de forma ambulatoria (recetados + venta libre) por
// farmacias y otros minoristas. En la nomenclatura SHA corresponde a
// <CodeRef c="HC.5.1"> (productos farmacéuticos y otros bienes médicos no
// duraderos, componente ambulatorio). NO incluye el medicamento administrado
// dentro de una hospitalización, que la OCDE imputa a la atención de internación
// y por tanto no es comparable entre países como "medicamento total".
//
// Fuente primaria: OECD (2023), "Health at a Glance 2023, Pharmaceutical
// expenditure". Año de referencia: 2021 (último disponible y armonizado en esa
// edición). Datos en USD ajustados por paridad de poder adquisitivo (PPA/PPP).
//
// Nota de trazabilidad de cada celda (campo `cita`):
// 'oecd-texto' → valor citado textualmente en el cuerpo del capítulo OCDE
// (p. ej. promedio OCDE USD 614; Chile 78% bolsillo;
// Alemania USD 1 158; Suiza USD 1 061; Francia 83/5/12;
// Canadá 40/34/26; Polonia 65% bolsillo).
// 'oecd-grafico'→ valor leído del gráfico/serie por país de la misma edición,
// redondeado; sujeto a revisión contra la tabla fuente.
// Donde un dato no pudo fijarse con la fuente a mano queda `null` y se renderiza
// como "s/d" (sin dato), sin inventar la cifra.
// ─────────────────────────────────────────────────────────────────────────

type Cita = 'oecd-texto' | 'oecd-grafico'

interface PaisFarma {
 pais: string
 /** Gasto farmacéutico retail per cápita, USD PPA, 2021. */
 perCapitaUsdPpa: number | null
 /** % del gasto farmacéutico retail pagado de bolsillo por los hogares. */
 bolsilloPct: number | null
 /** % del gasto farmacéutico retail financiado por esquemas públicos/obligatorios. */
 publicoPct: number | null
 cita: Cita
 esChile?: boolean
}

// Promedio OCDE (referencia): USD 614 p/c; 39% bolsillo; 58% público/obligatorio;
// 3% seguro voluntario. (OECD HaG 2023, texto.)
const PROMEDIO_OCDE = { perCapitaUsdPpa: 614, bolsilloPct: 39, publicoPct: 58 }

const DATOS: PaisFarma[] = [
 // Citados textualmente en el capítulo OCDE
 { pais: 'Estados Unidos', perCapitaUsdPpa: 1432, bolsilloPct: 11, publicoPct: 80, cita: 'oecd-grafico' },
 { pais: 'Alemania', perCapitaUsdPpa: 1158, bolsilloPct: 14, publicoPct: 83, cita: 'oecd-texto' },
 { pais: 'Suiza', perCapitaUsdPpa: 1061, bolsilloPct: 24, publicoPct: 70, cita: 'oecd-texto' },
 { pais: 'Francia', perCapitaUsdPpa: 681, bolsilloPct: 12, publicoPct: 83, cita: 'oecd-texto' },
 { pais: 'Canadá', perCapitaUsdPpa: 879, bolsilloPct: 26, publicoPct: 40, cita: 'oecd-texto' },
 { pais: 'Japón', perCapitaUsdPpa: 838, bolsilloPct: null, publicoPct: null, cita: 'oecd-grafico' },
 { pais: 'España', perCapitaUsdPpa: 596, bolsilloPct: null, publicoPct: null, cita: 'oecd-grafico' },
 { pais: 'Reino Unido', perCapitaUsdPpa: null, bolsilloPct: 35, publicoPct: 65, cita: 'oecd-texto' },
 { pais: 'Polonia', perCapitaUsdPpa: null, bolsilloPct: 65, publicoPct: null, cita: 'oecd-texto' },
 { pais: 'Dinamarca', perCapitaUsdPpa: 305, bolsilloPct: null, publicoPct: null, cita: 'oecd-texto' },
 { pais: 'Chile', perCapitaUsdPpa: 455, bolsilloPct: 78, publicoPct: null, cita: 'oecd-texto', esChile: true },
]

const FUENTE_URL =
 'https://www.oecd.org/en/publications/2023/11/health-at-a-glance-2023_e04f8239/full-report/pharmaceutical-expenditure_a58c1da0.html'

const fmtUsd = (v: number | null) => (v == null ? 's/d' : `US$ ${v.toLocaleString('es-CL')}`)
const fmtPct = (v: number | null) => (v == null ? 's/d' : `${v}%`)

// Mediana y cuartiles sobre los valores no nulos (incluyendo Chile), para
// situar a cada país en la distribución observada de esta muestra.
function cuantiles(xs: number[]) {
 const s = [...xs].sort((a, b) => a - b)
 const q = (p: number) => {
 const i = (s.length - 1) * p
 const lo = Math.floor(i)
 const hi = Math.ceil(i)
 if (lo === hi) return s[lo]
 return s[lo] + (s[hi] - s[lo]) * (i - lo)
 }
 return { min: s[0], q1: q(0.25), mediana: q(0.5), q3: q(0.75), max: s[s.length - 1] }
}

export default function IntlBenchmark() {
 const perCapVals = useMemo(
 () => DATOS.map(d => d.perCapitaUsdPpa).filter((v): v is number => v != null),
 [])
 const stats = useMemo(() => cuantiles(perCapVals), [perCapVals])
 const escalaMax = Math.max(stats.max, PROMEDIO_OCDE.perCapitaUsdPpa)

 const pos = (v: number) => `${(v / escalaMax) * 100}%`

 return (
 <section id="comparacion-intl">
 <h2 className="ptitle">Comparación internacional (OCDE)</h2>
 <p className="psub">
 Cómo se ubica Chile en la distribución OCDE del gasto farmacéutico{' '}
 <em>retail</em>, es decir, los{' '}
 <CodeRef c="HC.5.1">medicamentos de dispensación ambulatoria</CodeRef>{' '}
 (recetados más venta libre), en tres ejes. Todos los valores provienen de{' '}
 <a href={FUENTE_URL} target="_blank" rel="noreferrer">
 OECD, <em>Health at a Glance 2023, Pharmaceutical expenditure</em>
 </a>
 , año de referencia 2021, en dólares ajustados por paridad de poder
 adquisitivo (USD&nbsp;PPA).
 </p>

 <div className="card">
 <p style={{ marginTop: 0 }}>
 <strong>Denominador de cada eje.</strong> Las tres columnas comparten un
 mismo perímetro, el gasto farmacéutico <em>retail</em>,{' '}
 <CodeRef c="HC.5.1" />, pero responden preguntas distintas:
 </p>
 <ul style={{ marginBottom: 0 }}>
 <li>
 <strong>(1) Per cápita (USD&nbsp;PPA).</strong> Numerador: gasto
 farmacéutico retail del país. Denominador: población residente. Mide{' '}
 <em>cuánto</em> se gasta por persona, no quién lo paga.
 </li>
 <li>
 <strong>(2) Bolsillo (% del retail).</strong> Numerador: pago directo
 de los hogares, copagos de recetas reembolsadas más compra íntegra de
 no reembolsadas. Denominador: el mismo gasto farmacéutico retail. Mide{' '}
 <em>qué fracción</em> recae sobre el hogar.
 </li>
 <li>
 <strong>(3) Público / obligatorio (% del retail).</strong> Numerador:
 esquemas públicos y de aseguramiento obligatorio. Denominador: el gasto
 retail. El resto hasta 100% lo cubre el seguro voluntario (promedio
 OCDE 3%; excepciones notorias: Canadá 34%).
 </li>
 </ul>
 </div>

 {/* ── Tabla ── */}
 <h3>Tres ejes por país</h3>
 <p className="note">
 Orden descendente por gasto per cápita. «s/d» = sin dato fijado contra la
 fuente. La fila de promedio OCDE es referencia, no un país.
 </p>
 <Caption ch={5} n={4} kind="tabla" title="Gasto farmacéutico retail por país: per cápita, bolsillo y financiamiento público (OCDE, 2021)" />
 <div className="tablewrap">
 <table style={{ width: '100%', tableLayout: 'fixed' }}>
 <colgroup>
 <col style={{ width: '34%' }} />
 <col style={{ width: '24%' }} />
 <col style={{ width: '20%' }} />
 <col style={{ width: '22%' }} />
 </colgroup>
 <thead>
 <tr>
 <th style={{ textAlign: 'left' }}>País</th>
 <th>Per cápita (USD&nbsp;PPA)</th>
 <th>Bolsillo (% retail)</th>
 <th>Público / obligatorio (% retail)</th>
 </tr>
 </thead>
 <tbody>
 <tr style={{ fontStyle: 'italic', background: 'rgba(0,0,0,0.03)' }}>
 <td style={{ textAlign: 'left' }}>Promedio OCDE</td>
 <td style={{ textAlign: 'center' }}>{fmtUsd(PROMEDIO_OCDE.perCapitaUsdPpa)}</td>
 <td style={{ textAlign: 'center' }}>{fmtPct(PROMEDIO_OCDE.bolsilloPct)}</td>
 <td style={{ textAlign: 'center' }}>{fmtPct(PROMEDIO_OCDE.publicoPct)}</td>
 </tr>
 {[...DATOS]
 .sort((a, b) => (b.perCapitaUsdPpa ?? -1) - (a.perCapitaUsdPpa ?? -1))
 .map(d => (
 <tr key={d.pais} style={d.esChile ? { fontWeight: 700, background: 'rgba(43,108,176,0.10)' } : undefined}>
 <td style={{ textAlign: 'left' }}>
 <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
 <Flag pais={d.pais} />
 <span>{d.pais}</span>
 {d.cita === 'oecd-grafico' && (
 <span className="note" title="Valor leído del gráfico por país; sujeto a revisión contra la tabla fuente.">
 ◦
 </span>
 )}
 </span>
 </td>
 <td style={{ textAlign: 'center' }}>{fmtUsd(d.perCapitaUsdPpa)}</td>
 <td style={{ textAlign: 'center' }}>{fmtPct(d.bolsilloPct)}</td>
 <td style={{ textAlign: 'center' }}>{fmtPct(d.publicoPct)}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 <p className="note">
 ◦ = valor leído del gráfico de la edición OCDE (redondeado), no del texto
 citado; pendiente de cotejo contra la tabla fuente.
 </p>

 {/* ── Barra: Chile vs distribución OCDE (eje per cápita) ── */}
 <h3>Eje per cápita, Chile en la distribución de la muestra</h3>
 <p className="note">
 Posición sobre el rango de gasto farmacéutico retail per cápita (USD&nbsp;PPA,
 2021) de los países con dato en esta tabla. La banda sombreada es el rango
 intercuartílico (Q1–Q3); la línea, la mediana de la muestra; el rombo, el
 promedio OCDE oficial. Denominador del eje: población residente.
 </p>
 <Caption ch={5} n={5} kind="grafico" title="Posición de Chile en la distribución OCDE del gasto farmacéutico retail per cápita (USD PPA, 2021), con bandera por país" />
 {/* Banderas por país sobre el eje: cada país con dato per cápita se ubica en
 su posición del eje. Chile va resaltado abajo con su marcador propio. */}
 <div style={{ position: 'relative', height: 34, maxWidth: '100%', margin: '6px 0 0' }}>
 {[...DATOS]
 .filter(d => d.perCapitaUsdPpa != null && !d.esChile)
 .map(d => (
 <span
 key={d.pais}
 title={`${d.pais}: US$ ${d.perCapitaUsdPpa!.toLocaleString('es-CL')} per cápita`}
 style={{
 position: 'absolute',
 bottom: 0,
 left: pos(d.perCapitaUsdPpa!),
 transform: 'translateX(-50%)',
 display: 'inline-flex',
 }}
 >
 <Flag pais={d.pais} w={22} />
 </span>
 ))}
 </div>
 <div
 style={{
 position: 'relative',
 height: 64,
 maxWidth: '100%',
 margin: '4px 0 6px',
 background: 'linear-gradient(to right, rgba(0,0,0,0.04), rgba(0,0,0,0.04))',
 borderRadius: 6,
 }}
 role="img"
 aria-label={`Distribución OCDE de gasto farmacéutico per cápita: mínimo ${stats.min}, Q1 ${Math.round(stats.q1)}, mediana ${Math.round(stats.mediana)}, Q3 ${Math.round(stats.q3)}, máximo ${stats.max} USD PPA. Chile en 455.`}
 >
 {/* banda intercuartílica */}
 <div
 style={{
 position: 'absolute',
 top: 0,
 bottom: 0,
 left: pos(stats.q1),
 width: `calc(${pos(stats.q3)} - ${pos(stats.q1)})`,
 background: 'rgba(43,108,176,0.14)',
 borderLeft: '1px dashed rgba(43,108,176,0.5)',
 borderRight: '1px dashed rgba(43,108,176,0.5)',
 }}
 />
 {/* mediana */}
 <div style={{ position: 'absolute', top: 0, bottom: 0, left: pos(stats.mediana), width: 2, background: '#1a365d' }} />
 {/* promedio OCDE oficial (rombo) */}
 <div
 style={{
 position: 'absolute',
 top: '50%',
 left: pos(PROMEDIO_OCDE.perCapitaUsdPpa),
 width: 12,
 height: 12,
 background: '#c53030',
 transform: 'translate(-50%, -50%) rotate(45deg)',
 }}
 title={`Promedio OCDE oficial: US$ ${PROMEDIO_OCDE.perCapitaUsdPpa}`}
 />
 {/* marcador Chile */}
 <div
 style={{
 position: 'absolute',
 top: -6,
 bottom: -6,
 left: pos(455),
 width: 3,
 background: '#2b6cb0',
 }}
 />
 <div
 style={{
 position: 'absolute',
 bottom: -24,
 left: pos(455),
 transform: 'translateX(-50%)',
 fontSize: 12,
 fontWeight: 700,
 color: '#2b6cb0',
 whiteSpace: 'nowrap',
 display: 'inline-flex',
 alignItems: 'center',
 gap: 5,
 }}
 >
 <Flag pais="Chile" w={20} /> Chile · US$ 455
 </div>
 </div>
 <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#666', marginTop: 26 }}>
 <span>US$ 0</span>
 <span>
 Mediana muestra US$ {Math.round(stats.mediana).toLocaleString('es-CL')} · Q1–Q3 US${' '}
 {Math.round(stats.q1).toLocaleString('es-CL')}–{Math.round(stats.q3).toLocaleString('es-CL')}
 </span>
 <span>US$ {escalaMax.toLocaleString('es-CL')}</span>
 </div>

 <div className="card" style={{ marginTop: 18 }}>
 <p style={{ margin: 0 }}>
 <strong>Lectura.</strong> En el eje per cápita Chile (US$&nbsp;455) se ubica
 por debajo de la mediana de esta muestra y del promedio OCDE oficial
 (US$&nbsp;614). En el eje de bolsillo, su 78% es el más alto de los países
 aquí listados, frente a un promedio OCDE de 39%. Los dos ejes son
 independientes: describen, respectivamente, <em>cuánto</em> se gasta por
 persona y <em>cómo se reparte</em> ese gasto entre hogar y aseguramiento;
 un nivel per cápita dado es compatible con repartos muy distintos, compárese
 Canadá (público/obligatorio 40%, seguro voluntario 34%) con Francia
 (público/obligatorio 83%). Toda comparación se restringe al perímetro{' '}
 <CodeRef c="HC.5.1">retail / ambulatorio</CodeRef>; el medicamento
 hospitalario no es separable y queda fuera.
 </p>
 </div>

 <p className="note" style={{ marginTop: 12 }}>
 Fuente: OECD (2023),{' '}
 <a href={FUENTE_URL} target="_blank" rel="noreferrer">
 Health at a Glance 2023, Pharmaceutical expenditure
 </a>
 . Año de referencia 2021; USD&nbsp;PPA. Promedios OCDE citados del texto del
 capítulo (per cápita US$&nbsp;614; bolsillo 39%; público/obligatorio 58%;
 seguro voluntario 3%).
 </p>
 </section>
 )
}
