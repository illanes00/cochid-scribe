import { Link } from 'react-router-dom'
import Caption from '../components/Caption'
import CodeRef from '../components/CodeRef'

// Capítulo 7 · Esqueleto lógico del informe v7.
// Render visual (espina/flujo jerárquico) del documento
// docs/cif-review/output/v6/esqueleto-logico-v7.md: principios rectores,
// datos canónicos, el hilo lógico en tres partes, RE de 3 páginas, secuencia
// de capítulos, anexos, deltas v6→v7 y la coherencia explorador↔informe.
// No es markdown crudo: cada bloque es una sección visual con links a los
// capítulos del explorador (react-router <Link>).

// ── datos del esqueleto (transcritos del v7) ──────────────────────────────

const PRINCIPIOS = [
 { id: 'P1', t: 'Denominador primero', d: 'Ninguna cifra-titular sin su denominador explícito en la misma frase.', o: 'Eduardo + Carla' },
 { id: 'P2', t: '"Cómo se gasta", no "poco vs mucho"', d: 'Se elimina el encuadre "Chile gasta poco". El eje es composición y distribución.', o: 'Eduardo' },
 { id: 'P3', t: 'De-normalizar', d: 'Describir, no prescribir. Sin verbos de deber. El cierre son preguntas, no recomendación.', o: 'Eduardo + reunión' },
 { id: 'P4', t: 'Escenarios → anexo', d: 'El cuerpo no numera trayectorias fiscales; el capítulo de escenarios pasa al Anexo G.', o: 'Eduardo + live' },
 { id: 'P5', t: 'RE de 3 páginas', d: 'El resumen ejecutivo baja de 12–14 pp a 3 pp.', o: 'Directores' },
 { id: 'P6', t: 'Cifras que cuadran', d: 'Una sola verdad de datos, idéntica en RE, cuerpo, anexos, Excel y explorador.', o: 'Carla + mandato' },
]

// Instrumentos DISJUNTOS (aditivos) del gasto público, lado ejecución. El GES público
// y las Drogas de Alto Costo NO son líneas propias: se devengan dentro de la Farmacia
// de los Servicios de Salud y no se suman aparte (sería doble conteo).
const BOLSAS = [
 { i: 'Farmacia de los Servicios de Salud', mm: '736.761', n: 'línea 22.04.004.001 (2023); contiene el GES público y las Drogas de Alto Costo, no se cuentan aparte', est: false },
 { i: 'Ley Ricarte Soto', mm: '175.672', n: 'línea propia y aditiva (ejecución 2025)', est: false },
 { i: 'APS municipal (FOFAR adentro)', mm: '162.613', n: 'gasto comunal en farmacia, SINIM 2023', est: false },
 { i: 'FF.AA. y de Orden', mm: '62.339', n: 'sin fuente única consolidada', est: true },
 { i: 'Judicialización (glosa sub-presupuestada)', mm: '93.594', n: 'ejecución FONASA sentencias 2024 (DIPRES); presupuestado solo 28.914, la ejecución lo desborda', est: false },
 { i: 'PNI (vacunas)', mm: '30.000', n: 'prevención, biológico estricto, NO 176.876 (error previo)', est: false },
]

// Las tres partes del hilo lógico, con sus capítulos del informe y el link al
// capítulo-espejo del explorador.
const HILO = [
 {
 parte: 'PARTE I',
 titulo: 'El problema y su magnitud',
 sub: 'Cuantificación primero · responde "cómo se gasta"',
 tono: 'i',
 caps: [
 { n: 1, t: 'Introducción: el problema público', d: 'Qué cuenta como medicamento (ambulatorio vs hospital) y el doble frente: crónico ambulatorio de alto volumen + alto costo.', to: '/medicamento', toLabel: 'El medicamento' },
 { n: 2, t: 'Qué medimos y con qué denominador', d: 'Marco SHA mínimo (las 4 preguntas HC/HP/HF/FS), la frontera ambulatorio/hospital y por qué el denominador define el 71% vs 62%.', to: '/marco', toLabel: 'Marco SHA' },
 { n: 3, t: 'Cuánto y cómo se gasta hoy', d: 'Composición obligatorio (25,5%) / voluntario (3,5%) / bolsillo (≈71%); los instrumentos disjuntos del gasto público (banda 0,42-0,46% del PIB); judicialización como glosa sub-presupuestada (93.594, 2024).', to: '/instrumentos', toLabel: 'Instrumentos y presupuesto' },
 { n: 4, t: 'Distribución entre hogares', d: 'EPF IX: regresividad (Q1 ~5× Q5), catastrófico ×3 (22,0 / 8,2 / 1,1), dispersión intra-quintil y consumo postergado (29%).', to: '/sintesis', toLabel: 'Síntesis' },
 { n: 5, t: 'Puntos de quiebre del bolsillo', d: 'Los 5–6 quiebres con cuantificación: crónico fuera de GES, no-LRS de alto costo, copago GES sobre umbral, brecha hospitalaria, MLE sin tope, desabastos.', to: '/medicamento', toLabel: 'El medicamento' },
 ],
 },
 {
 parte: 'PARTE II',
 titulo: 'La arquitectura que lo explica',
 sub: 'Zoom institucional · segunda parte',
 tono: 'ii',
 caps: [
 { n: 6, t: 'El sistema chileno: instituciones, instrumentos y coberturas', d: 'Mapa institucional + TODAS las coberturas (FONASA/ISAPRE, GES, LRS, DAC, CAEC, MLE, APS/FOFAR, PNI) + matriz cobertura × subsistema × canal.', to: '/instrumentos', toLabel: 'Instrumentos y presupuesto' },
 { n: 7, t: 'Financiamiento bajo el lente SHA', d: 'Quién paga qué: el modelo biyectivo instrumento↔SHA, HF≠HP, GES = FONASA + ISAPRE-7%. Conciliación CIF/UC ↔ OECD.', to: '/explorador', toLabel: 'Explorar el dataset' },
 ],
 },
 {
 parte: 'PARTE III',
 titulo: 'Mirada comparada y opciones',
 sub: 'Neutral · no-prescriptivo',
 tono: 'iii',
 caps: [
 { n: 8, t: 'Comparación internacional', d: 'Qué observan otros sistemas (lista positiva, ETESA, compras, topes), con denominador explícito y SIN "Chile gasta poco".', to: '/sintesis', toLabel: 'Síntesis y comparación' },
 { n: 9, t: 'Síntesis: dónde está Chile', d: 'Brechas y palancas, descriptivo. Sin radar prescriptivo: "lo que muestran los datos", no "Chile debe".', to: '/sintesis', toLabel: 'Síntesis' },
 { n: 10, t: 'Medidas transversales', d: 'ETESA, compras y transparencia, operativas y por valor sanitario. Biosimilares ≠ genéricos. Sin cronograma prescriptivo.', to: '/instrumentos', toLabel: 'Instrumentos y presupuesto' },
 { n: 11, t: 'Preguntas abiertas y dilemas', d: 'Cierre = 5 preguntas para el taller. No-prescriptivo: "la elección es política y queda abierta".', to: '/sintesis', toLabel: 'Síntesis' },
 ],
 },
]

const ANEXOS = [
 { id: 'G', t: 'Escenarios fiscales', d: 'E0 status quo · E1 intermedio · E2 convergencia · E3 universal · IVA complementario.', delta: 'NUEVO destino: sale del cuerpo al anexo (P4).' },
 { id: 'S', t: 'Marco SHA técnico', d: 'Definiciones SHA, nota CHL de comparabilidad, crosswalk instrumento↔SHA, matrices HC/HP/HF/FS.', delta: 'NUEVO: extraído del explorador + link interactivo.' },
 { id: 'C', t: 'Fichas país', d: 'Tarjetas OECD + contraste LatAm.', delta: 'De v6, sin cambio mayor.' },
 { id: 'B', t: 'Metodología', d: 'SHA, EPF microdato por quintil, catastrófico ×3 (incl. OMS capacidad de pago), conciliación CIF/UC↔OECD.', delta: 'Ampliada con las 3 metodologías catastróficas.' },
 { id: 'D · E', t: 'Normativa · OECD raw', d: 'Detalle normativo y datos OECD crudos.', delta: 'Sin cambio.' },
]

const DELTAS = [
 { mov: 'Cuantificación al inicio', v6: 'Cap 5/6/7 (mitad)', v7: 'Parte I (Cap 3–5)', why: 'live "quiebres + cuantificación al inicio"' },
 { mov: 'Arquitectura como 2ª parte', v6: 'Cap 4 (temprano)', v7: 'Parte II (Cap 6–7)', why: 'live "arquitectura segunda parte"' },
 { mov: 'Marco internacional', v6: 'Cap 2–3 (temprano)', v7: 'Cap 8 (Parte III)', why: 'P2 (no abrir con "gasta poco")' },
 { mov: 'Escenarios', v6: 'Cap 9 (cuerpo)', v7: 'Anexo G', why: 'P4 (Eduardo)' },
 { mov: 'Resumen ejecutivo', v6: '~13 pp', v7: '3 pp', why: 'P5' },
 { mov: 'SHA técnico', v6: 'disperso', v7: 'Anexo S + explorador', why: 'coherencia sitio↔informe' },
 { mov: 'Cifras gasto público', v6: '920k + PNI 176.876', v7: 'banda disjunta 0,42-0,46% PIB (vista-programa 1.514.814 no aditiva)', why: 'reconciliación (P6)' },
 { mov: 'Tono', v6: 'normativo en partes', v7: 'de-normalizado', why: 'P3' },
]

// Coherencia explorador ↔ informe: cada sección viva del explorador y su
// capítulo-espejo, con link a la página correspondiente.
const COHERENCIA = [
 { sec: 'Tabla-resumen del intro (HC×HF + %fila/col)', cap: 'Cap 3 (cómo se gasta)', to: '/', toLabel: 'Inicio' },
 { sec: 'Definiciones (SHA, frontera HC.5.1/HC.1)', cap: 'Cap 2 + Anexo S', to: '/marco', toLabel: 'Marco SHA' },
 { sec: 'Taxonomía de códigos (HC/HP/HF/FS)', cap: 'Anexo S', to: '/marco', toLabel: 'Marco SHA' },
 { sec: 'Comparabilidad Chile (qué reporta / no)', cap: 'Anexo S + Cap 2', to: '/chile', toLabel: 'Cómo cuenta Chile' },
 { sec: 'Desglose del medicamento (ambul. vs hospital)', cap: 'Cap 2 + Cap 5', to: '/medicamento', toLabel: 'El medicamento' },
 { sec: 'Explorador pivote (cubo HC×HF)', cap: 'Anexo S + Cap 7', to: '/explorador', toLabel: 'Explorar el dataset' },
 { sec: 'Mosaico (Marimekko, 3 cortes)', cap: 'Cap 3 + Cap 7', to: '/explorador', toLabel: 'Explorar el dataset' },
 { sec: 'Instrumentos y dimensiones (biyectivo)', cap: 'Cap 6 + Cap 7', to: '/instrumentos', toLabel: 'Instrumentos' },
 { sec: 'Gráficos (gasto público, quintiles, quién paga)', cap: 'Cap 3 + Cap 4', to: '/instrumentos', toLabel: 'Instrumentos' },
]

export default function CapEsqueleto() {
 return (
 <section id="esqueleto">
 {/* Estilos propios de esta página (prefijo esq-) para la espina/flujo y la
 lista del RE. No tocan clases compartidas de index.css. */}
 <style>{`
 .esq-spine{display:flex;flex-direction:column;gap:14px;margin:16px 0;max-width:100%}
 .esq-part{border:1px solid var(--bd);border-radius:12px;overflow:hidden;background:#fcfcfd}
 .esq-part.esq-i{border-left:5px solid var(--ep)}
 .esq-part.esq-ii{border-left:5px solid var(--ep2)}
 .esq-part.esq-iii{border-left:5px solid var(--red)}
 .esq-part.esq-anexo{border-left:5px solid #94a3b8;border-style:dashed}
 .esq-head{padding:12px 16px;border-bottom:1px solid #eef0f3;display:flex;flex-direction:column;gap:2px}
 .esq-anexo .esq-head{border-bottom:0}
 .esq-kicker{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#98a2b3;font-weight:700}
 .esq-ptitle{font-size:17px;font-weight:700;color:var(--ep);line-height:1.2}
 .esq-psub{font-size:12.5px;color:var(--muted)}
 .esq-list{list-style:none;margin:0;padding:8px 12px 12px;display:flex;flex-direction:column;gap:8px}
 .esq-step{display:flex;gap:12px;align-items:flex-start;padding:8px 10px;border-radius:9px;background:#fff;border:1px solid #eef0f3}
 .esq-num{flex:none;width:26px;height:26px;border-radius:50%;background:var(--ep);color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
 .esq-ii .esq-num{background:var(--ep2)}
 .esq-iii .esq-num{background:var(--red)}
 .esq-body{display:flex;flex-direction:column;gap:2px;min-width:0}
 .esq-step-title{font-size:14.5px;font-weight:700;color:var(--ep);line-height:1.3}
 .esq-step-desc{font-size:12.5px;color:#475467;line-height:1.45}
 .esq-step-link{font-size:12px;font-weight:600;color:var(--ep2);text-decoration:none;margin-top:2px}
 .esq-step-link:hover{text-decoration:underline}
 .esq-re-list{margin:10px 0;padding-left:22px;max-width:100%}
 .esq-re-list li{margin:7px 0;font-size:14px;line-height:1.55}
 @media(max-width:600px){.esq-step{flex-wrap:wrap}}
 `}</style>
 <header>
 <h1 className="ptitle">Esqueleto lógico del informe</h1>
 <p className="psub">
 El hilo argumental completo del informe CIF-EP v7 «Inclusión sostenible de
 medicamentos en los planes de salud en Chile»: la columna vertebral que sincroniza
 el TOC, el feedback de directores, las cifras reconciliadas y este explorador.
 </p>
 </header>

 <div className="card">
 <b>Cómo leer esta página.</b> No es prosa: es la <b>espina argumental</b> del informe.
 De arriba abajo: los <b>principios rectores</b> que gobiernan todo el v7, los{' '}
 <b>datos canónicos</b> (única fuente de verdad), el <b>hilo lógico en tres partes</b>{' '}
 , con links al capítulo-espejo del explorador, el <b>resumen ejecutivo</b>, los{' '}
 <b>anexos</b>, los <b>deltas v6→v7</b> y la tabla de <b>coherencia explorador↔informe</b>.{' '}
 <span className="note">Versión v7.0 · 2026-05-28.</span>
 </div>

 {/* ── 1 · Principios rectores ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 1 · Principios rectores
 </h2>
 <p className="lead" style={{ fontSize: 16 }}>
 Seis principios, cada uno anclado a un input concreto de los directores o del feedback
 en vivo, gobiernan todas las decisiones estructurales del v7.
 </p>
 <div className="cardgrid">
 {PRINCIPIOS.map(p => (
 <div key={p.id} className="navcard" style={{ cursor: 'default' }}>
 <span className="navcard-num">{p.id} · {p.o}</span>
 <span className="navcard-title">{p.t}</span>
 <span className="navcard-blurb">{p.d}</span>
 </div>
 ))}
 </div>

 {/* ── 2 · Datos canónicos ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 2 · Datos canónicos (única fuente de verdad)
 </h2>
 <p className="lead" style={{ fontSize: 16 }}>
 Verificados celda a celda y reflejados en este explorador. Regla: los MM$ CLP nunca se
 mezclan con %PIB sin GDP explícito; el USD PPA es del año base 2022.
 </p>

 <div className="grid2">
 <div className="card">
 <b className="big" style={{ fontSize: 22 }}>≈71%</b> bolsillo (HF.3) ·{' '}
 <b>25,5%</b> obligatorio (HF.1) · <b>3,5%</b> voluntario (HF.2)
 <p className="note" style={{ marginBottom: 0, marginTop: 6 }}>
 Composición del <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> (OECD SHA 2022).
 Total HC.5.1 = <b>3.518.751 MM$</b> (1,34% del PIB) = 13,4% del gasto corriente en salud.
 Denominador: HC.5.1, todos los canales.
 </p>
 </div>
 <div className="card warn">
 <b className="big" style={{ fontSize: 22 }}>≈62%</b> bolsillo sobre el total
 <p className="note" style={{ marginBottom: 0, marginTop: 6 }}>
 Perímetro CIF, con el fármaco hospitalario embebido en <CodeRef c="HC.1" /> (no separable;{' '}
 <CodeRef c="HC.RI.1" /> = Missing). <b>No es celda directa OECD</b>: el intrahospitalario se
 <b> acota</b> a una banda de <b>250.000–725.000</b> (central ~485.000); el punto de cuadre
 algebraico (público total − ambulatorio público − PNI ≈ 246.000) sólo cierra la contabilidad
 , el cierre es algebraico, un marco que acota, no una prueba.
 </p>
 </div>
 </div>

 <Caption ch={7} n={1} kind="tabla" title="Gasto público en medicamentos: las ocho bolsas presupuestarias (MM$ CLP 2024)" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '46%' }} />
 <col style={{ width: '20%' }} />
 <col style={{ width: '34%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Instrumento</th>
 <th>MM$ CLP</th>
 <th>Nota</th>
 </tr>
 </thead>
 <tbody>
 {BOLSAS.map(b => (
 <tr key={b.i}>
 <td>{b.i}</td>
 <td className="num">{b.mm}</td>
 <td style={{ textAlign: 'left' }} className={b.est ? 'est' : undefined}>{b.n}</td>
 </tr>
 ))}
 <tr className="tot">
 <td>TOTAL gasto público (banda disjunta)</td>
 <td className="num">1,1 a 1,2 bill.</td>
 <td style={{ textAlign: 'left' }}>≈ 0,42% a 0,46% del PIB · suma de instrumentos disjuntos (lado ejecución), converge con el 0,46% del estudio CIF/UC. El GES público y las Drogas de Alto Costo NO se suman aparte: están dentro de la Farmacia de los Servicios de Salud.</td>
 </tr>
 </tbody>
 </table>
 </div>
 <p className="note">
 Cambio metodológico: la vista-programa de ocho instrumentos (que daba 1.514.814 MM$) no es un
 total aditivo. Sumaba la financiación FONASA (transferencias) y la ejecución de los Servicios de
 Salud, que son las dos caras de la misma plata, y contaba el GES público y las Drogas de Alto
 Costo aparte cuando ya están dentro de la Farmacia. Corregido el doble conteo (del orden de
 400.000 MM$), el gasto público disjunto cae en la banda de 1,1 a 1,2 billones de pesos (0,42% a
 0,46% del PIB), que converge con el 0,46% del estudio CIF/UC. PNI 30k (biológico estricto).
 </p>

 <Caption ch={7} n={2} kind="tabla" title="Distribución entre hogares: regresividad y gasto catastrófico (EPF IX, INE)" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '40%' }} />
 <col style={{ width: '24%' }} />
 <col style={{ width: '36%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Métrica</th>
 <th>Valor</th>
 <th>Definición / caveat</th>
 </tr>
 </thead>
 <tbody>
 <tr>
 <td>Carga regresiva (Q1 vs Q5)</td>
 <td className="num">~9,8% vs ~1,9% (≈5×)</td>
 <td style={{ textAlign: 'left' }}>% del ingreso per cápita a medicamentos. Declarar base usada.</td>
 </tr>
 <tr>
 <td>Catastrófico, variante informe</td>
 <td className="num">22,0% (≈953 mil hogares)</td>
 <td style={{ textAlign: 'left' }}>&gt;10% del ingreso per cápita.</td>
 </tr>
 <tr>
 <td>Catastrófico, ODS 3.8.2</td>
 <td className="num">8,2% (&gt;25%: 2,2%)</td>
 <td style={{ textAlign: 'left' }}>&gt;10% del ingreso total.</td>
 </tr>
 <tr>
 <td>Catastrófico, OMS capacidad de pago</td>
 <td className="num">1,1% (6,0% toda la salud)</td>
 <td style={{ textAlign: 'left' }}>&gt;40% del consumo neto de subsistencia.</td>
 </tr>
 <tr>
 <td>Consumo postergado</td>
 <td className="num">29%</td>
 <td style={{ textAlign: 'left' }}>Declaró dejar dosis por costo (Ipsos–EP 2025) → las cifras EPF son piso.</td>
 </tr>
 </tbody>
 </table>
 </div>

 {/* ── 3 · El hilo lógico ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 3 · El hilo lógico (la columna vertebral)
 </h2>
 <p className="lead" style={{ fontSize: 16 }}>
 El v7 abre con la <b>magnitud del problema</b> (cuánto, cómo, distribución, quiebres) y
 recién después entra a la <b>arquitectura institucional</b>. Cada capítulo enlaza con su
 capítulo-espejo en este explorador.
 </p>

 <div className="esq-spine">
 {HILO.map(parte => (
 <div key={parte.parte} className={`esq-part esq-${parte.tono}`}>
 <div className="esq-head">
 <span className="esq-kicker">{parte.parte}</span>
 <span className="esq-ptitle">{parte.titulo}</span>
 <span className="esq-psub">{parte.sub}</span>
 </div>
 <ol className="esq-list">
 {parte.caps.map(c => (
 <li key={c.n} className="esq-step">
 <span className="esq-num">{c.n}</span>
 <div className="esq-body">
 <span className="esq-step-title">{c.t}</span>
 <span className="esq-step-desc">{c.d}</span>
 <Link to={c.to} className="esq-step-link">→ {c.toLabel}</Link>
 </div>
 </li>
 ))}
 </ol>
 </div>
 ))}
 <div className="esq-part esq-anexo">
 <div className="esq-head">
 <span className="esq-kicker">ANEXOS</span>
 <span className="esq-ptitle">G · C · S · B · D · E</span>
 <span className="esq-psub">Escenarios fuera del cuerpo · SHA técnico desde el explorador</span>
 </div>
 </div>
 </div>

 {/* ── 4 · Resumen ejecutivo ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 4 · Resumen ejecutivo (3 páginas, no-normativo)
 </h2>
 <ol className="esq-re-list">
 <li>
 <b>Caja de 3 cifras (con denominador):</b> (a) composición del ambulatorio,
 bolsillo ≈71% / obligatorio 25,5% / voluntario 3,5%, sobre HC.5.1; (b) carga desigual,
 Q1 ~5× Q5, ~973 mil hogares (22,0%) sobre el umbral del 10% del ingreso per cápita;
 (c) el medicamento es una de las principales causas de gasto de bolsillo en salud.
 </li>
 <li><b>Qué medimos y con qué denominador.</b> Ambulatorio medible en SHA + hospitalario no separable; el 71% es sobre el ambulatorio, el 62% sobre el total estimado (no OECD).</li>
 <li><b>Cómo se gasta hoy.</b> Composición + instrumentos disjuntos (banda 0,42-0,46% del PIB) + judicialización como glosa sub-presupuestada. Descriptivo.</li>
 <li><b>Distribución entre hogares.</b> Regresividad, catastrófico (3 métricas declaradas), consumo postergado.</li>
 <li><b>Puntos de quiebre del bolsillo.</b> Tabla de 5 puntos.</li>
 <li><b>Qué observa la comparación internacional.</b> Componentes que otros sistemas usan, con denominador y SIN "Chile gasta poco". Neutral.</li>
 <li><b>Cierre = preguntas abiertas para el taller.</b> Sin recomendación ni escenarios numerados.</li>
 </ol>
 <p className="note">
 Guardrails: ≤3 pp · 0 normativo · 0 escenarios numerados · primer párrafo con
 composición + denominador · «Cifras que lo respaldan» (no «Evidencia clave / bloqueado»).
 </p>

 {/* ── 5 · Anexos ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 5 · Anexos
 </h2>
 <Caption ch={7} n={3} kind="tabla" title="Anexos v7 y su cambio respecto del v6" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '10%' }} />
 <col style={{ width: '22%' }} />
 <col style={{ width: '38%' }} />
 <col style={{ width: '30%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Anexo</th>
 <th>Título</th>
 <th>Contenido</th>
 <th>Cambio vs v6</th>
 </tr>
 </thead>
 <tbody>
 {ANEXOS.map(a => (
 <tr key={a.id}>
 <td style={{ textAlign: 'center', fontWeight: 700, color: 'var(--ep)' }}>{a.id}</td>
 <td style={{ textAlign: 'left' }}>{a.t}</td>
 <td style={{ textAlign: 'left' }}>{a.d}</td>
 <td style={{ textAlign: 'left' }} className="note">{a.delta}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {/* ── 6 · Deltas v6 → v7 ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 6 · Mapa v6 → v7 (deltas estructurales)
 </h2>
 <Caption ch={7} n={4} kind="tabla" title="Movimientos estructurales del v6 al v7 y su motivo" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '24%' }} />
 <col style={{ width: '22%' }} />
 <col style={{ width: '24%' }} />
 <col style={{ width: '30%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Movimiento</th>
 <th>v6</th>
 <th>v7</th>
 <th>Motivo</th>
 </tr>
 </thead>
 <tbody>
 {DELTAS.map(d => (
 <tr key={d.mov}>
 <td style={{ textAlign: 'left' }}>{d.mov}</td>
 <td style={{ textAlign: 'left' }} className="note">{d.v6}</td>
 <td style={{ textAlign: 'left', fontWeight: 600 }}>{d.v7}</td>
 <td style={{ textAlign: 'left' }} className="note">{d.why}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {/* ── 7 · Coherencia explorador ↔ informe ── */}
 <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>
 7 · Coherencia explorador ↔ informe
 </h2>
 <p className="lead" style={{ fontSize: 16 }}>
 Una sola verdad: cada sección viva de este explorador es el espejo de un capítulo o anexo
 del informe. Regla de oro: si una cifra cambia, cambia en los datos del explorador <b>y</b>{' '}
 en el informe a la vez.
 </p>
 <Caption ch={7} n={5} kind="tabla" title="Mapeo sección del explorador → capítulo del informe v7" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '46%' }} />
 <col style={{ width: '30%' }} />
 <col style={{ width: '24%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Sección del explorador</th>
 <th>Capítulo / anexo v7</th>
 <th>Ir a</th>
 </tr>
 </thead>
 <tbody>
 {COHERENCIA.map(c => (
 <tr key={c.sec}>
 <td style={{ textAlign: 'left' }}>{c.sec}</td>
 <td style={{ textAlign: 'left' }}>{c.cap}</td>
 <td style={{ textAlign: 'left' }}>
 <Link to={c.to}>{c.toLabel}</Link>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 <div className="card teaser" style={{ marginTop: 28 }}>
 Este esqueleto cierra el recorrido. Para empezar por el vocabulario, vuelve al{' '}
 <Link to="/marco"><b>Marco SHA</b></Link>; para los números crudos, entra al{' '}
 <Link to="/explorador"><b>explorador del dataset</b></Link>.
 </div>
 </section>
 )
}
