import { useState } from 'react'
import { BarList, type BarItem } from './HierBar'
import { RAINBOW } from '../data'
import { MP_LABORATORIO_2024, MP_CLASE_2024, MP_TOTAL_2024 } from '../data/gaps'
import Caption from './Caption'

// La compra pública de medicamentos (Mercado Público, UNSPSC-51), 2024, vista
// por laboratorio proveedor o por clase terapéutica. Es la vista COMPRA, no
// aditiva con el devengado ni con el bolsillo. CENABAST intermedia ~82% del canal.
type Modo = 'laboratorio' | 'clase'

export default function MercadoPublico() {
  const [modo, setModo] = useState<Modo>('clase')

  const fuente = 'Mercado Público, UNSPSC-51 (ChileCompra)'
  const items: BarItem[] = modo === 'clase'
    ? MP_CLASE_2024.map((f, i) => ({ label: f.clase, mm: f.mm, cert: 'real', fuente, color: RAINBOW[i % RAINBOW.length] }))
    : MP_LABORATORIO_2024.map((f, i) => ({ label: f.laboratorio, mm: f.mm, cert: 'real', fuente, color: RAINBOW[i % RAINBOW.length] }))

  const mostrado = items.reduce((a, it) => a + it.mm, 0)
  const cobertura = (mostrado / MP_TOTAL_2024) * 100

  return (
    <section id="mercado-publico">
      <h2 className="ptitle">Qué se compra: la vista de Mercado Público</h2>
      <p className="psub">
        La compra pública de medicamentos en 2024 sumó {MP_TOTAL_2024.toLocaleString('es-CL')} MM$
        (Mercado Público, segmento UNSPSC-51), con CENABAST intermediando cerca del 82% del canal. Es
        la vista de <b>compra</b>: no se suma con el devengado ni con el bolsillo. Se puede mirar por
        clase terapéutica o por laboratorio proveedor.
      </p>

      <div className="filterbox" style={{ display: 'inline-flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
        <label style={{ margin: 0 }}>Ver por</label>
        {(['clase', 'laboratorio'] as Modo[]).map(m => (
          <button
            key={m}
            className="preset"
            style={{
              width: 'auto', margin: 0,
              background: modo === m ? '#1a365d' : undefined,
              color: modo === m ? '#fff' : undefined,
              borderColor: modo === m ? '#1a365d' : undefined,
            }}
            onClick={() => setModo(m)}
          >
            {m === 'clase' ? 'Clase terapéutica' : 'Laboratorio'}
          </button>
        ))}
      </div>

      <Caption
        ch={4}
        n={6}
        kind="grafico"
        title={modo === 'clase'
          ? 'Compra pública por clase terapéutica, 2024 (MM$)'
          : 'Compra pública por laboratorio (top 18), 2024 (MM$)'}
      />
      <BarList items={items} base={MP_TOTAL_2024} unidad="MM$" />
      <p className="note">
        {modo === 'laboratorio'
          ? `Top 18 proveedores: cubren ${cobertura.toFixed(0)}% de la compra pública total. Los porcentajes son sobre el total de la compra (${MP_TOTAL_2024.toLocaleString('es-CL')} MM$).`
          : `Las clases mostradas cubren ${cobertura.toFixed(0)}% de la compra pública. Los porcentajes son sobre el total de la compra.`}
      </p>

      <div className="card" style={{ borderLeftColor: '#2b6cb0' }}>
        <b>El Estado compra alto costo; el hogar paga lo crónico.</b> En la compra pública pesan los
        antitumorales, los inmunomoduladores y las hormonas (alto costo, baja frecuencia). En el bolsillo
        de los hogares pesa lo contrario: lo crónico y de uso ambulatorio masivo (digestivo, cardiovascular,
        respiratorio). Son dos caras complementarias del mismo sistema: el Estado concentra el gasto en
        pocos pacientes muy caros y el hogar lo dispersa en muchos tratamientos de uso diario.
      </div>
      <p className="note">
        Fuente: <code>cochid_datos.meds.mp_clase</code> y <code>meds.mp_laboratorio</code>, a partir de
        las órdenes de compra de Mercado Público (ChileCompra), segmento UNSPSC-51.
      </p>
    </section>
  )
}
