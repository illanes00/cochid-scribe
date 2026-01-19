'use client'

import { useEditor, EditorContent, BubbleMenu, FloatingMenu, Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Highlight from '@tiptap/extension-highlight'
import TiptapLink from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import CharacterCount from '@tiptap/extension-character-count'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Image from '@tiptap/extension-image'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import TextAlign from '@tiptap/extension-text-align'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Code,
  List,
  ListOrdered,
  Quote,
  Heading1,
  Heading2,
  Heading3,
  Undo,
  Redo,
  Link as LinkIcon,
  Highlighter,
  Tag,
  BookOpen,
  Image as ImageIcon,
  Upload,
  Table as TableIcon,
  ListChecks,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Subscript as SubscriptIcon,
  Superscript as SuperscriptIcon,
  MessageSquare,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Trash2,
  Check,
  X,
} from 'lucide-react'
import { Claim } from './extensions/claim'
import { Citation } from './extensions/citation'
import { SlashCommands } from './extensions/slash-commands'
import { Comment } from './extensions/comment'
import { ChangeMark, TrackChanges } from './extensions/track-changes'
import { assetsApi, commentsApi } from '@/lib/api'

interface TiptapEditorContent {
  html?: string
  json?: Record<string, unknown>
}

interface TiptapEditorProps {
  content?: string | TiptapEditorContent
  onChange?: (content: { html: string; json: Record<string, unknown> }) => void
  onReady?: (editor: Editor) => void
  onClaimClick?: (
    claimId: string,
    claimText?: string,
    startOffset?: number | null,
    endOffset?: number | null
  ) => void
  activeClaimId?: string | null
  placeholder?: string
  documentSlug?: string
  trackChangesEnabled?: boolean
  docStyle?: string
  docFormat?: string
  docFont?: string
  docSize?: string
  docLeading?: string
  docMargin?: string
  commentAnchors?: { id: string; resolved: boolean; count: number }[]
}

export function TiptapEditor({
  content = '',
  onChange,
  onReady,
  onClaimClick,
  activeClaimId = null,
  placeholder = 'Start writing...',
  documentSlug,
  trackChangesEnabled = false,
  docStyle = 'modern',
  docFormat = 'a4',
  docFont = 'sans',
  docSize = 'md',
  docLeading = 'normal',
  docMargin = 'normal',
  commentAnchors = [],
}: TiptapEditorProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const editorWrapperRef = useRef<HTMLDivElement | null>(null)
  const [anchorPositions, setAnchorPositions] = useState<
    { id: string; top: number; resolved: boolean; count: number }[]
  >([])

  const EnhancedImage = Image.extend({
    addAttributes() {
      return {
        ...this.parent?.(),
        width: {
          default: null,
          parseHTML: (element) => element.getAttribute('data-width'),
          renderHTML: (attributes) => {
            if (!attributes.width) return {}
            return { 'data-width': attributes.width }
          },
        },
        align: {
          default: null,
          parseHTML: (element) => element.getAttribute('data-align'),
          renderHTML: (attributes) => {
            if (!attributes.align) return {}
            return { 'data-align': attributes.align }
          },
        },
      }
    },
  })
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      Highlight.configure({
        multicolor: true,
      }),
      TiptapLink.configure({
        openOnClick: false,
      }),
      Underline,
      CharacterCount,
      Claim,
      Citation,
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      EnhancedImage.configure({ inline: false, allowBase64: true }),
      TaskList,
      TaskItem.configure({ nested: true }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Subscript,
      Superscript,
      SlashCommands,
      Comment,
      ChangeMark,
      TrackChanges,
    ],
    content: typeof content === 'string' ? content : content?.json || content?.html || '',
    onUpdate: ({ editor }) => {
      onChange?.({ html: editor.getHTML(), json: editor.getJSON() })
    },
    editorProps: {
      attributes: {
        class: 'tiptap-editor',
      },
      handleClick: (_view, _pos, event) => {
        if (!onClaimClick) return false
        if (!(event.target instanceof HTMLElement)) return false
        const target = event.target.closest('[data-claim-id]') as HTMLElement | null
        const claimId = target?.dataset?.claimId
        if (claimId) {
          try {
            const pos = editor?.view.posAtDOM(target, 0)
            if (pos) {
              const textLen = target.textContent?.length || 1
              editor?.chain().focus().setTextSelection({ from: pos, to: pos + textLen }).run()
              editor?.chain().scrollIntoView().run()
            }
          } catch (err) {
            console.warn('Failed to scroll to claim', err)
          }
          const claimText = target?.textContent?.trim() || undefined
          onClaimClick(claimId, claimText)
        }
        return false
      },
    },
  })

  // Notify parent when editor is ready
  useEffect(() => {
    if (editor && onReady) {
      onReady(editor)
    }
  }, [editor, onReady])

  useEffect(() => {
    if (!editor) return
    editor.commands.setTrackChanges?.(trackChangesEnabled)
  }, [editor, trackChangesEnabled])

  // When a claim is selected from the sidebar, scroll to it in the editor
  useEffect(() => {
    if (!editor || !activeClaimId) return

    let target: { from: number; to: number } | null = null
    editor.state.doc.descendants((node, pos) => {
      if (!node.isText) return
      const mark = node.marks.find(
        (m) => m.type.name === 'claim' && m.attrs.claimId === activeClaimId
      )
      if (mark) {
        const length = node.text?.length || 1
        target = { from: pos, to: pos + length }
        return false
      }
      return
    })

    if (target) {
      editor.chain().focus().setTextSelection(target).scrollIntoView().run()
    }
  }, [activeClaimId, editor])

  // Update content when it changes from outside (only if different)
  useEffect(() => {
    if (!editor || !content) return
    if (typeof content === 'string') {
      if (editor.getHTML() !== content) {
        editor.commands.setContent(content)
      }
      return
    }
    if (content.json) {
      const current = JSON.stringify(editor.getJSON())
      const next = JSON.stringify(content.json)
      if (current !== next) {
        editor.commands.setContent(content.json)
      }
      return
    }
    if (content.html && editor.getHTML() !== content.html) {
      editor.commands.setContent(content.html)
    }
  }, [content, editor])

  useEffect(() => {
    if (!editor) return
    const root = editor.view.dom
    const claimNodes = root.querySelectorAll<HTMLElement>('[data-claim-id]')
    claimNodes.forEach((node) => {
      const isActive = activeClaimId && node.dataset.claimId === activeClaimId
      node.classList.toggle('active', Boolean(isActive))
    })
  }, [activeClaimId, editor])

  const setLink = useCallback(() => {
    if (!editor) return
    const previousUrl = editor.getAttributes('link').href
    const url = window.prompt('URL', previousUrl)

    if (url === null) return
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }

    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }, [editor])

  const markAsClaim = useCallback(() => {
    if (!editor) return
    const { from, to } = editor.state.selection
    if (from === to) return

    const claimId = `C-${Date.now().toString(36)}`
    editor.chain().focus().setClaim({ claimId }).run()
  }, [editor])

  const insertCitation = useCallback(() => {
    if (!editor) return
    const bibKey = window.prompt('Enter citation key (e.g., Bathelt_2004)')
    if (!bibKey) return

    editor.chain().focus().insertCitation({ bibKey }).run()
  }, [editor])

  const insertTable = useCallback(() => {
    if (!editor) return
    editor
      .chain()
      .focus()
      .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
      .run()
  }, [editor])

  const insertImage = useCallback(() => {
    if (!editor) return
    const url = window.prompt('Image URL')
    if (!url) return
    editor.chain().focus().setImage({ src: url }).run()
  }, [editor])

  const insertImageUpload = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleImageUpload = useCallback(
    async (file: File) => {
      if (!editor) return
      const result = await assetsApi.upload(file)
      const src = result.url.startsWith('http')
        ? result.url
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${result.url}`
      editor.chain().focus().setImage({ src }).run()
    },
    [editor]
  )

  const toggleTaskList = useCallback(() => {
    if (!editor) return
    editor.chain().focus().toggleTaskList().run()
  }, [editor])

  const markDeletion = useCallback(() => {
    if (!editor) return
    const { from, to } = editor.state.selection
    if (from === to) return
    editor.chain().focus().setMark('change', { kind: 'delete' }).run()
  }, [editor])

  const handleChangeAction = useCallback(
    (action: 'accept' | 'reject') => {
      if (!editor) return
      const kind = editor.getAttributes('change')?.kind || 'insert'
      const chain = editor.chain().focus().extendMarkRange('change')
      if (kind === 'insert') {
        if (action === 'accept') {
          chain.unsetMark('change').run()
        } else {
          chain.deleteSelection().run()
        }
        return
      }
      if (action === 'accept') {
        chain.deleteSelection().run()
      } else {
        chain.unsetMark('change').run()
      }
    },
    [editor]
  )

  const updateAnchorPositions = useCallback(() => {
    if (!editor || !editorWrapperRef.current) return
    const wrapper = editorWrapperRef.current
    const wrapperRect = wrapper.getBoundingClientRect()
    const positions: { id: string; top: number; resolved: boolean; count: number }[] = []

    commentAnchors.forEach((anchor) => {
      let foundPos: number | null = null
      editor.state.doc.descendants((node, pos) => {
        if (!node.isText) return
        const match = node.marks.find(
          (mark) => mark.type.name === 'comment' && mark.attrs.commentId === anchor.id
        )
        if (match) {
          foundPos = pos
          return false
        }
        return
      })

      if (foundPos !== null) {
        const coords = editor.view.coordsAtPos(foundPos)
        const top = coords.top - wrapperRect.top + wrapper.scrollTop
        positions.push({ id: anchor.id, top, resolved: anchor.resolved, count: anchor.count })
      }
    })

    setAnchorPositions(positions)
  }, [commentAnchors, editor])

  useEffect(() => {
    if (!editor) return
    updateAnchorPositions()
  }, [editor, updateAnchorPositions, commentAnchors])

  useEffect(() => {
    const wrapper = editorWrapperRef.current
    if (!wrapper) return
    const handleScroll = () => updateAnchorPositions()
    wrapper.addEventListener('scroll', handleScroll)
    return () => wrapper.removeEventListener('scroll', handleScroll)
  }, [updateAnchorPositions])

  const jumpToAnchor = useCallback(
    (anchorId: string) => {
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
    },
    [editor]
  )

  const addInlineComment = useCallback(async () => {
    if (!editor || !documentSlug) return
    const { from, to } = editor.state.selection
    if (from === to) return

    const quote = editor.state.doc.textBetween(from, to, ' ')
    const content = window.prompt('Comment')
    if (!content) return

    try {
      const comment = await commentsApi.create(documentSlug, { content, quote })
      const anchorId = comment.anchor_id || comment.id
      editor.chain().focus().setComment({ commentId: anchorId }).run()
    } catch (err) {
      console.error('Failed to add comment', err)
    }
  }, [editor, documentSlug])

  const removeInlineComment = useCallback(() => {
    if (!editor) return
    editor.chain().focus().unsetComment().run()
  }, [editor])

  const setImageSize = useCallback(
    (size: 'small' | 'medium' | 'large' | 'full') => {
      if (!editor) return
      editor.chain().focus().updateAttributes('image', { width: size }).run()
    },
    [editor]
  )

  const setImageAlign = useCallback(
    (align: 'left' | 'center' | 'right') => {
      if (!editor) return
      editor.chain().focus().updateAttributes('image', { align }).run()
    },
    [editor]
  )

  const setImageAlt = useCallback(() => {
    if (!editor) return
    const previous = editor.getAttributes('image').alt || ''
    const next = window.prompt('Alt text', previous)
    if (next === null) return
    editor.chain().focus().updateAttributes('image', { alt: next }).run()
  }, [editor])

  if (!editor) {
    return null
  }

  return (
    <div
      className={`editor-shell flex flex-col h-full doc-style-${docStyle} doc-format-${docFormat} doc-font-${docFont} doc-size-${docSize} doc-leading-${docLeading} doc-margin-${docMargin}`}
    >
      {/* Toolbar */}
      <div className="flex items-center gap-1 p-3 border-b border-line bg-paper flex-wrap">
        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
            title="Undo"
          >
            <Undo size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
            title="Redo"
          >
            <Redo size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            active={editor.isActive('bold')}
            title="Bold"
          >
            <Bold size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            active={editor.isActive('italic')}
            title="Italic"
          >
            <Italic size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            active={editor.isActive('underline')}
            title="Underline"
          >
            <UnderlineIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleStrike().run()}
            active={editor.isActive('strike')}
            title="Strikethrough"
          >
            <Strikethrough size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleCode().run()}
            active={editor.isActive('code')}
            title="Code"
          >
            <Code size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            active={editor.isActive('highlight')}
            title="Highlight"
          >
            <Highlighter size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 1 }).run()
            }
            active={editor.isActive('heading', { level: 1 })}
            title="Heading 1"
          >
            <Heading1 size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 2 }).run()
            }
            active={editor.isActive('heading', { level: 2 })}
            title="Heading 2"
          >
            <Heading2 size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 3 }).run()
            }
            active={editor.isActive('heading', { level: 3 })}
            title="Heading 3"
          >
            <Heading3 size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            active={editor.isActive('bulletList')}
            title="Bullet List"
          >
            <List size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            active={editor.isActive('orderedList')}
            title="Ordered List"
          >
            <ListOrdered size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={toggleTaskList}
            active={editor.isActive('taskList')}
            title="Task List"
          >
            <ListChecks size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            active={editor.isActive('blockquote')}
            title="Quote"
          >
            <Quote size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={setLink}
            active={editor.isActive('link')}
            title="Link"
          >
            <LinkIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertImage}
            title="Insert Image"
          >
            <ImageIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertImageUpload}
            title="Upload Image"
          >
            <Upload size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertTable}
            title="Insert Table"
          >
            <TableIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={markAsClaim}
            active={editor.isActive('claim')}
            title="Mark as Claim"
          >
            <Tag size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertCitation}
            title="Insert Citation"
          >
            <BookOpen size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().setTextAlign('left').run()}
            active={editor.isActive({ textAlign: 'left' })}
            title="Align Left"
          >
            <AlignLeft size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().setTextAlign('center').run()}
            active={editor.isActive({ textAlign: 'center' })}
            title="Align Center"
          >
            <AlignCenter size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().setTextAlign('right').run()}
            active={editor.isActive({ textAlign: 'right' })}
            title="Align Right"
          >
            <AlignRight size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleSubscript().run()}
            active={editor.isActive('subscript')}
            title="Subscript"
          >
            <SubscriptIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleSuperscript().run()}
            active={editor.isActive('superscript')}
            title="Superscript"
          >
            <SuperscriptIcon size={16} />
          </ToolbarButton>
        </ToolbarGroup>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-auto relative" ref={editorWrapperRef}>
        <EditorContent editor={editor} className="h-full" />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) {
              handleImageUpload(file)
            }
            e.currentTarget.value = ''
          }}
        />
        {anchorPositions.length > 0 && (
          <div className="comment-gutter">
            {anchorPositions.map((anchor) => (
              <button
                key={anchor.id}
                className={`comment-marker ${anchor.resolved ? 'is-resolved' : ''}`}
                style={{ top: anchor.top }}
                onClick={() => jumpToAnchor(anchor.id)}
                title={`Comment thread (${anchor.count})`}
              >
                {anchor.count}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bubble Menu */}
      {editor && (
        <BubbleMenu
          editor={editor}
          tippyOptions={{ duration: 100 }}
          className="flex items-center gap-1 p-1 bg-paper border border-line"
        >
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            active={editor.isActive('bold')}
            size="sm"
          >
            <Bold size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            active={editor.isActive('italic')}
            size="sm"
          >
            <Italic size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={setLink}
            active={editor.isActive('link')}
            size="sm"
          >
            <LinkIcon size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            active={editor.isActive('highlight')}
            size="sm"
          >
            <Highlighter size={14} />
          </ToolbarButton>
          <Divider />
          <ToolbarButton
            onClick={markAsClaim}
            active={editor.isActive('claim')}
            size="sm"
            title="Mark as Claim"
          >
            <Tag size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={editor.isActive('comment') ? removeInlineComment : addInlineComment}
            active={editor.isActive('comment')}
            size="sm"
            title="Add Comment"
          >
            <MessageSquare size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={markDeletion}
            active={editor.isActive('change') && editor.getAttributes('change')?.kind === 'delete'}
            size="sm"
            title="Mark Deletion"
          >
            <Strikethrough size={14} />
          </ToolbarButton>
          {editor.isActive('change') && (
            <>
              <ToolbarButton
                onClick={() => handleChangeAction('accept')}
                size="sm"
                title="Accept Change"
              >
                <Check size={14} />
              </ToolbarButton>
              <ToolbarButton
                onClick={() => handleChangeAction('reject')}
                size="sm"
                title="Reject Change"
              >
                <X size={14} />
              </ToolbarButton>
            </>
          )}
        </BubbleMenu>
      )}

      {/* Floating Menu */}
      {editor && (
        <FloatingMenu
          editor={editor}
          tippyOptions={{ duration: 100 }}
          shouldShow={({ state }) => {
            const { $from } = state.selection
            return $from.parent.type.name === 'paragraph' && $from.parent.textContent.length === 0
          }}
          className="flex items-center gap-1 p-1 bg-paper border border-line shadow-sm"
        >
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            active={editor.isActive('heading', { level: 2 })}
            size="sm"
            title="Heading 2"
          >
            <Heading2 size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            active={editor.isActive('bulletList')}
            size="sm"
            title="Bullet List"
          >
            <List size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertImage}
            size="sm"
            title="Insert Image"
          >
            <ImageIcon size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertTable}
            size="sm"
            title="Insert Table"
          >
            <TableIcon size={14} />
          </ToolbarButton>
        </FloatingMenu>
      )}

      {/* Table Menu */}
      {editor && (
        <BubbleMenu
          editor={editor}
          tippyOptions={{ duration: 100 }}
          shouldShow={() => editor.isActive('table')}
          className="flex items-center gap-1 p-1 bg-paper border border-line"
        >
          <ToolbarButton
            onClick={() => editor.chain().focus().addRowBefore().run()}
            size="sm"
            title="Add Row Before"
          >
            <ArrowUp size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().addRowAfter().run()}
            size="sm"
            title="Add Row After"
          >
            <ArrowDown size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().addColumnBefore().run()}
            size="sm"
            title="Add Column Before"
          >
            <ArrowLeft size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().addColumnAfter().run()}
            size="sm"
            title="Add Column After"
          >
            <ArrowRight size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHeaderRow().run()}
            size="sm"
            title="Toggle Header Row"
          >
            <TableIcon size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().deleteTable().run()}
            size="sm"
            title="Delete Table"
          >
            <Trash2 size={14} />
          </ToolbarButton>
        </BubbleMenu>
      )}

      {/* Image Menu */}
      {editor && (
        <BubbleMenu
          editor={editor}
          tippyOptions={{ duration: 100 }}
          shouldShow={() => editor.isActive('image')}
          className="flex items-center gap-1 p-1 bg-paper border border-line"
        >
          <ToolbarButton onClick={setImageAlt} size="sm" title="Edit Alt Text">
            <ImageIcon size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageAlign('left')} size="sm" title="Align Left">
            <AlignLeft size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageAlign('center')} size="sm" title="Align Center">
            <AlignCenter size={14} />
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageAlign('right')} size="sm" title="Align Right">
            <AlignRight size={14} />
          </ToolbarButton>
          <Divider />
          <ToolbarButton onClick={() => setImageSize('small')} size="sm" title="Small">
            S
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageSize('medium')} size="sm" title="Medium">
            M
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageSize('large')} size="sm" title="Large">
            L
          </ToolbarButton>
          <ToolbarButton onClick={() => setImageSize('full')} size="sm" title="Full">
            XL
          </ToolbarButton>
        </BubbleMenu>
      )}
    </div>
  )
}

function ToolbarGroup({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center gap-0.5">{children}</div>
}

function ToolbarButton({
  children,
  onClick,
  active,
  disabled,
  title,
  size = 'md',
}: {
  children: React.ReactNode
  onClick?: () => void
  active?: boolean
  disabled?: boolean
  title?: string
  size?: 'sm' | 'md'
}) {
  const sizeClasses = size === 'sm' ? 'p-1' : 'p-2'

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        ${sizeClasses}
        border border-transparent
        ${active ? 'bg-bg border-line text-c-blue' : 'text-ink hover:bg-bg'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {children}
    </button>
  )
}

function Divider() {
  return <div className="w-px h-6 bg-line mx-1" />
}
