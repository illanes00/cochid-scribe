'use client'

import { useEffect, useMemo } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { Slide } from './SlideNavigator'

function sanitizeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function formatInline(text: string): string {
  const sanitized = sanitizeHtml(text)
  return sanitized
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/_([^_]+)_/g, '<em>$1</em>')
}

function markdownToHtml(markdown: string): string {
  if (!markdown) return ''
  const lines = markdown.split('\n')
  const htmlParts: string[] = []
  let listType: 'ul' | 'ol' | null = null

  const closeList = () => {
    if (listType) {
      htmlParts.push(`</${listType}>`)
      listType = null
    }
  }

  lines.forEach((line) => {
    const trimmed = line.trim()
    if (!trimmed) {
      closeList()
      return
    }

    const bulletMatch = /^[-*]\s+(.+)$/.exec(trimmed)
    const numberedMatch = /^\d+\.\s+(.+)$/.exec(trimmed)

    if (bulletMatch) {
      if (listType !== 'ul') {
        closeList()
        listType = 'ul'
        htmlParts.push('<ul>')
      }
      htmlParts.push(`<li>${formatInline(bulletMatch[1])}</li>`)
      return
    }

    if (numberedMatch) {
      if (listType !== 'ol') {
        closeList()
        listType = 'ol'
        htmlParts.push('<ol>')
      }
      htmlParts.push(`<li>${formatInline(numberedMatch[1])}</li>`)
      return
    }

    closeList()

    if (trimmed.startsWith('### ')) {
      htmlParts.push(`<h3>${formatInline(trimmed.slice(4))}</h3>`)
    } else if (trimmed.startsWith('## ')) {
      htmlParts.push(`<h2>${formatInline(trimmed.slice(3))}</h2>`)
    } else if (trimmed.startsWith('# ')) {
      htmlParts.push(`<h1>${formatInline(trimmed.slice(2))}</h1>`)
    } else if (trimmed.startsWith('> ')) {
      htmlParts.push(`<blockquote>${formatInline(trimmed.slice(2))}</blockquote>`)
    } else {
      htmlParts.push(`<p>${formatInline(trimmed)}</p>`)
    }
  })

  closeList()

  return htmlParts.join('')
}

function isHtmlContent(text: string): boolean {
  return /<\/?[a-z][\s\S]*>/i.test(text)
}

interface SlideEditorProps {
  slide: Slide
  theme: {
    primaryColor: string
    secondaryColor: string
    fontFamily: string
    logoUrl?: string
  }
  isEditing?: boolean
  onSlideChange?: (slide: Slide) => void
}

export function SlideEditor({ slide, theme, isEditing = false, onSlideChange }: SlideEditorProps) {
  const initialContent = useMemo(() => {
    const content = slide.content || ''
    return isHtmlContent(content) ? content : markdownToHtml(content)
  }, [slide.content])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Image.configure({ inline: false, allowBase64: true }),
      Placeholder.configure({ placeholder: 'Write your slide content…' }),
    ],
    content: initialContent,
    editable: isEditing,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      onSlideChange?.({ ...slide, content: html })
    },
  })

  // Keep editor content in sync when switching slides
  useEffect(() => {
    if (!editor) return
    const nextContent = isHtmlContent(slide.content || '')
      ? slide.content || ''
      : markdownToHtml(slide.content || '')
    if (editor.getHTML() !== nextContent) {
      editor.commands.setContent(nextContent)
    }
    editor.setEditable(isEditing)
  }, [editor, slide.id, slide.content, isEditing])

  const layoutClass = useMemo(() => {
    switch (slide.layout) {
      case 'title':
        return 'slide-title-layout'
      case 'two-column':
        return 'slide-two-column-layout'
      case 'image-full':
        return 'slide-image-layout'
      case 'blank':
        return 'slide-blank-layout'
      default:
        return 'slide-content-layout'
    }
  }, [slide.layout])

  return (
    <div
      className={`slide-editor h-full w-full bg-paper border border-line p-6 ${layoutClass}`}
      style={{ fontFamily: theme.fontFamily }}
    >
      {/* Title input */}
      <input
        type="text"
        value={slide.title}
        disabled={!isEditing}
        onChange={(e) => onSlideChange?.({ ...slide, title: e.target.value })}
        placeholder="Slide title"
        className="w-full text-2xl font-bold mb-4 bg-transparent border-b border-line outline-none disabled:text-ink/60"
        style={{ color: theme.primaryColor }}
      />

      {/* Content editor */}
      <div className="flex-1 min-h-[280px] bg-bg/60 border border-line p-4">
        {editor && <EditorContent editor={editor} className="prose max-w-none" />}
      </div>

      {/* Speaker notes */}
      <div className="mt-4">
        <label className="text-xs text-muted block mb-1">Speaker notes</label>
        <textarea
          value={slide.notes || ''}
          disabled={!isEditing}
          onChange={(e) => onSlideChange?.({ ...slide, notes: e.target.value })}
          className="w-full h-20 border border-line p-2 text-sm bg-transparent outline-none disabled:text-ink/60"
          placeholder="Notes for this slide"
        />
      </div>
    </div>
  )
}

export default SlideEditor
