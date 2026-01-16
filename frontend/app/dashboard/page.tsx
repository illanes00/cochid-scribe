'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Plus,
  FileText,
  Clock,
  MoreVertical,
  Search,
  Filter,
  Trash2,
  RefreshCw,
} from 'lucide-react'
import { Document, documentsApi } from '@/lib/api'
import { templates } from '@/lib/templates'

export default function Dashboard() {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [importing, setImporting] = useState(false)
  const [templateMenuOpen, setTemplateMenuOpen] = useState(false)
  const perPage = 20

  useEffect(() => {
    loadDocuments()
  }, [page])

  async function loadDocuments() {
    try {
      setLoading(true)
      setError(null)
      const result = await documentsApi.list(page, perPage)
      setDocuments(result.documents)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(slug: string, e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('Delete this document? This cannot be undone.')) return

    try {
      await documentsApi.delete(slug)
      setDocuments((prev) => prev.filter((d) => d.slug !== slug))
      setTotal((prev) => prev - 1)
    } catch (err) {
      alert('Failed to delete document')
    }
  }

  async function handleCreate() {
    try {
      const doc = await documentsApi.create({
        title: 'Untitled Document',
        doc_type: 'paper',
      })
      router.push(`/editor/${doc.slug}`)
    } catch (err) {
      alert('Failed to create document')
    }
  }

  async function handleCreateFromTemplate(templateId: string) {
    const template = templates.find((t) => t.id === templateId)
    if (!template) return
    try {
      const doc = await documentsApi.create({
        title: template.title,
        doc_type: template.doc_type,
        markdown: template.markdown,
      })
      router.push(`/editor/${doc.slug}`)
    } catch (err) {
      alert('Failed to create document from template')
    }
  }

  async function handleImport(file: File) {
    try {
      setImporting(true)
      const doc = await documentsApi.import(file)
      router.push(`/editor/${doc.slug}`)
    } catch (err) {
      alert('Failed to import document')
    } finally {
      setImporting(false)
    }
  }

  const filteredDocs = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/knowledge" className="text-sm text-muted hover:text-ink">
              Knowledge Base
            </Link>
            <Link href="/data" className="text-sm text-muted hover:text-ink">
              Data
            </Link>
            <Link href="/integrations" className="text-sm text-muted hover:text-ink">
              Integrations
            </Link>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="container py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold mb-1">Documents</h1>
            <p className="text-sm text-muted">
              {total} document{total !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadDocuments}
              className="btn"
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <label className="btn" title="Import">
              <input
                type="file"
                accept=".md,.markdown,.docx,.pptx"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    handleImport(file)
                    e.currentTarget.value = ''
                  }
                }}
              />
              {importing ? 'Importing...' : 'Import'}
            </label>
            <div className="relative">
              <button
                onClick={() => setTemplateMenuOpen((v) => !v)}
                className="btn"
              >
                <FileText size={16} className="mr-2" />
                New from template
              </button>
              {templateMenuOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-paper border border-line shadow-sm z-10">
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-bg"
                      onClick={() => {
                        setTemplateMenuOpen(false)
                        handleCreateFromTemplate(template.id)
                      }}
                    >
                      <div className="font-medium text-ink">{template.title}</div>
                      <div className="text-xs text-muted">{template.description}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={handleCreate} className="btn btn-primary">
              <Plus size={16} className="mr-2" />
              New Document
            </button>
          </div>
        </div>

        {/* Search & Filter */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              type="text"
              placeholder="Search documents..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button className="btn">
            <Filter size={16} className="mr-2" />
            Filter
          </button>
        </div>

        {/* Error state */}
        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadDocuments} className="text-sm underline">
              Retry
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && documents.length === 0 && (
          <div className="card text-center py-12">
            <RefreshCw size={24} className="mx-auto mb-4 text-muted animate-spin" />
            <p className="text-muted">Loading documents...</p>
          </div>
        )}

        {/* Document list */}
        {!loading && (
          <div className="space-y-3">
            {filteredDocs.map((doc) => (
              <DocumentCard
                key={doc.slug}
                document={doc}
                onDelete={(e) => handleDelete(doc.slug, e)}
              />
            ))}

            {filteredDocs.length === 0 && (
              <div className="card text-center py-12">
                <FileText size={48} className="mx-auto mb-4 text-muted" />
                <p className="text-muted">
                  {searchQuery ? 'No documents match your search' : 'No documents yet'}
                </p>
                <button onClick={handleCreate} className="btn btn-primary mt-4">
                  Create your first document
                </button>
              </div>
            )}
          </div>
        )}

        {/* Pagination */}
        {total > perPage && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn btn-sm"
            >
              Previous
            </button>
            <span className="text-sm text-muted">
              Page {page} of {Math.ceil(total / perPage)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / perPage)}
              className="btn btn-sm"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

function DocumentCard({
  document,
  onDelete,
}: {
  document: Document
  onDelete: (e: React.MouseEvent) => void
}) {
  const typeLabels: Record<string, string> = {
    paper: 'Paper',
    thesis: 'Thesis',
    policy: 'Policy Brief',
  }

  const updatedDate = new Date(document.updated_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  const claimCount = document.claim_count || 0
  const verifiedCount = document.verified_count || 0
  const verifiedPercent = claimCount > 0
    ? Math.round((verifiedCount / claimCount) * 100)
    : 0

  return (
    <Link href={`/editor/${document.slug}`}>
      <div className="card flex items-center gap-4 hover:border-line-strong transition-colors">
        <FileText size={20} className="text-muted flex-shrink-0" />

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold truncate">{document.title}</h3>
          <div className="flex items-center gap-3 mt-1 text-sm text-muted">
            <span className="pill pill-info">
              {typeLabels[document.doc_type] || document.doc_type}
            </span>
            <span className="capitalize">{document.status}</span>
            <span className="flex items-center gap-1">
              <Clock size={12} />
              {updatedDate}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6 flex-shrink-0">
          {/* Claims status */}
          {claimCount > 0 && (
            <div className="text-right">
              <div className="text-sm font-medium">
                {verifiedCount}/{claimCount} claims
              </div>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-20 h-1 bg-line">
                  <div
                    className="h-full bg-c-green"
                    style={{ width: `${verifiedPercent}%` }}
                  />
                </div>
                <span className="text-xs text-muted">{verifiedPercent}%</span>
              </div>
            </div>
          )}

          <button
            className="p-2 hover:bg-bg text-muted hover:text-c-red"
            onClick={onDelete}
            title="Delete document"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </Link>
  )
}
