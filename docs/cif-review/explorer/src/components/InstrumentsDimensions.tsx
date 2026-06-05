import { useState, ReactNode } from 'react'
import { labelHF, labelHC } from '../data'
import CodeRef from './CodeRef'
import Caption from './Caption'

// ── El modelo biyectivo instrumento ↔ SHA ──
// Una fila por instrumento de la política chilena de medicamentos. Cada fila
// proyecta el instrumento sobre los ejes ortogonales del System of Health
// Accounts (SHA 2011): cuánto moviliza (monto), quién financia (HF), qué
// función cubre (HC), quién provee (HP) y cómo se contabiliza/fuente. La
// columna de monto lista líneas/coberturas del gasto público 2024; el gasto
// público total es 1.514.814 MM$ CLP, descompuesto por institución SIN doble
// conteo (GES/DAC/FOFAR son etiquetas, no sumandos). El fármaco intrahospitalario
// público NO lo aísla ninguna fuente: la fila usa el PUNTO DE CUADRE algebraico
// (público total − ambulatorio público − PNI ≈ 246.000) para no romper el total,
// pero la cifra reportable es una BANDA de 250.000–725.000 (central ~485.000), el
// cierre es algebraico, un marco que acota, no una prueba. El bolsillo y la
// composición del retail vienen de la serie SHA 2022 en USD PPA.
//
// ESTÁNDAR DE REDACCIÓN: cada columna LIDERA con la descripción en español
// (qué financia, qué función cubre, quién provee); el código SHA va al hover
// vía <CodeRef>. Las cifras no cambian, solo su forma de presentarse.

interface Instrument {
 id: string
 nombre: string
 sigla?: string
 monto: string // monto canónico (MM$ CLP 2024, o referencia SHA)
 hf: ReactNode // quién financia, descripción en español (código al hover)
 que: ReactNode // qué función, descripción en español (código al hover)
 donde: ReactNode // quién provee, descripción en español (código al hover)
 cuenta: ReactNode // cómo se contabiliza / fuente
 nota: ReactNode // glosa para el modal
}

// Ordenado por bloque de financiador y, dentro de cada bloque, por monto
// descendente: primero el agregado público fiscal y de seguridad social, luego
// la regulación de precio (que no financia), después el voluntario/NPISH, y al
// final el bolsillo, el mayor flujo, pero privado.
const ROWS: Instrument[] = [
 {
 id: 'ges',
 nombre: 'GES / AUGE',
 monto: '540.000 (GES-FONASA)',
 hf: (
 <>
 Público y obligatorio: aporte fiscal (impuestos) + cotizaciones obligatorias
 , la misma garantía sobre dos esquemas, <CodeRef c="HF.1.2.1">FONASA</CodeRef> y{' '}
 <CodeRef c="HF.1.2.2">la cotización del 7% en ISAPRE</CodeRef>
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.5.1">medicamentos ambulatorios de la canasta</CodeRef> + medicamentos
 administrados durante la <CodeRef c="HC.1">atención hospitalaria</CodeRef> (según canasta)
 </>
 ),
 donde: (
 <>
 red mixta: <CodeRef c="HP.1">hospitales</CodeRef>, farmacias de atención primaria
 y <CodeRef c="HP.5">farmacias retail en convenio</CodeRef>
 </>
 ),
 cuenta: 'DIPRES, fila GES-FONASA Tabla 4.3. GES-ISAPRE no aislable.',
 nota: (
 <>
 <p>
 Garantías Explícitas en Salud (Ley 19.966): el único instrumento transversal. La misma
 garantía opera sobre dos esquemas, FONASA
 (<CodeRef c="HF.1.2.1">cotizaciones obligatorias</CodeRef>) y el 7% obligatorio en ISAPRE
 (<CodeRef c="HF.1.2.2">7% en ISAPRE</CodeRef>), y por eso GES no es puramente estatal.
 </p>
 <p>
 El monto canónico (540.000 MM$) es solo la porción GES-FONASA. El componente GES-ISAPRE
 está embebido en los 845 USD PPA mill del 7% obligatorio, sin glosa segregada, y queda
 fuera del total CLP. El componente farmacéutico GES tampoco tiene glosa propia: alimenta a
 la vez {' '}<CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> y
 {' '}<CodeRef c="HC.1">atención hospitalaria</CodeRef>, sin poder aislarse.
 </p>
 </>
 ),
 },
 {
 id: 'ss',
 nombre: 'Fármaco intrahospitalario público (banda)',
 monto: 'banda 250.000–725.000 (central ~485.000 · cuadre ≈246.000)',
 hf: (
 <>
 Público y obligatorio: cotizaciones obligatorias del seguro social
 (<CodeRef c="HF.1.2.1">FONASA</CodeRef>)
 </>
 ),
 que: (
 <>
 medicamento administrado dentro de la
 <CodeRef c="HC.1">atención hospitalaria curativa</CodeRef> (embebido, no separable)
 </>
 ),
 donde: <>hospitales públicos de los Servicios de Salud (<CodeRef c="HP.1">hospitales</CodeRef>)</>,
 cuenta: 'Derivado por identidad: público total − ambulatorio público − PNI. No tiene glosa propia.',
 nota: (
 <>
 <p>
 El medicamento que el paciente recibe internado no tiene línea presupuestaria que lo aísle:
 ningún registro público distingue al hospitalizado del ambulatorio, y en SHA queda embebido en
 la <CodeRef c="HC.1">atención curativa hospitalaria</CodeRef> (su ítem de memoria,{' '}
 <CodeRef c="HC.RI.1">HC.RI.1</CodeRef>, figura como Missing).
 </p>
 <p>
 El <strong>punto de cuadre algebraico</strong>, gasto público total (1.514.814) − ambulatorio
 público (<CodeRef c="HC.5.1">HC.5.1</CodeRef>·<CodeRef c="HF.1">HF.1</CodeRef> = 804.882) −{' '}
 <CodeRef c="PNI">PNI</CodeRef> (30.000) ≈ <strong>246.000 MM$</strong> (0,105% del PIB), hace
 cuadrar la contabilidad y es coherente con la fracción del arsenal{' '}
 <CodeRef c="CENABAST">CENABAST</CodeRef> consumida en internación. Pero el modelo «cierra»
 algebraicamente (1,546% vs 1,54% del PIB), <strong>no lo prueba</strong>: su único ancla
 empírica es que el bolsillo OCDE ≈ bolsillo CIF, ambos de la EPF. Por eso la cifra reportable
 es una <strong>banda de 250.000–725.000 MM$</strong> (central ~485.000): un marco que{' '}
 <strong>acota</strong>, no una etiqueta de confianza.
 </p>
 </>
 ),
 },
 {
 id: 'fofar',
 nombre: 'APS, FOFAR / Arsenal',
 monto: '195.000',
 hf: (
 <>
 Público y obligatorio: financiamiento per cápita del seguro social
 (<CodeRef c="HF.1.2.1">FONASA</CodeRef>), gestión municipal
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.5.1">medicamentos ambulatorios no duraderos</CodeRef> para crónicos
 </>
 ),
 donde: 'farmacia del CESFAM (proveedor de atención primaria)',
 cuenta: 'DIPRES Partida 16 APS, Tabla 4.3. Producción medida vía REM.',
 nota: (
 <>
 <p>
 Fondo de Farmacia para crónicos (hipertensión, diabetes tipo 2, dislipidemia), más el
 arsenal farmacológico municipal. La farmacia del establecimiento APS entrega estos
 {' '}<CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> con gratuidad total (0%),
 financiados por el seguro social vía per cápita
 (<CodeRef c="HF.1.2.1">cotizaciones obligatorias en FONASA</CodeRef>) y gestión municipal.
 </p>
 <p>
 La cobertura nominal supera a la dispensación efectiva: cuando hay quiebres de stock, parte
 de la demanda crónica termina empujada al retail de bolsillo.
 </p>
 </>
 ),
 },
 {
 id: 'lrs',
 nombre: 'Ley Ricarte Soto',
 sigla: 'LRS',
 monto: '175.672',
 hf: (
 <>
 Público y fiscal: íntegramente con impuestos generales
 (<CodeRef c="HF.1.1">aporte fiscal del gobierno</CodeRef>, vía FONASA)
 </>
 ),
 que: (
 <>
 medicamentos de alto costo, sea
 <CodeRef c="HC.5.1">dispensados de forma ambulatoria</CodeRef> o
 <CodeRef c="HC.1">administrados en el hospital</CodeRef>
 </>
 ),
 donde: <>farmacias hospitalarias autorizadas, públicas o privadas en convenio (<CodeRef c="HP.1">hospitales</CodeRef>)</>,
 cuenta: (
 <>DIPRES Cap. 02 asig. 410. Financiado con <CodeRef c="FS.1">recaudación de impuestos</CodeRef>.</>
 ),
 nota: (
 <>
 <p>
 Fondo de Diagnóstico y Tratamiento de Alto Costo (Ley 20.850): una lista positiva cerrada,
 con cobertura financiera integral (0% para el beneficiario) y transversal a FONASA e
 ISAPRE.
 </p>
 <p>
 El financiamiento es íntegramente fiscal
 (<CodeRef c="HF.1.1">aporte fiscal con impuestos</CodeRef>) y lo ejecuta FONASA, pero la
 prestación la entrega un prestador autorizado, público o privado en convenio: el caso
 canónico de que financiamiento y provisión son ejes distintos. Su lista cerrada y el
 retraso del 5° decreto son el principal motor de judicialización.
 </p>
 </>
 ),
 },
 {
 id: 'judicial',
 nombre: 'Judicialización (glosa sub-presupuestada)',
 monto: '93.594',
 hf: (
 <>
 Esquema fantasma: paga quien la sentencia obligue, seguro social
 (<CodeRef c="HF.1.2.1">FONASA</CodeRef>), 7% obligatorio
 (<CodeRef c="HF.1.2.2">ISAPRE</CodeRef>) o
 <CodeRef c="HF.2.1">complemento voluntario de ISAPRE</CodeRef>
 </>
 ),
 que: (
 <>
 medicamentos de alto costo,
 <CodeRef c="HC.5.1">ambulatorios</CodeRef> u
 <CodeRef c="HC.1">hospitalarios</CodeRef>
 </>
 ),
 donde: (
 <>
 <CodeRef c="HP.1">hospitales</CodeRef> o
 <CodeRef c="HP.5">farmacias retail</CodeRef>, según el caso
 </>
 ),
 cuenta: 'Ejecución FONASA sentencias 2024 = 93.594 MM$ (DIPRES). Presupuestado solo 28.914: la ejecución desborda la glosa año a año. Sin categoría SHA propia.',
 nota: (
 <>
 <p>
 No es un instrumento de diseño, sino el mecanismo residual: absorbe la demanda de alto
 costo que las listas cerradas (GES/LRS/DAC) y los planes ISAPRE rechazan, y la financia por
 orden judicial. Sin esquema SHA propio, el gasto se imputa al financiador que la sentencia
 obliga a pagar, seguro social (<CodeRef c="HF.1.2.1">FONASA</CodeRef>), 7% obligatorio
 (<CodeRef c="HF.1.2.2">ISAPRE</CodeRef>) o complemento voluntario
 (<CodeRef c="HF.2.1">seguro privado voluntario</CodeRef>).
 </p>
 <p>
 Su existencia mide, en negativo, el tamaño de las listas cerradas. El caso AME (atrofia
 muscular espinal) por sí solo absorbe ~23.000 MM$ para unos 350 pacientes, con una
 concentración mayoritariamente ISAPRE.
 </p>
 </>
 ),
 },
 {
 id: 'dac',
 nombre: 'Drogas de Alto Costo',
 sigla: 'DAC',
 monto: '70.803',
 hf: (
 <>
 Público: aporte fiscal directo
 (<CodeRef c="HF.1.1">impuestos generales</CodeRef>) canalizado por el seguro social
 (<CodeRef c="HF.1.2.1">FONASA</CodeRef>)
 </>
 ),
 que: (
 <>
 medicamentos oncológicos de alto costo,
 <CodeRef c="HC.5.1">ambulatorios</CodeRef> u
 <CodeRef c="HC.1">administrados en el hospital</CodeRef>
 </>
 ),
 donde: 'farmacia hospitalaria de los Servicios de Salud (solo red pública)',
 cuenta: 'DIPRES Glosa 11, Tabla 4.3.',
 nota: (
 <>
 <p>
 Fondo focalizado para oncológicos de alto costo que quedan fuera de GES y de LRS, con
 aprobación caso a caso por comité técnico del MINSAL, financiamiento fiscal directo
 (<CodeRef c="HF.1.1">aporte fiscal con impuestos</CodeRef>) y 0% en la red pública.
 </p>
 <p>
 Solo es elegible para pacientes FONASA con diagnóstico oncológico confirmado y provisión
 exclusiva en la red pública hospitalaria. La demanda ISAPRE, al ser inelegible, termina
 derivando a judicialización.
 </p>
 </>
 ),
 },
 {
 id: 'ffaa',
 nombre: 'FF.AA. y de Orden',
 monto: '62.339 (sin fuente única consolidada)',
 hf: (
 <>
 Público: impuestos generales + cotizaciones obligatorias de sus miembros, clasificado como
 seguro social (<CodeRef c="HF.1.2.1">FONASA y mutuales/cajas obligatorias</CodeRef>)
 </>
 ),
 que: (
 <>
 medicamento embebido en la
 <CodeRef c="HC.1">atención curativa</CodeRef> (no separable)
 </>
 ),
 donde: <>hospitales institucionales propios (<CodeRef c="HP.1">hospitales</CodeRef>)</>,
 cuenta: 'Estimación EP; sin fuente única consolidada. Fuente: rentas de la propiedad y transferencias.',
 nota: (
 <>
 <p>
 Sistemas de salud de las Fuerzas Armadas y de Orden, financiados por impuestos generales
 más cotizaciones obligatorias de sus miembros, con hospitales propios. La submission
 oficial de Chile los clasifica como seguro social
 (<CodeRef c="HF.1.2.1">cotizaciones obligatorias</CodeRef>, junto a FONASA y Mutuales), y
 en SHA el grueso se asume dentro de la {' '}<CodeRef c="HC.1">atención curativa</CodeRef>,
 sin desglose por niveles de función.
 </p>
 <p>
 El monto en CLP es una estimación propia de EP, porque no existe una fuente única
 consolidada.
 </p>
 </>
 ),
 },
 {
 id: 'pni',
 nombre: 'PNI (vacunas)',
 monto: '30.000 (biológicos estrictos)',
 hf: (
 <>
 Público y fiscal: financiado con impuestos generales
 (<CodeRef c="HF.1.1">aporte fiscal del gobierno</CodeRef>)
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.6.2">inmunización (función preventiva)</CodeRef>, no medicamento de
 tratamiento ambulatorio
 </>
 ),
 donde: 'red pública preventiva: vacunatorios y farmacias de atención primaria',
 cuenta: 'DIPRES; biológicos estrictos. NO confundir con presupuesto agregado.',
 nota: (
 <>
 <p>
 Programa Nacional de Inmunizaciones: vacunación universal, copago 0%. Es función preventiva
 (<CodeRef c="HC.6.2">inmunización</CodeRef>), no un medicamento de tratamiento;
 clasificarlo como {' '}<CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> sería un error
 de función.
 </p>
 <p>
 El monto canónico (30.000 MM$) corresponde a los biológicos estrictos. Una cifra cercana a
 la de la LRS, que circula en versiones previas, confunde el presupuesto agregado del
 programa con el costo de las vacunas: no debe sumarse.
 </p>
 </>
 ),
 },
 {
 id: 'mutuales',
 nombre: 'Mutuales (ACHS, Mutual, IST)',
 monto: 'Reportado vía IFRS (no separable)',
 hf: (
 <>
 Público: cotizaciones obligatorias de las empresas, clasificadas como seguro social
 (<CodeRef c="HF.1.2.1">cotización obligatoria del seguro social</CodeRef>)
 </>
 ),
 que: (
 <>
 medicamento embebido en la
 <CodeRef c="HC.1">atención curativa</CodeRef> de la contingencia laboral
 </>
 ),
 donde: <>red propia: centros ambulatorios y hospitales (<CodeRef c="HP.1">hospitales</CodeRef>)</>,
 cuenta: 'Estados financieros IFRS a SHA. Fuente: transferencias / aportes.',
 nota: (
 <>
 <p>
 Seguro de accidentes y enfermedades laborales (Ley 16.744), financiado por cotizaciones de
 las empresas, seguro social en SHA
 (<CodeRef c="HF.1.2.1">cotizaciones obligatorias</CodeRef>), con centros propios. Los
 medicamentos van asociados al tratamiento de la contingencia laboral y se asumen embebidos
 en la {' '}<CodeRef c="HC.1">atención curativa</CodeRef>, sin desglose por función.
 </p>
 </>
 ),
 },
 {
 id: 'isapre7',
 nombre: 'ISAPRE, cotización 7%',
 monto: 'HF.1.2.2 = 845 (USD PPA mill, HC.5.1 2022)',
 hf: (
 <>
 Privado pero obligatorio: el 7% de cotización legal del afiliado
 (<CodeRef c="HF.1.2.2">7% obligatorio en ISAPRE</CodeRef>), que pese al nombre suma al bloque
 público/obligatorio (<CodeRef c="HF.1">aporte fiscal + cotizaciones obligatorias</CodeRef>)
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> y
 <CodeRef c="HC.1">administrados en el hospital</CodeRef>
 </>
 ),
 donde: (
 <>
 clínicas (<CodeRef c="HP.1">hospitales privados</CodeRef>) y
 <CodeRef c="HP.5">farmacias retail</CodeRef>
 </>
 ),
 cuenta: 'Superintendencia, split por residuo. Fuera del total CLP.',
 nota: (
 <>
 <p>
 El 7% de cotización obligatoria del afiliado ISAPRE
 (<CodeRef c="HF.1.2.2">cotización obligatoria del 7% en ISAPRE</CodeRef>) suma, pese al
 nombre "privado", al bloque público/obligatorio
 (<CodeRef c="HF.1">aporte fiscal + cotizaciones obligatorias</CodeRef>). Resuelve una
 confusión recurrente: "obligatorio" no es lo mismo que "privado".
 </p>
 <p>
 La Superintendencia separa el gasto ISAPRE en obligatorio y voluntario por método de
 residuo. En {' '}<CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> de 2022 el
 componente obligatorio aporta 845 USD PPA mill: parte de los 2.112 con que el bloque
 público/obligatorio (<CodeRef c="HF.1">público y obligatorio</CodeRef>) los financia.
 </p>
 </>
 ),
 },
 {
 id: 'isaprecompl',
 nombre: 'ISAPRE, complemento + seguros',
 monto: 'HF.2 = 255 (USD PPA mill, HC.5.1 2022)',
 hf: (
 <>
 Voluntario: el complemento del plan ISAPRE por sobre el 7% + seguros privados
 complementarios (<CodeRef c="HF.2">seguro privado voluntario</CodeRef>)
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> con reembolso parcial
 </>
 ),
 donde: (
 <>
 <CodeRef c="HP.5">farmacias retail</CodeRef> y clínicas
 (<CodeRef c="HP.1">hospitales privados</CodeRef>)
 </>
 ),
 cuenta: 'Serie SHA HC.5.1 por HF. Solo 3,1% de HC.5.1 (2022).',
 nota: (
 <>
 <p>
 El gasto por sobre el 7% obligatorio, el complemento del plan ISAPRE y los seguros privados
 complementarios, es un esquema voluntario
 (<CodeRef c="HF.2">seguro privado voluntario complementario</CodeRef>).
 </p>
 <p>
 La cobertura farmacéutica ambulatoria voluntaria suele ser débil: reembolso parcial con
 topes bajos. Representa apenas un 3,1% de los
 {' '}<CodeRef c="HC.5.1">medicamentos no duraderos por todos los canales</CodeRef>
 {' '}(255 USD PPA mill, 2022): ni el bolsillo ni el público le dejan espacio. ISAPRE es el
 único instrumento que parte su financiamiento en dos esquemas distintos.
 </p>
 </>
 ),
 },
 {
 id: 'cenabast',
 nombre: 'CENABAST (Ley 21.198)',
 monto: 'Ahorro estimado 26.824 (no financia)',
 hf: (
 <>
 No financia: interviene el precio sobre la compra directa de los hogares
 (<CodeRef c="HF.3">bolsillo de los hogares</CodeRef>)
 </>
 ),
 que: <><CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef></>,
 donde: <>farmacias adheridas, populares y privadas (<CodeRef c="HP.5">farmacias retail</CodeRef>)</>,
 cuenta: 'Anuario Cenabast 2024. Logística de compra, no cobertura.',
 nota: (
 <>
 <p>
 La Ley Cenabast permite a la Central de Abastecimiento intermediar la compra de
 medicamentos para ~1.100 farmacias adheridas, populares municipales y privadas.
 </p>
 <p>
 No es cobertura, sino regulación de precio: abastece la logística pero no financia el
 consumo final. El medicamento dispensado sigue siendo
 {' '}<CodeRef c="HF.3">bolsillo del hogar</CodeRef> →
 {' '}<CodeRef c="HC.5.1">medicamento ambulatorio</CodeRef> en
 {' '}<CodeRef c="HP.5">farmacia retail</CodeRef>; el Estado solo baja el precio (ahorro
 estimado ~26.824 MM$ frente al retail privado). Es un caso de manual: el gobierno regula la
 provisión privada sin asumir el pago.
 </p>
 </>
 ),
 },
 {
 id: 'npish',
 nombre: 'NPISH (TELETÓN, COANIQUEM, HdC)',
 monto: 'Cuestionario financiero (Cuenta Satélite)',
 hf: (
 <>
 Voluntario sin fines de lucro: donaciones a instituciones privadas sin fines de lucro
 (parte del bloque <CodeRef c="HF.2">financiamiento voluntario</CodeRef>)
 </>
 ),
 que: (
 <>
 medicamentos dentro de la
 <CodeRef c="HC.1">atención curativa</CodeRef> y la rehabilitación
 </>
 ),
 donde: 'proveedores ambulatorios propios (TELETÓN figura explícita en SHA)',
 cuenta: 'Cuenta Satélite SHA; donaciones.',
 nota: (
 <>
 <p>
 Instituciones privadas sin fines de lucro que proveen atención de salud (rehabilitación de
 discapacidad, niños quemados, personas en situación de calle) e incluyen medicamentos en
 sus tratamientos. Es un esquema sin fines de lucro (parte del
 {' '}<CodeRef c="HF.2">financiamiento voluntario</CodeRef>), estimado vía el cuestionario
 financiero anual de la Cuenta Satélite. TELETÓN figura explícitamente como proveedor
 ambulatorio en SHA.
 </p>
 </>
 ),
 },
 {
 id: 'bolsillo',
 nombre: 'Bolsillo (compra directa)',
 monto: '1.725.000 (EPF 2021-22) · 71% de HC.5.1',
 hf: (
 <>
 Bolsillo de los hogares: copagos + compra directa del hogar
 (<CodeRef c="HF.3">pago de bolsillo de los hogares</CodeRef>)
 </>
 ),
 que: (
 <>
 <CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> + copagos de
 <CodeRef c="HC.1">atención hospitalaria</CodeRef>
 </>
 ),
 donde: <>farmacias retail (<CodeRef c="HP.5">farmacias retail</CodeRef>)</>,
 cuenta: 'EPF IX (MINSAL), serie SHA HC.5.1 por HF.',
 nota: (
 <>
 <p>
 Pago directo del hogar en farmacia retail, más los copagos
 (<CodeRef c="HF.3">bolsillo de los hogares: copagos + compra directa</CodeRef>). Concentra
 el 71,36% del gasto en {' '}<CodeRef c="HC.5.1">medicamentos ambulatorios</CodeRef> (SHA
 2022): la cifra canónica, OECD-pura.
 </p>
 <p>
 Conviene leer bien ese 71%: mide el bolsillo sobre el bien-médico farmacéutico no duradero
 por todos los canales, no sobre el retail estricto. El "62%" del informe CIF es distinto:
 bolsillo sobre el gasto farmacéutico TOTAL, en el perímetro CIF que incluye el fármaco
 hospitalario. Ese denominador del 62% es estimado, porque el detalle intrahospitalario
 {' '}(<CodeRef c="HC.RI.1">medicamentos como ítem de memoria intrahospitalario</CodeRef>)
 figura como Missing en SHA.
 </p>
 <p>
 Una última precisión: el retail no es 100% privado. Cerca de un cuarto lo financia el
 sector público, vía FOFAR, GES-retail y CENABAST.
 </p>
 </>
 ),
 },
]

export default function InstrumentsDimensions() {
 const [open, setOpen] = useState<Instrument | null>(null)

 return (
 <section id="instrumentos-dimensiones">
 <h2 className="ptitle">El mapa biyectivo: cada instrumento chileno en las cuentas SHA</h2>
 <p className="psub">
 Instrumento · Monto · Quién financia · Qué función cubre · Quién provee · Cómo se contabiliza
 </p>

 <p className="lead">
 Hasta aquí vimos los datos OECD ordenados por función, proveedor y financiador. Ahora damos
 el paso inverso: mapeamos cómo cada <strong>instrumento de la política chilena</strong>{' '}
 (GES, Ley Ricarte Soto, APS/FOFAR, judicialización…) se sitúa en ese espacio SHA, con su
 forma de financiamiento, la función que cubre, su proveedor y su monto ejecutado.
 </p>
 <p className="lead">
 Esta tabla es el diccionario uno-a-uno entre la política chilena de medicamentos y las
 cuentas de salud de la OECD: una fila por instrumento, proyectada sobre los ejes ortogonales
 del System of Health Accounts. Leídas juntas, las columnas muestran que{' '}
 <strong>quién paga, qué se compra y quién lo entrega son preguntas independientes</strong>.
 </p>
 <p className="lead">
 Las filas están ordenadas por bloque de financiador, primero el agregado público fiscal y de
 seguridad social, después la regulación de precio y el voluntario, y al final el bolsillo, y
 dentro de cada bloque, por monto descendente. Cada descripción está en español; al pasar el
 cursor sobre un término se muestra el código SHA y su definición.
 </p>

 <div className="card">
 <p>
 El <b>gasto público en medicamentos se ubica en una banda de 0,42% a 0,46% del PIB</b>{' '}
 (≈1,1 a 1,2 billones de pesos, lado ejecución, que converge con el 0,46% del estudio CIF/UC).
 La forma correcta de descomponerlo es <b>por institución</b>: Servicios de Salud (la Farmacia
 736.761 MM$, 2023), Municipios/APS (162.613 MM$, 2023) y las <b>líneas propias y aditivas</b>{' '}
 (Ley Ricarte Soto, PNI, FF.AA.). Así no hay doble conteo. <b>GES, DAC, FOFAR y CEM son
 etiquetas de cobertura</b>, no sumandos: marcan qué medicamento está garantizado, pero ese
 gasto <em>ya está contado</em> dentro del objeto de gasto de su institución. La vista-programa
 de ocho instrumentos (que daba 1.514.814 MM$) no es aditiva: sumar las líneas cuenta la misma
 plata dos veces (financiación FONASA más ejecución de los Servicios de Salud), del orden de
 400.000 MM$ de más.
 </p>
 <p>
 Por eso esta tabla lista los instrumentos para mostrar <em>cómo</em> opera cada uno (quién
 financia, qué función, quién provee), no para sumarlos a un total: las filas con monto en CLP
 son líneas presupuestarias o coberturas, y conviven con la descomposición institucional. El{' '}
 <b>fármaco intrahospitalario público</b> no lo aísla ninguna fuente: la fila usa el{' '}
 <b>punto de cuadre</b> algebraico (público total − ambulatorio público − PNI ≈ <b>246.000 MM$</b>)
 para no romper el total, pero la cifra reportable es una <b>banda de 250.000–725.000</b>{' '}
 (central ~485.000), el cierre es algebraico, un marco que acota, no una prueba. El bolsillo y
 la composición del retail vienen de la serie SHA 2022.
 </p>
 <p>
 No todo instrumento tiene monto propio, y conviene distinguir dos motivos. Uno es de
 clasificación: el <b>componente GES-ISAPRE obligatorio</b> (la cotización del 7% en ISAPRE) sí
 existe en SHA, pero no se puede aislar del total CLP, porque DIPRES reporta por institución y
 no por esquema. Es una <em>brecha de clasificación</em>, no un dato que falte. El otro es de
 transparencia: el CAEC y la porción farmacéutica de varias glosas no tienen ejecución
 reportada, ahí sí hay <em>vacíos</em> reales. Haz clic en cualquier instrumento para ver la
 glosa metodológica completa.
 </p>
 </div>

 <Caption
 ch={5}
 n={1}
 kind="tabla"
 title="Mapa biyectivo: cada instrumento chileno en las cuentas SHA (monto, financiador, función, proveedor)"
 />
 <div className="tablewrap">
 <table>
 <colgroup>
 <col style={{ width: '13%' }} />
 <col style={{ width: '11%' }} />
 <col style={{ width: '22%' }} />
 <col style={{ width: '18%' }} />
 <col style={{ width: '18%' }} />
 <col style={{ width: '18%' }} />
 </colgroup>
 <thead>
 <tr>
 <th>Instrumento</th>
 <th>Monto (MM$ CLP)</th>
 <th>Quién financia</th>
 <th>Qué función cubre</th>
 <th>Quién provee</th>
 <th>Cómo se contabiliza</th>
 </tr>
 </thead>
 <tbody>
 {ROWS.map(r => (
 <tr
 key={r.id}
 onClick={() => setOpen(r)}
 style={{ cursor: 'pointer' }}
 >
 <td>
 <span className="expander">{r.nombre}</span>
 {r.sigla ? <span className="pill" style={{ marginLeft: 6 }}>{r.sigla}</span> : null}
 </td>
 <td style={{ textAlign: 'right', fontWeight: 600, whiteSpace: 'nowrap' }}>{r.monto}</td>
 <td style={{ textAlign: 'left', fontWeight: 700, color: 'var(--ep)', background: '#eaf2fb' }}>
 {r.hf}
 </td>
 <td style={{ textAlign: 'left' }}>{r.que}</td>
 <td style={{ textAlign: 'left' }}>{r.donde}</td>
 <td style={{ textAlign: 'left', fontSize: 13 }}>{r.cuenta}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 <p className="note">
 El gasto público en medicamentos se ubica en una <strong>banda de 0,42% a 0,46% del PIB</strong>{' '}
 (≈1,1 a 1,2 billones de pesos, lado ejecución), descompuesto sin doble conteo por institución
 (Servicios de Salud, Municipios/APS) más líneas propias y aditivas (LRS, PNI, FF.AA.). En el
 marco SHA ese gasto cae en dos funciones: los{' '}
 {labelHC('HC51')} (medicamentos ambulatorios) y el fármaco administrado en la {labelHC('HC1')},
 que no es separable y va embebido, su detalle por insumo
 (<CodeRef c="HC.RI.1">medicamentos como ítem de memoria intrahospitalario</CodeRef>) figura
 como Missing, y por eso el intrahospitalario público se acota a una banda de 250.000–725.000 MM$
 (punto de cuadre algebraico ≈246.000). En esquemas, el
 bloque {labelHF('HF1')} reúne el aporte fiscal y las cotizaciones obligatorias{' '}
 {labelHF('HF121')} (FONASA) y {labelHF('HF122')} (7% en ISAPRE). La
 composición del retail viene de la serie SHA 2022 (USD PPA). Pasa el cursor sobre cualquier
 término para ver su código SHA.
 </p>

 {open ? (
 <div className="modal-backdrop" onClick={() => setOpen(null)}>
 <div className="modal" onClick={e => e.stopPropagation()}>
 <button className="close" onClick={() => setOpen(null)} aria-label="Cerrar">×</button>
 <h3>
 {open.nombre}
 {open.sigla ? <span className="pill" style={{ marginLeft: 8 }}>{open.sigla}</span> : null}
 </h3>
 <div className="grid2" style={{ margin: '12px 0' }}>
 <div className="card">
 <div className="note">Monto (MM$ CLP)</div>
 <strong>{open.monto}</strong>
 </div>
 <div className="card warn">
 <div className="note">Quién financia</div>
 <strong>{open.hf}</strong>
 </div>
 <div className="card">
 <div className="note">Qué función cubre</div>
 {open.que}
 </div>
 <div className="card">
 <div className="note">Quién provee</div>
 {open.donde}
 </div>
 <div className="card" style={{ gridColumn: '1 / -1' }}>
 <div className="note">Cómo se contabiliza / fuente</div>
 {open.cuenta}
 </div>
 </div>
 <div style={{ fontSize: 14 }}>{open.nota}</div>
 </div>
 </div>
 ) : null}
 </section>
 )
}
