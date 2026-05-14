"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import {
  ArrowLeft,
  BookMarked,
  BookOpen,
  Database,
  ExternalLink,
  FileDown,
  FileText,
  GraduationCap,
  Library,
  Plus,
  RefreshCw,
  Settings,
  Shield,
} from "lucide-react";

import {
  documentsApi,
  ProjectChapter,
  ProjectDetail,
  projectsApi,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

function metaString(
  project: ProjectDetail | null,
  key: string,
): string | null {
  if (!project) return null;
  const meta = project.metadata_json as Record<string, unknown> | null;
  if (!meta) return null;
  const v = meta[key];
  return typeof v === "string" && v.length > 0 ? v : null;
}

const STATUS_PILL_CLASSES: Record<string, string> = {
  drafting: "pill-info",
  in_review: "bg-c-amber/10 text-c-amber border-transparent",
  defended: "bg-c-green/10 text-c-green border-transparent",
  archived: "bg-muted/10 text-muted border-transparent",
};

const VISIBILITY_PILL_CLASSES: Record<string, string> = {
  private: "bg-muted/10 text-muted border-transparent",
  shared: "pill-info",
  public: "bg-c-green/10 text-c-green border-transparent",
};

function statusLabel(status: string | undefined | null): string {
  if (!status) return "Sin estado";
  switch (status) {
    case "drafting":
      return "Redacción";
    case "in_review":
      return "En revisión";
    case "defended":
      return "Defendida";
    case "archived":
      return "Archivada";
    default:
      return status;
  }
}

export default function ThesisDetailPage() {
  const pathname = usePathname();
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { loginWithSSO } = useAuth();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [creatingChapter, setCreatingChapter] = useState(false);
  const [embedDashboard, setEmbedDashboard] = useState(false);

  const load = useCallback(async () => {
    if (!slug) return;
    try {
      setLoading(true);
      setError(null);
      setErrorStatus(null);
      const result = await projectsApi.get(slug);
      setProject(result);
    } catch (err) {
      const e = err as { status?: number; message?: string };
      setErrorStatus(e.status ?? null);
      setError(e.message ?? "Error cargando tesis");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateChapter() {
    if (!project) return;
    try {
      setCreatingChapter(true);
      const chapterIndex = project.chapters.length + 1;
      const doc = await documentsApi.create({
        title: `Capítulo ${chapterIndex}`,
        doc_type: "thesis",
        front_matter: {
          order: chapterIndex,
          project_slug: project.slug,
          project_id: project.id,
        },
      });
      window.location.href = `/editor/${doc.slug}`;
    } catch {
      alert("No se pudo crear el capítulo");
    } finally {
      setCreatingChapter(false);
    }
  }

  const navLinks = [
    { href: "/dashboard", label: "Documents", icon: FileText },
    { href: "/thesis", label: "Tesis", icon: GraduationCap },
    { href: "/knowledge", label: "Knowledge", icon: BookOpen },
    { href: "/data", label: "Data", icon: Database },
    { href: "/integrations", label: "Integrations", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => {
              const isActive = pathname?.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors ${
                    isActive
                      ? "bg-bg text-ink font-medium"
                      : "text-muted hover:text-ink hover:bg-bg/50"
                  }`}
                >
                  <Icon size={14} />
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="container py-8">
        <Link
          href="/thesis"
          className="text-sm text-muted hover:text-ink inline-flex items-center gap-1 mb-4"
        >
          <ArrowLeft size={14} /> Todas las tesis
        </Link>

        {loading && (
          <div className="py-16 text-center">
            <RefreshCw
              size={24}
              className="mx-auto mb-4 text-muted animate-spin"
            />
            <p className="text-muted">Cargando tesis…</p>
          </div>
        )}

        {!loading && error && (
          <div className="card bg-c-red/10 text-c-red mb-6">
            <p className="mb-3">{error}</p>
            <div className="flex gap-2">
              <button onClick={load} className="btn btn-sm">
                Reintentar
              </button>
              {errorStatus === 404 && (
                <button onClick={loginWithSSO} className="btn btn-sm">
                  Iniciar sesión
                </button>
              )}
            </div>
          </div>
        )}

        {!loading && project && (
          <>
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-2">
                <span className="pill bg-c-purple/10 text-c-purple border-transparent text-xs">
                  <GraduationCap size={12} className="mr-1" />
                  Tesis
                </span>
                <span
                  className={`pill text-xs ${VISIBILITY_PILL_CLASSES[project.visibility] ?? "pill-info"}`}
                >
                  {project.visibility}
                </span>
                {metaString(project, "status") && (
                  <span
                    className={`pill text-xs ${STATUS_PILL_CLASSES[metaString(project, "status") || ""] ?? "pill-info"}`}
                  >
                    {statusLabel(metaString(project, "status"))}
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-bold mb-2 leading-tight">
                {project.name}
              </h1>
              {project.description && (
                <p className="text-muted max-w-3xl">{project.description}</p>
              )}
              <dl className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-sm mt-4">
                <Meta label="Profesor guía" value={metaString(project, "advisor")} />
                <Meta label="Universidad" value={metaString(project, "university")} />
                <Meta label="Programa" value={metaString(project, "programme")} />
                <Meta
                  label="Defensa"
                  value={metaString(project, "defense_date") ?? "Por definir"}
                />
              </dl>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                icon={<BookMarked size={16} />}
                label="Capítulos"
                value={project.chapters.length}
              />
              <StatCard
                icon={<Shield size={16} />}
                label="Claims"
                value={project.claim_count}
              />
              <StatCard
                icon={<Library size={16} />}
                label="Bibliografía"
                value={project.bibliography_count}
              />
              <StatCard
                icon={<FileText size={16} />}
                label="Visibilidad"
                value={project.visibility}
              />
            </div>

            {/* Chapters */}
            <section className="mb-10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg flex items-center gap-2">
                  <BookMarked size={18} className="text-muted" />
                  Capítulos
                </h2>
                <button
                  onClick={handleCreateChapter}
                  disabled={creatingChapter}
                  className="btn btn-primary btn-sm"
                >
                  <Plus size={14} className="mr-1.5" />
                  {creatingChapter ? "Creando…" : "Nuevo capítulo"}
                </button>
              </div>

              {project.chapters.length === 0 ? (
                <div className="border border-line bg-paper text-center py-12 px-6">
                  <p className="text-muted mb-4">
                    Esta tesis aún no tiene capítulos.
                  </p>
                  <button
                    onClick={handleCreateChapter}
                    disabled={creatingChapter}
                    className="btn btn-primary"
                  >
                    <Plus size={14} className="mr-1.5" />
                    Crear primer capítulo
                  </button>
                </div>
              ) : (
                <ol className="border border-line bg-paper divide-y divide-line">
                  {project.chapters.map((ch, idx) => (
                    <ChapterRow key={ch.id} index={idx + 1} chapter={ch} />
                  ))}
                </ol>
              )}
            </section>

            {/* Evidence dashboard */}
            <section className="mb-10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg flex items-center gap-2">
                  <Database size={18} className="text-muted" />
                  Dashboard de evidencia
                </h2>
                {project.evidence_dashboard_url && (
                  <button
                    onClick={() => setEmbedDashboard((v) => !v)}
                    className="btn btn-sm"
                  >
                    {embedDashboard ? "Ocultar preview" : "Mostrar preview"}
                  </button>
                )}
              </div>

              {project.evidence_dashboard_url ? (
                <div className="border border-line bg-paper p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {project.evidence_dashboard_url}
                      </p>
                      <p className="text-xs text-muted">
                        Dashboard externo con datos, gráficos y métricas.
                      </p>
                    </div>
                    <a
                      href={project.evidence_dashboard_url}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-primary btn-sm flex-shrink-0"
                    >
                      <ExternalLink size={14} className="mr-1.5" />
                      Abrir
                    </a>
                  </div>
                  {embedDashboard && (
                    <div className="mt-4 border border-line aspect-video">
                      <iframe
                        src={project.evidence_dashboard_url}
                        title="Evidence dashboard"
                        className="w-full h-full"
                        sandbox="allow-scripts allow-same-origin allow-popups"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="border border-line bg-paper p-6 text-sm text-muted">
                  No hay dashboard de evidencia configurado para esta tesis.
                </div>
              )}
            </section>

            {/* Export */}
            <section>
              <h2 className="font-bold text-lg flex items-center gap-2 mb-4">
                <FileDown size={18} className="text-muted" />
                Exportar
              </h2>
              <div className="flex flex-wrap gap-2">
                <button
                  className="btn"
                  disabled
                  title="Pipeline Quarto pendiente"
                >
                  <FileDown size={14} className="mr-1.5" />
                  Export PDF
                </button>
                <button
                  className="btn"
                  disabled
                  title="Pipeline Quarto pendiente"
                >
                  <FileDown size={14} className="mr-1.5" />
                  Export DOCX
                </button>
                <span className="text-xs text-muted self-center ml-2">
                  Próximamente · Quarto pipeline en construcción
                </span>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-xs text-muted uppercase tracking-wide">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="border border-line bg-paper p-4">
      <div className="text-xs text-muted uppercase tracking-wide mb-1 flex items-center gap-1.5">
        {icon}
        {label}
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function ChapterRow({
  index,
  chapter,
}: {
  index: number;
  chapter: ProjectChapter;
}) {
  const updatedAt = new Date(chapter.updated_at).toLocaleDateString("es-CL", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  return (
    <li>
      <Link
        href={`/editor/${chapter.slug}`}
        className="flex items-center gap-4 px-4 py-3 hover:bg-bg transition-colors"
      >
        <span className="text-sm font-mono text-muted w-8 text-right flex-shrink-0">
          {String(chapter.order ?? index).padStart(2, "0")}
        </span>
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate">{chapter.title}</div>
          <div className="text-xs text-muted">
            {updatedAt} · {chapter.status}
          </div>
        </div>
        <div className="text-xs text-muted flex items-center gap-1 flex-shrink-0">
          <Shield size={12} />
          {chapter.verified_count}/{chapter.claim_count}
        </div>
      </Link>
    </li>
  );
}
