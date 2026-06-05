import { useMemo, useState } from 'react'
import {
  PieChart, Pie, Cell as RCell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts'
import { EP, RAINBOW, hcxhp } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

const API = '/api/v1/medicamentos/dev/v6'
const fInt = (v: number) => v.toLocaleString('es-CL', { maximumFractionDigits: 0 })
const fPct = (v: number) => v.toFixed(1).replace('.', ',') + '%'

// `name` es la descripción en español (lo que se ve); `chile` aclara qué es concretamente en Chile.
// Ambos pueden llevar <CodeRef> para mostrar el código SHA al hover. `key` es el identificador estable
// que recharts necesita como string para nameKey/dataKey y para las keys de React.
interface Item { key: string; name: React.ReactNode; chile: React.ReactNode; value: number; color: string }

// Leyenda-tabla HTML: color · etiqueta (correspondencia Chile) · valor+unidad · % del total.
// Numerada como Tabla 6.{capN} y envuelta en .tablewrap para scroll horizontal sin desbordar.
function LegendTable({
  items, total, unit, capN, capTitle,
}: { items: Item[]; total: number; unit: string; capN: number; capTitle: string }) {
  return (
    <>
      <Caption ch={5} n={capN} kind="tabla" title={capTitle} />
      <div className="tablewrap">
        <table style={{ margin: '4px 0 0', fontSize: 12, width: '100%', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '64%' }} />
            <col style={{ width: '20%' }} />
            <col style={{ width: '16%' }} />
          </colgroup>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Categoría (qué es en Chile)</th>
              <th>{unit}</th>
              <th>% del total</th>
            </tr>
          </thead>
          <tbody>
            {items.map(it => (
              <tr key={it.key}>
                <td style={{ textAlign: 'left' }}>
                  <span style={{ display: 'inline-block', width: 10, height: 10, background: it.color, borderRadius: 2, marginRight: 7 }} />
                  {it.name} <span className="note">({it.chile})</span>
                </td>
                <td className="num">{fInt(it.value)}</td>
                <td className="num pct">{total ? fPct((it.value / total) * 100) : '·'}</td>
              </tr>
            ))}
            <tr className="tot">
              <td style={{ textAlign: 'left' }}>TOTAL</td>
              <td className="num">{fInt(total)}</td>
              <td className="num">100,0%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  )
}

function ChartCard(props: {
  title: string; pill: string; note: React.ReactNode; children: React.ReactNode
  items: Item[]; total: number; unit: string; totalLabel: React.ReactNode; source: React.ReactNode
  graficoN: number; graficoTitle: string; tablaN: number; tablaTitle: string
}) {
  return (
    <div className="chartbox">
      <h3 style={{ marginTop: 0, fontSize: 15 }}>{props.title} <span className="pill">{props.pill}</span></h3>
      <p className="note" style={{ marginTop: 0 }}>{props.note}</p>
      <Caption ch={5} n={props.graficoN} kind="grafico" title={props.graficoTitle} />
      <div style={{ width: '100%', height: 230, maxWidth: '100%' }}>{props.children}</div>
      <LegendTable
        items={props.items} total={props.total} unit={props.unit}
        capN={props.tablaN} capTitle={props.tablaTitle}
      />
      <p className="note" style={{ marginTop: 6 }}>
        <b>Total:</b> {fInt(props.total)} {props.totalLabel} · {props.source}
      </p>
    </div>
  )
}

export default function Charts() {
  const [openNota, setOpenNota] = useState(false)

  const disp: Item[] = useMemo(() => {
    const h = hcxhp['HC51'] || {}
    return [
      { key: 'HP5', name: <><CodeRef c="HP.5">Farmacias minoristas privadas</CodeRef></>, chile: 'cadenas y locales de venta al público: Cruz Verde, Salcobrand, Ahumada', value: h.HP5 ?? 4502, color: RAINBOW[2] },
      { key: 'HP1', name: <><CodeRef c="HP.1">Farmacias de hospital</CodeRef></>, chile: 'dispensación ambulatoria desde el hospital público', value: h.HP1 ?? 2531, color: RAINBOW[6] },
      { key: 'HP3', name: <><CodeRef c="HP.3">Atención primaria municipal</CodeRef></>, chile: 'CESFAM y consultorios; entrega gratuita vía FOFAR', value: h.HP3 ?? 1233, color: RAINBOW[3] },
    ]
  }, [])
  const dispTot = disp.reduce((a, d) => a + d.value, 0)

  // % del ingreso TOTAL del hogar gastado en medicamentos, por quintil de ingreso per cápita.
  // Ponderado por factor de expansión, microdato INE EPF IX (verificado: ratio Q1/Q5 = 5,35×).
  const quintiles = [
    { q: 'Q1', value: 9.6 }, { q: 'Q2', value: 3.5 }, { q: 'Q3', value: 2.9 },
    { q: 'Q4', value: 2.8 }, { q: 'Q5', value: 1.8 },
  ]

  // Gasto público en medicamentos por instrumento (vista-programa ILUSTRATIVA, NO ADITIVA).
  // Las filas se SOLAPAN: el GES público y las Drogas de Alto Costo se devengan DENTRO de la
  // Farmacia de los Servicios de Salud; sumar las cajas duplicaría del orden de 400.000 MM$.
  // El total público DISJUNTO (lado ejecución) está en la banda 0,42-0,46% del PIB (≈1,1-1,2
  // billones), que converge con el 0,46% del estudio CIF/UC. Aquí se muestran solo los
  // instrumentos ADITIVOS (perímetros disjuntos), no la suma inflada. Cifras firmes re-arquitectura v8.
  const programas: Item[] = [
    { key: 'FarmaciaSS', name: 'Farmacia de los Servicios de Salud', chile: 'línea 22.04.004.001 (2023); contiene el GES público y las Drogas de Alto Costo, no se cuentan aparte', value: 736761, color: RAINBOW[5] },
    { key: 'APS', name: 'Atención primaria municipal', chile: 'gasto comunal en farmacia, incluye el Fondo de Farmacia (FOFAR), SINIM 2023', value: 162613, color: RAINBOW[2] },
    { key: 'RicarteSoto', name: 'Fondo de alto costo (Ley Ricarte Soto)', chile: 'línea propia y aditiva: no baja a los Servicios de Salud (ejecución 2025)', value: 175672, color: RAINBOW[0] },
    { key: 'FFAA', name: 'Sanidad de las Fuerzas Armadas y de Orden', chile: 'medicamentos del sistema de salud militar y policial', value: 62339, color: RAINBOW[3] },
    { key: 'Judicial', name: 'Judicialización (glosa sub-presupuestada)', chile: 'sentencias FONASA, subt 26.02 público (2023); la ejecución desborda el presupuesto', value: 32679, color: EP.red },
    { key: 'PNI', name: 'Programa Nacional de Inmunizaciones', chile: 'vacunas (prevención), línea propia de otra función', value: 30000, color: RAINBOW[7] },
  ]
  const progTot = programas.reduce((a, d) => a + d.value, 0)

  const quienPaga: Item[] = [
    { key: 'HF3', name: <><CodeRef c="HF.3">Bolsillo de los hogares</CodeRef></>, chile: 'copagos del plan y compra directa del medicamento por la familia', value: 71.0, color: EP.red },
    { key: 'HF1', name: <><CodeRef c="HF.1">Financiamiento obligatorio</CodeRef></>, chile: 'aporte fiscal (impuestos) + cotizaciones obligatorias (FONASA + 7% ISAPRE), Mutuales y FF.AA.', value: 25.5, color: EP.primary },
    { key: 'HF2', name: <><CodeRef c="HF.2">Financiamiento voluntario</CodeRef></>, chile: 'ISAPRE complementario sobre el 7% + seguros privados + sin fines de lucro', value: 3.5, color: RAINBOW[2] },
  ]
  const qpTot = quienPaga.reduce((a, d) => a + d.value, 0)

  return (
    <section id="visualizaciones">
      <h2 className="ptitle">Visualizaciones: composición y carga distributiva</h2>
      <p className="psub">
        Cuatro lecturas del gasto en medicamentos. Cada gráfico muestra su total, las unidades y
        de dónde sale el dato. <button className="link" onClick={() => setOpenNota(true)}>Notas metodológicas</button>
      </p>

      <div className="grid2">
        {/* (1) Dispensación */}
        <ChartCard
          title="¿Dónde se dispensan los medicamentos ambulatorios?" pill="HC.5.1 · 2022"
          note={<>Gasto en <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> según dónde se entregan al paciente, en dólares ajustados por poder de compra (USD PPA, millones).</>}
          items={disp} total={dispTot} unit="USD PPA mill." totalLabel={<>USD PPA millones en <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef></>}
          source={<>Fuente: cuentas de salud OCDE (SHA) · <a href="#explorador">ver en el explorador ↗</a></>}
          graficoN={1} graficoTitle="Dispensación de medicamentos ambulatorios por canal de entrega (USD PPA mill.)"
          tablaN={1} tablaTitle="Dispensación ambulatoria por canal: valor y participación"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
              <Pie data={disp} dataKey="value" nameKey="key" cx="50%" cy="50%" outerRadius={78} labelLine={false}
                label={(e: any) => (e.value / dispTot >= 0.06 ? fPct((e.value / dispTot) * 100) : '')}>
                {disp.map((d, i) => <RCell key={i} fill={d.color} stroke="#fff" strokeWidth={1.5} />)}
              </Pie>
              <Tooltip formatter={(v: number) => [fInt(v) + ' USD PPA mill.', 'dispensación']} contentStyle={{ fontSize: 12.5 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* (2) Quintiles */}
        <div className="chartbox">
          <h3 style={{ marginTop: 0, fontSize: 15 }}>Carga del bolsillo por quintil <span className="pill">EPF IX · 2022</span></h3>
          <p className="note" style={{ marginTop: 0 }}>
            Gasto de bolsillo en medicamentos como % del ingreso del hogar, por quintil de ingreso per
            cápita. Q1 (9,6%) gasta proporcionalmente <strong>~5 veces</strong> más que Q5 (1,8%).
          </p>
          <Caption ch={5} n={2} kind="grafico" title="Gasto de bolsillo en medicamentos como % del ingreso del hogar, por quintil" />
          <div style={{ width: '100%', height: 230, maxWidth: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={quintiles} margin={{ top: 18, right: 12, left: -6, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef0f3" />
                <XAxis dataKey="q" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(0) + '%'} />
                <Tooltip formatter={(v: number) => [fPct(v), '% del ingreso pc']} contentStyle={{ fontSize: 12.5 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="value" position="top" formatter={(v: number) => fPct(v)} style={{ fontSize: 11, fill: EP.primary }} />
                  {quintiles.map((d, i) => <RCell key={i} fill={d.q === 'Q1' ? EP.red : EP.accent} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="note" style={{ marginTop: 6 }}>
            <b>Unidad:</b> % del ingreso per cápita del hogar. La incidencia del gasto catastrófico es <b>22,0%</b> de
            los hogares con esta métrica (umbral &gt;10% del ingreso per cápita); baja a 8,2% con la definición ODS 3.8.2
            (ingreso total) y a 1,1% con capacidad de pago OMS. Fuente: microdato INE EPF IX 2021-2022.
          </p>
        </div>

        {/* (3) Gasto público por instrumento (disjunto, aditivo) */}
        <ChartCard
          title="Gasto público en medicamentos por instrumento" pill="MM$ CLP · instrumentos disjuntos"
          note={<>Instrumentos del gasto público con perímetros <strong>disjuntos</strong> (aditivos), del lado ejecución (DIPRES y SINIM). El GES público y las Drogas de Alto Costo NO aparecen como cajas propias: se devengan <strong>dentro</strong> de la Farmacia de los Servicios de Salud, así que contarlos aparte sería doble conteo. El total público disjunto se ubica en una banda de <strong>0,42% a 0,46% del PIB</strong> (≈1,1 a 1,2 billones de pesos), que converge con el 0,46% del estudio CIF/UC.</>}
          items={programas} total={progTot} unit="MM$ CLP" totalLabel="MM$ CLP por instrumento disjunto (Farmacia de los Servicios de Salud 2023, APS municipal 2023, Ley Ricarte Soto 2025, FF.AA., judicialización 2023, PNI). El GES público y las Drogas de Alto Costo están dentro de la Farmacia, no se suman aparte."
          source={<>Fuente: DIPRES, SINIM y MINSAL · <a href={`${API}/datos.xlsx`}>descargar datos ↗</a></>}
          graficoN={3} graficoTitle="Gasto público en medicamentos por instrumento disjunto (MM$ CLP)"
          tablaN={2} tablaTitle="Gasto público en medicamentos por instrumento disjunto: monto y participación"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
              <Pie data={programas} dataKey="value" nameKey="key" cx="50%" cy="50%" innerRadius={38} outerRadius={78} labelLine={false}
                label={(e: any) => (e.value / progTot >= 0.06 ? fPct((e.value / progTot) * 100) : '')}>
                {programas.map((d, i) => <RCell key={i} fill={d.color} stroke="#fff" strokeWidth={1.5} />)}
              </Pie>
              <Tooltip formatter={(v: number) => [fInt(v) + ' MM$', 'gasto público']} contentStyle={{ fontSize: 12.5 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* (4) Quién paga */}
        <ChartCard
          title="¿Quién paga el medicamento ambulatorio?" pill="Medicamentos ambulatorios · 2022"
          note={<>Cómo se reparte quién financia los <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (todos los canales de venta). El <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> cubre cerca del <strong>71%</strong> del total, uno de los más altos de la OCDE.</>}
          items={quienPaga} total={qpTot} unit="% del total" totalLabel={<>% de la composición del financiamiento de <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (todos los canales)</>}
          source={<>Fuente: cuentas de salud OCDE (SHA) · <a href="#explorador">ver en el explorador ↗</a></>}
          graficoN={4} graficoTitle="Composición del financiamiento de medicamentos ambulatorios por agente pagador"
          tablaN={3} tablaTitle="Financiamiento de medicamentos ambulatorios por agente: participación"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
              <Pie data={quienPaga} dataKey="value" nameKey="key" cx="50%" cy="50%" outerRadius={78} labelLine={false}
                label={(e: any) => fPct(e.value)}>
                {quienPaga.map((d, i) => <RCell key={i} fill={d.color} stroke="#fff" strokeWidth={1.5} />)}
              </Pie>
              <Tooltip formatter={(v: number) => [fPct(v), 'del financiamiento']} contentStyle={{ fontSize: 12.5 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {openNota && (
        <div className="modal-backdrop" onClick={() => setOpenNota(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <button className="close" onClick={() => setOpenNota(false)}>×</button>
            <h3>Notas metodológicas</h3>
            <p><span className="badge ok">SHA-OCDE</span> Gráficos (1) y (4): matriz de función × proveedor × financiamiento reportada por Chile a la OCDE bajo el estándar de cuentas de salud (SHA), 2022, en USD PPA. La categoría de <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> no distingue receta de venta libre y excluye el medicamento administrado dentro del hospital, que va embebido en la <CodeRef c="HC.1">atención hospitalaria</CodeRef> y no es separable.</p>
            <p><span className="badge miss">Fuera de SHA</span> Gráfico (3): cifras nacionales por programa (DIPRES/MINSAL). No consolidadas como una sola función del estándar SHA; Chile no reporta el <CodeRef c="HC.RI.1">gasto farmacéutico total como partida de memoria</CodeRef> ni el gasto de las <CodeRef c="HP.5.1">farmacias minoristas</CodeRef> como proveedor.</p>
            <p><span className="badge miss">EPF</span> Gráfico (2): IX Encuesta de Presupuestos Familiares (INE); gasto de bolsillo en medicamentos como porcentaje del ingreso per cápita del hogar, por quintil.</p>
            <p className="note">Fuentes: cuentas de salud OCDE (SHA), DIPRES, MINSAL, INE-EPF IX.</p>
          </div>
        </div>
      )}
    </section>
  )
}
