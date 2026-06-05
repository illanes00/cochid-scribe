import Definitions from '../components/Definitions'
import CodeTaxonomy from '../components/CodeTaxonomy'

// Capítulo 1 · Marco SHA: las cuatro preguntas (HF/HC/HP/FS) y la gramática
// de códigos ICHA, el vocabulario que usa el resto del informe.
export default function CapMarco() {
 return (
 <>
 <header>
 <p className="psub" style={{ textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 700, color: '#2b6cb0', margin: 0 }}>
 Capítulo 6 · Referencia
 </p>
 <h1 className="ptitle" style={{ marginTop: 2 }}>Marco OCDE: definiciones y códigos</h1>
 <p className="psub">
 Material de referencia. Las cuatro preguntas del System of Health Accounts (SHA 2011)
 (¿qué se compra?, ¿quién provee?, ¿quién financia?, ¿con qué fuente?) y la gramática de
 códigos ICHA (HC · HP · HF · FS) que usa el resto del informe.
 </p>
 </header>
 <p className="lead">
 Antes de las definiciones, el mapa de códigos que usa todo el informe: las cuatro
 clasificaciones ICHA (HC funciones · HP proveedores · HF financiamiento · FS fuentes) y qué
 reporta Chile en cada una.
 </p>
 <CodeTaxonomy />
 <Definitions />
 </>
 )
}
