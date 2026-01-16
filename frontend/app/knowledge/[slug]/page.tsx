'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  ChevronLeft,
  Save,
  Tag,
  Link2,
  Trash2,
  Clock,
} from 'lucide-react'
import { Editor } from '@tiptap/core'
import { TiptapEditor } from '@/components/editor/TiptapEditor'
import { Note, notesApi, NoteUpdate } from '@/lib/api'

export default function NotePage() {
  const params = useParams()
  const router = useRouter()
  const slug = params.slug as string

  const editorRef = useRef<Editor | null>(null)
  const [note, setNote] = useState<Note | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [title, setTitle] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

  const pendingUpdates = useRef<NoteUpdate>({})
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null)

  // Load note
  useEffect(() => {
    async function loadNote() {
      try {
        setLoading(true)
        const data = await notesApi.get(slug)
        setNote(data)
        setTitle(data.title)
        setTags(data.tags || [])
        setLastSaved(new Date(data.updated_at))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load note')
      } finally {
        setLoading(false)
      }
    }
    loadNote()
  }, [slug])

  // Save note
  const saveNote = useCallback(async () => {
    if (!note || Object.keys(pendingUpdates.current).length === 0) return

    try {
      setSaving(true)
      const updates = { ...pendingUpdates.current }
      pendingUpdates.current = {}

      const updated = await notesApi.update(slug, updates)
      setNote(updated)
      setLastSaved(new Date())
      setHasUnsavedChanges(false)
    } catch (err) {
      console.error('Save failed:', err)
      setHasUnsavedChanges(true)
    } finally {
      setSaving(false)
    }
  }, [note, slug])

  // Update note (queues for auto-save)
  const updateNote = useCallback(
    (updates: NoteUpdate) => {
      pendingUpdates.current = {
        ...pendingUpdates.current,
        ...updates,
      }
      setHasUnsavedChanges(true)

      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }

      autoSaveTimer.current = setTimeout(() => {
        saveNote()
      }, 2000)
    },
    [saveNote]
  )

  const handleContentChange = useCallback(
    (payload: { html: string; json: Record<string, unknown> }) => {
      updateNote({ content: { html: payload.html, json: payload.json } })
    },
    [updateNote]
  )

  const handleTitleChange = useCallback(
    (newTitle: string) => {
      setTitle(newTitle)
      updateNote({ title: newTitle })
    },
    [updateNote]
  )

  const handleEditorReady = useCallback((editor: Editor) => {
    editorRef.current = editor
  }, [])

  const handleAddTag = useCallback(() => {
    if (!newTag.trim() || tags.includes(newTag.trim())) return
    const updated = [...tags, newTag.trim()]
    setTags(updated)
    setNewTag('')
    updateNote({ tags: updated })
  }, [newTag, tags, updateNote])

  const handleRemoveTag = useCallback(
    (tag: string) => {
      const updated = tags.filter((t) => t !== tag)
      setTags(updated)
      updateNote({ tags: updated })
    },
    [tags, updateNote]
  )

  const handleDelete = async () => {
    if (!confirm('Delete this note? This cannot be undone.')) return

    try {
      await notesApi.delete(slug)
      router.push('/knowledge')
    } catch (err) {
      alert('Failed to delete note')
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }
      if (Object.keys(pendingUpdates.current).length > 0) {
        saveNote()
      }
    }
  }, [saveNote])

  // Warn before unload
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-muted">Loading note...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-center">
          <p className="text-c-red mb-4">{error}</p>
          <Link href="/knowledge" className="text-c-blue hover:underline">
            Back to Knowledge Base
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper flex-shrink-0">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link href="/knowledge" className="text-muted hover:text-ink">
              <ChevronLeft size={20} />
            </Link>
            <input
              type="text"
              value={title}
              onChange={(e) => handleTitleChange(e.target.value)}
              placeholder="Untitled Note"
              className="text-lg font-semibold bg-transparent border-none outline-none w-96"
            />
            <span className="pill pill-info text-xs capitalize">
              {note?.note_type || 'idea'}
            </span>
            {hasUnsavedChanges && (
              <span className="text-xs text-c-amber">Unsaved changes</span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {lastSaved && (
              <span className="text-xs text-muted flex items-center gap-1">
                <Clock size={12} />
                Saved {lastSaved.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => saveNote()}
              className="btn btn-sm"
              disabled={saving || !hasUnsavedChanges}
            >
              <Save size={14} className="mr-1" />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button onClick={handleDelete} className="btn btn-sm text-c-red">
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor */}
        <main className="flex-1 overflow-hidden">
          <TiptapEditor
            content={note?.content || note?.markdown || ''}
            onChange={handleContentChange}
            onReady={handleEditorReady}
            placeholder="Start writing your note..."
          />
        </main>

        {/* Sidebar */}
        <aside className="w-64 border-l border-line bg-paper flex-shrink-0 p-4 overflow-y-auto">
          {/* Tags */}
          <div className="mb-6">
            <h3 className="font-medium text-sm mb-2 flex items-center gap-2">
              <Tag size={14} />
              Tags
            </h3>
            <div className="flex flex-wrap gap-1 mb-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-1 bg-bg text-ink flex items-center gap-1 group"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="text-muted hover:text-c-red opacity-0 group-hover:opacity-100"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-1">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                placeholder="Add tag..."
                className="input text-xs flex-1"
              />
              <button onClick={handleAddTag} className="btn btn-sm">
                +
              </button>
            </div>
          </div>

          {/* Backlinks */}
          {note && note.backlink_count > 0 && (
            <div>
              <h3 className="font-medium text-sm mb-2 flex items-center gap-2">
                <Link2 size={14} />
                Backlinks ({note.backlink_count})
              </h3>
              <p className="text-xs text-muted">
                {note.backlink_count} note{note.backlink_count !== 1 ? 's' : ''} link to this note
              </p>
            </div>
          )}

          {/* Note Type */}
          <div className="mt-6">
            <h3 className="font-medium text-sm mb-2">Type</h3>
            <select
              value={note?.note_type || 'idea'}
              onChange={(e) => updateNote({ note_type: e.target.value as Note['note_type'] })}
              className="input text-sm w-full"
            >
              <option value="idea">Idea</option>
              <option value="summary">Summary</option>
              <option value="quote">Quote</option>
              <option value="concept">Concept</option>
            </select>
          </div>
        </aside>
      </div>
    </div>
  )
}
