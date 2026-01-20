'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
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
  MessageCircle,
} from 'lucide-react'
import { Editor } from '@tiptap/core'
import { TiptapEditor } from '@/components/editor/TiptapEditor'
import { PresentationView } from '@/components/editor/PresentationView'
import { Slide } from '@/components/editor/SlideNavigator'
import { ClaimsPanel } from '@/components/panels/ClaimsPanel'
import { BibliographyPanel } from '@/components/panels/BibliographyPanel'
import { AIAssistantPanel } from '@/components/panels/AIAssistantPanel'
import { OutlinePanel } from '@/components/panels/OutlinePanel'
import { CommentsPanel } from '@/components/panels/CommentsPanel'
import { VersionsPanel } from '@/components/panels/VersionsPanel'
import { useDocument } from '@/hooks/useDocument'
import { Claim, Comment, Document, claimsApi, documentsApi, exportsApi, ExportFormat } from '@/lib/api'
import { googleApi } from '@/lib/api'

type PanelType = 'claims' | 'bib' | 'ai' | 'comments' | 'versions' | 'outline'

/**
 * Default TipTap document structure for empty/new documents.
 * Provides a valid ProseMirror schema that initializes the editor correctly.
 */
const DEFAULT_TIPTAP_CONTENT = {
  json: {
    type: 'doc',
    content: [{ type: 'paragraph' }],
  },
}

/**
 * Extract valid editor content from a document, handling null/undefined/empty cases.
 * Returns a valid content structure that TipTap can initialize with.
 */
function getEditorContent(document: Document | null): { html?: string; json?: Record<string, unknown> } | string {
  // No document loaded yet
  if (!document) {
    return DEFAULT_TIPTAP_CONTENT
  }

  // Check if content object has actual data
  const content = document.content
  if (content && typeof content === 'object') {
    // Has JSON content (preferred format)
    if (content.json && typeof content.json === 'object' && Object.keys(content.json).length > 0) {
      return content
    }
    // Has HTML content
    if (content.html && typeof content.html === 'string' && content.html.trim()) {
      return content
    }
  }

  // Fallback to markdown if available
  if (document.markdown && document.markdown.trim()) {
    return document.markdown
  }

  // Return default empty document structure
  return DEFAULT_TIPTAP_CONTENT
}

export default function EditorPage() {
  const params = useParams()
  const slug = params.slug as string
  const isNew = slug === 'new'

  const editorRef = useRef<Editor | null>(null)
  const [activePanel, setActivePanel] = useState<PanelType>('claims')
  const [selectedText, setSelectedText] = useState('')
  const [title, setTitle] = useState('')
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [exportMenuOpen, setExportMenuOpen] = useState(false)
  const [googleMenuOpen, setGoogleMenuOpen] = useState(false)
  const [wordCount, setWordCount] = useState(0)
  const [docStyle, setDocStyle] = useState('modern')
  const [docFormat, setDocFormat] = useState('a4')
  const [docFont, setDocFont] = useState('sans')
  const [docSize, setDocSize] = useState('md')
  const [docLeading, setDocLeading] = useState('normal')
  const [docMargin, setDocMargin] = useState('normal')
  const [layoutMenuOpen, setLayoutMenuOpen] = useState(false)
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null)
  const [editorReady, setEditorReady] = useState(false)
  const [commentAnchors, setCommentAnchors] = useState<
    { id: string; resolved: boolean; count: number }[]
  >([])
  const [claims, setClaims] = useState<Claim[]>([])
  const appliedClaimIds = useRef<Set<string>>(new Set())

  const {
    document,
    loading,
    error,
    saving,
    lastSaved,
    hasUnsavedChanges,
    updateDocument,
    saveDocument,
    reloadDocument,
  } = useDocument(slug, {
    autoSaveDelay: 3000,
  })

  // Initialize title from document
  useState(() => {
    if (document?.title) {
      setTitle(document.title)
    }
  })

  useEffect(() => {
    if (!document?.front_matter) return
    const style = (document.front_matter as Record<string, any>)?.style
    const format = (document.front_matter as Record<string, any>)?.format
    const layout = (document.front_matter as Record<string, any>)?.layout || {}
    if (style) setDocStyle(style)
    if (format) setDocFormat(format)
    if (layout.font) setDocFont(layout.font)
    if (layout.size) setDocSize(layout.size)
    if (layout.leading) setDocLeading(layout.leading)
    if (layout.margin) setDocMargin(layout.margin)
  }, [document?.front_matter])

  useEffect(() => {
    setActiveClaimId(null)
    setEditorReady(false)
  }, [slug])

  useEffect(() => {
    appliedClaimIds.current = new Set()
  }, [slug, document?.updated_at])

  const handleContentChange = useCallback(
    (payload: { html: string; json: Record<string, unknown> }) => {
      updateDocument({ content: { html: payload.html, json: payload.json } })
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
    setEditorReady(true)

    setWordCount(editor.storage.characterCount?.words?.() || 0)

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

    editor.on('update', () => {
      setWordCount(editor.storage.characterCount?.words?.() || 0)
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

  const handleClaimClick = useCallback((
    claimId: string,
    claimText?: string,
    startOffset?: number | null,
    endOffset?: number | null
  ) => {
    const editor = editorRef.current
    if (!editor) return

    setActivePanel('claims')
    setActiveClaimId(claimId)

    let found: { from: number; to: number } | null = null
    editor.state.doc.descendants((node, pos) => {
      if (!node.isText) return
      const mark = node.marks.find(
        (m) => m.type.name === 'claim' && m.attrs.claimId === claimId
      )
      if (mark) {
        const length = node.text?.length || 1
        found = { from: pos, to: pos + length }
        return false
      }
      return
    })

    if (!found && startOffset != null) {
      let from: number | null = null
      let to: number | null = null
      let cursor = 0

      editor.state.doc.descendants((node, pos) => {
        if (!node.isText || !node.text) return
        const nextCursor = cursor + node.text.length
        if (from === null && startOffset >= cursor && startOffset <= nextCursor) {
          from = pos + (startOffset - cursor)
        }
        if (to === null && endOffset != null && endOffset >= cursor && endOffset <= nextCursor) {
          to = pos + (endOffset - cursor)
        }
        cursor = nextCursor
        if (from !== null && (to !== null || endOffset == null)) {
          return false
        }
        return
      })

      if (from !== null) {
        found = { from, to: to ?? from + 1 }
      }
    }

    if (!found && claimText) {
      const needle = claimText.trim()
      if (needle) {
        type Segment = { start: number; end: number; pos: number; text: string }
        const segments: Segment[] = []
        let cursor = 0

        editor.state.doc.descendants((node, pos) => {
          if (!node.isText || !node.text) return
          segments.push({
            start: cursor,
            end: cursor + node.text.length,
            pos,
            text: node.text,
          })
          cursor += node.text.length
        })

        const haystack = segments.map((s) => s.text).join('')
        const idx = haystack.indexOf(needle)
        if (idx !== -1) {
          const endIdx = idx + needle.length
          let from: number | null = null
          let to: number | null = null

          for (const seg of segments) {
            if (from === null && idx >= seg.start && idx < seg.end) {
              from = seg.pos + (idx - seg.start)
            }
            if (to === null && endIdx >= seg.start && endIdx <= seg.end) {
              to = seg.pos + (endIdx - seg.start)
              break
            }
          }

          if (from !== null && to !== null) {
            found = { from, to }
          }
        }
      }
    }

    if (found) {
      editor.chain().focus().setTextSelection(found).scrollIntoView().run()
    }
  }, [])

  const loadClaims = useCallback(async () => {
    if (!slug || slug === 'new') return
    try {
      const data = await claimsApi.listByDocument(slug)
      setClaims(data)
    } catch (err) {
      console.error('Failed to load claims', err)
    }
  }, [slug])

  useEffect(() => {
    loadClaims()
  }, [loadClaims])

  useEffect(() => {
    if (activePanel === 'claims') {
      loadClaims()
    }
  }, [activePanel, loadClaims])

  useEffect(() => {
    if (!lastSaved) return
    loadClaims()
  }, [lastSaved, loadClaims])

  const applyClaimMarks = useCallback(() => {
    const editor = editorRef.current
    if (!editor || !claims.length) return

    const existingClaimIds = new Set<string>()
    editor.state.doc.descendants((node) => {
      if (!node.isText) return
      node.marks.forEach((mark) => {
        if (mark.type.name === 'claim' && mark.attrs?.claimId) {
          existingClaimIds.add(mark.attrs.claimId as string)
        }
      })
    })

    const tr = editor.state.tr
    let cursor = 0
    editor.state.doc.descendants((node, pos) => {
      if (!node.isText || !node.text) return
      const nodeText = node.text
      const nodeStart = cursor
      const nodeEnd = cursor + nodeText.length

      claims.forEach((claim) => {
        if (existingClaimIds.has(claim.claim_id)) return
        if (appliedClaimIds.current.has(claim.claim_id)) return
        if (claim.start_offset == null) return

        const start = claim.start_offset
        const end =
          claim.end_offset ?? claim.start_offset + (claim.claim_text?.length || 1)

        if (start >= nodeEnd || end <= nodeStart) return
        const from = pos + Math.max(0, start - nodeStart)
        const to = pos + Math.min(nodeText.length, end - nodeStart)
        if (to <= from) return

        tr.addMark(
          from,
          to,
          editor.schema.marks.claim.create({
            claimId: claim.claim_id,
            claimType: claim.claim_type,
            status: claim.status,
          })
        )
      })

      cursor = nodeEnd
    })

    if (tr.docChanged) {
      editor.view.dispatch(tr)
      claims.forEach((claim) => appliedClaimIds.current.add(claim.claim_id))
    }
  }, [claims])

  useEffect(() => {
    if (!editorReady) return
    applyClaimMarks()
  }, [applyClaimMarks, editorReady])

  const handleCommentSelect = useCallback((anchorId: string) => {
    const editor = editorRef.current
    if (!editor) return

    let found: { from: number; to: number } | null = null
    editor.state.doc.descendants((node, pos) => {
      if (!node.isText) return
      const mark = node.marks.find(
        (m) => m.type.name === 'comment' && m.attrs.commentId === anchorId
      )
      if (mark) {
        const length = node.text?.length || 1
        found = { from: pos, to: pos + length }
        return false
      }
      return
    })

    if (found) {
      editor.chain().focus().setTextSelection(found).run()
    }
  }, [])

  const handleStyleChange = useCallback(
    (style: string) => {
      setDocStyle(style)
      updateDocument({
        front_matter: {
          ...(document?.front_matter || {}),
          style,
        },
      })
    },
    [document?.front_matter, updateDocument]
  )

  const handleFormatChange = useCallback(
    (format: string) => {
      setDocFormat(format)
      updateDocument({
        front_matter: {
          ...(document?.front_matter || {}),
          format,
        },
      })
    },
    [document?.front_matter, updateDocument]
  )

  const updateLayout = useCallback(
    (updates: { font?: string; size?: string; leading?: string; margin?: string }) => {
      const currentLayout = ((document?.front_matter as Record<string, any>)?.layout || {}) as Record<
        string,
        string
      >
      const nextLayout = { ...currentLayout, ...updates }
      updateDocument({
        front_matter: {
          ...(document?.front_matter || {}),
          layout: nextLayout,
        },
      })
    },
    [document?.front_matter, updateDocument]
  )

  const handleFontChange = useCallback(
    (font: string) => {
      setDocFont(font)
      updateLayout({ font })
    },
    [updateLayout]
  )

  const handleSizeChange = useCallback(
    (size: string) => {
      setDocSize(size)
      updateLayout({ size })
    },
    [updateLayout]
  )

  const handleLeadingChange = useCallback(
    (leading: string) => {
      setDocLeading(leading)
      updateLayout({ leading })
    },
    [updateLayout]
  )

  const handleMarginChange = useCallback(
    (margin: string) => {
      setDocMargin(margin)
      updateLayout({ margin })
    },
    [updateLayout]
  )

  const [trackChanges, setTrackChanges] = useState(false)

  const applyCommentStates = useCallback((list: Comment[]) => {
    const editor = editorRef.current
    if (!editor) return

    const resolvedByAnchor = new Map<string, boolean>()
    list.forEach((comment) => {
      const anchorId = comment.anchor_id || comment.id
      const existing = resolvedByAnchor.get(anchorId)
      const resolved = existing === undefined ? comment.resolved : existing && comment.resolved
      resolvedByAnchor.set(anchorId, resolved)
    })

    const { state, view } = editor
    const { tr } = state

    state.doc.descendants((node, pos) => {
      if (!node.isText) return
      node.marks.forEach((mark) => {
        if (mark.type.name !== 'comment') return
        const anchorId = mark.attrs.commentId
        const resolved = resolvedByAnchor.get(anchorId) ?? false
        if (mark.attrs.resolved === resolved) return
        const newMark = mark.type.create({ ...mark.attrs, resolved })
        tr.removeMark(pos, pos + node.nodeSize, mark.type)
        tr.addMark(pos, pos + node.nodeSize, newMark)
      })
    })

    if (tr.docChanged) {
      view.dispatch(tr)
    }
  }, [])

  const handleCommentsChange = useCallback(
    (list: Comment[]) => {
      applyCommentStates(list)
      const anchorMap = new Map<string, { id: string; resolved: boolean; count: number }>()
      list.forEach((comment) => {
        const anchorId = comment.anchor_id || comment.id
        const existing = anchorMap.get(anchorId)
        const resolved = existing ? existing.resolved && comment.resolved : comment.resolved
        const count = (existing?.count || 0) + 1
        anchorMap.set(anchorId, { id: anchorId, resolved, count })
      })
      setCommentAnchors(Array.from(anchorMap.values()))
    },
    [applyCommentStates]
  )

  const handleExport = useCallback(async (format: ExportFormat) => {
    if (!slug || slug === 'new') return
    try {
      setExporting(true)
      setExportError(null)
      const job = await documentsApi.export(slug, format)
      let status = job.status
      let attempts = 0
      while (status !== 'done' && status !== 'failed' && attempts < 30) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
        const updated = await exportsApi.get(job.id)
        status = updated.status
        if (status === 'done') {
          window.location.href = exportsApi.downloadUrl(job.id)
          return
        }
        if (status === 'failed') {
          setExportError(updated.error || 'Export failed')
          return
        }
        attempts += 1
      }
      if (status !== 'done') {
        setExportError('Export is taking too long. Try again in a moment.')
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(false)
    }
  }, [slug])

  const handleGoogleExport = useCallback(async (target: 'docs' | 'slides') => {
    if (!slug || slug === 'new') return
    try {
      if (target === 'docs') {
        const result = await googleApi.exportDoc(slug)
        if (result.url) window.open(result.url, '_blank')
      } else if (target === 'slides') {
        const result = await googleApi.exportSlides(slug)
        if (result.url) window.open(result.url, '_blank')
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Google export failed')
    }
  }, [slug])

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
            <select
              className="input text-xs w-32"
              value={docStyle}
              onChange={(e) => handleStyleChange(e.target.value)}
              title="Document style"
            >
              <option value="modern">Style: Modern</option>
              <option value="classic">Style: Classic</option>
              <option value="compact">Style: Compact</option>
            </select>
            <select
              className="input text-xs w-32"
              value={docFormat}
              onChange={(e) => handleFormatChange(e.target.value)}
              title="Document format"
            >
              <option value="a4">Format: A4</option>
              <option value="letter">Format: Letter</option>
              <option value="wide">Format: Wide</option>
            </select>
            <div className="relative">
              <button
                className="btn btn-sm"
                onClick={() => setLayoutMenuOpen((v) => !v)}
              >
                Layout
              </button>
              {layoutMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-paper border border-line shadow-sm z-10 p-2 space-y-2">
                  <div className="text-xs text-muted">Font</div>
                  <select
                    className="input text-xs w-full"
                    value={docFont}
                    onChange={(e) => handleFontChange(e.target.value)}
                  >
                    <option value="sans">Sans</option>
                    <option value="serif">Serif</option>
                    <option value="mono">Mono</option>
                  </select>
                  <div className="text-xs text-muted">Size</div>
                  <select
                    className="input text-xs w-full"
                    value={docSize}
                    onChange={(e) => handleSizeChange(e.target.value)}
                  >
                    <option value="sm">Small</option>
                    <option value="md">Medium</option>
                    <option value="lg">Large</option>
                  </select>
                  <div className="text-xs text-muted">Line height</div>
                  <select
                    className="input text-xs w-full"
                    value={docLeading}
                    onChange={(e) => handleLeadingChange(e.target.value)}
                  >
                    <option value="tight">Tight</option>
                    <option value="normal">Normal</option>
                    <option value="relaxed">Relaxed</option>
                  </select>
                  <div className="text-xs text-muted">Margins</div>
                  <select
                    className="input text-xs w-full"
                    value={docMargin}
                    onChange={(e) => handleMarginChange(e.target.value)}
                  >
                    <option value="narrow">Narrow</option>
                    <option value="normal">Normal</option>
                    <option value="wide">Wide</option>
                  </select>
                </div>
              )}
            </div>
            <button
              className={`btn btn-sm ${trackChanges ? 'btn-primary' : ''}`}
              onClick={() => setTrackChanges((v) => !v)}
              title="Track changes"
            >
              {trackChanges ? 'Tracking' : 'Track changes'}
            </button>
            <button
              onClick={() => saveDocument()}
              className="btn btn-sm"
              disabled={saving || !hasUnsavedChanges}
            >
              <Save size={14} className="mr-1" />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <div className="relative">
              <button
                className="btn btn-sm btn-primary"
                onClick={() => setExportMenuOpen((v) => !v)}
                disabled={exporting}
              >
                <Download size={14} className="mr-1" />
                {exporting ? 'Exporting...' : 'Export'}
              </button>
              {exportMenuOpen && (
                <div className="absolute right-0 mt-2 w-44 bg-paper border border-line shadow-sm z-10">
                  {(['pdf', 'docx', 'pptx', 'markdown', 'html', 'latex'] as ExportFormat[]).map(
                    (format) => (
                      <button
                        key={format}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-bg"
                        onClick={() => {
                          setExportMenuOpen(false)
                          handleExport(format)
                        }}
                      >
                        Export {format.toUpperCase()}
                      </button>
                    )
                  )}
                </div>
              )}
            </div>
            <div className="relative">
              <button
                className="btn btn-sm"
                onClick={() => setGoogleMenuOpen((v) => !v)}
              >
                <MoreVertical size={14} />
              </button>
              {googleMenuOpen && (
                <div className="absolute right-0 mt-2 w-44 bg-paper border border-line shadow-sm z-10">
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-bg"
                    onClick={() => {
                      setGoogleMenuOpen(false)
                      handleGoogleExport('docs')
                    }}
                  >
                    Export to Google Docs
                  </button>
                  <button
                    className="w-full text-left px-3 py-2 text-sm hover:bg-bg"
                    onClick={() => {
                      setGoogleMenuOpen(false)
                      handleGoogleExport('slides')
                    }}
                  >
                    Export to Google Slides
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      {exportError && (
        <div className="px-4 py-2 text-xs text-c-red bg-paper border-b border-line">
          {exportError}
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {document?.doc_type === 'presentation' ? (
          /* Presentation mode */
          <PresentationView
            slidesData={
              (document?.front_matter as Record<string, unknown>)?.slides_data as {
                slides: Slide[]
                theme: {
                  primaryColor: string
                  secondaryColor: string
                  fontFamily: string
                  logoUrl?: string
                }
              } || {
                slides: [],
                theme: {
                  primaryColor: '#1a365d',
                  secondaryColor: '#c53030',
                  fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
                },
              }
            }
            documentTitle={document?.title}
            googleSlidesUrl={
              (document?.front_matter as Record<string, unknown>)?.google_slides_url as string | undefined
            }
            onSlidesChange={(slides) => {
              const currentFrontMatter = (document?.front_matter || {}) as Record<string, unknown>
              const currentSlidesData = (currentFrontMatter.slides_data || {}) as Record<string, unknown>
              updateDocument({
                front_matter: {
                  ...currentFrontMatter,
                  slides_data: {
                    ...currentSlidesData,
                    slides,
                  },
                },
              })
            }}
          />
        ) : (
          /* Regular document mode */
          <>
            {/* Left sidebar - Outline */}
            <aside className="w-56 border-r border-line bg-paper flex-shrink-0 overflow-hidden">
              <OutlinePanel editor={editorRef.current} />
            </aside>

            {/* Editor */}
            <main className="flex-1 overflow-hidden">
              <TiptapEditor
                content={getEditorContent(document)}
                onChange={handleContentChange}
                onReady={handleEditorReady}
                onClaimClick={handleClaimClick}
                activeClaimId={activeClaimId}
                placeholder="Start writing your document..."
                documentSlug={slug}
                trackChangesEnabled={trackChanges}
                docStyle={docStyle}
                docFormat={docFormat}
                docFont={docFont}
                docSize={docSize}
                docLeading={docLeading}
                docMargin={docMargin}
                commentAnchors={commentAnchors}
              />
            </main>
          </>
        )}

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
            <PanelTab
              active={activePanel === 'comments'}
              onClick={() => setActivePanel('comments')}
              icon={<MessageCircle size={14} />}
              label="Comments"
            />
            <PanelTab
              active={activePanel === 'versions'}
              onClick={() => setActivePanel('versions')}
              icon={<Clock size={14} />}
              label="Versions"
            />
          </div>

          {/* Panel content */}
          <div className="flex-1 overflow-hidden">
            {activePanel === 'claims' && (
              <ClaimsPanel
                documentSlug={slug}
                onClaimClick={handleClaimClick}
                activeClaimId={activeClaimId}
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
            {activePanel === 'comments' && (
              <CommentsPanel
                documentSlug={slug}
                sourceProvider={document?.source_provider}
                onSelectComment={handleCommentSelect}
                onCommentsChange={handleCommentsChange}
              />
            )}
            {activePanel === 'versions' && (
              <VersionsPanel
                documentSlug={slug}
                onRestore={reloadDocument}
                currentMarkdown={document?.markdown || ''}
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
