import { Link } from 'react-router-dom'
import OverviewTable from '../components/OverviewTable'
import CodeRef from '../components/CodeRef'
import { CHAPTERS } from '../chapters'

// Enlaces de entrega (Drive del proyecto "Informe Medicamentos").
const DRIVE_FOLDER = 'https://drive.google.com/drive/folders/1UhWNcxHjNBPRWWcEvPdalSlsQFy3C5p6'
const INFORME_PDF = 'https://drive.google.com/file/d/1_Bt92MWGuIFP4aeaLh07Tl0YIEw8-VrS/view'
const EXCEL_CIFRAS = 'https://drive.google.com/file/d/1uRp6M96-kBS8qeLuzCT1RxYZBme4IHOD/view'

// Portada del explorador. Abre TOP-DOWN: del gasto en salud total al medicamento,
// la cifra de gasto público como banda disjunta (no la vista-programa no aditiva),
// acciones de entrega (descargar informe, Drive, navegar) y el recorrido por capítulos.
export default function Home() {
  return (
    <section>
      <h1 className="ptitle">El gasto en medicamentos en Chile, reconstruido</h1>
      <p className="psub">
        Explorador de datos del informe <i>Inclusión sostenible de medicamentos en los planes de salud
        en Chile</i> · Espacio Público · marco OCDE System of Health Accounts (SHA 2011)
      </p>
      <p className="lead">
        Ninguna fuente publica cuánto gasta Chile en medicamentos. Este explorador lo reconstruye
        cruzando tres fuentes que miran el gasto desde ángulos distintos: el presupuesto público
        (DIPRES), la encuesta de hogares (Encuesta de Presupuestos Familiares del INE) y las cuentas
        de salud de la OCDE. Parte de lo más grande, el gasto en salud total, y va cerrando el foco
        hasta el hogar. Cada cifra queda trazable a su fuente, su denominador y su perímetro.
      </p>

      {/* Acciones de entrega: intuitivas, arriba de todo */}
      <div className="portal">
        <a className="portal-card primary" href={INFORME_PDF} target="_blank" rel="noreferrer">
          <span className="portal-ico" aria-hidden>⬇</span>
          <span className="portal-t">Descargar el informe</span>
          <span className="portal-d">Documento completo en PDF (resumen ejecutivo, capítulos y anexos).</span>
        </a>
        <a className="portal-card" href={EXCEL_CIFRAS} target="_blank" rel="noreferrer">
          <span className="portal-ico" aria-hidden>▦</span>
          <span className="portal-t">Excel de cifras</span>
          <span className="portal-d">Todas las cifras auditadas, con su denominador y su fuente, hoja por hoja.</span>
        </a>
        <a className="portal-card" href={DRIVE_FOLDER} target="_blank" rel="noreferrer">
          <span className="portal-ico" aria-hidden>◰</span>
          <span className="portal-t">Carpeta en Drive</span>
          <span className="portal-d">Todas las versiones del informe, el Excel y los insumos del proyecto.</span>
        </a>
        <Link className="portal-card" to={CHAPTERS[0].route}>
          <span className="portal-ico" aria-hidden>→</span>
          <span className="portal-t">Navegar el explorador</span>
          <span className="portal-d">Empezar por el gasto en salud total y descomponerlo paso a paso.</span>
        </Link>
      </div>

      {/* Cuadro resumen TOP-DOWN: del gasto en salud total al medicamento */}
      <div className="card summary">
        <b className="summary-q">¿Cuánto se gasta en medicamentos en Chile?</b>
        <ul className="summary-list">
          <li>
            El <b>gasto corriente en salud</b> de Chile fue de <b>10,0% del PIB</b> en 2022
            {' '}<span className="note">(26.259.336 MM$, es decir 26,3 billones de pesos; 61.642 millones de USD PPA, factor ~426 CLP/USD, no es el dólar de mercado)</span>.
          </li>
          <li>
            Dentro de esa salud, los <CodeRef c="HC.5.1">medicamentos de uso ambulatorio</CodeRef> pesan
            {' '}<b>1,34% del PIB</b> <span className="note">(3.518.751 MM$, ≈3,5 billones de pesos; 13,4% del gasto en salud)</span>:
            es una de las principales causas de gasto de bolsillo en salud de los hogares.
          </li>
          <li>
            El <b>gasto público</b> en medicamentos se ubica en una banda de
            {' '}<b>0,42% a 0,46% del PIB</b> <span className="note">(≈1,1 a 1,2 billones de pesos, lado ejecución; converge con el 0,46% del PIB del estudio CIF/UC)</span>.
            La suma de instrumentos (GES, DAC, FONASA, Ricarte Soto y otros) <b>no es aditiva</b>: varios se solapan dentro de la misma plata.
          </li>
          <li>
            Del medicamento ambulatorio, el <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> financia cerca de
            {' '}<b>71%</b> <span className="note">(perímetro HC.5.1 de la OCDE)</span>:
            es lo más desprotegido del sistema.
          </li>
          <li>
            La carga es desigual: el quintil de menores ingresos destina cerca de <b>9,6%</b> de su ingreso a
            medicamentos, frente a <b>1,8%</b> del quintil superior <span className="note">(≈5 veces más)</span>.
          </li>
        </ul>
        <p className="note" style={{ marginBottom: 0 }}>
          Unidades: la principal es el <b>% del PIB</b>; entre paréntesis, pesos (MM$ = millones de pesos)
          y USD PPA (dólar ajustado por poder de compra, rotulado, no el dólar de mercado).
        </p>
      </div>

      <OverviewTable />

      <h2 className="ptitle" style={{ fontSize: 22, marginTop: 34 }}>Recorrido</h2>
      <p className="lead" style={{ fontSize: 16 }}>
        El explorador sigue un embudo de arriba hacia abajo: del <b>gasto en salud total</b> al
        {' '}<b>medicamento</b> dentro de la salud, después el <b>cubo OCDE 2023 y las áreas</b> del gasto,
        los <b>instrumentos</b> de la política y, al final, la <b>síntesis</b> y la comparación
        internacional. Cada capítulo es una página:
      </p>

      <div className="cardgrid">
        {CHAPTERS.map(c => (
          <Link key={c.route} to={c.route} className="navcard">
            <span className="navcard-num">Capítulo {c.num}</span>
            <span className="navcard-title">{c.title}</span>
            <span className="navcard-blurb">{c.blurb}</span>
          </Link>
        ))}
      </div>

      <div className="card teaser">
        ¿Quieres el hilo argumental completo de un vistazo? El
        {' '}<Link to="/esqueleto"><b>esqueleto lógico del informe</b></Link> traza cómo se encadena cada pieza,
        del gasto en salud total a la carga del medicamento sobre los hogares.
      </div>
    </section>
  )
}
