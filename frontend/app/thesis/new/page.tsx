"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, GraduationCap } from "lucide-react";

import { projectsApi, ProjectVisibility } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function NewThesisPage() {
  const router = useRouter();
  const { authenticated, loading: authLoading, loginWithSSO } = useAuth();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [advisor, setAdvisor] = useState("");
  const [university, setUniversity] = useState("");
  const [programme, setProgramme] = useState("Magíster");
  const [visibility, setVisibility] = useState<ProjectVisibility>("private");
  const [evidenceDashboardUrl, setEvidenceDashboardUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const project = await projectsApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        project_type: "thesis",
        visibility,
        evidence_dashboard_url: evidenceDashboardUrl.trim() || null,
        metadata_json: {
          advisor: advisor.trim() || "(por definir)",
          university: university.trim() || "(por definir)",
          programme: programme.trim() || "Magíster",
          status: "drafting",
          defense_date: null,
        },
      });
      router.push(`/thesis/${project.slug}`);
    } catch (err) {
      const e = err as { message?: string };
      setError(e.message ?? "No se pudo crear la tesis");
    } finally {
      setSubmitting(false);
    }
  }

  if (!authLoading && !authenticated) {
    return (
      <div className="min-h-screen bg-bg">
        <main className="container py-16 max-w-xl">
          <h1 className="text-2xl font-bold mb-3">Iniciar sesión</h1>
          <p className="text-muted mb-6">
            Necesitas iniciar sesión para crear una tesis.
          </p>
          <button onClick={loginWithSSO} className="btn btn-primary">
            Iniciar sesión
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <main className="container py-8 max-w-2xl">
        <Link
          href="/thesis"
          className="text-sm text-muted hover:text-ink inline-flex items-center gap-1 mb-4"
        >
          <ArrowLeft size={14} /> Todas las tesis
        </Link>

        <h1 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <GraduationCap size={22} className="text-c-purple" />
          Nueva tesis
        </h1>
        <p className="text-muted mb-8">
          Crea un proyecto de tesis con capítulos, dashboard y export.
        </p>

        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Título" required>
            <input
              type="text"
              required
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mi tesis sobre…"
            />
          </Field>

          <Field label="Descripción">
            <textarea
              className="input min-h-24"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Resumen breve del proyecto"
            />
          </Field>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Profesor guía">
              <input
                type="text"
                className="input"
                value={advisor}
                onChange={(e) => setAdvisor(e.target.value)}
              />
            </Field>
            <Field label="Universidad">
              <input
                type="text"
                className="input"
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
              />
            </Field>
            <Field label="Programa">
              <input
                type="text"
                className="input"
                value={programme}
                onChange={(e) => setProgramme(e.target.value)}
              />
            </Field>
            <Field label="Visibilidad">
              <select
                className="input"
                value={visibility}
                onChange={(e) =>
                  setVisibility(e.target.value as ProjectVisibility)
                }
              >
                <option value="private">Privada (solo yo)</option>
                <option value="shared">Compartida (autenticados)</option>
                <option value="public">Pública (todos)</option>
              </select>
            </Field>
          </div>

          <Field label="Dashboard de evidencia (URL)">
            <input
              type="url"
              className="input"
              value={evidenceDashboardUrl}
              onChange={(e) => setEvidenceDashboardUrl(e.target.value)}
              placeholder="https://thesis.cochid.cl"
            />
          </Field>

          <div className="flex items-center gap-2 pt-4">
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="btn btn-primary"
            >
              {submitting ? "Creando…" : "Crear tesis"}
            </button>
            <Link href="/thesis" className="btn">
              Cancelar
            </Link>
          </div>
        </form>
      </main>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium block mb-1">
        {label}
        {required && <span className="text-c-red ml-0.5">*</span>}
      </span>
      {children}
    </label>
  );
}
