// Datos de los "gaps" que el hub estático viejo mostraba y que faltaban en la
// SPA React. Horneados desde cochid_datos.meds (DIPRES + Mercado Público),
// la misma fuente de verdad del informe. Montos en MM$ (millones de pesos).
// Fuente y año anotados por bloque. NO se suman entre vistas: son perímetros
// distintos del mismo gasto.

// ── Evolución de la línea Farmacia de los Servicios de Salud, 2010-2024 ──
// Ejecución presupuestaria 22.04.004.001 (DIPRES). Nominal y deflactado a
// pesos de 2024. meds.serie_farmacia.
export interface FarmaciaAnio { anio: number; nominal: number; real2024: number }
export const SERIE_FARMACIA: FarmaciaAnio[] = [
  { anio: 2010, nominal: 184_024, real2024: 323_902 },
  { anio: 2011, nominal: 248_634, real2024: 423_643 },
  { anio: 2012, nominal: 263_098, real2024: 435_231 },
  { anio: 2013, nominal: 296_328, real2024: 481_533 },
  { anio: 2014, nominal: 345_428, real2024: 537_664 },
  { anio: 2015, nominal: 396_388, real2024: 591_548 },
  { anio: 2016, nominal: 402_771, real2024: 579_069 },
  { anio: 2017, nominal: 459_963, real2024: 647_059 },
  { anio: 2018, nominal: 517_889, real2024: 711_473 },
  { anio: 2019, nominal: 503_451, real2024: 676_087 },
  { anio: 2020, nominal: 573_664, real2024: 747_938 },
  { anio: 2021, nominal: 613_605, real2024: 765_562 },
  { anio: 2022, nominal: 648_288, real2024: 724_762 },
  { anio: 2023, nominal: 736_761, real2024: 765_494 },
  { anio: 2024, nominal: 775_616, real2024: 775_616 },
]

// ── Farmacia por Servicio de Salud, 2024 (MM$) ──
// Reparto territorial de la línea Farmacia entre los 29 Servicios de Salud y 2
// Centros de Referencia. meds.farmacia_servicio.
export interface ServicioFila { servicio: string; mm: number }
export const FARMACIA_SERVICIO_2024: ServicioFila[] = [
  { servicio: 'Metropolitano Sur-Oriente', mm: 66_027 },
  { servicio: 'Metropolitano Oriente', mm: 58_677 },
  { servicio: 'Maule', mm: 48_301 },
  { servicio: 'Metropolitano Sur', mm: 43_369 },
  { servicio: 'Metropolitano Occidente', mm: 42_652 },
  { servicio: 'Concepción', mm: 40_773 },
  { servicio: 'Araucanía Sur', mm: 39_802 },
  { servicio: 'Metropolitano Central', mm: 39_516 },
  { servicio: 'Viña del Mar - Quillota', mm: 36_057 },
  { servicio: 'Metropolitano Norte', mm: 32_938 },
  { servicio: "O'Higgins", mm: 32_795 },
  { servicio: 'Coquimbo', mm: 31_001 },
  { servicio: 'Del Reloncaví', mm: 28_854 },
  { servicio: 'Valparaíso - San Antonio', mm: 25_414 },
  { servicio: 'Ñuble', mm: 23_215 },
  { servicio: 'Biobío', mm: 22_558 },
  { servicio: 'Antofagasta', mm: 22_542 },
  { servicio: 'Talcahuano', mm: 21_473 },
  { servicio: 'Los Ríos', mm: 19_729 },
  { servicio: 'Magallanes', mm: 14_307 },
  { servicio: 'Osorno', mm: 12_762 },
  { servicio: 'Tarapacá', mm: 10_500 },
  { servicio: 'Arica y Parinacota', mm: 10_330 },
  { servicio: 'Aconcagua', mm: 10_001 },
  { servicio: 'Atacama', mm: 9_695 },
  { servicio: 'Araucanía Norte', mm: 9_636 },
  { servicio: 'Arauco', mm: 7_888 },
  { servicio: 'Aysén', mm: 7_612 },
  { servicio: 'Chiloé', mm: 5_585 },
  { servicio: 'CRS Peñalolén Cordillera Oriente', mm: 1_192 },
  { servicio: 'CRS Maipú', mm: 414 },
]

// ── Compra pública por laboratorio, 2024 (MM$) — Mercado Público, UNSPSC 51 ──
// Top proveedores. meds.mp_laboratorio. El total de la compra pública de
// medicamentos en 2024 es MP_TOTAL_2024; lo no listado va a "Otros".
export interface LabFila { laboratorio: string; mm: number }
export const MP_LABORATORIO_2024: LabFila[] = [
  { laboratorio: 'Roche Chile', mm: 96_192 },
  { laboratorio: 'Scienza Chile', mm: 70_380 },
  { laboratorio: 'Novofarma Service', mm: 69_364 },
  { laboratorio: 'Merck Sharp & Dohme (MSD)', mm: 64_414 },
  { laboratorio: 'Sanofi Pasteur', mm: 58_396 },
  { laboratorio: 'Gador', mm: 42_680 },
  { laboratorio: 'GlaxoSmithKline (GSK)', mm: 41_756 },
  { laboratorio: 'Novartis Chile', mm: 41_404 },
  { laboratorio: 'Johnson & Johnson', mm: 41_366 },
  { laboratorio: 'Bristol Myers Squibb', mm: 28_466 },
  { laboratorio: 'Pfizer Chile', mm: 27_762 },
  { laboratorio: 'Arama Natural Products', mm: 27_550 },
  { laboratorio: 'Wyeth (Pfizer)', mm: 26_829 },
  { laboratorio: 'Farmacéutica Caribean', mm: 26_560 },
  { laboratorio: 'Grünenthal Chilena', mm: 25_284 },
  { laboratorio: 'Novo Nordisk', mm: 24_313 },
  { laboratorio: 'AstraZeneca', mm: 23_148 },
  { laboratorio: 'Fresenius Kabi', mm: 22_921 },
]
export const MP_TOTAL_2024 = 1_397_068

// ── Compra pública por clase terapéutica, 2024 (MM$) — Mercado Público ──
// meds.mp_clase (agrupación por segmento UNSPSC 51).
export interface ClaseFila { clase: string; mm: number }
export const MP_CLASE_2024: ClaseFila[] = [
  { clase: 'Sistema nervioso central', mm: 243_580 },
  { clase: 'Hormonas y antagonistas hormonales', mm: 198_928 },
  { clase: 'Agentes antitumorales', mm: 198_606 },
  { clase: 'Anti-infecciosos', mm: 156_305 },
  { clase: 'Inmunomoduladores', mm: 135_301 },
  { clase: 'Sistema gastrointestinal', mm: 117_274 },
  { clase: 'Tracto respiratorio', mm: 89_635 },
  { clase: 'Hematológicos', mm: 86_393 },
  { clase: 'Agua y electrolitos', mm: 67_146 },
  { clase: 'Cardiovasculares', mm: 48_580 },
  { clase: 'Sistema nervioso autónomo', mm: 29_363 },
  { clase: 'Varios', mm: 14_335 },
  { clase: 'Oídos, ojos, nariz y piel', mm: 11_619 },
]

// ── Vistas anuales no aditivas (MM$) — el mismo gasto físico, tres marcos ──
// meds.vistas_anuales / meds.gold_resumen.
export interface VistaFila { vista: string; detalle: string; mm: number; marco: string }
export const VISTAS_NO_ADITIVAS: VistaFila[] = [
  { vista: 'Devengado público', detalle: 'Farmacia SS + APS municipal + ISAPRE (no separa función)', mm: 1_049_761, marco: 'Ejecución presupuestaria, 2023' },
  { vista: 'Compra (Mercado Público)', detalle: 'UNSPSC-51, CENABAST ~82% del canal', mm: 1_397_068, marco: 'Procurement, 2024' },
  { vista: 'Bolsillo de los hogares', detalle: 'Gasto directo en medicamentos (HF.3)', mm: 1_725_000, marco: 'Encuesta de hogares (EPF), 2024' },
]

// ── Esquema del lake cochid_datos.meds: las tablas que alimentan el explorador ──
export interface TablaMeds { tabla: string; descripcion: string; filas: string }
export const SCHEMA_MEDS: TablaMeds[] = [
  { tabla: 'serie_farmacia', descripcion: 'Línea Farmacia 22.04.004.001 por año, nominal y real 2024', filas: '15 (2010-2024)' },
  { tabla: 'serie_anual', descripcion: 'Series firmes por concepto (LRS, DAC, judicial, PNI, APS…) por año', filas: 'multi-concepto' },
  { tabla: 'farmacia_servicio', descripcion: 'Reparto de la línea Farmacia por Servicio de Salud', filas: '~62 (varios años)' },
  { tabla: 'mp_laboratorio', descripcion: 'Compra pública por laboratorio (Mercado Público, UNSPSC-51)', filas: '40 (2024)' },
  { tabla: 'mp_clase', descripcion: 'Compra pública por clase terapéutica', filas: '14 (2024)' },
  { tabla: 'mp_establecimiento', descripcion: 'Compra por establecimiento comprador, flag CENABAST', filas: 'multi' },
  { tabla: 'programas', descripcion: 'Gasto público por programa, con su solapamiento (overlap)', filas: '8' },
  { tabla: 'vistas_anuales', descripcion: 'Las tres vistas no aditivas (devengado/compra/bolsillo)', filas: '4' },
  { tabla: 'sha_separacion', descripcion: 'Separación SHA HC.5.1 / HC.1.1 / HC.6 (público vs total)', filas: '4' },
  { tabla: 'gold_resumen', descripcion: 'Resumen consolidado de las vistas por marco', filas: '3' },
  { tabla: 'meta_gaps', descripcion: 'Catálogo de vacíos de medición y su grado de resolubilidad', filas: '6' },
]

// ── Crosswalks (puentes entre clasificaciones) que sostienen la reconstrucción ──
export interface Crosswalk { de: string; a: string; para: string }
export const CROSSWALKS: Crosswalk[] = [
  { de: 'UNSPSC (Mercado Público)', a: 'ATC / clase terapéutica', para: 'Agrupar la compra pública en categorías clínicas comparables' },
  { de: 'Folio SIGFE (devengado)', a: 'Orden de compra (Mercado Público)', para: 'Cruzar lo ejecutado con lo efectivamente comprado' },
  { de: 'RUT comprador', a: 'Capítulo / Servicio de Salud (DIPRES)', para: 'Atribuir cada compra a su establecimiento y red' },
  { de: 'Glosa presupuestaria 22.04.004', a: 'Función SHA (HC.5.1 / HC.1.1)', para: 'Ubicar la línea Farmacia en las cuentas de salud OCDE' },
  { de: 'Instrumento de política (GES, LRS, DAC…)', a: 'Esquema de financiamiento SHA (HF)', para: 'Evitar el doble conteo entre instrumentos solapados' },
]

// ── Vacíos de medición (gaps) y su resolubilidad — meds.meta_gaps ──
export interface MetaGap { gap: string; descripcion: string; resoluble: string }
export const META_GAPS: MetaGap[] = [
  { gap: 'Hospital vs ambulatorio', descripcion: 'La línea Farmacia mezcla el fármaco de internación (HC.1.1) con el ambulatorio (HC.5.1); el presupuesto no los separa.', resoluble: 'Solo con WinSIG (consumo por unidad)' },
  { gap: 'FF.AA. depurado', descripcion: 'El gasto en medicamentos de las sanidades de las FF.AA. viene en bundle con otros insumos.', resoluble: 'Parcial' },
  { gap: 'Ejecución real', descripcion: 'Falta re-ingerir los Informes de Ejecución para cerrar los años más recientes.', resoluble: 'Sí: re-ingerir Informes de Ejecución' },
  { gap: 'ISAPRE desglosado', descripcion: 'El gasto en medicamentos dentro de ISAPRE aparece agregado, no desglosado por función.', resoluble: 'Como residuo' },
  { gap: 'Mutuales y NPISH', descripcion: 'Mutuales y entidades sin fines de lucro aún no incorporadas al perímetro.', resoluble: 'Sí' },
  { gap: 'Crosswalk UNSPSC↔ATC↔COICOP', descripcion: 'Falta el puente fino entre la clasificación de compra, la clínica y la de hogares.', resoluble: 'A construir' },
]
