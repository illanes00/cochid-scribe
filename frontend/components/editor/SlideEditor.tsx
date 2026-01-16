'use client'

import { useMemo } from 'react'
import { Slide } from './SlideNavigator'

// Simple text sanitizer - removes potentially dangerous HTML
function sanitizeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

// Format markdown text to safe HTML
function formatText(text: string): string {
  const sanitized = sanitizeHtml(text)
  return sanitized
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/_([^_]+)_/g, '<em>$1</em>')
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
  onContentChange?: (content: string) => void
}

export function SlideEditor({
  slide,
  theme,
  isEditing = false,
  onContentChange,
}: SlideEditorProps) {
  // Parse markdown content into structured elements
  const parsedContent = useMemo(() => {
    const lines = slide.content.split('\n').filter(Boolean)
    const elements: Array<{
      type: 'heading' | 'bullet' | 'numbered' | 'paragraph' | 'quote'
      level?: number
      text: string
    }> = []

    lines.forEach((line) => {
      const trimmed = line.trim()

      if (trimmed.startsWith('# ')) {
        elements.push({ type: 'heading', level: 1, text: trimmed.slice(2) })
      } else if (trimmed.startsWith('## ')) {
        elements.push({ type: 'heading', level: 2, text: trimmed.slice(3) })
      } else if (trimmed.startsWith('### ')) {
        elements.push({ type: 'heading', level: 3, text: trimmed.slice(4) })
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        elements.push({ type: 'bullet', text: trimmed.slice(2) })
      } else if (/^\d+\. /.test(trimmed)) {
        elements.push({ type: 'numbered', text: trimmed.replace(/^\d+\. /, '') })
      } else if (trimmed.startsWith('> ')) {
        elements.push({ type: 'quote', text: trimmed.slice(2) })
      } else if (trimmed) {
        elements.push({ type: 'paragraph', text: trimmed })
      }
    })

    return elements
  }, [slide.content])

  const renderElement = (
    el: { type: string; level?: number; text: string },
    key: number
  ) => {
    const formattedText = formatText(el.text)

    switch (el.type) {
      case 'heading':
        const HeadingTag = `h${Math.min((el.level || 1) + 1, 6)}` as keyof JSX.IntrinsicElements
        return (
          <HeadingTag
            key={key}
            className={`font-bold ${
              el.level === 1 ? 'text-2xl' : el.level === 2 ? 'text-xl' : 'text-lg'
            }`}
            style={{ color: theme.primaryColor }}
          >
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </HeadingTag>
        )
      case 'bullet':
        return (
          <div key={key} className="flex items-start gap-2 text-base">
            <span
              className="mt-1.5 w-2 h-2 shrink-0"
              style={{ backgroundColor: theme.secondaryColor }}
            />
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </div>
        )
      case 'numbered':
        return (
          <div key={key} className="flex items-start gap-2 text-base">
            <span
              className="font-bold shrink-0"
              style={{ color: theme.secondaryColor }}
            >
              {key + 1}.
            </span>
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </div>
        )
      case 'quote':
        return (
          <blockquote
            key={key}
            className="border-l-4 pl-4 italic text-muted text-base"
            style={{ borderColor: theme.secondaryColor }}
          >
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </blockquote>
        )
      case 'paragraph':
      default:
        return (
          <p key={key} className="text-base">
            <span dangerouslySetInnerHTML={{ __html: formattedText }} />
          </p>
        )
    }
  }

  const renderLayout = () => {
    const titleFormatted = formatText(slide.title || '')

    switch (slide.layout) {
      case 'title':
        return (
          <div className="slide-layout-title flex flex-col items-center justify-center h-full text-center p-8">
            <h1
              className="slide-title text-4xl font-bold mb-4"
              style={{ color: theme.primaryColor }}
            >
              <span dangerouslySetInnerHTML={{ __html: titleFormatted }} />
            </h1>
            {parsedContent.filter(e => e.type === 'paragraph').slice(0, 1).map((el, i) => (
              <p key={i} className="slide-subtitle text-xl text-muted">
                <span dangerouslySetInnerHTML={{ __html: formatText(el.text) }} />
              </p>
            ))}
          </div>
        )

      case 'two-column':
        const midPoint = Math.ceil(parsedContent.length / 2)
        const leftContent = parsedContent.slice(0, midPoint)
        const rightContent = parsedContent.slice(midPoint)

        return (
          <div className="slide-layout-twocol h-full flex flex-col">
            <h2
              className="slide-heading text-2xl font-bold mb-4 px-6 pt-6"
              style={{ color: theme.primaryColor }}
            >
              <span dangerouslySetInnerHTML={{ __html: titleFormatted }} />
            </h2>
            <div className="flex-1 grid grid-cols-2 gap-6 px-6 pb-6">
              <div className="space-y-2">
                {leftContent.map((el, i) => renderElement(el, i))}
              </div>
              <div className="space-y-2">
                {rightContent.map((el, i) => renderElement(el, i))}
              </div>
            </div>
          </div>
        )

      case 'image-full':
        return (
          <div className="slide-layout-image h-full flex flex-col">
            <h2
              className="slide-heading text-2xl font-bold mb-4 px-6 pt-6"
              style={{ color: theme.primaryColor }}
            >
              <span dangerouslySetInnerHTML={{ __html: titleFormatted }} />
            </h2>
            <div className="flex-1 flex items-center justify-center bg-bg mx-6 mb-6">
              <div className="text-muted text-center">
                <div className="text-4xl mb-2">🖼</div>
                <div className="text-sm">Image placeholder</div>
              </div>
            </div>
          </div>
        )

      case 'blank':
        return (
          <div className="slide-layout-blank h-full flex items-center justify-center">
            <div className="text-muted text-sm">Empty slide</div>
          </div>
        )

      case 'content':
      default:
        return (
          <div className="slide-layout-content h-full flex flex-col px-6 py-6">
            <h2
              className="slide-heading text-2xl font-bold mb-4"
              style={{ color: theme.primaryColor }}
            >
              <span dangerouslySetInnerHTML={{ __html: titleFormatted }} />
            </h2>
            <div className="flex-1 space-y-2 overflow-y-auto">
              {parsedContent.map((el, i) => renderElement(el, i))}
            </div>
          </div>
        )
    }
  }

  return (
    <div
      className="slide-editor-container aspect-[16/9] bg-paper border border-line shadow-none overflow-hidden"
      style={{
        fontFamily: theme.fontFamily,
      }}
    >
      {/* Slide header bar */}
      <div
        className="slide-header h-2"
        style={{ backgroundColor: theme.primaryColor }}
      />

      {/* Slide content */}
      <div className="slide-body h-[calc(100%-0.5rem-2rem)]">
        {renderLayout()}
      </div>

      {/* Slide footer */}
      <div
        className="slide-footer h-8 flex items-center justify-between px-4 text-xs"
        style={{ backgroundColor: theme.primaryColor, color: 'white' }}
      >
        <span className="opacity-75">Espacio Publico</span>
        <span className="font-bold">{slide.slideNumber}</span>
      </div>
    </div>
  )
}

export default SlideEditor
