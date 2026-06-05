// Módulo de datos compartido, contrato único para todos los componentes.
// Fuente: OECD SHA (DSD_SHA@DF_SHA) para Chile, verificado contra SDMX. Datos en
// explorer-data.json (consolidado de los pulls + metadata oficial OECD-Chile).
import raw from './data/explorer-data.json'

export type Unit = 'usd' | 'usd_pc' | 'pib' | 'salud'
export interface Cell { hc: string; hf: string; year: number; usd: number | null; usd_pc: number | null; pib: number | null; salud: number | null }
export interface CompCode { code: string; desc: string; status: string; expl: string }
export interface Source { name: string; desc: string; type: string; vars: string }
export interface TreeNode { code: string; es: string; en: string; level: number; chile?: string }

export const META = raw.meta as { pais: string; dataset: string; años: string; precio: string }
export const cube = raw.cube as Cell[]
export const hcxhp = raw.hcxhp as Record<string, Record<string, number>>
export const hpxhf = raw.hpxhf as Record<string, Record<string, number>>
export const HP_LABEL = raw.hp_label as Record<string, string>
export const comparability = raw.comparability as CompCode[]
export const dataSources = raw.data_sources as Source[]

export const UNITS: { key: Unit; label: string; short: string }[] = [
 { key: 'usd', label: 'USD PPA (millones)', short: 'USD mill.' },
 { key: 'usd_pc', label: 'USD PPA per cápita', short: 'USD pc' },
 { key: 'pib', label: '% del PIB', short: '% PIB' },
 { key: 'salud', label: '% del gasto en salud (CHE)', short: '% salud' },
]
export const YEARS = Array.from(new Set(cube.map(c => c.year))).sort()

// ── Jerarquía de financiamiento (ICHA-HF), con la lectura chilena ──
export const HF_TREE: TreeNode[] = [
 { code: '_T', es: 'TOTAL', en: 'All financing schemes', level: 0 },
 { code: 'HF1', es: 'Público / obligatorio', en: 'Government & compulsory', level: 0, chile: 'FONASA + el 7% obligatorio de ISAPRE + aporte fiscal' },
 { code: 'HF11', es: 'Esquemas de gobierno', en: 'Government schemes', level: 1, chile: 'ISP, CENABAST, SEREMI, Subsecretarías, aporte fiscal directo' },
 { code: 'HF121', es: 'Seguro social', en: 'Social health insurance', level: 1, chile: 'FONASA, Mutuales, FF.AA. y de Orden' },
 { code: 'HF122', es: 'Seguro privado obligatorio', en: 'Compulsory private insurance', level: 1, chile: 'ISAPRE, el 7% de cotización obligatoria' },
 { code: 'HF2', es: 'Voluntario', en: 'Voluntary schemes', level: 0, chile: 'ISAPRE complementario, seguros, NPISH' },
 { code: 'HF21', es: 'Seguro voluntario', en: 'Voluntary health insurance', level: 1, chile: 'ISAPRE complemento + seguros privados' },
 { code: 'HF22', es: 'NPISH (sin fines de lucro)', en: 'NPISH financing', level: 1, chile: 'COANIQUEM, TELETÓN, Hogar de Cristo' },
 { code: 'HF3', es: 'Bolsillo de los hogares', en: 'Household out-of-pocket', level: 0, chile: 'Copagos + compra directa; estimado de la EPF (INE)' },
 { code: 'HF31', es: 'Bolsillo sin cost-sharing', en: 'OOP excl. cost-sharing', level: 1, chile: 'Pago directo sin seguro' },
 { code: 'HF32', es: 'Cost-sharing (copagos)', en: 'Cost-sharing with third party', level: 1, chile: 'Copagos dentro de FONASA/ISAPRE' },
]
// ── Jerarquía de funciones (ICHA-HC) ──
export const HC_TREE: TreeNode[] = [
 { code: '_T', es: 'TOTAL salud (CHE)', en: 'Current health expenditure', level: 0 },
 { code: 'HC1', es: 'Atención curativa (incl. fármaco hospitalario)', en: 'Curative care', level: 0, chile: 'Hospitales públicos (SIGFE+WinSIG/PERC); el fármaco intrahospitalario va embebido aquí' },
 { code: 'HC2', es: 'Rehabilitación', en: 'Rehabilitative care', level: 0 },
 { code: 'HC3', es: 'Larga duración (salud)', en: 'Long-term care (health)', level: 0 },
 { code: 'HC4', es: 'Servicios auxiliares', en: 'Ancillary services', level: 0 },
 { code: 'HC41', es: 'Laboratorio', en: 'Laboratory', level: 1 },
 { code: 'HC42', es: 'Imagenología', en: 'Imaging', level: 1 },
 { code: 'HC43', es: 'Transporte de pacientes', en: 'Patient transportation', level: 1 },
 { code: 'HC5', es: 'Bienes médicos', en: 'Medical goods', level: 0 },
 { code: 'HC51', es: 'Medicamentos (ambulatorio/retail)', en: 'Pharmaceuticals & non-durables', level: 1, chile: 'SIGFE (SNSS) + SINIM (APS) + Superintendencia (ISAPRE). Recetado+OTC sin desagregar' },
 { code: 'HC52', es: 'Aparatos terapéuticos', en: 'Therapeutic appliances', level: 1 },
 { code: 'HC6', es: 'Prevención', en: 'Preventive care', level: 0 },
 { code: 'HC61', es: 'Información y educación', en: 'IEC programmes', level: 1 },
 { code: 'HC62', es: 'Inmunización (PNI)', en: 'Immunisation', level: 1 },
 { code: 'HC65', es: 'Vigilancia epidemiológica', en: 'Epidemiological surveillance', level: 1 },
 { code: 'HC7', es: 'Gobernanza y administración', en: 'Governance & administration', level: 0 },
 { code: 'HC71', es: 'Gobernanza del sistema', en: 'System governance', level: 1 },
 { code: 'HC72', es: 'Administración del financiamiento', en: 'Financing administration', level: 1 },
 { code: 'HC0', es: 'No clasificado por función', en: 'Unspecified', level: 0, chile: '~20% del gasto que Chile no clasifica por función (caveat JHAQ)' },
]
export const HP_ORDER = ['HP1', 'HP2', 'HP3', 'HP4', 'HP5', 'HP6', 'HP7', '_U']

const idx = new Map<string, Cell>()
for (const c of cube) idx.set(`${c.hc}|${c.hf}|${c.year}`, c)
export function cell(hc: string, hf: string, year: number, unit: Unit): number | null {
 const c = idx.get(`${hc}|${hf}|${year}`); return c ? c[unit] : null
}
export const labelHF = (c: string) => HF_TREE.find(n => n.code === c)?.es ?? c
export const labelHC = (c: string) => HC_TREE.find(n => n.code === c)?.es ?? c

// formato es-CL
export const fmt = (v: number | null, unit: Unit): string => {
 if (v == null) return '·'
 if (unit === 'pib' || unit === 'salud') return v.toFixed(v < 1 ? 3 : 1).replace('.', ',') + '%'
 return v.toLocaleString('es-CL', { maximumFractionDigits: 1 })
}
export const pct = (v: number | null): string => v == null ? '·' : (v).toFixed(1).replace('.', ',') + '%'
// CLP en millones (MM$): miles con punto, es-CL. Para los números DUROS OCDE/CIF en CLP.
export const clp = (v: number): string => v.toLocaleString('es-CL', { maximumFractionDigits: 0 })

// ── Números DUROS HC.5.1 (OECD SHA, Chile 2022, en CLP MM$), fuente-de-verdad v10 §1 ──
// HC.5.1 = medicamentos DISPENSADOS para uso AMBULATORIO, por cualquier canal (retail + hospital
// a externos + APS). NO es "todos los medicamentos": excluye el fármaco de internación (HC.1) y
// las vacunas (HC.6.2 = PNI). Sumas que CIERRAN a la unidad contra el total.
export const HC51_2022 = {
 total_mm: 3_518_751, // MM$ CLP · = 1,34% PIB · = 13,4% gasto salud · = 8.260 USD PPA · FIRME (re-arquitectura v8)
 pib: 1.34, // % del PIB (unidad primaria)
 salud: 13.4, // % del gasto en salud
 usd_ppa: 8260, // USD PPA millones (rotulado: dólar ajustado por poder de compra, no de mercado)
 // Por CANAL de dispensación (proveedor), Σ = total. Reparto firme 54,5 / 30,6 / 14,9.
 canal: [
 { code: 'HP.5', label: 'Retail', sub: 'farmacia de venta al público', mm: 1_917_719, pctv: 54.5 },
 { code: 'HP.1', label: 'Hospital (pacientes externos)', sub: 'farmacia hospitalaria a ambulatorios', mm: 1_076_738, pctv: 30.6 },
 { code: 'HP.3', label: 'APS', sub: 'CESFAM y consultorios municipales', mm: 524_294, pctv: 14.9 },
 ],
 // Por FINANCIADOR, Σ = total. Cifras firmes re-arquitectura v8 (bolsillo banda ~71%,
 // público HF.1 celda dura 25,5%, voluntario HF.2 3,5%).
 financiador: [
 { code: 'HF.1', label: 'Público / obligatorio', sub: 'aporte fiscal + FONASA + 7% ISAPRE', mm: 897_282, pctv: 25.5, salud: 3.42 },
 { code: 'HF.2', label: 'Voluntario', sub: 'ISAPRE complementario + seguros + NPISH', mm: 123_156, pctv: 3.5, salud: 0.47 },
 { code: 'HF.3', label: 'Bolsillo de los hogares', sub: 'copago + compra directa sin reembolso', mm: 2_498_313, pctv: 71.0, salud: 9.56 },
 ],
 // Desglose FINO del público (HF.1), OCDE SHA 2022, CLP MM$ · hallazgos v11 §1.
 // El aporte fiscal PURO (impuestos, HF11) al medicamento ambulatorio es ≈0,4%:
 // casi todo lo "obligatorio" es contributivo (cotización FONASA + 7% obligatorio ISAPRE).
 publicoFino: [
 { code: 'HF.1.1', label: 'Aporte fiscal puro (impuestos)', sub: 'ISP, CENABAST, SEREMI, Subsecretarías', mm: 14_075, pctv: 0.4 },
 { code: 'HF.1.2.1', label: 'FONASA (cotización social)', sub: 'seguro social, Mutuales y FF.AA.', mm: 524_294, pctv: 14.9 },
 { code: 'HF.1.2.2', label: 'ISAPRE 7% obligatorio', sub: 'cotización obligatoria gestionada por ISAPRE', mm: 358_913, pctv: 10.2 },
 ],
} as const

// ── Banda honesta del fármaco INTRAHOSPITALARIO público, hallazgos v11 §3 ──
// Ninguna de las 5 fuentes lo aísla (OCDE lo embebe en HC.1; CIF no lo separa; CNEP
// lo mezcla con dispositivos). La derivación algebraica (público_total − ambulatorio
// público − PNI) da el punto ~246.000, pero ese cierre es CASI TAUTOLÓGICO: su único
// ancla empírica es que el bolsillo OCDE (0,956% PIB) ≈ bolsillo CIF (0,95%), ambos de
// la EPF. Por eso la banda HONESTA es 250.000–725.000 (central ~485.000), un MARCO
// QUE ACOTA, no una prueba. El punto algebraico ~246.000 se conserva sólo como línea
// de cuadre contable contra el total público 1.514.814; la cifra reportable es la banda.
export const HOSP_BANDA = {
 lo: 250_000,
 hi: 725_000,
 central: 485_000,
 algebraico: 246_000, // punto de cuadre (público total − ambulatorio público − PNI)
 rango: '250.000–725.000',
 centralStr: '≈485.000',
 nota: 'cierre algebraico/casi tautológico, marco que ACOTA, no prueba',
} as const

// ── CNEP 2024 (Informe Gasto Hospitalario), corrobora MAGNITUD, no aísla el fármaco ──
export const CNEP_2024 = {
 arsenalMM: 1_450_000, // fármacos + dispositivos hospitalarios 2023 ≈ 1,45 billones
 creceReal: '+23% real 2018-2023',
 concentracion: '16% de los hospitales = 75% del gasto',
 compra: 'Convenio Marco 45% · CENABAST 25% · compra directa 30%',
 caveat: 'trata fármacos y dispositivos JUNTOS, corrobora el orden de magnitud, NO aísla el fármaco intrahospitalario',
} as const

// Paleta institucional Espacio Público (rainbow oficial sampleado del informe)
export const EP = { primary: '#1a365d', accent: '#2b6cb0', red: '#c53030', amber: '#fef3c7', amberInk: '#92400e' }
export const RAINBOW = ['#F2920B', '#B1A35E', '#1CA29A', '#138691', '#196883', '#1C4E75', '#213366', '#4B3B7C', '#764494']

// ── Glosario para el hover de códigos (CodeRef) ──
// Lidera con el nombre DESCRIPTIVO en español; el código y su definición corta aparecen al hover.
// Clave = código tal como se escribe en la narrativa (con puntos).
export const GLOSARIO: Record<string, { nombre: string; def: string }> = {
 'HC.1': { nombre: 'Atención curativa', def: 'Servicios para aliviar o curar una enfermedad o lesión. El fármaco administrado en hospitalización va embebido aquí (no es separable).' },
 'HC.5': { nombre: 'Bienes médicos', def: 'Medicamentos y otros bienes médicos no duraderos + aparatos terapéuticos.' },
 'HC.5.1': { nombre: 'Medicamentos ambulatorios', def: 'Productos farmacéuticos no duraderos de consumo ambulatorio, por todos los canales (farmacia retail, hospital y APS). Recetado + venta libre.' },
 'HC.5.1.1': { nombre: 'Medicamentos recetados', def: 'Subnivel de HC.5.1. No reportado por Chile (Missing).' },
 'HC.5.1.2': { nombre: 'Venta libre (OTC)', def: 'Subnivel de HC.5.1. No reportado por Chile (Missing).' },
 'HC.6': { nombre: 'Prevención', def: 'Atención preventiva. Incluye HC.6.2 = inmunización (PNI). El medicamento preventivo (vacunas) NO está en HC.5.1.' },
 'HC.6.2': { nombre: 'Inmunización (PNI)', def: 'Vacunas del Programa Nacional de Inmunizaciones. Función preventiva, no medicamento de tratamiento. Es línea presupuestaria propia, NO se cuenta en HC.5.1.' },
 'HC.0': { nombre: 'No clasificado por función', def: '~23% del gasto en salud que Chile no asigna a una función específica (caveat JHAQ).' },
 'HC.RI.1': { nombre: 'Gasto farmacéutico total', def: 'Retail + hospital. NO reportado por Chile (Missing): el total exige estimación.' },
 'CHE': { nombre: 'Gasto corriente en salud', def: 'Total del consumo de bienes y servicios de salud del año (suma de las funciones HC.1–HC.7). Es el denominador de referencia.' },
 'HF.1': { nombre: 'Obligatorio', def: 'Financiamiento obligatorio: aporte fiscal (impuestos) + cotizaciones obligatorias (FONASA + el 7% obligatorio de ISAPRE). En el medicamento ambulatorio es 25,5% de HC.5.1; casi todo es contributivo, el aporte fiscal puro es solo 0,4%. "Obligatorio" (no "público"): la mayor parte son cotizaciones, no impuestos.' },
 'HF.1.1': { nombre: 'Aporte fiscal puro (impuestos)', def: 'Esquemas de gobierno financiados con impuestos generales: ISP, CENABAST, SEREMI, Subsecretarías. En el medicamento ambulatorio es 0,4% de HC.5.1 (≈14.075 MM$): la mayor parte del financiamiento obligatorio es contributivo, no por impuestos.' },
 'HF.1.2.1': { nombre: 'Seguro social (FONASA)', def: 'Cotización obligatoria administrada por una entidad pública. Incluye FONASA, Mutuales y FF.AA. Es el grueso del financiamiento obligatorio en medicamentos: 14,9% de HC.5.1 (≈524.294 MM$).' },
 'HF.1.2.2': { nombre: 'ISAPRE obligatorio (7%)', def: 'El 7% de cotización obligatoria gestionado por ISAPRE. Cuenta como obligatorio (HF.1.2 compulsory) pese al administrador privado, igual que FONASA: 10,2% de HC.5.1 (≈358.913 MM$).' },
 'HF.2': { nombre: 'Voluntario', def: 'ISAPRE complementario sobre el 7% + seguros privados + instituciones sin fines de lucro.' },
 'HF.2.1': { nombre: 'Seguro voluntario', def: 'Complemento ISAPRE sobre el 7% obligatorio y seguros privados complementarios.' },
 'HF.3': { nombre: 'Bolsillo de los hogares', def: 'Pago directo del hogar: copagos + compra directa sin reembolso de un tercero.' },
 'HP.1': { nombre: 'Hospitales', def: 'Proveedor: establecimientos hospitalarios.' },
 'HP.3': { nombre: 'Atención primaria (APS)', def: 'Proveedor: CESFAM y consultorios municipales.' },
 'HP.5': { nombre: 'Farmacias (retail)', def: 'Proveedor: farmacias de venta al público (Cruz Verde, Salcobrand, Ahumada, populares).' },
 'HP.5.1': { nombre: 'Farmacias (subnivel)', def: 'Subnivel de HP.5. No reportado por Chile (Missing); el agregado HP.5 sí se reporta.' },
 'FS.1': { nombre: 'Impuestos', def: 'Fuente de ingreso: transferencias del gobierno desde impuestos generales.' },
 'FS.3': { nombre: 'Cotizaciones', def: 'Fuente de ingreso: cotizaciones sociales de trabajadores y empleadores.' },
 // ── Programas de cobertura chilenos (NO son códigos SHA): etiquetas sobre medicamentos ya contados ──
 'GES': { nombre: 'GES / AUGE', def: 'Garantías Explícitas en Salud: ~90 problemas con cobertura garantizada. Es una ETIQUETA de cobertura, no una línea presupuestaria: su medicamento ya está contado en el objeto de gasto. NO se suma a SS/DAC/FOFAR.' },
 'LRS': { nombre: 'Ley Ricarte Soto', def: 'Fondo para diagnósticos y tratamientos de alto costo (~27 patologías). Línea presupuestaria propia y ADITIVA (175.672 MM$, ejecución 2025; no baja a los Servicios de Salud, no está dentro de Farmacia). El alto costo administrado en internación cae en HC.1, no en HC.5.1.' },
 'DAC': { nombre: 'Drogas de Alto Costo', def: 'Cobertura de fármacos oncológicos y de alto costo en los Servicios de Salud, vía Glosa 11 (70.803 MM$, 2025). Es una ETIQUETA de cobertura DENTRO de la Farmacia de los Servicios de Salud: no se suma aparte (sería doble conteo).' },
 'FOFAR': { nombre: 'Fondo de Farmacia', def: 'Fondo de Farmacia para enfermedades crónicas no transmisibles en APS (hipertensión, diabetes, dislipidemia). ETIQUETA de cobertura sobre el medicamento de APS, que SÍ está dentro de HC.5.1 (canal APS). Se reporta vía SINIM.' },
 'PNI': { nombre: 'Programa Nacional de Inmunizaciones', def: 'Vacunas. Línea presupuestaria propia (~30.000 MM$, 2024). Mapea a HC.6.2 (prevención), NO a HC.5.1: el medicamento preventivo no se cuenta como medicamento de tratamiento.' },
 'CEM': { nombre: 'Cobertura Especial / Medicamentos', def: 'Cobertura especial de medicamentos. ETIQUETA de cobertura: no es una línea propia, no se suma al resto.' },
 'CENABAST': { nombre: 'Central de Abastecimiento (CENABAST)', def: 'Compra y distribución intermediada del SNSS. Es flujo de aprovisionamiento (intermedia ~79% del gasto), no una línea aparte: lo que provee ya está contado en el objeto de gasto del comprador final.' },
}

// Presets "nuestros datos": qué filtro produce cada cifra del informe
export interface Preset { id: string; label: string; rowDim: 'HC' | 'HF'; colDim: 'HC' | 'HF'; unit: Unit; year: number; focusHC?: string; focusHF?: string; note: string }
export const PRESETS: Preset[] = [
 { id: 'p71', label: '≈71% bolsillo en medicamentos', rowDim: 'HC', colDim: 'HF', unit: 'pib', year: 2022, focusHC: 'HC51', focusHF: 'HF3', note: 'HC51·HF3 ÷ HC51·_T ≈ 71% (bolsillo sobre medicamentos ambulatorios, 2022).' },
 { id: 'fonasa', label: 'FONASA vs ISAPRE en medicamentos', rowDim: 'HC', colDim: 'HF', unit: 'usd', year: 2023, focusHC: 'HC51', note: 'HC51 por subesquema: FONASA (HF121) vs ISAPRE-7% (HF122) vs ISAPRE-voluntario (HF21) vs bolsillo (HF3).' },
 { id: 'pubcomp', label: 'Composición del gasto público', rowDim: 'HC', colDim: 'HF', unit: 'usd', year: 2023, focusHF: 'HF1', note: 'HF1 = HF11 gobierno + HF121 FONASA + HF122 ISAPRE-obligatorio.' },
 { id: 'oop', label: 'Bolsillo sobre toda la salud', rowDim: 'HC', colDim: 'HF', unit: 'salud', year: 2022, focusHC: '_T', focusHF: 'HF3', note: '_T·HF3 ÷ CHE ≈ 35,6% (bolsillo total, no solo medicamentos).' },
]
