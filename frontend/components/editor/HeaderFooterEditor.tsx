'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import TextAlign from '@tiptap/extension-text-align'
import { useCallback, useEffect, useRef } from 'react'
import { Image as ImageIcon, AlignLeft, AlignCenter, AlignRight, Hash } from 'lucide-react'

export interface HeaderFooterContent {
  json?: Record<string, unknown>
  html?: string
}

interface HeaderFooterVariables {
  pageNumber: number
  totalPages: number
  documentTitle: string
  date?: string
}

interface HeaderFooterEditorProps {
  type: 'header' | 'footer'
  content?: HeaderFooterContent
  onChange: (content: HeaderFooterContent) => void
  variables: HeaderFooterVariables
  logoUrl?: string
  onLogoChange?: (url: string | null) => void
}

/**
 * Mini TipTap editor for headers and footers.
 *
 * Features:
 * - Simplified toolbar (text, bold, italic, image, alignment)
 * - Page variable insertion ({pageNumber}, {totalPages}, {documentTitle})
 * - Logo image support
 * - Separate from main document content
 */
export function HeaderFooterEditor({
  type,
  content,
  onChange,
  variables,
}: HeaderFooterEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        codeBlock: false,
        blockquote: false,
        bulletList: false,
        orderedList: false,
        horizontalRule: false,
      }),
      Image.configure({
        inline: true,
        allowBase64: true,
      }),
      TextAlign.configure({
        types: ['paragraph'],
      }),
    ],
    content: content?.json || content?.html || '',
    editorProps: {
      attributes: {
        class: `header-footer-editor ${type}`,
      },
    },
    onUpdate: ({ editor }) => {
      onChange({
        html: editor.getHTML(),
        json: editor.getJSON(),
      })
    },
  })

  // Update content from outside
  useEffect(() => {
    if (!editor || !content) return
    const currentJson = JSON.stringify(editor.getJSON())
    const newJson = content.json ? JSON.stringify(content.json) : null

    if (newJson && currentJson !== newJson) {
      editor.commands.setContent(content.json!)
    }
  }, [content, editor])

  const insertImage = useCallback(() => {
    const url = window.prompt('Image URL (or leave empty to upload)')
    if (url) {
      editor?.chain().focus().setImage({ src: url }).run()
    } else {
      fileInputRef.current?.click()
    }
  }, [editor])

  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !editor) return

    // Convert to base64 for simplicity
    const reader = new FileReader()
    reader.onload = () => {
      const src = reader.result as string
      editor.chain().focus().setImage({ src }).run()
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }, [editor])

  const insertVariable = useCallback((variable: string) => {
    if (!editor) return
    editor.chain().focus().insertContent(`{${variable}}`).run()
  }, [editor])

  if (!editor) return null

  // Replace variables in displayed content
  const renderPreview = () => {
    let html = editor.getHTML()
    html = html.replace(/\{pageNumber\}/g, String(variables.pageNumber))
    html = html.replace(/\{totalPages\}/g, String(variables.totalPages))
    html = html.replace(/\{documentTitle\}/g, variables.documentTitle)
    html = html.replace(/\{date\}/g, variables.date || new Date().toLocaleDateString())
    return html
  }

  return (
    <div className={`header-footer-wrapper ${type}`}>
      {/* Mini toolbar */}
      <div className="header-footer-toolbar">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`hf-btn ${editor.isActive('bold') ? 'active' : ''}`}
          title="Bold"
        >
          B
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`hf-btn ${editor.isActive('italic') ? 'active' : ''}`}
          title="Italic"
        >
          I
        </button>
        <div className="hf-divider" />
        <button
          onClick={() => editor.chain().focus().setTextAlign('left').run()}
          className={`hf-btn ${editor.isActive({ textAlign: 'left' }) ? 'active' : ''}`}
          title="Align Left"
        >
          <AlignLeft size={12} />
        </button>
        <button
          onClick={() => editor.chain().focus().setTextAlign('center').run()}
          className={`hf-btn ${editor.isActive({ textAlign: 'center' }) ? 'active' : ''}`}
          title="Align Center"
        >
          <AlignCenter size={12} />
        </button>
        <button
          onClick={() => editor.chain().focus().setTextAlign('right').run()}
          className={`hf-btn ${editor.isActive({ textAlign: 'right' }) ? 'active' : ''}`}
          title="Align Right"
        >
          <AlignRight size={12} />
        </button>
        <div className="hf-divider" />
        <button onClick={insertImage} className="hf-btn" title="Insert Image">
          <ImageIcon size={12} />
        </button>
        <div className="hf-divider" />
        {/* Page variables dropdown */}
        <div className="hf-dropdown">
          <button className="hf-btn" title="Insert Variable">
            <Hash size={12} />
          </button>
          <div className="hf-dropdown-menu">
            <button onClick={() => insertVariable('pageNumber')}>
              Page Number
            </button>
            <button onClick={() => insertVariable('totalPages')}>
              Total Pages
            </button>
            <button onClick={() => insertVariable('documentTitle')}>
              Document Title
            </button>
            <button onClick={() => insertVariable('date')}>
              Date
            </button>
          </div>
        </div>
      </div>

      {/* Editor content */}
      <EditorContent editor={editor} />

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleImageUpload}
      />
    </div>
  )
}

/**
 * Default header content with logo placeholder and page numbers
 */
export const DEFAULT_HEADER_CONTENT: HeaderFooterContent = {
  json: {
    type: 'doc',
    content: [
      {
        type: 'paragraph',
        attrs: { textAlign: 'right' },
        content: [
          { type: 'text', text: 'Page {pageNumber} of {totalPages}' },
        ],
      },
    ],
  },
}

/**
 * Default footer content with document title and date
 */
export const DEFAULT_FOOTER_CONTENT: HeaderFooterContent = {
  json: {
    type: 'doc',
    content: [
      {
        type: 'paragraph',
        attrs: { textAlign: 'center' },
        content: [
          { type: 'text', text: '{documentTitle}' },
        ],
      },
    ],
  },
}

/**
 * Espacio Publico branded header
 */
export const EP_HEADER_CONTENT: HeaderFooterContent = {
  json: {
    type: 'doc',
    content: [
      {
        type: 'paragraph',
        attrs: { textAlign: 'left' },
        content: [
          {
            type: 'image',
            attrs: {
              src: '/logo-ep.png',
              alt: 'Espacio Publico',
            },
          },
        ],
      },
    ],
  },
}
