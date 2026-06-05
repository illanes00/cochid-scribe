import { Fragment, useState, ReactNode } from 'react'
import { HC_TREE, HF_TREE, TreeNode } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// ── Definiciones técnicas SHA 2011 y cómo se cuentan en Chile ──────────────
// Marco "A System of Health Accounts 2011" (OECD/Eurostat/WHO). Las tres
// clasificaciones ICHA: funciones HC (cap. 5), proveedores HP (cap. 6) y
// esquemas de financiamiento HF (cap. 7), más la dimensión de fuentes de
// ingreso FS (cap. 8). Audiencia: directores de política sanitaria.

interface DimCard { tag: string; titulo: string; pregunta: string; clasif: string; cap: string; ejemplo: ReactNode }
const DIMENSIONES: DimCard[] = [
 {
 tag: 'HC',
 titulo: '¿Qué se compra?',
 pregunta: 'Función del consumo de salud: el tipo de bien o servicio que recibe el paciente',
 clasif: 'ICHA-HC',
 cap: 'SHA 2011, cap. 5',
 ejemplo: (
 <>
 <CodeRef c="HC.1">atención curativa (consultas, procedimientos, hospitalización)</CodeRef>,{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef>,{' '}
 <CodeRef c="HC.6.2">vacunas del programa de inmunización</CodeRef>…
 </>
 ),
 },
 {
 tag: 'HP',
 titulo: '¿Dónde / quién provee?',
 pregunta: 'Establecimiento que entrega el bien o servicio al paciente',
 clasif: 'ICHA-HP',
 cap: 'SHA 2011, cap. 6',
 ejemplo: (
 <>
 <CodeRef c="HP.1">hospitales</CodeRef>,{' '}
 <CodeRef c="HP.3">consultorios de atención primaria (CESFAM)</CodeRef>,{' '}
 <CodeRef c="HP.5">farmacias de venta al público</CodeRef>…
 </>
 ),
 },
 {
 tag: 'HF',
 titulo: '¿Quién financia?',
 pregunta: 'Esquema de financiamiento que paga la cuenta',
 clasif: 'ICHA-HF',
 cap: 'SHA 2011, cap. 7',
 ejemplo: (
 <>
 <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef>,{' '}
 <CodeRef c="HF.1.2.2">el 7% obligatorio de cotización ISAPRE</CodeRef>,{' '}
 <CodeRef c="HF.3">bolsillo de los hogares (copagos y compra directa)</CodeRef>…
 </>
 ),
 },
 {
 tag: 'FS',
 titulo: '¿Con qué fuente de ingreso?',
 pregunta: 'Origen último de los recursos con que el esquema paga',
 clasif: 'ICHA-FS',
 cap: 'SHA 2011, cap. 8',
 ejemplo: (
 <>
 <CodeRef c="FS.1">impuestos generales del gobierno</CodeRef>,{' '}
 <CodeRef c="FS.3">cotizaciones sociales de trabajadores y empleadores</CodeRef>, prepago de
 los hogares…
 </>
 ),
 },
]

// ── Filas de la tabla de definiciones ──────────────────────────────────────
interface DefRow {
 concepto: string
 code: string
 tree: 'HC' | 'HF' | null
 sha: ReactNode // definición técnica SHA 2011 (resumen para la celda)
 chile: ReactNode // cómo se cuenta en Chile: incluye / no incluye
 ejemplo: ReactNode
 cap: string
 // texto largo del manual para el modal
 manual: ReactNode
}

const ROWS: DefRow[] = [
 {
 concepto: 'HC.5.1, Productos farmacéuticos y bienes médicos no duraderos',
 code: 'HC51',
 tree: 'HC',
 sha: (
 <>
 <CodeRef c="HC.5.1">Medicamentos y bienes médicos no duraderos</CodeRef> para el consumo
 final de los hogares fuera de la hospitalización (uso ambulatorio / retail), tanto recetados
 como de venta libre. Mide el producto entregado al consumidor final, no la producción ni la
 distribución mayorista.
 </>
 ),
 chile: (
 <>
 Incluye la dispensación en <CodeRef c="HP.5">farmacias</CodeRef>,{' '}
 <CodeRef c="HP.3">atención primaria (FOFAR)</CodeRef> y la receta-en-mano hospitalaria si el
 hogar la compra afuera. NO el fármaco administrado en hospitalización (ver HC.1 vs HC.5.1 en
 manual). Por proveedor (2022, US$ PPA mill): farmacias 4.502, hospitales 2.531, APS 1.233. Los
 subcomponentes <CodeRef c="HC.5.1.1">recetados</CodeRef> y{' '}
 <CodeRef c="HC.5.1.2">OTC</CodeRef> son Missing; el agregado sí se reporta.
 </>
 ),
 ejemplo: (
 <>
 Losartán comprado en una <CodeRef c="HP.5">farmacia</CodeRef> y pagado por el hogar →{' '}
 <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> financiado con{' '}
 <CodeRef c="HF.3">bolsillo del hogar</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 5, §5.x (HC.5 Medical goods)',
 manual: (
 <>
 Los <CodeRef c="HC.5.1">medicamentos y bienes médicos no duraderos de uso ambulatorio</CodeRef>{' '}
 cubren los productos farmacéuticos consumidos fuera de una prestación de atención. Comprende{' '}
 <CodeRef c="HC.5.1.1">recetados</CodeRef>,{' '}
 <CodeRef c="HC.5.1.2">venta libre (OTC)</CodeRef> y otros bienes no duraderos. Frontera clave:
 el fármaco que el paciente ambulatorio se autoadministra es{' '}
 <CodeRef c="HC.5.1">HC.5.1</CodeRef>; el consumido como parte de un episodio de atención (p. ej.
 administrado en hospitalización) va a la función de esa atención (
 <CodeRef c="HC.1">HC.1</CodeRef>). Valoración a precio de comprador final (márgenes minoristas
 e impuestos no deducibles incluidos).
 </>
 ),
 },
 {
 concepto: 'HC.5, Bienes médicos',
 code: 'HC5',
 tree: 'HC',
 sha: 'Bienes médicos de consumo final de los hogares: medicamentos y bienes no duraderos (HC.5.1) más aparatos terapéuticos y otros duraderos (HC.5.2). Es el paraguas que contiene a los medicamentos ambulatorios.',
 chile: 'En Chile se reporta HC.5.1 (medicamentos ambulatorios) y HC.5.2 (aparatos). El medicamento administrado en hospitalización NO está aquí: va embebido en la atención curativa (HC.1).',
 ejemplo: 'Una caja de remedios o una silla de ruedas que compra el hogar → bienes médicos (HC.5).',
 cap: 'SHA 2011, cap. 5 (HC.5 Medical goods)',
 manual: 'HC.5 agrupa los bienes médicos que el hogar consume directamente, separándolos de los servicios de atención (HC.1–HC.4). Se desagrega en medicamentos y otros bienes no duraderos (HC.5.1) y aparatos terapéuticos y otros bienes duraderos (HC.5.2). El fármaco consumido como insumo de una atención no se cuenta aquí, sino en la función de esa atención.',
 },
 {
 concepto: 'HC.1, Atención curativa',
 code: 'HC1',
 tree: 'HC',
 sha: (
 <>
 <CodeRef c="HC.1">Servicios de atención curativa</CodeRef> en los que el principal propósito
 clínico es aliviar síntomas, reducir la severidad de una enfermedad o lesión o protegerse
 contra su exacerbación, ya sea en régimen hospitalario, de día o ambulatorio.
 </>
 ),
 chile: (
 <>
 El fármaco intrahospitalario va embebido en <CodeRef c="HC.1">la atención curativa</CodeRef> y
 NO se reclasifica como <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> (fuentes: SIGFE +
 WinSIG/PERC), por lo que no es directamente comparable con el ambulatorio.
 </>
 ),
 ejemplo: (
 <>
 Quimioterapia administrada en hospitalización → <CodeRef c="HC.1">atención curativa</CodeRef>{' '}
 (el citostático va embebido, no se cuenta como{' '}
 <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef>).
 </>
 ),
 cap: 'SHA 2011, cap. 5, §5.x (HC.1 Curative care)',
 manual: (
 <>
 <CodeRef c="HC.1">La atención curativa</CodeRef> agrupa los servicios que alivian síntomas o
 reducen la severidad de enfermedades o lesiones; se desagrega por modo de provisión
 (hospitalaria, de día, ambulatoria, domiciliaria). Todos los insumos del episodio, incluido el
 fármaco administrado en hospitalización, se imputan aquí y NO a los{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef>. Por eso{' '}
 <CodeRef c="HC.RI.1">HC.RI.1</CodeRef> es Missing. Ver sección 3 (vacíos).
 </>
 ),
 },
 {
 concepto: 'HF.1, Esquemas de financiamiento público/obligatorios',
 code: 'HF1',
 tree: 'HF',
 sha: (
 <>
 <CodeRef c="HF.1">
 Aporte fiscal (impuestos) más cotizaciones obligatorias (FONASA + el 7% de ISAPRE)
 </CodeRef>
 : esquemas de gobierno y de contribución obligatoria cuya participación, base contributiva o
 cobertura está fijada por ley.
 </>
 ),
 chile: (
 <>
 Incluye el <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef>, el{' '}
 <CodeRef c="HF.1.2.2">7% obligatorio de ISAPRE</CodeRef> y el{' '}
 <CodeRef c="HF.1.1">aporte fiscal de esquemas de gobierno (ISP, CENABAST, SEREMI)</CodeRef>. NO
 el <CodeRef c="HF.2.1">complemento voluntario sobre el 7%</CodeRef>. Financia 25,6% del{' '}
 <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> (ver Panel A); fuentes: FOFAR, GES-retail,
 CENABAST. Prueba de que el mercado ambulatorio no es puramente privado.
 </>
 ),
 ejemplo: (
 <>
 Pacientes crónicos atendidos en <CodeRef c="HP.3">CESFAM</CodeRef> con fármacos del programa
 FOFAR → <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> financiado con{' '}
 <CodeRef c="HF.1">recursos públicos y obligatorios</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 7, §7.x (HF.1)',
 manual: (
 <>
 El bloque de{' '}
 <CodeRef c="HF.1">financiamiento público y obligatorio</CodeRef> reúne los{' '}
 <CodeRef c="HF.1.1">esquemas de gobierno financiados con aporte fiscal</CodeRef> y los
 esquemas contributivos obligatorios de seguro de salud (
 <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> +{' '}
 <CodeRef c="HF.1.2.2">7% obligatorio de ISAPRE</CodeRef>). Un esquema se clasifica como
 obligatorio cuando la participación, la base de cotización o la cobertura están determinadas
 por ley o regulación, con independencia de que el administrador sea público o privado. En el
 caso chileno, el manual lleva a clasificar el componente legal del 7% gestionado por las
 ISAPRE como <CodeRef c="HF.1.2.2">seguro privado obligatorio</CodeRef>, separándolo del{' '}
 <CodeRef c="HF.2.1">prepago voluntario por sobre ese 7%</CodeRef>. Esta frontera es la que
 permite leer «cuánto del gasto en medicamentos es público/obligatorio vs. voluntario vs.
 bolsillo».
 </>
 ),
 },
 {
 concepto: 'HF.1.2.1, Seguro social de salud (FONASA)',
 code: 'HF121',
 tree: 'HF',
 sha: (
 <>
 <CodeRef c="HF.1.2.1">Cotización obligatoria administrada por una entidad pública (FONASA)</CodeRef>:
 esquema contributivo de seguro social con afiliación determinada por ley.
 </>
 ),
 chile: (
 <>
 Incluye <CodeRef c="HF.1.2.1">FONASA, las Mutuales y los sistemas de salud de las FF.AA. y de
 Orden</CodeRef>. Es el principal financista público de{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef>, vía la Modalidad de Atención
 Institucional, los programas de atención primaria (FOFAR) y las garantías transversales (GES,
 parte FONASA). Punto crítico de lectura: el{' '}
 <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> paga rutinariamente a proveedores
 privados, <CodeRef c="HP.1">clínicas en Modalidad de Libre Elección</CodeRef> y{' '}
 <CodeRef c="HP.5">farmacias intermediadas por CENABAST</CodeRef>, de modo que «financiado por
 FONASA» nunca debe leerse como «provisto en establecimiento público».
 </>
 ),
 ejemplo: (
 <>
 Bono FONASA que cubre parte de un medicamento dispensado en convenio → la fracción que cubre
 el <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 7, §7.x (HF.1.2.1)',
 manual: (
 <>
 El <CodeRef c="HF.1.2.1">seguro social de salud</CodeRef> corresponde a los programas
 contributivos obligatorios en los que la elegibilidad se basa en el pago de cotizaciones
 (propias o de terceros) y cuya administración recae en una entidad pública o cuasi-pública. En
 Chile se mapean aquí <CodeRef c="HF.1.2.1">FONASA, las Mutualidades de empleadores y los
 sistemas de las Fuerzas Armadas y de Orden</CodeRef>. El manual exige separar la parte
 financiada por el esquema de la fracción de{' '}
 <CodeRef c="HF.3">copago a cargo del hogar (bolsillo)</CodeRef>. Una consecuencia de cuenta
 nacional relevante para Chile: la cobertura de medicamentos obtenida por sentencia judicial
 (recurso de protección) no tiene categoría SHA propia y se diluye en el financiador que la
 sentencia obliga a pagar, habitualmente el{' '}
 <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef>. Esa glosa de sentencias estaba
 presupuestada en 28.914 MM$ (2024), pero la ejecución la desbordó hasta 93.594 MM$ (DIPRES):
 la brecha mide, en negativo, el tamaño de las listas cerradas (GES, Ley Ricarte Soto, drogas
 de alto costo) que dejan demanda sin cubrir.
 </>
 ),
 },
 {
 concepto: 'HF.1.2.2, Seguro privado obligatorio (ISAPRE, 7%)',
 code: 'HF122',
 tree: 'HF',
 sha: (
 <>
 <CodeRef c="HF.1.2.2">El 7% de cotización obligatoria gestionado por ISAPRE</CodeRef>:
 seguro privado cuya contratación o cuya base mínima de cotización es obligatoria por ley.
 </>
 ),
 chile: (
 <>
 Incluye exclusivamente el{' '}
 <CodeRef c="HF.1.2.2">tramo del 7% de cotización obligatoria gestionado por las ISAPRE</CodeRef>.
 NO incluye el{' '}
 <CodeRef c="HF.2.1">complemento voluntario por sobre el 7%</CodeRef>.
 </>
 ),
 ejemplo: (
 <>
 Reembolso ISAPRE de un medicamento con cargo a la cobertura financiada por el{' '}
 <CodeRef c="HF.1.2.2">7% obligatorio</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 7, §7.x (HF.1.2.2)',
 manual: (
 <>
 El <CodeRef c="HF.1.2.2">seguro privado obligatorio (el 7% de ISAPRE)</CodeRef> captura los
 esquemas en que la afiliación o un nivel mínimo de prima están mandatados por ley, aun cuando
 la administración sea de aseguradoras privadas. El criterio metodológico aplicado a Chile
 divide la cotización ISAPRE en dos por método de residuo: el{' '}
 <CodeRef c="HF.1.2.2">7% legal obligatorio</CodeRef> (contabilizado dentro del bloque{' '}
 <CodeRef c="HF.1">público y obligatorio</CodeRef>) y la{' '}
 <CodeRef c="HF.2.1">prima adicional voluntaria por sobre ese 7%</CodeRef>. Esta partición es
 una decisión de cuenta nacional, no un dato directo del estado financiero de la aseguradora, y
 explica por qué el GES de ISAPRE, financiado con ese 7%, pertenece al bloque{' '}
 <CodeRef c="HF.1">público y obligatorio</CodeRef> y no al{' '}
 <CodeRef c="HF.2">gasto voluntario</CodeRef>: la garantía GES es transversal y opera sobre dos
 esquemas de financiamiento a la vez (<CodeRef c="HF.1.2.1">FONASA</CodeRef> y{' '}
 <CodeRef c="HF.1.2.2">ISAPRE</CodeRef>).
 </>
 ),
 },
 {
 concepto: 'HF.2.1, Seguro voluntario de salud (ISAPRE complementario)',
 code: 'HF21',
 tree: 'HF',
 sha: (
 <>
 <CodeRef c="HF.2.1">Complemento ISAPRE sobre el 7% obligatorio y seguros privados
 complementarios</CodeRef>: esquemas cuya contratación es voluntaria, financiados con primas
 privadas no obligatorias.
 </>
 ),
 chile: (
 <>
 Incluye el <CodeRef c="HF.2.1">prepago ISAPRE por sobre el 7% obligatorio y los seguros
 privados complementarios</CodeRef>. NO incluye el{' '}
 <CodeRef c="HF.1.2.2">7% obligatorio</CodeRef>. En{' '}
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> es marginal: financia apenas el 3,1%
 del total (US$ PPA 255 mill, 2022). El cuadro chileno está dominado por el{' '}
 <CodeRef c="HF.3">bolsillo de los hogares</CodeRef> y el{' '}
 <CodeRef c="HF.1">financiamiento público</CodeRef>, no por el aseguramiento voluntario.
 </>
 ),
 ejemplo: (
 <>
 Cobertura adicional de farmacia de un seguro complementario contratado libremente →{' '}
 <CodeRef c="HF.2.1">seguro voluntario</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 7, §7.x (HF.2.1)',
 manual: (
 <>
 El <CodeRef c="HF.2.1">seguro voluntario de salud (VHI)</CodeRef> corresponde a la cobertura
 financiada por primas cuya contratación no está mandatada por ley. En Chile incluye el{' '}
 <CodeRef c="HF.2.1">complemento ISAPRE por sobre el 7% obligatorio y los seguros privados
 complementarios</CodeRef> comercializados por compañías de seguros. El manual los distingue
 del <CodeRef c="HF.1.2.2">7% obligatorio de ISAPRE</CodeRef> precisamente por el carácter
 voluntario de la decisión de aseguramiento.
 </>
 ),
 },
 {
 concepto: 'HF.2, Esquemas voluntarios',
 code: 'HF2',
 tree: 'HF',
 sha: 'Esquemas cuya contratación NO está mandatada por ley: seguro voluntario de salud (HF.2.1) y financiamiento de instituciones sin fines de lucro (HF.2.2).',
 chile: 'Incluye el complemento ISAPRE por sobre el 7% obligatorio, los seguros privados complementarios y el sector sin fines de lucro (TELETÓN, COANIQUEM). En medicamentos ambulatorios es marginal: 3,1% del HC.5.1.',
 ejemplo: 'Reembolso de un seguro complementario contratado libremente → HF.2.',
 cap: 'SHA 2011, cap. 7 (HF.2)',
 manual: 'HF.2 reúne los esquemas voluntarios. Se distingue del 7% obligatorio de ISAPRE, que es HF.1.2.2 y cuenta como público/obligatorio, precisamente por el carácter voluntario de la contratación.',
 },
 {
 concepto: 'HF.3, Pago directo de los hogares (gasto de bolsillo)',
 code: 'HF3',
 tree: 'HF',
 sha: (
 <>
 <CodeRef c="HF.3">Copagos y compra directa del hogar</CodeRef>: pagos directos de los hogares
 por bienes y servicios de salud, netos de cualquier reembolso de un tercer pagador. Incluye
 copagos (cost-sharing) y la compra directa sin seguro.
 </>
 ),
 chile: (
 <>
 Incluye los <CodeRef c="HF.3">copagos dentro de FONASA/ISAPRE y la compra directa en farmacia
 sin cobertura</CodeRef>. En <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> el bolsillo
 financia el 71,36% del total (US$ PPA 5.898 mill, 2022): es la cifra canónica, trazable celda
 a celda en SHA, y se estima a partir de la EPF (INE), no de registro administrativo. No debe
 confundirse con el «62%» que circula en el debate público, que mide el bolsillo sobre el{' '}
 <CodeRef c="HC.RI.1">gasto farmacéutico total (incluido el hospitalario embebido)</CodeRef> y
 descansa en una estimación, no en una celda OECD.
 </>
 ),
 ejemplo: (
 <>
 Copago de un bono o compra directa del medicamento en farmacia →{' '}
 <CodeRef c="HF.3">bolsillo del hogar</CodeRef>.
 </>
 ),
 cap: 'SHA 2011, cap. 7, §7.x (HF.3)',
 manual: (
 <>
 El <CodeRef c="HF.3">gasto de bolsillo</CodeRef> son copagos + compra directa, neto de
 reembolsos. En Chile se estima con la EPF (INE), no con registro administrativo (incertidumbre
 a declarar). En <CodeRef c="HC.5.1">HC.5.1</CodeRef>: cerca del 71% (SHA 2022), todos los canales, NO
 confundir con el 62% sobre el total farmacéutico (ver sección 4). Carga sobre los hogares: gasto
 catastrófico 22,0% (umbral 10% ingreso per cápita), 8,2% (ODS 3.8.2) y 1,1% (capacidad de pago
 OMS), tres preguntas distintas, no intercambiables.
 </>
 ),
 },
 {
 concepto: 'CHE, Gasto corriente en salud (Current Health Expenditure)',
 code: '_T',
 tree: 'HC',
 sha: (
 <>
 <CodeRef c="CHE">Total del consumo de bienes y servicios de salud del año</CodeRef>, excluyendo
 la formación de capital. Es el agregado de referencia (el denominador) del marco SHA 2011.
 </>
 ),
 chile: (
 <>
 Incluye todas las <CodeRef c="HC.1">funciones de atención y bienes de salud</CodeRef> del año.
 NO incluye inversión ni infraestructura (capital). En Chile ~20% del gasto queda{' '}
 <CodeRef c="HC.0">sin clasificar por función</CodeRef>, caveat declarado en el cuestionario
 conjunto JHAQ.
 </>
 ),
 ejemplo: (
 <>
 El <CodeRef c="CHE">total de gasto en salud</CodeRef> contra el que se calcula el porcentaje
 que representan los medicamentos.
 </>
 ),
 cap: 'SHA 2011, cap. 4 (boundaries) y cap. 5',
 manual: (
 <>
 El <CodeRef c="CHE">gasto corriente en salud (CHE)</CodeRef> es el agregado central del SHA
 2011: representa el consumo final de bienes y servicios de salud por residentes durante el año
 contable, medido por la suma de las funciones de atención y bienes (HC.1 a HC.7). Excluye
 explícitamente la formación bruta de capital del sistema de salud. El{' '}
 <CodeRef c="CHE">CHE</CodeRef> es la base de los indicadores comparables internacionalmente
 (CHE/PIB, CHE per cápita, participación del bolsillo en el CHE). Una limitación reportada por
 Chile es el peso del ítem{' '}
 <CodeRef c="HC.0">no clasificado por función</CodeRef>, del orden del 20%, que erosiona la
 comparabilidad funcional fina.
 </>
 ),
 },
]

export default function Definitions() {
 // Modal inline (sin componente compartido)
 const [open, setOpen] = useState<DefRow | null>(null)

 const treeLabel = (r: DefRow): TreeNode | undefined => {
 if (r.tree === 'HC') return HC_TREE.find(n => n.code === r.code)
 if (r.tree === 'HF') return HF_TREE.find(n => n.code === r.code)
 return undefined
 }

 return (
 <section id="definiciones">
 <h2 className="ptitle">Definiciones técnicas SHA 2011 y cómo se cuentan en Chile</h2>
 <p className="psub">
 Marco <em>A System of Health Accounts 2011</em> (OECD/Eurostat/WHO). Las tres
 clasificaciones ICHA y las dimensiones de lectura de toda cifra de gasto en salud.
 </p>

 <p className="lead">
 Cada peso del gasto en salud se clasifica a la vez en cuatro dimensiones ortogonales que el SHA
 2011 separa para responder cuatro preguntas independientes:
 <strong> qué se compra</strong> (función, HC), <strong> dónde o quién provee</strong>{' '}
 (proveedor, HP), <strong> quién financia</strong> (esquema, HF) y{' '}
 <strong> con qué fuente</strong> (FS). La clave analítica es no confundirlas, y en particular la{' '}
 <strong>regla de oro: quién financia (HF) no es quién provee (HP)</strong>. En Chile el
 financiador público paga rutinariamente a proveedores privados, el{' '}
 <CodeRef c="HF.1.2.1">seguro social FONASA</CodeRef> paga a{' '}
 <CodeRef c="HP.1">clínicas en libre elección</CodeRef> y el Estado interviene el precio de{' '}
 <CodeRef c="HP.5">farmacias</CodeRef> vía CENABAST, así que cada dimensión se lee por separado.
 </p>

 {/* (1) Las 4 dimensiones de lectura */}
 <div className="grid2">
 {DIMENSIONES.map(d => (
 <div className="card" key={d.tag}>
 <div>
 <span className="pill">{d.tag}</span> <strong>{d.titulo}</strong>
 </div>
 <div style={{ marginTop: 6 }}>{d.pregunta}</div>
 <div className="note" style={{ marginTop: 6 }}>
 Clasificación <code>{d.clasif}</code> · {d.cap}
 </div>
 <div className="note" style={{ marginTop: 4 }}>{d.ejemplo}</div>
 </div>
 ))}
 </div>

 <div className="card warn">
 <strong>Frontera clave para medicamentos.</strong> El SHA 2011 separa el{' '}
 <CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> del fármaco consumido como insumo de un
 episodio de atención, que va embebido en su función (p. ej.{' '}
 <CodeRef c="HC.1">la atención curativa</CodeRef> en hospitalización) y no es separable. Por eso{' '}
 <CodeRef c="HC.RI.1">HC.RI.1</CodeRef> es <span className="badge miss">Missing</span> en Chile
 y el fármaco hospitalario no se puede leer directo de las cuentas OECD (ver sección 3). El
 Panel B lo recupera por una <strong>identidad contable que cierra</strong>, no por un supuesto
 libre: el <strong>fármaco intrahospitalario público se acota</strong> con el punto de cuadre
 gasto público total (1.514.814) − ambulatorio público (<CodeRef c="HC.5.1">HC.5.1</CodeRef>·<CodeRef c="HF.1">HF.1</CodeRef>{' '}
 = 804.882) − <CodeRef c="PNI">PNI</CodeRef> (30.000) ≈ <strong>246.000 MM$</strong> (0,105% del
 PIB), cifra reportable como <strong>banda 250.000–725.000 (central ~485.000)</strong>. El modelo
 completo cierra contra el CIF, HC.5.1 1,340% + intrahospitalario 0,105% + privado intramural
 0,089% + PNI 0,013% = 1,546% del PIB vs CIF total 1,54%, pero ese cierre es{' '}
 <strong>algebraico/casi tautológico</strong>: su único ancla empírica es que el bolsillo OCDE ≈
 bolsillo CIF, ambos de la EPF. Se cruza en magnitud con el arsenal del SNSS (CENABAST devengado
 2024, MM$ 1.323.645) y con la CNEP (≈1,45 billones 2023, mezcla dispositivos), pero ninguna
 aísla el fármaco. Es un <strong>marco que ACOTA</strong>, no una prueba, HC.RI.1 sigue Missing.
 </div>

 {/* (2) Tabla de definiciones */}
 <h3 style={{ marginTop: 26 }}>Tabla de definiciones</h3>
 <p className="note">
 Agrupada por familia ICHA (<b>HC</b> funciones · <b>HF</b> esquemas de financiamiento ·
 agregado de referencia). Dentro de cada familia, el chip azul oscuro es la categoría raíz y
 el «↳ subnivel» indentado es su desagregación. Cada fila contrasta la definición del manual
 con la práctica de medición chilena (qué incluye / qué no) y un ejemplo; el botón abre el
 texto del manual y su referencia de capítulo.
 </p>
 <Caption ch={1} n={1} kind="tabla" title="Definiciones SHA 2011 por familia ICHA y su medición en Chile" />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '26%' }} />
 <col style={{ width: '28%' }} />
 <col style={{ width: '30%' }} />
 <col style={{ width: '16%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Concepto</th>
 <th>Definición técnica (SHA 2011)</th>
 <th>Cómo se cuenta en Chile (incluye / no incluye)</th>
 <th>Ejemplo</th>
 </tr>
 </thead>
 <tbody>
 {([
 { fam: 'HC', label: 'ICHA-HC · Funciones', eje: '¿QUÉ se compra?', codes: ['HC1', 'HC5', 'HC51'] },
 { fam: 'HF', label: 'ICHA-HF · Esquemas de financiamiento', eje: '¿QUIÉN paga?', codes: ['HF1', 'HF121', 'HF122', 'HF2', 'HF21', 'HF3'] },
 { fam: 'AGG', label: 'Agregado de referencia', eje: 'el total contra el que se calculan los %', codes: ['_T'] },
 ] as const).map(grp => (
 <Fragment key={grp.fam}>
 {/* fila-encabezado de familia: separa HC / HF / agregado */}
 <tr>
 <td colSpan={4} style={{ background: '#1a365d', color: '#fff', fontWeight: 700, fontSize: 13, padding: '7px 10px' }}>
 {grp.label} <span style={{ fontWeight: 400, opacity: .85 }}>, {grp.eje}</span>
 </td>
 </tr>
 {grp.codes.map(code => {
 const r = ROWS.find(x => x.code === code)
 if (!r) return null
 const [codeTok, ...nameParts] = r.concepto.split(', ')
 const name = nameParts.join(', ')
 // 2 niveles: 0 = categoría raíz, 1 = subnivel (solo indentado, sin color ni borde)
 const lvl = (code === 'HC1' || code === 'HC5' || code === 'HF1' || code === 'HF2' || code === 'HF3' || code === '_T') ? 0 : 1
 const isMed = code === 'HC51'
 return (
 <tr key={code}>
 <td style={{ paddingLeft: 12 + lvl * 22 }}>
 <div style={{ display: 'flex', alignItems: 'baseline', gap: 7, flexWrap: 'wrap' }}>
 {lvl > 0 && <span className="note" style={{ fontWeight: 400 }}>↳</span>}
 <CodeRef c={codeTok}>
 <code style={{
 background: '#eaf2fb', color: '#1a365d',
 fontWeight: 700, padding: '1px 6px', borderRadius: 4, fontSize: 12, whiteSpace: 'nowrap',
 }}>{codeTok}</code>
 </CodeRef>
 <strong style={{ fontSize: lvl === 0 ? 13.5 : 12.5 }}>{name}</strong>
 {isMed && <span className="tag-med">medicamento</span>}
 </div>
 <div style={{ marginTop: 6 }}>
 <button className="link" onClick={() => setOpen(r)}>definición técnica completa</button>
 </div>
 </td>
 <td style={{ textAlign: 'left' }}>{r.sha}</td>
 <td style={{ textAlign: 'left' }}>{r.chile}</td>
 <td style={{ textAlign: 'left' }}>{r.ejemplo}</td>
 </tr>
 )
 })}
 </Fragment>
 ))}
 </tbody>
 </table>
 </div>

 <p className="note" style={{ marginTop: 14 }}>
 Fuente: OECD/Eurostat/WHO, <em>A System of Health Accounts 2011</em> (ed. revisada 2017),
 capítulos 5 (funciones HC), 6 (proveedores HP) y 7 (esquemas de financiamiento HF).
 </p>

 {/* (3) Modal inline con el texto del manual */}
 {open && (
 <div className="modal-backdrop" onClick={() => setOpen(null)}>
 <div className="modal" onClick={e => e.stopPropagation()}>
 <button className="close" aria-label="Cerrar" onClick={() => setOpen(null)}>
 ×
 </button>
 <h3>{open.concepto}</h3>
 <div className="note" style={{ marginBottom: 10 }}>
 <CodeRef c={open.concepto.split(', ')[0]}>
 <code>{open.concepto.split(', ')[0]}</code>
 </CodeRef> · {open.cap}
 {treeLabel(open) && (
 <>
 {' '}· {treeLabel(open)?.es} <span className="note">({treeLabel(open)?.en})</span>
 </>
 )}
 </div>
 <div className="quote">{open.manual}</div>
 {treeLabel(open)?.chile && (
 <div className="card" style={{ marginBottom: 0 }}>
 <strong>Lectura chilena.</strong> {treeLabel(open)?.chile}
 </div>
 )}
 <p className="note" style={{ marginTop: 12 }}>
 Cita: OECD/Eurostat/WHO, <em>A System of Health Accounts 2011</em>, {open.cap}.
 </p>
 </div>
 </div>
 )}
 </section>
 )
}
