'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { FileText, RefreshCw } from 'lucide-react'
import { WorkspaceGate } from '@/components/auth/WorkspaceGate'
import { DictationPanel } from '@/components/panels/DictationPanel'
import { WorkspaceContextPanel } from '@/components/panels/WorkspaceContextPanel'
import { useAuth } from '@/lib/auth'
import { renderMarkdown } from '@/lib/markdown'
import { Document, documentsApi } from '@/lib/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

export default function MedicamentosWorkspacePage() {
  const { authenticated, loading } = useAuth()
  const [document, setDocument] = useState<Document | null>(null)
  const [documentSlug, setDocumentSlug] = useState('cif-medicamentos-workspace')
  const [pageLoading, setPageLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadWorkspace = useCallback(async (showSpinner = true) => {
    if (!authenticated) return
    try {
      if (showSpinner) {
        setPageLoading(true)
      } else {
        setRefreshing(true)
      }
      setError(null)

      const seedResponse = await fetch(`${API_BASE}/api/v1/dictation/workspace/cif-medicamentos/seed`, {
        method: 'POST',
        credentials: 'include',
      })

      if (!seedResponse.ok) {
        const payload = await seedResponse.json().catch(() => ({}))
        throw new Error(payload.detail || 'No se pudo preparar el workspace')
      }

      const seeded = await seedResponse.json()
      setDocumentSlug(seeded.slug)
      const loadedDocument = await documentsApi.get(seeded.slug)
      setDocument(loadedDocument)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado')
    } finally {
      setPageLoading(false)
      setRefreshing(false)
    }
  }, [authenticated])

  useEffect(() => {
    if (loading || !authenticated) return
    loadWorkspace(true)
  }, [authenticated, loading, loadWorkspace])

  const renderedDocument = useMemo(() => {
    if (!document) return null
    const html = document.content?.html
    if (html && html.trim()) {
      return <article className="workspace-reading tiptap-editor" dangerouslySetInnerHTML={{ __html: html }} />
    }
    return <article className="workspace-reading">{renderMarkdown(document.markdown || '')}</article>
  }, [document])

  if (!loading && !authenticated) {
    return (
      <WorkspaceGate
        title="Medicamentos CIF"
        description="Protege el informe, las fuentes, las figuras y el flujo de dictado antes de abrir el workspace."
      />
    )
  }

  if (pageLoading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-6">
        <div className="border border-line bg-paper p-6 w-full max-w-lg">
          <h1 className="text-xl font-bold mb-2">Workspace Medicamentos CIF</h1>
          <p className="text-sm text-muted">
            Preparando lectura, borrador por voz y contexto del informe.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="border-b border-line bg-paper sticky top-0 z-20">
        <div className="px-5 py-4 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Workspace CIF</div>
            <h1 className="text-2xl font-bold truncate">Informe de medicamentos</h1>
            <p className="text-sm text-muted mt-1">
              Lectura a la izquierda, voz al centro y contexto auditado a la derecha para reescribir sin salir del flujo.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <button className="btn btn-sm" onClick={() => loadWorkspace(false)} disabled={refreshing}>
              <RefreshCw size={14} className={`mr-1 ${refreshing ? 'animate-spin' : ''}`} />
              Recargar
            </button>
            <Link href="/medicamentos" className="btn btn-sm btn-primary">
              Workspace CIF
            </Link>
            <Link href={`/editor/${documentSlug}`} className="btn btn-sm">
              <FileText size={14} className="mr-1" />
              Abrir editor de reescritura
            </Link>
          </div>
        </div>
      </header>

      <main className="cif-shell min-h-[calc(100vh-81px)]">
        <section className="cif-column min-w-0 border-r border-line">
          <div className="px-6 py-4 border-b border-line bg-paper">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-wide text-muted">Lectura renderizada</div>
                <h2 className="text-lg font-semibold mt-1">{document?.title || 'CIF Medicamentos Workspace'}</h2>
                <p className="text-xs text-muted mt-1">
                  Usa esta columna como referencia visual mientras limpias cada bloque de reescritura.
                </p>
              </div>
              <div className="text-xs text-muted">
                {document?.status ? `Estado: ${document.status}` : 'Vista de lectura'}
              </div>
            </div>
            {error && <div className="text-sm text-c-red mt-3">{error}</div>}
          </div>

          <div className="p-6">
            <div className="workspace-paper">
              {renderedDocument || (
                <div className="text-sm text-muted">No se pudo renderizar el documento.</div>
              )}
            </div>
          </div>
        </section>

        <aside className="cif-column min-h-0 border-r border-line">
          <div className="px-4 py-4 border-b border-line bg-paper">
            <div className="text-xs uppercase tracking-wide text-muted">Centro de voz</div>
            <h2 className="text-lg font-semibold mt-1">Borrador por dictado</h2>
            <p className="text-xs text-muted mt-1">
              Dicta, reorganiza el bloque y pasa al editor solo cuando el texto esté listo para reemplazar o insertar.
            </p>
          </div>
          <div className="min-h-0 flex-1 bg-paper">
            <DictationPanel documentSlug={documentSlug} showCanvas />
          </div>
        </aside>

        <aside className="cif-column min-h-0 bg-paper">
          <WorkspaceContextPanel />
        </aside>
      </main>
    </div>
  )
}
