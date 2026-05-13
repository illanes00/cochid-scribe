import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Condiciones del Servicio — Scribe',
  description:
    'Condiciones del servicio de Scribe, plataforma de escritura académica',
};

export default function TermsPage() {
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
          Condiciones del Servicio
        </h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Última actualización: 8 de abril de 2026
        </p>
      </header>

      <article className="prose prose-sm max-w-none space-y-6 leading-relaxed">
        <section>
          <h2 className="text-xl font-semibold">1. Aceptación</h2>
          <p>
            Al acceder o usar Scribe (en adelante, “el Servicio”), aceptas
            estas Condiciones del Servicio. Si no estás de acuerdo con alguna
            parte, no uses el Servicio.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">2. Descripción del Servicio</h2>
          <p>
            Scribe es una plataforma de escritura, revisión y compilación de
            documentos académicos desarrollada y operada por{' '}
            <strong>Martín Illanes</strong> como parte del ecosistema personal
            de herramientas de illanes00. Ofrece funcionalidades de edición,
            gestión de comentarios, sincronización con Google Workspace, y
            asistencia por inteligencia artificial.
          </p>
          <p>
            Está destinada al uso personal del operador y de colaboradores
            autorizados explícitamente. No es un servicio comercial abierto al
            público general.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">3. Cuentas y autenticación</h2>
          <p>
            Para usar el Servicio debes autenticarte mediante uno de los
            mecanismos disponibles (Authentik o Google OAuth). Eres responsable
            de mantener la confidencialidad de tus credenciales y de toda
            actividad realizada bajo tu cuenta.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">4. Uso aceptable</h2>
          <p>Al usar el Servicio te comprometes a no:</p>
          <ul className="list-disc pl-6">
            <li>
              Subir o procesar contenido ilegal, difamatorio, o que infrinja
              derechos de terceros.
            </li>
            <li>
              Intentar acceder a documentos, comentarios o información de
              otros usuarios sin autorización.
            </li>
            <li>
              Realizar ingeniería inversa, descompilar o intentar extraer el
              código fuente del Servicio.
            </li>
            <li>
              Usar el Servicio para enviar spam, malware o cualquier contenido
              dañino.
            </li>
            <li>
              Sobrecargar la infraestructura mediante usos automatizados que no
              hayan sido explícitamente autorizados.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold">5. Propiedad del contenido</h2>
          <p>
            El contenido que creas, importas o subes a Scribe sigue siendo
            tuyo. Scribe no reclama propiedad sobre tus documentos,
            comentarios, claims, citas o notas.
          </p>
          <p>
            Concedes a Scribe únicamente la licencia técnica necesaria para
            almacenar, procesar y mostrar tu contenido en el contexto del
            Servicio (por ejemplo, generar previsualizaciones, indexar para
            búsqueda interna, sincronizar con Google Drive cuando lo
            autorizas).
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">6. Asistencia por IA</h2>
          <p>
            Cuando solicitas funcionalidades de inteligencia artificial
            (resumen, análisis, respuesta a comentarios, sugerencias de
            edición), el contenido relevante de tu documento se envía al
            proveedor de IA correspondiente (actualmente Anthropic Claude) para
            generar la respuesta.
          </p>
          <p>
            Las respuestas generadas por IA son sugerencias, no afirmaciones
            verificadas. Eres responsable de revisar críticamente cualquier
            sugerencia antes de incorporarla a tus documentos. Scribe no
            garantiza la exactitud, completitud o pertinencia académica de las
            respuestas generadas.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            7. Integración con Google Workspace
          </h2>
          <p>
            Cuando autorizas la integración con Google, Scribe puede leer y
            escribir documentos, presentaciones y archivos del Drive sobre los
            cuales ejecutas acciones explícitas. La integración respeta las
            políticas de Google API Services User Data Policy. Puedes revocar
            el acceso en cualquier momento desde tu cuenta de Google.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">8. Disponibilidad</h2>
          <p>
            Scribe se ofrece “tal cual” y “según disponibilidad”. No
            garantizamos disponibilidad continua del Servicio ni ausencia de
            errores. Realizamos respaldos periódicos pero recomendamos que
            mantengas copias propias del contenido crítico mediante exportación
            o sincronización con Google Docs.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">
            9. Limitación de responsabilidad
          </h2>
          <p>
            En la máxima medida permitida por la ley, Scribe y su desarrollador
            no son responsables por pérdida de datos, daños indirectos, lucro
            cesante, ni perjuicios derivados del uso o imposibilidad de uso
            del Servicio.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">10. Cambios al Servicio</h2>
          <p>
            Scribe está en desarrollo activo. Podemos modificar, agregar o
            descontinuar funcionalidades en cualquier momento. Cuando los
            cambios afecten significativamente la forma en que usas el
            Servicio, haremos un esfuerzo razonable por notificarte con
            anticipación.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">11. Cancelación de la cuenta</h2>
          <p>
            Puedes solicitar el cierre de tu cuenta y la eliminación de tu
            contenido en cualquier momento escribiendo a{' '}
            <a
              href="mailto:martinillanesv@gmail.com"
              className="text-[var(--c-blue)] underline"
            >
              martinillanesv@gmail.com
            </a>
            . El operador se reserva el derecho de suspender cuentas que
            violen estas Condiciones.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">12. Ley aplicable</h2>
          <p>
            Estas Condiciones se rigen por las leyes de la República de Chile.
            Cualquier controversia relacionada con el Servicio será resuelta
            ante los tribunales ordinarios de Santiago de Chile.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold">13. Contacto</h2>
          <p>
            Cualquier consulta sobre estas Condiciones puedes dirigirla a:
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
        <Link href="/privacy" className="hover:underline">
          Política de Privacidad
        </Link>
      </footer>
    </main>
  );
}
