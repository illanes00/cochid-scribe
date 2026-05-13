'use client'

import { useEffect, useMemo, useState } from 'react'
import { FileCode2, FileText, FolderTree, ImageIcon, Layers3, Workflow } from 'lucide-react'

type WorkspaceFile = {
  name: string
  relative_path: string
  category: string
  kind: 'text' | 'image' | 'binary'
  size_bytes: number
  preview_url: string
}

type WorkspaceBundle = {
  workspace: {
    slug: string
    title: string
    description: string
    recommended_document_slug: string
  }
  report: {
    title: string
    relative_path: string
    preview_url: string
    sections: { level: number; title: string }[]
    excerpt: string
  }
  sources: {
    report_files: WorkspaceFile[]
    review_files: WorkspaceFile[]
    verification_files: WorkspaceFile[]
    figure_files: WorkspaceFile[]
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

async function fetchTextPreview(path: string): Promise<string> {
  const response = await fetch(
    `${API_BASE}/api/v1/workspaces/cif-medicamentos/file?path=${encodeURIComponent(path)}`
  )
  if (!response.ok) {
    throw new Error('No se pudo cargar el archivo')
  }
  return response.text()
}

export function WorkspaceContextPanel() {
  const [bundle, setBundle] = useState<WorkspaceBundle | null>(null)
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null)
  const [activeGroupKey, setActiveGroupKey] = useState<string>('report')
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(true)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/workspaces/cif-medicamentos`)
      .then((response) => {
        if (!response.ok) throw new Error('No se pudo cargar el workspace')
        return response.json()
      })
      .then((data: WorkspaceBundle) => {
        setBundle(data)
        const groupsByPriority = [
          { key: 'report', items: data.sources.report_files },
          { key: 'verification', items: data.sources.verification_files },
          { key: 'review', items: data.sources.review_files },
          { key: 'figures', items: data.sources.figure_files },
        ]
        const firstNonEmptyGroup = groupsByPriority.find((group) => group.items.length > 0)
        const firstFile = firstNonEmptyGroup?.items[0] || null
        setActiveGroupKey(firstNonEmptyGroup?.key || 'report')
        setSelectedFile(firstFile)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Error inesperado'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedFile || selectedFile.kind !== 'text') {
      setPreview('')
      return
    }
    setPreviewLoading(true)
    fetchTextPreview(selectedFile.relative_path)
      .then((text) => setPreview(text.slice(0, 16000)))
      .catch((err) => setPreview(err instanceof Error ? err.message : 'No se pudo cargar vista previa'))
      .finally(() => setPreviewLoading(false))
  }, [selectedFile])

  const groups = useMemo(() => {
    if (!bundle) return []
    return [
      { key: 'report', title: 'Texto base', description: 'Informe fuente y anexos principales', items: bundle.sources.report_files, icon: <FileText size={14} /> },
      { key: 'verification', title: 'Cálculos', description: 'Tablas y verificaciones numéricas', items: bundle.sources.verification_files, icon: <Workflow size={14} /> },
      { key: 'review', title: 'Revisión', description: 'Hallazgos y respaldo editorial', items: bundle.sources.review_files.slice(0, 24), icon: <FolderTree size={14} /> },
      { key: 'figures', title: 'Figuras', description: 'Gráficos e imágenes del informe', items: bundle.sources.figure_files, icon: <ImageIcon size={14} /> },
    ].filter((group) => group.items.length > 0)
  }, [bundle])
  const activeGroup = groups.find((group) => group.key === activeGroupKey) || groups[0] || null
  const totalSources = groups.reduce((count, group) => count + group.items.length, 0)

  useEffect(() => {
    if (!activeGroup) return
    if (selectedFile && activeGroup.items.some((item) => item.relative_path === selectedFile.relative_path)) return
    setSelectedFile(activeGroup.items[0] || null)
  }, [activeGroup, selectedFile])

  if (loading) {
    return <div className="p-4 text-sm text-muted">Cargando contexto del informe...</div>
  }

  if (error || !bundle) {
    return <div className="p-4 text-sm text-c-red">{error || 'No hay bundle disponible'}</div>
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-4 border-b border-line bg-paper space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted">Contexto CIF</div>
          <h3 className="text-base font-semibold mt-1">{bundle.workspace.title}</h3>
          <p className="text-xs text-muted mt-1">{bundle.workspace.description}</p>
        </div>

        <div className="grid grid-cols-3 gap-2 text-[11px]">
          <div className="cif-kpi">
            <div className="text-muted">Documento recomendado</div>
            <div className="font-medium truncate">{bundle.workspace.recommended_document_slug}</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Fuentes visibles</div>
            <div className="font-medium">{totalSources}</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Secciones</div>
            <div className="font-medium">{bundle.report.sections.length}</div>
          </div>
        </div>

        <div className="border border-line bg-bg p-3">
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-wide text-muted">
            <Layers3 size={13} />
            Extracto de referencia
          </div>
          <p className="text-xs text-ink mt-2 leading-5">
            {bundle.report.excerpt || 'Sin extracto disponible.'}
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-[220px,1fr] flex-1 min-h-0">
        <div className="border-r border-line overflow-y-auto bg-bg">
          <div className="p-3 border-b border-line">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">Estructura del informe</div>
            <div className="mt-2 max-h-40 overflow-y-auto border border-line bg-paper">
              {bundle.report.sections.map((section, index) => (
                <div
                  key={`${section.title}-${index}`}
                  className="px-2 py-1 text-[11px] border-b border-line last:border-b-0"
                  style={{ paddingLeft: `${12 + section.level * 10}px` }}
                >
                  {section.title}
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 space-y-2">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">Bloques de trabajo</div>
            {groups.map((group) => (
              <button
                key={group.key}
                onClick={() => setActiveGroupKey(group.key)}
                className={`w-full text-left border px-3 py-3 transition-colors ${
                  activeGroupKey === group.key ? 'border-c-blue bg-paper text-ink' : 'border-line text-muted hover:bg-paper'
                }`}
              >
                <div className="flex items-center gap-2 text-xs font-medium">
                  {group.icon}
                  {group.title}
                </div>
                <div className="text-[11px] mt-1">{group.description}</div>
                <div className="text-[11px] mt-2">{group.items.length} archivo(s)</div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col min-h-0">
          <div className="px-3 py-3 border-b border-line bg-paper">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[11px] uppercase tracking-wide text-muted">
                  {activeGroup?.title || 'Fuentes'}
                </div>
                <div className="text-xs text-muted mt-1">
                  {activeGroup?.description || 'Selecciona una fuente para abrir su vista previa.'}
                </div>
              </div>
              {selectedFile && (
                <a
                  href={selectedFile.preview_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-c-blue hover:underline whitespace-nowrap"
                >
                  Abrir raw
                </a>
              )}
            </div>
          </div>

          <div className="grid xl:grid-cols-[260px,1fr] flex-1 min-h-0">
            <div className="border-r border-line overflow-y-auto bg-bg">
              {(activeGroup?.items || []).map((file) => (
                <button
                  key={file.relative_path}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full text-left px-3 py-3 text-xs border-b border-line hover:bg-paper ${
                    selectedFile?.relative_path === file.relative_path ? 'bg-paper text-ink' : 'text-muted'
                  }`}
                >
                  <div className="font-medium truncate">{file.name}</div>
                  <div className="truncate mt-1">{file.relative_path}</div>
                  <div className="text-[11px] mt-2">{file.category}</div>
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-3 bg-paper">
              <div className="mb-3 border border-line bg-bg px-3 py-2">
                <div className="text-xs font-medium truncate">{selectedFile?.name || 'Sin archivo seleccionado'}</div>
                <div className="text-[11px] text-muted truncate mt-1">{selectedFile?.relative_path}</div>
              </div>
              {!selectedFile && <div className="text-sm text-muted">Selecciona una fuente.</div>}
              {selectedFile?.kind === 'image' && (
                <img src={selectedFile.preview_url} alt={selectedFile.name} className="max-w-full border border-line" />
              )}
              {selectedFile?.kind === 'binary' && (
                <div className="text-sm text-muted flex items-center gap-2">
                  <FileCode2 size={14} />
                  Archivo binario. Ábrelo en una pestaña nueva para inspeccionarlo.
                </div>
              )}
              {selectedFile?.kind === 'text' && (
                <pre className="text-[11px] leading-5 whitespace-pre-wrap break-words bg-bg border border-line p-3">
                  {previewLoading ? 'Cargando vista previa...' : preview}
                </pre>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
