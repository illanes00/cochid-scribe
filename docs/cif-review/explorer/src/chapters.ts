// Modelo de navegación unificado de la SPA: una portada, seis capítulos
// numerados (el recorrido del informe) y dos secciones de referencia
// (modelo de datos/fuentes y esqueleto lógico). El Layout arma el menú y el
// pager prev/next a partir de NAV_ORDER; Home arma su grilla con CHAPTERS.

export interface Chapter {
  num?: number
  route: string
  title: string
  short?: string
  blurb?: string
}

// Portada.
export const HOME: Chapter = {
  route: '/',
  title: 'El gasto en medicamentos en Chile',
  short: 'Inicio',
}

// Los seis capítulos del recorrido, en orden descendente (del total al hogar y
// de ahí a los instrumentos, la comparación y el marco).
export const CHAPTERS: Chapter[] = [
  {
    num: 1,
    route: '/jerarquia',
    title: 'La jerarquía del gasto',
    short: 'Jerarquía',
    blurb: 'Del gasto en salud total al bolsillo del hogar, peso a peso: el recorrido descendente con sus ocho títulos, el núcleo público disjunto y la carga por quintil.',
  },
  {
    num: 2,
    route: '/medicamento',
    title: 'El medicamento dentro de la salud',
    short: 'Medicamento',
    blurb: 'El medicamento ambulatorio (HC.5.1), el dato duro de la OCDE: cuánto pesa, quién lo paga, por qué canal, y el modelo de cierre que reconcilia las vistas.',
  },
  {
    num: 3,
    route: '/explorador',
    title: 'El cubo OCDE y las áreas del gasto',
    short: 'Explorador',
    blurb: 'Exploración libre: el cubo función × proveedor × financiador para un año, el treemap de áreas con capas conmutables y los diagramas de flujo (Sankey).',
  },
  {
    num: 4,
    route: '/instrumentos',
    title: 'Instrumentos y presupuesto',
    short: 'Instrumentos',
    blurb: 'Cada instrumento de la política ubicado en los ejes SHA, el cruce DIPRES→OCDE, el gasto municipal (SINIM), la evolución de Farmacia 2010-2024, su reparto por Servicio de Salud y la compra (Mercado Público) por laboratorio y clase.',
  },
  {
    num: 5,
    route: '/comparacion',
    title: 'Síntesis y comparación internacional',
    short: 'Comparación',
    blurb: 'La composición del gasto y la carga sobre los hogares, puestas en perspectiva: Chile frente a la OCDE, con su lugar en la distribución de cada indicador.',
  },
  {
    num: 6,
    route: '/marco',
    title: 'Marco SHA y comparabilidad',
    short: 'Marco',
    blurb: 'La gramática de las cuentas de salud (HF/HC/HP/FS), la taxonomía de códigos, el gasto en salud total como punto de partida y la comparabilidad OCDE-Chile.',
  },
]

// Referencia / apéndice: no numeradas, van al final del recorrido.
export const REFERENCIA: Chapter[] = [
  {
    route: '/fuentes',
    title: 'Modelo de datos y fuentes',
    short: 'Fuentes',
    blurb: 'El linaje de los datos (fuentes → bronze/silver/gold → vistas), el esquema cochid_datos.meds, los crosswalks entre clasificaciones y las descargas para auditar cada cifra.',
  },
  {
    route: '/esqueleto',
    title: 'Esqueleto lógico del informe',
    short: 'Esqueleto',
    blurb: 'El hilo argumental completo de un vistazo: cómo se encadena cada pieza del informe, del gasto en salud total a la carga del medicamento sobre los hogares.',
  },
]

// Orden de navegación completo: portada, capítulos y referencia.
export const NAV_ORDER: Chapter[] = [HOME, ...CHAPTERS, ...REFERENCIA]

// Vecinos prev/next para el pager, según el orden de navegación.
export function neighbors(route: string): { prev?: Chapter; next?: Chapter } {
  const i = NAV_ORDER.findIndex(x => x.route === route)
  if (i === -1) return {}
  return { prev: NAV_ORDER[i - 1], next: NAV_ORDER[i + 1] }
}

// Título a mostrar para una ruta dada (con su número si es capítulo).
export function titleFor(route: string): string {
  const c = NAV_ORDER.find(x => x.route === route)
  if (!c) return ''
  return c.num ? `${c.num} · ${c.title}` : c.title
}
