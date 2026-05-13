import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Política de Privacidad — Scribe',
  description:
    'Política de privacidad de Scribe, plataforma de escritura académica',
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 text-[var(--ink)]">
      <header className="mb-12 border-b border-[var(--line)] pb-6">
        <p className="mb-2 text-xs uppercase tracking-wider text-[var(--muted)]">
          <Link href="/" className="hover:underline">
            Scribe
          </Link>{' '}
          · Documentos legales
        </p>
        <h1 className="text-3xl font-bold tracking-tight">
          Política de Privacidad
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Última actualización: 8 de abril de 2026
        </p>
      </header>

      <article className="prose prose-sm max-w-none space-y-6 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold">1. Quiénes somos</h2>
          <p>
            Scribe es una plataforma de escritura y revisión de documentos
            académicos desarrollada y operada por <strong>Martín Illanes</strong>{' '}
            como parte del ecosistema de herramientas personales de illanes00. La
            plataforma está alojada en{' '}
            <a
              href="https://scribe.illanes00.cl"
              className="text-[var(--c-blue)] underline"
            >
              scribe.illanes00.cl
            </a>
            .
          </p>
          <p>
            Scribe se ofrece para uso personal del operador y de colaboradores
            autorizados explícitamente. No es un servicio comercial abierto al
            público general.
          </p>
          <p>
            Para consultas sobre esta política puedes escribir a{' '}
            <a
              href="mailto:martinillanesv@gmail.com"
              className="text-[var(--c-blue)] underline"
            >
              martinillanesv@gmail.com
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            2. Qué información recopilamos
          </h2>
          <p>
            Scribe recopila únicamente la información estrictamente necesaria
            para ofrecer sus funcionalidades:
          </p>
          <ul className="list-disc pl-6">
            <li>
              <strong>Identificación de usuario:</strong> nombre y correo
              electrónico provistos por el proveedor de identidad (Authentik o
              Google OAuth, según el flujo) cuando inicias sesión.
            </li>
            <li>
              <strong>Contenido que tú creas:</strong> los documentos,
              comentarios, claims, citas bibliográficas y notas que generas o
              importas dentro de la plataforma.
            </li>
            <li>
              <strong>Metadatos de uso:</strong> registros de actividad básica
              (creación, edición, eliminación, exportación) para auditoría y
              recuperación ante errores.
            </li>
            <li>
              <strong>Tokens de integración:</strong> cuando autorizas a Scribe
              a conectarse con servicios externos como Google Docs, almacenamos
              de forma cifrada los tokens necesarios para esa integración.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            3. Para qué usamos la información
          </h2>
          <ul className="list-disc pl-6">
            <li>
              Permitirte editar, comentar y revisar documentos académicos.
            </li>
            <li>
              Sincronizar tu trabajo con servicios externos como Google Docs y
              Google Drive cuando lo autorices.
            </li>
            <li>
              Generar respuestas asistidas por inteligencia artificial sobre el
              contenido de tus documentos cuando lo solicitas.
            </li>
            <li>
              Mantener un historial de versiones para que puedas restaurar
              cambios anteriores.
            </li>
          </ul>
          <p>
            <strong>No usamos tu contenido para entrenar modelos.</strong> El
            contenido enviado a servicios de IA (Anthropic Claude) se procesa
            según las condiciones del proveedor, que excluyen el uso de
            entradas API para entrenamiento de modelos.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            4. Acceso a Google Workspace
          </h2>
          <p>
            Cuando autorizas la integración con Google, Scribe solicita los
            siguientes permisos:
          </p>
          <ul className="list-disc pl-6">
            <li>
              <strong>Google Drive y Documents:</strong> para importar y
              exportar documentos seleccionados por ti.
            </li>
            <li>
              <strong>Google Slides:</strong> para importar y exportar
              presentaciones seleccionadas por ti.
            </li>
          </ul>
          <p>
            Scribe solo accede a archivos sobre los cuales ejecutas una acción
            explícita (vincular, importar, sincronizar). No escanea tu Drive en
            segundo plano. Puedes revocar el acceso en cualquier momento desde{' '}
            <a
              href="https://myaccount.google.com/permissions"
              className="text-[var(--c-blue)] underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              tu cuenta de Google
            </a>
            .
          </p>
          <p>
            El uso de información obtenida de las APIs de Google Workspace por
            parte de Scribe cumple con la{' '}
            <a
              href="https://developers.google.com/terms/api-services-user-data-policy"
              className="text-[var(--c-blue)] underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Google API Services User Data Policy
            </a>
            , incluyendo los requisitos de uso limitado.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            5. Con quién compartimos información
          </h2>
          <p>
            Scribe no comparte tu información personal ni el contenido de tus
            documentos con terceros, con las siguientes excepciones técnicas
            necesarias para el funcionamiento de la plataforma:
          </p>
          <ul className="list-disc pl-6">
            <li>
              <strong>Google</strong>, cuando ejecutas una acción de
              importación, exportación o sincronización con tus propios
              documentos de Google.
            </li>
            <li>
              <strong>Anthropic</strong>, cuando ejecutas una función de
              análisis o respuesta asistida por IA sobre el contenido del
              documento que estás revisando.
            </li>
            <li>
              <strong>Authentik</strong>, como proveedor de identidad para
              autenticación, si usas el flujo de inicio de sesión institucional.
            </li>
          </ul>
          <p>
            En todos los casos, los datos viajan cifrados en tránsito (HTTPS).
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">6. Almacenamiento y retención</h2>
          <p>
            La información se almacena en infraestructura propia (servidores VPS
            gestionados por illanes00). Los datos se conservan mientras tengas
            una cuenta activa o mientras sean necesarios para los proyectos en
            curso.
          </p>
          <p>
            Puedes solicitar la eliminación de tu cuenta y de los datos
            asociados en cualquier momento escribiendo al correo de contacto.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">7. Tus derechos</h2>
          <p>
            De acuerdo con la legislación chilena (Ley 19.628 sobre Protección
            de la Vida Privada) y, cuando corresponda, el Reglamento General de
            Protección de Datos europeo, tienes derecho a:
          </p>
          <ul className="list-disc pl-6">
            <li>Acceder a la información personal que tenemos sobre ti.</li>
            <li>Solicitar la corrección de datos inexactos.</li>
            <li>Solicitar la eliminación de tus datos.</li>
            <li>Revocar consentimientos que hayas otorgado previamente.</li>
            <li>Exportar tu contenido en formatos abiertos.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold">8. Cambios a esta política</h2>
          <p>
            Si actualizamos esta política, cambiaremos la fecha de “Última
            actualización” al inicio. Para cambios significativos te
            notificaremos por correo electrónico cuando sea posible.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">9. Contacto</h2>
          <p>
            Cualquier consulta sobre privacidad, manejo de datos o ejercicio de
            derechos puedes dirigirla a:
          </p>
          <p>
            <strong>Martín Illanes</strong>
            <br />
            <a
              href="mailto:martinillanesv@gmail.com"
              className="text-[var(--c-blue)] underline"
            >
              martinillanesv@gmail.com
            </a>
          </p>
        </section>
      </article>

      <footer className="mt-16 border-t border-[var(--line)] pt-6 text-xs text-[var(--muted)]">
        <Link href="/" className="hover:underline">
          ← Volver a Scribe
        </Link>
        <span className="mx-3">·</span>
        <Link href="/terms" className="hover:underline">
          Condiciones del Servicio
        </Link>
      </footer>
    </main>
  );
}
