'use client'

import { useState, useRef, useCallback } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ChevronLeft,
  Save,
  Download,
  MoreVertical,
  Clock,
  BookOpen,
  CheckCircle,
  Sparkles,
  List,
} from 'lucide-react'
import { Editor } from '@tiptap/core'
import { TiptapEditor } from '@/components/editor/TiptapEditor'
import { ClaimsPanel } from '@/components/panels/ClaimsPanel'
import { BibliographyPanel } from '@/components/panels/BibliographyPanel'
import { AIAssistantPanel } from '@/components/panels/AIAssistantPanel'
import { OutlinePanel } from '@/components/panels/OutlinePanel'
import { useDocument } from '@/hooks/useDocument'

type PanelType = 'claims' | 'bib' | 'ai' | 'outline'

export default function EditorPage() {
  const params = useParams()
  const slug = params.slug as string
  const isNew = slug === 'new'

  const editorRef = useRef<Editor | null>(null)
  const [activePanel, setActivePanel] = useState<PanelType>('claims')
  const [selectedText, setSelectedText] = useState('')
  const [title, setTitle] = useState('')

  const {
    document,
    loading,
    error,
    saving,
    lastSaved,
    hasUnsavedChanges,
    updateDocument,
    saveDocument,
  } = useDocument(slug, {
    autoSaveDelay: 3000,
  })

  // Initialize title from document
  useState(() => {
    if (document?.title) {
      setTitle(document.title)
    }
  })

  const handleContentChange = useCallback(
    (html: string) => {
      updateDocument({ content: { html } })
    },
    [updateDocument]
  )

  const handleTitleChange = useCallback(
    (newTitle: string) => {
      setTitle(newTitle)
      updateDocument({ title: newTitle })
    },
    [updateDocument]
  )

  const handleEditorReady = useCallback((editor: Editor) => {
    editorRef.current = editor

    // Track selection changes for AI panel
    editor.on('selectionUpdate', () => {
      const { from, to } = editor.state.selection
      if (from !== to) {
        const text = editor.state.doc.textBetween(from, to, ' ')
        setSelectedText(text)
      } else {
        setSelectedText('')
      }
    })
  }, [])

  const handleCite = useCallback(
    (bibKey: string) => {
      if (editorRef.current) {
        editorRef.current
          .chain()
          .focus()
          .insertCitation({ bibKey })
          .run()
      }
    },
    []
  )

  const handleApplyRewrite = useCallback(
    (text: string) => {
      if (editorRef.current) {
        editorRef.current
          .chain()
          .focus()
          .deleteSelection()
          .insertContent(text)
          .run()
      }
    },
    []
  )

  const handleClaimClick = useCallback(
    (claimId: string) => {
      // Scroll to claim in editor (would need claim position tracking)
      console.log('Navigate to claim:', claimId)
    },
    []
  )

  // Calculate word count from editor
  const wordCount = editorRef.current?.storage?.characterCount?.words?.() || 0

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-muted">Loading document...</div>
      </div>
    )
  }

  if (error && !isNew) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-center">
          <p className="text-c-red mb-4">{error}</p>
          <Link href="/dashboard" className="text-c-blue hover:underline">
            Back to Dashboard
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
            <Link href="/dashboard" className="text-muted hover:text-ink">
              <ChevronLeft size={20} />
            </Link>
            <input
              type="text"
              value={title || document?.title || ''}
              onChange={(e) => handleTitleChange(e.target.value)}
              placeholder="Untitled Document"
              className="text-lg font-semibold bg-transparent border-none outline-none w-96"
            />
            <span className="pill pill-info text-xs">
              {document?.doc_type || 'paper'}
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
              onClick={() => saveDocument()}
              className="btn btn-sm"
              disabled={saving || !hasUnsavedChanges}
            >
              <Save size={14} className="mr-1" />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button className="btn btn-sm btn-primary">
              <Download size={14} className="mr-1" />
              Export
            </button>
            <button className="btn btn-sm">
              <MoreVertical size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Outline */}
        <aside className="w-56 border-r border-line bg-paper flex-shrink-0 overflow-hidden">
          <OutlinePanel editor={editorRef.current} />
        </aside>

        {/* Editor */}
        <main className="flex-1 overflow-hidden">
          <TiptapEditor
            content={
              typeof document?.content === 'object' && 'html' in document.content
                ? String(document.content.html)
                : ''
            }
            onChange={handleContentChange}
            onReady={handleEditorReady}
            placeholder="Start writing your document..."
          />
        </main>

        {/* Right sidebar */}
        <aside className="w-80 border-l border-line bg-paper flex-shrink-0 flex flex-col">
          {/* Panel tabs */}
          <div className="flex border-b border-line">
            <PanelTab
              active={activePanel === 'claims'}
              onClick={() => setActivePanel('claims')}
              icon={<CheckCircle size={14} />}
              label="Claims"
            />
            <PanelTab
              active={activePanel === 'bib'}
              onClick={() => setActivePanel('bib')}
              icon={<BookOpen size={14} />}
              label="Bib"
            />
            <PanelTab
              active={activePanel === 'ai'}
              onClick={() => setActivePanel('ai')}
              icon={<Sparkles size={14} />}
              label="AI"
            />
          </div>

          {/* Panel content */}
          <div className="flex-1 overflow-hidden">
            {activePanel === 'claims' && (
              <ClaimsPanel
                documentSlug={slug}
                onClaimClick={handleClaimClick}
              />
            )}
            {activePanel === 'bib' && (
              <BibliographyPanel onCite={handleCite} />
            )}
            {activePanel === 'ai' && (
              <AIAssistantPanel
                selectedText={selectedText}
                onApplyRewrite={handleApplyRewrite}
              />
            )}
          </div>
        </aside>
      </div>

      {/* Status bar */}
      <footer className="border-t border-line bg-paper px-4 py-2 flex items-center justify-between text-xs text-muted">
        <div className="flex items-center gap-4">
          <span>{wordCount} words</span>
          <span className="flex items-center gap-1">
            <span className="dot dot-ok" />
            {document?.verified_count || 0}/{document?.claim_count || 0} claims verified
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span>Version {document?.version || '1.0.0'}</span>
          <span className="capitalize">{document?.status || 'draft'}</span>
        </div>
      </footer>
    </div>
  )
}

function PanelTab({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium
        border-b-2
        ${active ? 'border-c-blue text-c-blue' : 'border-transparent text-muted hover:text-ink'}
      `}
    >
      {icon}
      {label}
    </button>
  )
}
