// Leyenda numerada para ir JUSTO ENCIMA de cada tabla o gráfico.
// Lidera con "Tabla {ch}.{n}" o "Gráfico {ch}.{n}" en negrita azul EP,
// seguido del título descriptivo en gris.
export default function Caption({
  ch,
  n,
  kind,
  title,
}: {
  ch: number
  n: number
  kind: 'tabla' | 'grafico'
  title: string
}) {
  const word = kind === 'tabla' ? 'Tabla' : 'Gráfico'
  return (
    <p className="caption">
      <span className="cap-num">
        {word} {ch}.{n}
      </span>
      <span className="cap-title">: {title}</span>
    </p>
  )
}
