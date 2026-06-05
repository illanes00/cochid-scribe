import { ReactNode } from 'react'
import { GLOSARIO } from '../data'

// Referencia a un código SHA con hover explicativo.
// Uso narrativo (español primero):  <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef>
//   → muestra "medicamentos ambulatorios", y al hover el código + su definición.
// Uso técnico (código visible):      <CodeRef c="HC.5.1" />
//   → muestra el código en <code>, con el mismo hover.
export default function CodeRef({ c, children }: { c: string; children?: ReactNode }) {
  const g = GLOSARIO[c]
  const label = children ?? <code>{c}</code>
  if (!g) return <span>{label}</span>
  return (
    <span className="coderef" tabIndex={0}>
      {label}
      <span className="coderef-tip" role="tooltip">
        <b>{g.nombre}</b> <span className="coderef-code">{c}</span>
        <br />
        {g.def}
      </span>
    </span>
  )
}
