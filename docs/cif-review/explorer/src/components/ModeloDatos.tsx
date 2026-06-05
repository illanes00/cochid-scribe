import { VISTAS_NO_ADITIVAS, SCHEMA_MEDS, CROSSWALKS, META_GAPS } from '../data/gaps'

// Modelo de datos del explorador: el linaje (fuentes → bronze/silver/gold →
// vistas), el esquema cochid_datos.meds, los crosswalks entre clasificaciones y
// el catálogo de vacíos. Es la pieza de reproducibilidad: cómo se reconstruyó
// cada cifra y qué queda fuera del perímetro.
const fMM = (v: number) => v.toLocaleString('es-CL')

export default function ModeloDatos() {
  return (
    <section id="modelo-datos">
      <h2 className="ptitle">El modelo de datos</h2>
      <p className="psub">
        Ninguna fuente publica el gasto en medicamentos de Chile como un único número. El explorador lo
        reconstruye cruzando tres fuentes administrativas, cada una con su marco. Aquí están el linaje,
        el esquema y los puentes entre clasificaciones para auditar cada cifra y cada vacío.
      </p>

      {/* Linaje: fuentes → capas → vistas */}
      <div className="card" style={{ borderLeftColor: '#1a365d' }}>
        <b>El linaje, en una línea.</b> Fuentes oficiales (DIPRES, Mercado Público, SINIM, EPF del INE,
        cuentas OCDE-SHA) → capa <b>bronze</b> (ingesta cruda, idempotente) → capa <b>silver</b> (parseo,
        normalización, deduplicación) → capa <b>gold</b> (agregados auditados) → las <b>tres vistas</b> no
        aditivas. Todo versionado en migraciones y reproducible desde el origen.
      </div>

      {/* Las tres vistas no aditivas */}
      <h3 style={{ fontSize: 17, color: '#1a365d', marginTop: 26 }}>Las tres vistas del mismo gasto (no aditivas)</h3>
      <div className="tablewrap">
        <table style={{ width: '100%', fontSize: 12.5, marginTop: 6 }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Vista</th>
              <th style={{ textAlign: 'left' }}>Qué mide</th>
              <th>MM$</th>
              <th style={{ textAlign: 'left' }}>Marco</th>
            </tr>
          </thead>
          <tbody>
            {VISTAS_NO_ADITIVAS.map(v => (
              <tr key={v.vista}>
                <td style={{ textAlign: 'left' }}><b>{v.vista}</b></td>
                <td style={{ textAlign: 'left' }}>{v.detalle}</td>
                <td className="num">{fMM(v.mm)}</td>
                <td style={{ textAlign: 'left' }} className="note">{v.marco}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        Cada vista mira el mismo gasto físico desde un marco distinto (ejecución, compra, hogar). Sumarlas
        sería doble o triple conteo. La línea Farmacia es el nodo común que aparece en las tres.
      </p>

      {/* Esquema cochid_datos.meds */}
      <h3 style={{ fontSize: 17, color: '#1a365d', marginTop: 26 }}>El esquema <code>cochid_datos.meds</code></h3>
      <div className="tablewrap">
        <table style={{ width: '100%', fontSize: 12.5, marginTop: 6 }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Tabla</th>
              <th style={{ textAlign: 'left' }}>Contenido</th>
              <th style={{ textAlign: 'left' }}>Filas</th>
            </tr>
          </thead>
          <tbody>
            {SCHEMA_MEDS.map(t => (
              <tr key={t.tabla}>
                <td style={{ textAlign: 'left' }}><code>{t.tabla}</code></td>
                <td style={{ textAlign: 'left' }}>{t.descripcion}</td>
                <td style={{ textAlign: 'left' }} className="note">{t.filas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Crosswalks */}
      <h3 style={{ fontSize: 17, color: '#1a365d', marginTop: 26 }}>Los puentes entre clasificaciones (crosswalks)</h3>
      <div className="tablewrap">
        <table style={{ width: '100%', fontSize: 12.5, marginTop: 6 }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>De</th>
              <th style={{ textAlign: 'left' }}>A</th>
              <th style={{ textAlign: 'left' }}>Para qué</th>
            </tr>
          </thead>
          <tbody>
            {CROSSWALKS.map(c => (
              <tr key={c.de + c.a}>
                <td style={{ textAlign: 'left' }}>{c.de}</td>
                <td style={{ textAlign: 'left' }}>{c.a}</td>
                <td style={{ textAlign: 'left' }} className="note">{c.para}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Vacíos de medición */}
      <h3 style={{ fontSize: 17, color: '#c53030', marginTop: 26 }}>Lo que todavía no se puede medir (vacíos)</h3>
      <p className="psub">
        La honestidad del explorador está en declarar sus límites. Estos son los vacíos conocidos y su
        grado de resolubilidad.
      </p>
      <div className="tablewrap">
        <table style={{ width: '100%', fontSize: 12.5, marginTop: 6 }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Vacío</th>
              <th style={{ textAlign: 'left' }}>Por qué</th>
              <th style={{ textAlign: 'left' }}>¿Resoluble?</th>
            </tr>
          </thead>
          <tbody>
            {META_GAPS.map(g => (
              <tr key={g.gap}>
                <td style={{ textAlign: 'left' }}><b>{g.gap}</b></td>
                <td style={{ textAlign: 'left' }}>{g.descripcion}</td>
                <td style={{ textAlign: 'left' }} className="note">{g.resoluble}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        Fuente del esquema y los vacíos: lake <code>cochid_datos.meds</code> (tablas{' '}
        <code>gold_resumen</code>, <code>vistas_anuales</code>, <code>sha_separacion</code>,{' '}
        <code>meta_gaps</code>). Linaje completo en las migraciones del repositorio cochid-datos.
      </p>
    </section>
  )
}
