'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Plus,
  FileText,
  Search,
  Tag,
  Link2,
  RefreshCw,
  Trash2,
  Network,
} from 'lucide-react'
import { Note, notesApi } from '@/lib/api'

export default function KnowledgeBasePage() {
  const router = useRouter()
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string>('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const perPage = 20

  useEffect(() => {
    loadNotes()
  }, [page, selectedType])

  async function loadNotes() {
    try {
      setLoading(true)
      setError(null)
      const result = await notesApi.list(page, perPage, searchQuery || undefined, selectedType || undefined)
      setNotes(result.notes)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(slug: string, e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('Delete this note? This cannot be undone.')) return

    try {
      await notesApi.delete(slug)
      setNotes((prev) => prev.filter((n) => n.slug !== slug))
      setTotal((prev) => prev - 1)
    } catch (err) {
      alert('Failed to delete note')
    }
  }

  async function handleCreate() {
    try {
      const note = await notesApi.create({
        title: 'Untitled Note',
        note_type: 'idea',
      })
      router.push(`/knowledge/${note.slug}`)
    } catch (err) {
      alert('Failed to create note')
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setPage(1)
    loadNotes()
  }

  const noteTypes = [
    { value: '', label: 'All Types' },
    { value: 'idea', label: 'Ideas' },
    { value: 'summary', label: 'Summaries' },
    { value: 'quote', label: 'Quotes' },
    { value: 'concept', label: 'Concepts' },
  ]

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-muted hover:text-ink">
              Documents
            </Link>
            <Link href="/knowledge" className="text-sm text-ink font-medium">
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
            <h1 className="text-2xl font-bold mb-1">Knowledge Base</h1>
            <p className="text-sm text-muted">
              {total} note{total !== 1 ? 's' : ''} - Ideas, summaries, and connected thoughts
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/knowledge/graph" className="btn">
              <Network size={16} className="mr-2" />
              Graph View
            </Link>
            <button
              onClick={loadNotes}
              className="btn"
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <button onClick={handleCreate} className="btn btn-primary">
              <Plus size={16} className="mr-2" />
              New Note
            </button>
          </div>
        </div>

        {/* Search & Filter */}
        <div className="flex gap-4 mb-6">
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              type="text"
              placeholder="Search notes..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value)
              setPage(1)
            }}
            className="input w-40"
          >
            {noteTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Error state */}
        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadNotes} className="text-sm underline">
              Retry
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && notes.length === 0 && (
          <div className="card text-center py-12">
            <RefreshCw size={24} className="mx-auto mb-4 text-muted animate-spin" />
            <p className="text-muted">Loading notes...</p>
          </div>
        )}

        {/* Notes grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {notes.map((note) => (
              <NoteCard
                key={note.slug}
                note={note}
                onDelete={(e) => handleDelete(note.slug, e)}
              />
            ))}

            {notes.length === 0 && (
              <div className="col-span-full card text-center py-12">
                <FileText size={48} className="mx-auto mb-4 text-muted" />
                <p className="text-muted">
                  {searchQuery ? 'No notes match your search' : 'No notes yet'}
                </p>
                <button onClick={handleCreate} className="btn btn-primary mt-4">
                  Create your first note
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

function NoteCard({
  note,
  onDelete,
}: {
  note: Note
  onDelete: (e: React.MouseEvent) => void
}) {
  const typeIcons: Record<string, string> = {
    idea: '💡',
    summary: '📋',
    quote: '💬',
    concept: '🧠',
  }

  const updatedDate = new Date(note.updated_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })

  return (
    <Link href={`/knowledge/${note.slug}`}>
      <div className="card h-full flex flex-col hover:border-line-strong transition-colors">
        <div className="flex items-start justify-between mb-2">
          <span className="text-xl">
            {typeIcons[note.note_type] || '📝'}
          </span>
          <button
            className="p-1 hover:bg-bg text-muted hover:text-c-red"
            onClick={onDelete}
            title="Delete note"
          >
            <Trash2 size={14} />
          </button>
        </div>

        <h3 className="font-semibold mb-2 line-clamp-2">{note.title}</h3>

        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {note.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-xs px-2 py-0.5 bg-bg text-muted flex items-center gap-1">
                <Tag size={10} />
                {tag}
              </span>
            ))}
            {note.tags.length > 3 && (
              <span className="text-xs text-muted">+{note.tags.length - 3}</span>
            )}
          </div>
        )}

        <div className="mt-auto flex items-center justify-between text-xs text-muted">
          <span>{updatedDate}</span>
          {note.backlink_count > 0 && (
            <span className="flex items-center gap-1">
              <Link2 size={12} />
              {note.backlink_count} link{note.backlink_count !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
