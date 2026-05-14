"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Database,
  FileText,
  GraduationCap,
  Plus,
  RefreshCw,
  Settings,
} from "lucide-react";

import { Project, projectsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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

function metaString(
  project: Project,
  key: "advisor" | "university" | "programme" | "status",
): string | null {
  const meta = project.metadata_json as Record<string, unknown> | null;
  if (!meta) return null;
  const v = meta[key];
  return typeof v === "string" && v.length > 0 ? v : null;
}

export default function ThesisIndexPage() {
  const pathname = usePathname();
  const { authenticated, loading: authLoading, loginWithSSO } = useAuth();
  const [theses, setTheses] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await projectsApi.listThesis();
      setTheses(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error cargando tesis");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) {
      load();
    }
  }, [authLoading, load]);

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
              const isActive = pathname === href;
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold mb-1 flex items-center gap-2">
              <GraduationCap size={22} className="text-c-purple" />
              Tesis
            </h1>
            <p className="text-sm text-muted">
              Proyectos de tesis con capítulos, claims, bibliografía y dashboard
              de evidencia.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              className="btn btn-sm"
              disabled={loading}
              title="Refrescar"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>
            <Link href="/thesis/new" className="btn btn-primary">
              <Plus size={16} className="mr-1.5" />
              Nueva tesis
            </Link>
          </div>
        </div>

        {!authLoading && !authenticated && (
          <div className="card mb-6">
            <p className="mb-3">
              Inicia sesión para ver tus tesis privadas.
            </p>
            <button onClick={loginWithSSO} className="btn btn-primary">
              Iniciar sesión
            </button>
          </div>
        )}

        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={load} className="text-sm underline">
              Reintentar
            </button>
          </div>
        )}

        {loading && (
          <div className="py-16 text-center">
            <RefreshCw
              size={24}
              className="mx-auto mb-4 text-muted animate-spin"
            />
            <p className="text-muted">Cargando tesis…</p>
          </div>
        )}

        {!loading && theses.length === 0 && (
          <div className="border border-line bg-paper text-center py-20 px-8">
            <div className="w-16 h-16 mx-auto mb-6 border-2 border-line flex items-center justify-center">
              <GraduationCap size={28} className="text-muted" />
            </div>
            <h3 className="font-bold text-xl mb-2">Aún no tienes tesis</h3>
            <p className="text-muted max-w-lg mx-auto mb-8">
              Una tesis es un proyecto especial con capítulos, dashboard de
              evidencia y export PDF/DOCX. Crea la primera para empezar.
            </p>
            <Link href="/thesis/new" className="btn btn-primary">
              <Plus size={16} className="mr-2" />
              Crear mi tesis
            </Link>
          </div>
        )}

        {!loading && theses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {theses.map((t) => (
              <ThesisCard key={t.slug} project={t} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function ThesisCard({ project }: { project: Project }) {
  const status = metaString(project, "status");
  const advisor = metaString(project, "advisor");
  const university = metaString(project, "university");
  const updated = new Date(project.created_at).toLocaleDateString("es-CL", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <Link href={`/thesis/${project.slug}`} className="block group">
      <div className="card h-full flex flex-col hover:border-line-strong transition-colors">
        <div className="flex items-center justify-between mb-3">
          <span className="pill bg-c-purple/10 text-c-purple border-transparent text-xs">
            <GraduationCap size={12} className="mr-1" />
            Tesis
          </span>
          <div className="flex items-center gap-2">
            <span
              className={`pill text-xs ${VISIBILITY_PILL_CLASSES[project.visibility] ?? "pill-info"}`}
            >
              {project.visibility}
            </span>
            {status && (
              <span
                className={`pill text-xs ${STATUS_PILL_CLASSES[status] ?? "pill-info"}`}
              >
                {statusLabel(status)}
              </span>
            )}
          </div>
        </div>

        <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-c-blue transition-colors mb-2">
          {project.name}
        </h3>

        {project.description && (
          <p className="text-sm text-muted line-clamp-2 mb-3">
            {project.description}
          </p>
        )}

        <div className="text-xs text-muted mt-auto pt-3 border-t border-line space-y-0.5">
          {advisor && <div>Profesor guía: {advisor}</div>}
          {university && <div>Universidad: {university}</div>}
          <div>Creada: {updated}</div>
        </div>
      </div>
    </Link>
  );
}
