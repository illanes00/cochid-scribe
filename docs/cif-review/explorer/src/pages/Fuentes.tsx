import { META } from '../data'
import CodeRef from '../components/CodeRef'
import ModeloDatos from '../components/ModeloDatos'

// Página "Modelo de datos y fuentes": el modelo de datos (linaje, esquema,
// crosswalks y vacíos) seguido del bloque de descargas para auditar cada cifra.
const API = '/api/v1/medicamentos/dev/v6'

export default function Fuentes() {
 return (
 <section id="dl">
 <h1 className="ptitle">Modelo de datos y fuentes</h1>

 <ModeloDatos />

 <h2 className="ptitle" style={{ marginTop: 34 }}>Descargas</h2>
 <p className="psub">
 Insumos para auditar cada cifra del explorador: dataset OECD SHA, metadata oficial
 de comparabilidad Chile, la cara en pesos del gasto público y el bolsillo de los hogares.
 </p>
 <p>
 Todo es reproducible. El bloque OECD, dataset SHA <code>DSD_SHA@DF_SHA</code> para Chile, verificado
 celda a celda contra el SDMX, se complementa con la cara en pesos del gasto público (DIPRES + CIF/UC) y con
 el <CodeRef c="HF.3">bolsillo de los hogares (copagos y compra directa)</CodeRef> medido en la EPF del INE.
 Aquí están los insumos para auditar cada cifra y, sobre todo, cada vacío declarado: el medicamento
 administrado en hospital, no separable porque queda embebido en la <CodeRef c="HC.1">atención curativa hospitalaria</CodeRef>, el
 <CodeRef c="HC.RI.1"> gasto farmacéutico total (retail + hospital) que Chile no reporta</CodeRef> y la diferencia de perímetro entre el
 71% (bolsillo sobre <CodeRef c="HC.5.1">medicamentos ambulatorios por todos los canales (medición SHA)</CodeRef>) y el
 62% (bolsillo sobre el gasto farmacéutico total, estimación CIF).
 </p>
 <div className="dl">
 <a href={`${API}/datos.xlsx`}>⬇ Excel «Datos y cálculos»</a>
 <a className="alt" href={`${API}/fuente/oecd-raw`}>⬇ Cruce OECD HC×HF (CSV)</a>
 <a className="alt" href={`${API}/fuente/oecd-metadata-xls`}>⬇ Metadata OECD–Chile (XLS oficial)</a>
 <a className="alt" href={`${API}/fuente/oecd-metadata-md`}>⬇ Sources &amp; methods (MD)</a>
 <a className="alt" href={`${API}/fuente/jhaq-full`}>⬇ Submisión JHAQ Chile (MD)</a>
 <a className="alt" href={`${API}/fuente/reconciliacion`}>⬇ Reconciliación 71/62</a>
 </div>
 <ul className="note">
 <li><b>Datos:</b> OECD Health expenditure and financing, <a href="https://data-explorer.oecd.org/vis?df[id]=DSD_SHA@DF_SHA&df[ag]=OECD.ELS.HD" target="_blank" rel="noreferrer">Data Explorer ↗</a></li>
 <li><b>Comparabilidad/metadata:</b> <a href="https://stats.oecd.org/wbos/fileview2.aspx?IDFile=8c9a9676-c5cb-4d37-9fb4-18923ce901c4" target="_blank" rel="noreferrer">Note on data sources and comparability, CHL ↗</a></li>
 <li><b>Bolsillo / hogares:</b> INE EPF IX 2021-2022. <b>Gasto público:</b> DIPRES 2024-2025 + CIF/UC. <b>Marco:</b> SHA 2011 (OECD/Eurostat/WHO).</li>
 </ul>
 <p className="note">Dataset: <code>{META.dataset}</code> · {META.años} · precios {META.precio}.</p>
 </section>
 )
}
