import { useMemo, useState } from 'react'
import { BarList, StackedBar, CertPill, HIER_BAR_CSS, type BarItem } from '../components/HierBar'
import {
  T1, ANCLA, FILTROS, FILTRO_A, FILTRO_B, FILTRO_C, GT, pctGT,
  T4, NUCLEO_PUBLICO, NUCLEO_TOTAL, NUCLEO_PIB, BANDA_PIB, ANIOS_PUBLICO,
  FUERA_DEL_NUCLEO, FARMACIA_2024, FARMACIA_NIVEL, FARMACIA_PROVISION,
  T5, CARGA_QUINTIL, T6, T7, JUDICIAL_PUBLICO, JUDICIAL_NOTA, COBERTURA_FUERA, T8,
} from '../data/hierarchy'

const fInt = (v: number) => Math.round(v).toLocaleString('es-CL')
const fPct = (v: number) => v.toFixed(1).replace('.', ',') + '%'

// Página 1 · LA JERARQUÍA ÚNICA, ordenada por los OCHO títulos del documento.
// El gasto total ancla arriba (sticky) como 100%. Tres filtros lo reparten, un
// zoom abre el lado público disjunto con selector de año. Cada vista trae su año
// y su fuente. Solo barras, sin jerga de códigos, cero em-dash.
export default function CapJerarquia() {
  const [filtro, setFiltro] = useState<'A' | 'B' | 'C'>('A')
  const [anio, setAnio] = useState<number>(2024)

  const F = filtro === 'A' ? FILTRO_A : filtro === 'B' ? FILTRO_B : FILTRO_C
  // Solo el filtro A reparte el gasto total entero. B y C reparten el
  // ambulatorio, así que cada pieza muestra también su % del gasto total.
  const baseEsGT = F.base === GT
  const items: BarItem[] = F.piezas.map(p => ({
    label: p.label, sub: p.sub, mm: p.mm, cert: p.cert, fuente: p.fuente, color: p.color,
  }))

  const nucleoTot = NUCLEO_TOTAL[anio]
  const nucleoItems: BarItem[] = useMemo(() => NUCLEO_PUBLICO.map(n => ({
    label: n.label, sub: n.sub, mm: n.mm[anio], cert: n.cert, fuente: n.fuente, color: n.color,
  })), [anio])

  const cargaMax = Math.max(...CARGA_QUINTIL.quintiles.map(q => q.value))
  const judMax = Math.max(...JUDICIAL_PUBLICO.map(j => j.mm))

  return (
    <section id="jerarquia">
      <style>{`
        ${HIER_BAR_CSS}
        /* Encabezado de cada título-afirmación */
        .jq-h{display:flex;align-items:baseline;gap:10px;margin:36px 0 4px}
        .jq-h-num{flex:none;width:30px;height:30px;border-radius:8px;background:var(--ep);color:#fff;
          font-size:15px;font-weight:800;display:flex;align-items:center;justify-content:center}
        .jq-h-t{font-size:21px;font-weight:800;color:var(--ep);line-height:1.22;margin:0}
        .jq-bajada{font-size:15.5px;color:#344054;line-height:1.55;margin:6px 0 4px}
        /* Ancla nivel 0 (sticky bajo la topbar) */
        .jq-anchor{position:sticky;top:60px;z-index:20;background:#fff;border:1px solid var(--bd);
          border-left:5px solid var(--ep);border-radius:12px;padding:14px 18px;margin:10px 0 8px;
          box-shadow:0 2px 10px rgba(16,24,40,.05)}
        .jq-anchor-k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#98a2b3;font-weight:700}
        .jq-anchor-t{font-size:17px;font-weight:700;color:var(--ep);line-height:1.25;margin:2px 0}
        .jq-anchor-big{font-size:26px;font-weight:800;color:var(--ep)}
        .jq-anchor-row{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;margin-top:4px}
        .jq-anchor-meta{font-size:12px;color:var(--muted)}
        .jq-anchor-100{display:inline-block;background:var(--ep);color:#fff;border-radius:8px;
          padding:2px 10px;font-size:14px;font-weight:800;margin-left:6px}
        /* Tabs de filtros nivel 1 */
        .jq-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}
        .jq-tab{flex:1 1 200px;text-align:left;border:1px solid var(--bd);border-radius:11px;
          padding:11px 14px;background:#fcfcfd;cursor:pointer;transition:background .12s,border-color .12s}
        .jq-tab:hover{background:#f2f6fb}
        .jq-tab.on{background:#eaf2fb;border-color:#9cc1ec;box-shadow:inset 0 0 0 1px #9cc1ec}
        .jq-tab-k{font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;color:#98a2b3;font-weight:700}
        .jq-tab-q{display:block;font-size:15px;font-weight:700;color:var(--ep);line-height:1.2;margin-top:2px}
        .jq-tab-d{display:block;font-size:11.5px;color:var(--muted);line-height:1.4;margin-top:3px}
        .jq-panel{border:1px solid var(--bd);border-radius:12px;padding:16px 18px;background:#fff;margin-top:6px}
        .jq-panel-base{font-size:12.5px;color:#475467;margin:0 0 12px}
        .jq-panel-base b{color:var(--ep)}
        /* Regla de suma (una sola vez) */
        .jq-rule{display:flex;gap:11px;align-items:flex-start;background:var(--amber);
          border:1px solid #f6d98a;border-radius:11px;padding:12px 15px;margin:16px 0;color:var(--amber-ink)}
        .jq-rule-ico{font-size:18px;line-height:1.2}
        .jq-rule b{color:var(--amber-ink)}
        /* Selector de año */
        .jq-yearbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:8px 0 14px}
        .jq-yearbar .lab{font-size:12px;font-weight:700;color:var(--ep)}
        .jq-year{border:1px solid var(--bd);background:#fff;color:var(--ep);border-radius:8px;
          padding:5px 14px;font-size:13px;font-weight:600;cursor:pointer}
        .jq-year.on{background:var(--ep);color:#fff;border-color:var(--ep)}
        /* Caja de núcleo público */
        .jq-core{border:1px solid var(--bd);border-left:5px solid var(--ep2);border-radius:12px;
          padding:16px 18px;background:#fcfcfd;margin:10px 0}
        .jq-core-tot{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;
          border-top:2px solid #e4e7ec;margin-top:8px;padding-top:10px}
        .jq-core-tot .big{font-size:24px}
        /* Filas mini (farmacia, carga, catastrófico, judicial) */
        .jq-mini{display:flex;flex-direction:column;gap:7px;margin:8px 0}
        .jq-mini-row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}
        .jq-mini-lab{font-size:12.5px;color:#344054}
        .jq-mini-track{grid-column:1 / -1;height:13px;background:#eef2f7;border-radius:4px;overflow:hidden}
        .jq-mini-fill{height:100%;border-radius:4px}
        /* Preguntas abiertas */
        .jq-q{display:flex;gap:11px;align-items:flex-start;padding:11px 0;border-top:1px solid var(--bd)}
        .jq-q:first-child{border-top:none}
        .jq-q-n{flex:none;width:24px;height:24px;border-radius:50%;background:#eaf2fb;color:var(--ep);
          font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center}
        .jq-q-t{font-size:14.5px;color:#1d2939;line-height:1.5}
        @media(max-width:700px){.jq-anchor{top:54px}.jq-tab{flex-basis:100%}}
      `}</style>

      <header>
        <h1 className="ptitle">La jerarquía del gasto en medicamentos</h1>
        <p className="psub">
          Una sola estructura, la misma del informe y del Excel de cifras, ordenada por los ocho
          títulos del documento. Arriba, el gasto total como ancla del 100%. Cada cifra trae su año
          y su fuente, y dice si es un dato o una estimación.
        </p>
      </header>

      {/* ── TÍTULO 1 ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T1.num}</span>
        <h2 className="jq-h-t">{T1.titulo}</h2>
      </div>
      <p className="jq-bajada">{T1.bajada}</p>
      <div className="card">
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          {T1.puntos.map((p, i) => (
            <li key={i} style={{ marginBottom: 4, fontSize: 14, lineHeight: 1.5 }}>{p}</li>
          ))}
        </ul>
        <span className="note">Versión jerarquía única, copiada del diccionario congelado · 2026-06-04.</span>
      </div>

      {/* ── TÍTULO 2 · ANCLA (sticky) ── */}
      <div className="jq-h">
        <span className="jq-h-num">{ANCLA.num}</span>
        <h2 className="jq-h-t">{ANCLA.titulo}</h2>
      </div>
      <p className="jq-bajada">{ANCLA.bajada}</p>

      <div className="jq-anchor">
        <span className="jq-anchor-k">El punto de partida</span>
        <div className="jq-anchor-t">
          {ANCLA.tituloCorto}
          <span className="jq-anchor-100">= 100%</span>
        </div>
        <div className="jq-anchor-row">
          <span className="jq-anchor-big">{ANCLA.pibTitular}</span>
          <span className="jq-anchor-meta">
            {ANCLA.pesos} · banda {fInt(ANCLA.mmLo)} a {fInt(ANCLA.mmHi)} millones de pesos · año {ANCLA.anio}
          </span>
        </div>
        <p className="jq-anchor-meta" style={{ marginTop: 6, marginBottom: 0 }}>
          {ANCLA.nota} <span className="hb-src">Fuente: {ANCLA.fuente}.</span>
        </p>
      </div>

      <div className="card">
        <b>Cómo leer esta página.</b> Todo lo que sigue es una fracción del 100% de arriba, que
        queda fijo mientras te desplazas. Los <b>tres filtros</b> reparten ese gasto de tres formas:
        para qué se usa, quién lo paga y por dónde llega. Cambia de filtro con los botones.
      </div>

      {/* Regla de suma (una sola vez) */}
      <div className="jq-rule">
        <span className="jq-rule-ico" aria-hidden>⚖</span>
        <span>
          <b>Regla de suma.</b> Dentro de un mismo filtro las piezas suman 100%. Entre filtros
          distintos no se suman: es el mismo gasto visto de otra manera. Sumar dos filtros contaría
          el mismo medicamento dos veces.
        </span>
      </div>

      {/* NIVEL 1 · FILTROS */}
      <div className="jq-tabs" role="tablist">
        {FILTROS.map(f => (
          <button
            key={f.id}
            role="tab"
            aria-selected={filtro === f.id}
            className={'jq-tab' + (filtro === f.id ? ' on' : '')}
            onClick={() => setFiltro(f.id as 'A' | 'B' | 'C')}
          >
            <span className="jq-tab-k">Filtro {f.id}</span>
            <span className="jq-tab-q">{f.pregunta}</span>
            <span className="jq-tab-d">{f.resumen}</span>
          </button>
        ))}
      </div>

      <div className="jq-panel" role="tabpanel">
        <p className="jq-panel-base">
          Base de este filtro: <b>{F.baseLabel}</b> ({fInt(F.base)} millones de pesos, año {F.anio}).
          {baseEsGT
            ? ' Es el gasto total, así que estas piezas reparten el 100% del ancla.'
            : ' El gasto total se reparte por el filtro A; este filtro abre solo el tramo ambulatorio, por eso cada pieza muestra también su tamaño respecto del gasto total.'}
        </p>

        <BarList
          items={items}
          base={F.base}
          gtPct={baseEsGT ? undefined : pctGT}
        />

        {/* En el filtro B aparece el TÍTULO 3 (el hogar como principal pagador) */}
        {filtro === 'B' && (
          <div style={{ marginTop: 16 }}>
            <div className="jq-h" style={{ marginTop: 8 }}>
              <span className="jq-h-num">3</span>
              <h3 className="jq-h-t" style={{ fontSize: 18 }}>El hogar es el principal pagador: el 71% del medicamento ambulatorio sale del bolsillo</h3>
            </div>
            <p className="note" style={{ marginTop: 2 }}>
              Las mismas piezas agrupadas en dos cajas sobre el medicamento ambulatorio: lo público
              obligatorio frente a lo privado, que es sobre todo bolsillo.
            </p>
            <StackedBar segs={FILTRO_B.resumenPubPriv} />
            <p className="note" style={{ marginTop: 6 }}>{FILTRO_B.notaBolsillo}</p>
          </div>
        )}

        {/* Nota de canal del filtro C */}
        {filtro === 'C' && (
          <p className="note" style={{ marginTop: 4 }}>
            La farmacia comercial concentra cerca de la mitad del medicamento ambulatorio; el resto
            se entrega por el hospital a pacientes externos y por la atención primaria municipal.
          </p>
        )}
      </div>
      {filtro !== 'B' && (
        <p className="note" style={{ marginTop: 6 }}>
          Abre el filtro <b>¿Quién paga?</b> para ver cómo el bolsillo de los hogares paga el 71% del
          medicamento ambulatorio (título 3 del documento).
        </p>
      )}

      {/* ── TÍTULO 4 · ZOOM al público disjunto ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T4.num}</span>
        <h2 className="jq-h-t">{T4.titulo}</h2>
      </div>
      <p className="jq-bajada">{T4.bajada}</p>
      <p className="lead" style={{ fontSize: 15 }}>
        El financiamiento obligatorio del filtro anterior se puede medir también por presupuesto,
        sumando líneas que no se solapan. Esta es la única vista donde las piezas <b>sí se suman</b>:
        cada peso entra una sola vez. El resultado es <b>{BANDA_PIB}</b>.
      </p>

      <div className="jq-yearbar">
        <span className="lab">Año</span>
        {ANIOS_PUBLICO.map(y => (
          <button key={y} className={'jq-year' + (anio === y ? ' on' : '')} onClick={() => setAnio(y)}>
            {y}
          </button>
        ))}
        <span className="note">Vista de ejecución presupuestaria. Cambia el año para ver cada cifra.</span>
      </div>

      <div className="jq-core">
        <h3 style={{ fontSize: 14.5, margin: '0 0 4px' }}>
          Núcleo público trazable · {anio} <CertPill cert="real" />
        </h3>
        <p className="note" style={{ marginTop: 0 }}>
          Cuatro piezas con perímetros distintos que sí se suman. La barra muestra el peso de cada
          una dentro del núcleo público.
        </p>
        <BarList items={nucleoItems} base={nucleoTot} />
        <div className="jq-core-tot">
          <b className="big">{fInt(nucleoTot)}</b>
          <span>millones de pesos = <b>{NUCLEO_PIB[anio]}</b> ({anio})</span>
          <span className="note">
            Suma de las cuatro piezas, con el hospital público ya incluido. El estudio CIF de la
            Universidad Católica lo estima en 0,46% del PIB por el método de cuentas de la OCDE, el
            mismo orden de magnitud.
          </span>
        </div>
      </div>

      {/* Cómo se abre la línea de Farmacia */}
      <h3 className="ptitle" style={{ fontSize: 18, marginTop: 26 }}>
        Dentro de la Farmacia de los Servicios de Salud
      </h3>
      <p className="lead" style={{ fontSize: 15 }}>
        La pieza mayor del núcleo ({fInt(FARMACIA_2024)} millones en 2024) se puede abrir de dos
        maneras. Las proporciones vienen de otras vistas oficiales, por eso se rotulan con su fuente.
      </p>
      <div className="grid2">
        <div className="card" style={{ borderLeftColor: 'var(--ep2)' }}>
          <b>Por dónde se usa</b>
          <div className="jq-mini">
            {FARMACIA_NIVEL.map(n => (
              <div key={n.label}>
                <div className="jq-mini-row">
                  <span className="jq-mini-lab">{n.label} <CertPill cert={n.cert} /></span>
                  <span className="note"><b>{fPct(n.pct)}</b> · {fInt(n.mm)}</span>
                </div>
                <div className="jq-mini-track">
                  <div className="jq-mini-fill" style={{ width: n.pct + '%', background: n.cert === 'estimacion' ? '#f59e0b' : 'var(--ep2)' }} />
                </div>
                <span className="note">Fuente: {n.fuente}.</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card" style={{ borderLeftColor: 'var(--ep2)' }}>
          <b>De dónde llega</b>
          <div className="jq-mini">
            {FARMACIA_PROVISION.map(n => (
              <div key={n.label}>
                <div className="jq-mini-row">
                  <span className="jq-mini-lab">{n.label} <CertPill cert={n.cert} /></span>
                  <span className="note"><b>{fPct(n.pct)}</b> · {fInt(n.mm)}</span>
                </div>
                <div className="jq-mini-track">
                  <div className="jq-mini-fill" style={{ width: n.pct + '%', background: 'var(--ep)' }} />
                </div>
                <span className="note">Fuente: {n.fuente}.</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="card warn" style={{ marginTop: 6 }}>
        El medicamento del GES público y el de alto costo ya están dentro de esta línea de Farmacia.
        No se suman aparte: hacerlo sería contar dos veces el mismo gasto.
      </div>

      {/* Lo que NO entra al núcleo (y por qué) */}
      <h3 className="ptitle" style={{ fontSize: 18, marginTop: 26 }}>
        Lo que no entra al núcleo (y por qué)
      </h3>
      <p className="lead" style={{ fontSize: 15 }}>
        Estos montos miran el mismo gasto desde otro ángulo, o ya están contados adentro. Se muestran
        como contexto, nunca como suma.
      </p>
      <div className="tablewrap">
        <table>
          <colgroup>
            <col style={{ width: '28%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '42%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Componente</th>
              <th>Monto (millones)</th>
              <th>Dato</th>
              <th>Por qué no se suma al núcleo</th>
            </tr>
          </thead>
          <tbody>
            {FUERA_DEL_NUCLEO.map(f => (
              <tr key={f.label}>
                <td style={{ textAlign: 'left' }}>
                  <b>{f.label}</b>
                  <span className="note" style={{ display: 'block' }}>{f.sub}</span>
                </td>
                <td className="num">{f.mm ? fInt(f.mm) : f.banda}</td>
                <td style={{ textAlign: 'center' }}>
                  <CertPill cert={f.cert} />
                </td>
                <td style={{ textAlign: 'left' }} className="note">
                  {f.razon} <span style={{ fontStyle: 'italic' }}>Fuente: {f.fuente}.</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── TÍTULO 5 · carga por quintil ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T5.num}</span>
        <h2 className="jq-h-t">{T5.titulo}</h2>
      </div>
      <p className="jq-bajada">
        El bolsillo del filtro <b>¿Quién paga?</b> no pesa igual en todos los hogares. El quintil de
        menos ingreso destina una parte mucho mayor de su presupuesto a los medicamentos.
      </p>
      <div className="card" style={{ borderLeftColor: 'var(--red)' }}>
        <div className="jq-mini">
          {CARGA_QUINTIL.quintiles.map(q => (
            <div key={q.q}>
              <div className="jq-mini-row">
                <span className="jq-mini-lab">{q.q}</span>
                <span className="note"><b>{fPct(q.value)}</b> del ingreso</span>
              </div>
              <div className="jq-mini-track">
                <div className="jq-mini-fill" style={{ width: (q.value / cargaMax) * 100 + '%', background: q.color }} />
              </div>
            </div>
          ))}
        </div>
        <p className="note" style={{ marginTop: 8, marginBottom: 0 }}>
          {CARGA_QUINTIL.nota} <span className="hb-src">Año {CARGA_QUINTIL.anio}. Fuente: {CARGA_QUINTIL.fuente}.</span>
        </p>
      </div>

      {/* ── TÍTULO 6 · catastrófico ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T6.num}</span>
        <h2 className="jq-h-t">{T6.titulo}</h2>
      </div>
      <p className="jq-bajada">{T6.bajada}</p>
      <div className="card" style={{ borderLeftColor: 'var(--ep)' }}>
        <div className="jq-mini">
          {T6.items.map(it => (
            <div key={it.label}>
              <div className="jq-mini-row">
                <span className="jq-mini-lab">{it.label}</span>
                <span className="note"><b>{fPct(it.pct)}</b> · {it.hogares}</span>
              </div>
              <div className="jq-mini-track">
                <div className="jq-mini-fill" style={{ width: (it.pct / 6.5) * 100 + '%', background: it.color }} />
              </div>
            </div>
          ))}
        </div>
        <p className="note" style={{ marginTop: 8, marginBottom: 0 }}>
          {T6.nota} <span className="hb-src">Año {T6.anio}. Fuente: {T6.fuente}.</span>
        </p>
      </div>

      {/* ── TÍTULO 7 · cobertura y judicialización ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T7.num}</span>
        <h2 className="jq-h-t">{T7.titulo}</h2>
      </div>
      <p className="jq-bajada">{T7.bajada}</p>

      <div className="card" style={{ borderLeftColor: 'var(--red)' }}>
        <b>Gasto público en medicamentos ganado por fallo</b>
        <div className="jq-mini" style={{ marginTop: 6 }}>
          {JUDICIAL_PUBLICO.map(j => (
            <div key={j.anio}>
              <div className="jq-mini-row">
                <span className="jq-mini-lab">Año {j.anio} <CertPill cert={j.cert} /></span>
                <span className="note"><b>{fInt(j.mm)}</b> millones</span>
              </div>
              <div className="jq-mini-track">
                <div className="jq-mini-fill" style={{ width: (j.mm / judMax) * 100 + '%', background: 'var(--red)' }} />
              </div>
            </div>
          ))}
        </div>
        <p className="note" style={{ marginTop: 8, marginBottom: 0 }}>{JUDICIAL_NOTA}</p>
      </div>

      <p className="lead" style={{ fontSize: 15, marginTop: 18 }}>
        Otras piezas que quedan fuera de las listas cerradas, cada una con su perímetro y su año. No
        se suman al núcleo: se muestran para dimensionar lo que la cobertura ordinaria no alcanza.
      </p>
      <div className="tablewrap">
        <table>
          <colgroup>
            <col style={{ width: '26%' }} />
            <col style={{ width: '22%' }} />
            <col style={{ width: '8%' }} />
            <col style={{ width: '44%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Componente</th>
              <th>Cifra</th>
              <th>Año</th>
              <th>Fuente y alcance</th>
            </tr>
          </thead>
          <tbody>
            {COBERTURA_FUERA.map(c => (
              <tr key={c.label}>
                <td style={{ textAlign: 'left' }}>
                  <b>{c.label}</b>
                  <span className="note" style={{ display: 'block' }}>{c.sub}</span>
                </td>
                <td className="num">{c.valor} <CertPill cert={c.cert} /></td>
                <td style={{ textAlign: 'center' }} className="note">{c.anio}</td>
                <td style={{ textAlign: 'left' }} className="note">{c.fuente}.</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── TÍTULO 8 · preguntas abiertas ── */}
      <div className="jq-h">
        <span className="jq-h-num">{T8.num}</span>
        <h2 className="jq-h-t">{T8.titulo}</h2>
      </div>
      <p className="jq-bajada">{T8.bajada}</p>
      <div className="card">
        {T8.preguntas.map((q, i) => (
          <div className="jq-q" key={i}>
            <span className="jq-q-n">{i + 1}</span>
            <span className="jq-q-t">{q}</span>
          </div>
        ))}
      </div>

      <div className="card teaser" style={{ marginTop: 28 }}>
        Esta jerarquía es la columna vertebral del informe: el gasto total como ancla, los tres
        filtros que lo reparten y el zoom al lado público trazable. Cada cifra trae su año y su
        fuente, y dice si es un dato o una estimación.
      </div>
    </section>
  )
}
