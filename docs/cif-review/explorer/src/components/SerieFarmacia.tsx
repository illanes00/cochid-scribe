import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import { EP } from '../data'
import { SERIE_FARMACIA } from '../data/gaps'
import Caption from './Caption'

// Evolución de la línea Farmacia de los Servicios de Salud, 2010-2024.
// Nominal vs deflactado a pesos de 2024: la cifra crece fuerte en nominal, pero
// el crecimiento real es más sobrio y muestra la caída de 2022.
const fMM = (v: number) => v.toLocaleString('es-CL', { maximumFractionDigits: 0 })

// CAGR real 2010-2024 a partir de los extremos de la serie deflactada.
const r0 = SERIE_FARMACIA[0].real2024
const rN = SERIE_FARMACIA[SERIE_FARMACIA.length - 1].real2024
const anios = SERIE_FARMACIA[SERIE_FARMACIA.length - 1].anio - SERIE_FARMACIA[0].anio
const cagrReal = ((rN / r0) ** (1 / anios) - 1) * 100

export default function SerieFarmacia() {
  return (
    <section id="serie-farmacia">
      <h2 className="ptitle">La línea Farmacia crece, pero menos en términos reales</h2>
      <p className="psub">
        El gasto público devengado en la línea Farmacia de los Servicios de Salud (cuenta
        22.04.004.001) más que se cuadruplicó en pesos corrientes entre 2010 y 2024. Deflactado a
        pesos de 2024, el crecimiento es más moderado (cerca de {cagrReal.toFixed(1).replace('.', ',')}%
        real anual) y deja ver la caída de 2022.
      </p>

      <Caption ch={4} n={4} kind="grafico" title="Farmacia de los Servicios de Salud, 2010-2024 (MM$)" />
      <div className="chartbox">
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={SERIE_FARMACIA} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef0f3" vertical={false} />
            <XAxis dataKey="anio" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => (v / 1000).toLocaleString('es-CL') + 'k'} width={48} />
            <Tooltip
              formatter={(v: number, name: string) => [fMM(v) + ' MM$', name]}
              labelFormatter={(l) => `Año ${l}`}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="nominal" name="Nominal (pesos del año)" stroke={EP.accent} strokeWidth={2} dot={{ r: 2 }} />
            <Line type="monotone" dataKey="real2024" name="Real (pesos de 2024)" stroke={EP.red} strokeWidth={2.5} dot={{ r: 2 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="note">
        Fuente: ejecución presupuestaria de la línea de Productos Farmacéuticos (DIPRES),
        <code> cochid_datos.meds.serie_farmacia</code>. Deflactado con IPC a pesos de 2024.
        El nominal 2024 (775.616 MM$) es la misma cifra dura que se usa en el resto del explorador.
      </p>
    </section>
  )
}
