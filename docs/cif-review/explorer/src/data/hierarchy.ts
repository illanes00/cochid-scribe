// ─────────────────────────────────────────────────────────────────────────────
// JERARQUÍA ÚNICA del gasto en medicamentos en Chile.
//
// Esta página sigue, en orden, los OCHO títulos-afirmación del documento. Cada
// cifra se COPIA literalmente del diccionario congelado final
// (/tmp/cif-prod/rootcause/DICCIONARIO-CONGELADO-FINAL.md, congelado 2026-06-04).
// NUNCA se recalcula aquí: si una cifra cambia, se cambia primero en el
// diccionario y después se copia. Cada cifra trae su AÑO y su FUENTE, y dice si
// es un dato observado o una estimación / banda. Sin jerga de códigos. Solo barras.
//
// Anclaje: el gasto total (GT) es el 100% y vive sticky arriba de la página.
// Tres filtros reparten ese total visto de tres maneras. Un zoom abre el lado
// público disjunto (las únicas cifras que sí se suman, cada peso una sola vez).
// ─────────────────────────────────────────────────────────────────────────────

// Paleta institucional EP, inlineada para que esta página no arrastre el módulo
// de datos del explorador viejo.
const EP = { primary: '#1a365d', accent: '#2b6cb0', red: '#c53030', amber: '#fef3c7', amberInk: '#92400e' }
const RAINBOW = ['#F2920B', '#B1A35E', '#1CA29A', '#138691', '#196883', '#1C4E75', '#213366', '#4B3B7C', '#764494']

export type Cert = 'real' | 'estimacion'

// Una pieza dentro de un filtro: su monto y de dónde sale.
export interface Pieza {
  label: string          // etiqueta legible, sin códigos
  sub?: string           // aclaración corta de qué es en Chile
  mm: number             // monto en millones de pesos (MM$)
  pct?: number           // % congelado (cuando es el dato duro, no el monto)
  cert: Cert             // dato real o estimación / banda
  fuente: string         // fuente puntual de la cifra
  color: string
}

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 1 · No existe una cifra oficial del gasto en medicamentos: se reconstruye.
// ─────────────────────────────────────────────────────────────────────────────
export const T1 = {
  num: 1,
  titulo: 'No existe una cifra oficial del gasto en medicamentos: se reconstruye',
  bajada: 'Chile no publica un número único del gasto en medicamentos. Hay que armarlo juntando fuentes que miden cosas distintas, en años distintos, con perímetros distintos. Esta página muestra ese armado pieza por pieza, y deja a la vista qué es dato y qué es estimación.',
  puntos: [
    'El medicamento de uso ambulatorio sí tiene un dato firme: las cuentas de salud de la OCDE de 2022.',
    'El medicamento que se usa dentro del hospital no tiene registro propio: se obtiene por diferencia, por eso el total es una banda y no un punto.',
    'Cada cifra que sigue trae su año y su fuente. Las que se construyen se marcan como estimación.',
  ],
} as const

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 2 · Chile destina cerca de 4 billones de pesos (1,5% del PIB) a medicamentos.
// ANCLA · Nivel 0. El gasto total = 100%, sticky arriba.
// Banda congelada del GT 2022: 4.037.290 a 4.062.459 MM$.
// ─────────────────────────────────────────────────────────────────────────────
export const ANCLA = {
  num: 2,
  titulo: 'Chile destina cerca de 4 billones de pesos a medicamentos (1,5% del PIB)',
  tituloCorto: 'Gasto total en medicamentos en Chile',
  bajada: 'Sumando el medicamento que se usa fuera del hospital y el que se administra dentro, el gasto total en medicamentos del país ronda los 4 billones de pesos al año, cerca del 1,5% del PIB. Es el 100% del que cuelga todo lo demás en esta página.',
  // Banda congelada (diccionario fila 1).
  mmLo: 4_037_290,
  mmHi: 4_062_459,
  mmCentral: 4_049_875,            // punto medio, solo para dibujar las barras
  pibTitular: '1,5% del PIB',
  pesos: 'cerca de 4 billones de pesos al año',
  anio: 2022,
  fuente: 'Cuentas de salud de la OCDE para el ambulatorio (dato 2022), más una banda derivada para el medicamento de uso dentro del hospital',
  nota: 'Todo lo demás se lee como una fracción de esta cifra. Como el medicamento de uso dentro del hospital no tiene registro propio, el total es una banda y no un punto único.',
} as const

// El ambulatorio es el tramo medible con dato duro de la OCDE (diccionario fila 2).
export const AMBULATORIO_TOTAL = 3_518_751   // MM$, 2022, dato duro OCDE
// Medicamento de uso dentro del hospital = GT central − ambulatorio (banda).
export const HOSP_LO = ANCLA.mmLo - AMBULATORIO_TOTAL   // 518.539
export const HOSP_HI = ANCLA.mmHi - AMBULATORIO_TOTAL   // 543.708
export const HOSP_CENTRAL = ANCLA.mmCentral - AMBULATORIO_TOTAL

// Para leer cualquier pieza como fracción del Gasto Total usamos el punto medio.
export const GT = ANCLA.mmCentral
export const pctGT = (mm: number): number => (mm / GT) * 100

// ── FILTRO A · ¿para qué y dónde se usa? (ambulatorio vs dentro del hospital) ──
export const FILTRO_A = {
  id: 'A',
  pregunta: '¿Para qué y dónde se usa?',
  resumen: 'Reparte todo el gasto según si el medicamento se toma fuera del hospital (uso ambulatorio) o se administra dentro del hospital.',
  base: GT,
  baseLabel: 'gasto total en medicamentos',
  piezas: [
    { label: 'Fuera del hospital (uso ambulatorio)', sub: 'lo que la persona retira en la farmacia, el consultorio o el hospital para llevar a casa, recetado o de venta libre', mm: AMBULATORIO_TOTAL, cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: EP.accent },
    { label: 'Dentro del hospital', sub: 'medicamento administrado durante la internación; no tiene registro propio, se obtiene por diferencia, por eso es una banda', mm: HOSP_CENTRAL, cert: 'estimacion', fuente: 'Banda derivada sobre cuentas de la OCDE, 2022', color: RAINBOW[5] },
  ] as Pieza[],
  anio: 2022,
} as const

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 3 · El hogar es el principal pagador: el 71% del medicamento ambulatorio
// sale del bolsillo.
// FILTRO B · ¿quién paga? Composición congelada del ambulatorio:
// bolsillo 71,3% · obligatorio 25,5% · voluntario 3,1%.
// Los % son el dato duro (OCDE HF/_T 2022); el monto es derivado del %.
// ─────────────────────────────────────────────────────────────────────────────
export const FILTRO_B = {
  id: 'B',
  pregunta: '¿Quién paga?',
  resumen: 'Reparte el medicamento de uso ambulatorio según quién pone la plata. La OCDE lo separa en tres: el bolsillo del hogar, el financiamiento obligatorio y el voluntario.',
  base: AMBULATORIO_TOTAL,
  baseLabel: 'medicamento de uso ambulatorio',
  // % congelados (dato duro); mm derivado del % sobre el ambulatorio.
  piezas: [
    { label: 'Bolsillo de los hogares', sub: 'copago del plan y compra directa en la farmacia, sin reembolso', pct: 71.3, mm: Math.round(AMBULATORIO_TOTAL * 0.713), cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: EP.red },
    { label: 'Financiamiento obligatorio', sub: 'aporte fiscal de los impuestos más el 7% de cotización obligatoria, tanto en FONASA como en ISAPRE', pct: 25.5, mm: Math.round(AMBULATORIO_TOTAL * 0.255), cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: EP.primary },
    { label: 'Financiamiento voluntario', sub: 'seguros complementarios y aseguramiento privado por sobre el 7% obligatorio', pct: 3.1, mm: Math.round(AMBULATORIO_TOTAL * 0.031), cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: RAINBOW[2] },
  ] as Pieza[],
  // Resumen de dos cajas (público / privado) sobre el mismo ambulatorio.
  resumenPubPriv: [
    { label: 'Público obligatorio', mm: Math.round(AMBULATORIO_TOTAL * 0.255), pct: 25.5, color: EP.primary },
    { label: 'Privado (sobre todo bolsillo)', mm: Math.round(AMBULATORIO_TOTAL * 0.744), pct: 74.4, color: EP.red },
  ] as { label: string; mm: number; pct: number; color: string }[],
  anio: 2022,
  notaBolsillo: 'El bolsillo de los hogares paga el 71,3% del medicamento de uso ambulatorio, de los más altos de la OCDE. Esa proporción sale de la misma fuente, año y perímetro que las otras dos. El voluntario es el 3,1%.',
} as const

// ─────────────────────────────────────────────────────────────────────────────
// FILTRO C · ¿por dónde llega? (canal de dispensación del ambulatorio).
// Reparte el ambulatorio por el proveedor que lo entrega. Suma 100%.
// ─────────────────────────────────────────────────────────────────────────────
export const FILTRO_C = {
  id: 'C',
  pregunta: '¿Por dónde llega?',
  resumen: 'Reparte el medicamento de uso ambulatorio según el lugar donde la persona lo recibe: la farmacia comercial, el hospital para pacientes externos o el consultorio de atención primaria.',
  base: AMBULATORIO_TOTAL,
  baseLabel: 'medicamento de uso ambulatorio',
  piezas: [
    { label: 'Farmacia comercial', sub: 'cadenas y locales de venta al público (Cruz Verde, Salcobrand, Ahumada, farmacias populares)', mm: 1_917_719, cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: RAINBOW[0] },
    { label: 'Hospital (pacientes externos)', sub: 'farmacia del hospital público que entrega al paciente para llevar a casa', mm: 1_076_738, cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: RAINBOW[4] },
    { label: 'Atención primaria', sub: 'CESFAM y consultorios municipales; entrega gratuita, sobre todo a pacientes crónicos', mm: 524_294, cert: 'real', fuente: 'Cuentas de salud de la OCDE, 2022', color: RAINBOW[2] },
  ] as Pieza[],
  anio: 2022,
} as const

export const FILTROS = [FILTRO_A, FILTRO_B, FILTRO_C] as const

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 4 · El gasto público en medicamentos ronda 1,1 a 1,2 billones de pesos al año.
// NIVEL 2 · ZOOM al lado público trazable. Núcleo congelado 1.077.136 (2023) /
// 1.177.893 (2024), cerca de 0,4% del PIB, con el hospital público ya incluido.
// ─────────────────────────────────────────────────────────────────────────────
export const T4 = {
  num: 4,
  titulo: 'El gasto público en medicamentos ronda 1,1 a 1,2 billones de pesos al año (cerca de 0,4% del PIB)',
  bajada: 'Reconstruido peso a peso, el gasto público en medicamentos queda del orden de 1,1 a 1,2 billones de pesos al año, cerca del 0,4% del PIB, con el hospital público ya incluido porque la Farmacia de los Servicios de Salud no separa el uso hospitalario del ambulatorio.',
} as const

export interface NucleoPieza {
  label: string
  sub: string
  mm: Record<number, number>     // por año
  cert: Cert
  fuente: string
  color: string
}

// Núcleo público disjunto (diccionario filas 7, 7b, 8, 9, 10, 11).
export const NUCLEO_PUBLICO: NucleoPieza[] = [
  { label: 'Farmacia de los Servicios de Salud', sub: 'medicamento que la red pública entrega a sus pacientes, en el hospital y en los consultorios que dependen de ella. Ya contiene el GES público y el alto costo dispensados.', mm: { 2023: 736_761, 2024: 775_616 }, cert: 'real', fuente: 'Ejecución presupuestaria, línea de Productos Farmacéuticos (DIPRES)', color: RAINBOW[4] },
  { label: 'Atención primaria municipal', sub: 'medicamento que entregan los consultorios administrados por los municipios, sobre todo crónicos de uso masivo a través del Fondo de Farmacia.', mm: { 2023: 162_613, 2024: 182_581 }, cert: 'real', fuente: 'Sistema Nacional de Información Municipal (SINIM)', color: RAINBOW[2] },
  { label: 'Ley Ricarte Soto', sub: 'fondo separado que financia tratamientos de alto costo para un conjunto definido de patologías. Es una línea propia, aditiva, que no baja a los Servicios de Salud.', mm: { 2023: 147_762, 2024: 189_696 }, cert: 'real', fuente: 'Aplicación de la Ley 20.850 en FONASA (DIPRES)', color: RAINBOW[0] },
  { label: 'Vacunas del calendario', sub: 'solo el componente biológico de las vacunas. Se cuenta aparte porque su función es prevenir, no tratar.', mm: { 2023: 30_000, 2024: 30_000 }, cert: 'estimacion', fuente: 'Componente biológico aislado del Programa Nacional de Inmunizaciones (Monitoreo DIPRES)', color: RAINBOW[6] },
]

export const NUCLEO_TOTAL: Record<number, number> = { 2023: 1_077_136, 2024: 1_177_893 }
export const NUCLEO_PIB: Record<number, string> = { 2023: 'cerca de 0,4% del PIB', 2024: 'cerca de 0,4% del PIB' }
export const BANDA_PIB = 'cerca de 0,4% del PIB'
export const ANIOS_PUBLICO = [2023, 2024] as const

// Componentes que NO entran al núcleo (cada uno mira el mismo gasto de otro
// modo, o ya está contado adentro). Se muestran como contexto, nunca se suman.
export interface FueraPieza { label: string; sub: string; mm?: number; banda?: string; cert: Cert; fuente: string; razon: string }
export const FUERA_DEL_NUCLEO: FueraPieza[] = [
  { label: 'Medicamento dentro del hospital (público)', sub: 'el que se administra durante la internación en la red pública. No tiene línea propia.', banda: '280.000 (banda 250.000 a 725.000)', cert: 'estimacion', fuente: 'Cifra derivada de las cuentas de la OCDE, 2022', razon: 'Se obtiene por diferencia, no de una línea de presupuesto. Por eso es una banda amplia y se reporta dentro del gasto total del país, no en el zoom público. Vive en el filtro A.' },
  { label: 'Bolsillo de los hogares (encuesta de hogares)', sub: 'lo que las familias pagan directo, medido desde los hogares.', mm: 1_725_000, cert: 'real', fuente: 'Encuesta de Presupuestos Familiares del INE', razon: 'Gasto privado, queda fuera del perímetro público. Es además otra medición, distinta de la de la OCDE, y no se mezcla con ella.' },
]

// Cómo se abre la línea de Farmacia (por nivel de atención y por provisión),
// con la proporción derivada de otras vistas oficiales (2024).
export const FARMACIA_2024 = 775_616
export const FARMACIA_NIVEL = [
  { label: 'Ambulatorio (fuera del hospital)', pct: 76.5, mm: 593_434, cert: 'real' as Cert, fuente: 'Reparto de las cuentas de la OCDE, 2022, aplicado a la línea 2024' },
  { label: 'Hospitalario (dentro del hospital)', pct: 23.5, mm: 182_182, cert: 'estimacion' as Cert, fuente: 'Cifra derivada, no separable directamente en el presupuesto' },
]
export const FARMACIA_PROVISION = [
  { label: 'Intermediada por CENABAST', pct: 82.4, mm: 639_108, cert: 'real' as Cert, fuente: 'Datos de Mercado Público, 2024' },
  { label: 'Compra directa del Servicio y retail', pct: 17.6, mm: 136_508, cert: 'real' as Cert, fuente: 'Datos de Mercado Público, 2024' },
]

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 5 · La carga cae más fuerte en los hogares de menores ingresos.
// Quintil congelado: bajo 9,6% vs alto 1,8% del ingreso del hogar (≈5,4 veces).
// IX EPF 2021-2022, denominador estándar OMS/MINSAL (base hogar).
// ─────────────────────────────────────────────────────────────────────────────
export const T5 = {
  num: 5,
  titulo: 'La carga cae más fuerte en los hogares de menores ingresos',
} as const
export const CARGA_QUINTIL = {
  anio: '2021-2022',
  fuente: 'Encuesta de Presupuestos Familiares del INE (microdato), denominador por hogar (estándar OMS/MINSAL)',
  quintiles: [
    { q: 'Quintil de menos ingreso', value: 9.6, color: EP.red },
    { q: 'Quintil 2', value: 3.5, color: EP.accent },
    { q: 'Quintil 3', value: 2.9, color: EP.accent },
    { q: 'Quintil 4', value: 2.8, color: EP.accent },
    { q: 'Quintil de más ingreso', value: 1.8, color: EP.accent },
  ],
  nota: 'Gasto de bolsillo en medicamentos como porcentaje del ingreso del hogar, por quintil. El quintil de menos ingreso destina cerca de 5,4 veces más de su ingreso que el de más ingreso.',
}

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 6 · Para una parte de los hogares el gasto es catastrófico.
// Xu chileno, umbral 30% de la capacidad de pago, IX EPF 2021-2022:
// salud total 6,5% de los hogares · solo medicamentos 1,0%.
// ─────────────────────────────────────────────────────────────────────────────
export const T6 = {
  num: 6,
  titulo: 'Para una parte de los hogares el gasto es catastrófico',
  bajada: 'Un gasto en salud es catastrófico cuando se come una parte tan grande del presupuesto del hogar que desplaza lo básico. Con el umbral chileno (30% de la capacidad de pago), el 6,5% de los hogares cae en gasto catastrófico por salud, y el 1,0% por medicamentos solos.',
  anio: '2021-2022',
  fuente: 'Recompute propio sobre el microdato de la IX Encuesta de Presupuestos Familiares del INE, método Xu, umbral del 30% de la capacidad de pago',
  items: [
    { label: 'Hogares con gasto catastrófico en salud', pct: 6.5, hogares: '287.002 hogares', color: EP.primary },
    { label: 'Hogares con gasto catastrófico solo en medicamentos', pct: 1.0, hogares: '42.518 hogares', color: EP.red },
  ],
  nota: 'El medicamento solo explica una porción del gasto catastrófico en salud, pero es una porción evitable: depende de la cobertura.',
} as const

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 7 · La judicialización por medicamentos crece año a año y se concentra
// en fármacos de muy alto costo.
// Judicial público congelado: 32.679 (2023) → 81.000 (2024) → 89.821 (2025).
// FFAA piso 1.955 (2024). Bolsillo hospitalario meds banda 50.000 a 160.000.
// Judicial privado ISAPRE: sin cifra agregada (gap).
// ─────────────────────────────────────────────────────────────────────────────
export const T7 = {
  num: 7,
  titulo: 'La judicialización por medicamentos crece año a año y se concentra en fármacos de muy alto costo',
  bajada: 'El gasto público por fallo en medicamentos crece fuerte año a año y se concentra en fármacos de altísimo costo, que la persona obtiene por un fallo y no por la cobertura ordinaria.',
} as const

// Serie del judicial público (porción medicamentos vía fallo, FONASA).
export const JUDICIAL_PUBLICO = [
  { anio: 2023, mm: 32_679, cert: 'real' as Cert },
  { anio: 2024, mm: 81_000, cert: 'estimacion' as Cert },
  { anio: 2025, mm: 89_821, cert: 'real' as Cert },
]
export const JUDICIAL_NOTA = 'Porción medicamentos del gasto público por sentencia. El salto de 2023 a 2024 es de cerca de 148%. La composición de los 81.000 (2024) es Trikafta 37.866 (fibrosis quística) más AME cerca de 18.400 (atrofia muscular espinal) más un residual de otras sentencias.'

// Otras piezas fuera de las listas cerradas, con su perímetro y su año.
export interface CoberturaItem { label: string; sub: string; valor: string; cert: Cert; fuente: string; anio: string }
export const COBERTURA_FUERA: CoberturaItem[] = [
  { label: 'Judicial privado (ISAPRE)', sub: 'las ISAPRE también son condenadas a cubrir medicamentos de alto costo por fallo, pero ese desembolso se diluye en la siniestralidad y no se reporta separado.', valor: 'sin cifra agregada', cert: 'estimacion', fuente: 'No existe agregado público en pesos. El monto de 34.000 millones que circula es litigio por alza de planes, no medicamentos', anio: 's/serie' },
  { label: 'Sanidad de las Fuerzas Armadas y de Orden', sub: 'la farmacia militar va bajo glosa reservada y no aparece en la ejecución pública. Lo único visible y estable es la sanidad de Carabineros.', valor: '1.955 millones (piso trazable)', cert: 'real', fuente: 'Ejecución del ítem de Productos Farmacéuticos, presupuestoabierto.gob.cl, dominado por el Hospital de Carabineros', anio: '2024' },
  { label: 'Bolsillo en medicamentos dentro de una hospitalización', sub: 'lo que el paciente paga de su bolsillo por el fármaco durante una internación, sobre todo en clínica privada.', valor: 'banda 50.000 a 160.000 millones', cert: 'estimacion', fuente: 'Cuentas de salud de la OCDE y EPF para el continente; fracción de farmacia hospitalaria estimada (15% a 25%)', anio: '2022' },
]

// ─────────────────────────────────────────────────────────────────────────────
// TÍTULO 8 · Preguntas abiertas para el debate.
// ─────────────────────────────────────────────────────────────────────────────
export const T8 = {
  num: 8,
  titulo: 'Preguntas abiertas para el debate',
  bajada: 'Esta reconstrucción deja la cifra sobre la mesa. Lo que sigue son las preguntas que esa cifra abre, no las respuestas.',
  preguntas: [
    'Si el bolsillo paga el 71% del medicamento ambulatorio, ¿qué instrumento baja esa carga sin agrandar la judicialización?',
    'Si la cobertura por listas cerradas deja fuera el crónico masivo, ¿conviene cubrir por problema de salud o por nivel de gasto del hogar?',
    'El gasto público por fallo crece cerca de 148% en un año. ¿Es sostenible cubrir por sentencia lo que no cubre la garantía ordinaria?',
    'El medicamento de uso dentro del hospital y el judicial privado de ISAPRE no tienen cifra propia. ¿Qué registro habría que abrir para medirlos?',
    'La carga catastrófica por medicamentos cae sobre el quintil de menos ingreso. ¿Cuánto de eso es evitable solo con mejor cobertura?',
  ],
} as const
