'use client'

import { useState, useEffect } from 'react'
import { Editor } from '@tiptap/core'

interface HeadingItem {
  level: number
  text: string
  pos: number
  id: string
}

interface OutlinePanelProps {
  editor: Editor | null
}

export function OutlinePanel({ editor }: OutlinePanelProps) {
  const [headings, setHeadings] = useState<HeadingItem[]>([])

  useEffect(() => {
    if (!editor) return

    function updateHeadings() {
      if (!editor) return
      const items: HeadingItem[] = []
      const { doc } = editor.state

      doc.descendants((node, pos) => {
        if (node.type.name === 'heading') {
          const id = `heading-${pos}`
          items.push({
            level: node.attrs.level,
            text: node.textContent || 'Untitled',
            pos,
            id,
          })
        }
      })

      setHeadings(items)
    }

    // Initial update
    updateHeadings()

    // Subscribe to changes
    editor.on('update', updateHeadings)

    return () => {
      editor.off('update', updateHeadings)
    }
  }, [editor])

  function scrollToHeading(pos: number) {
    if (!editor) return

    editor.chain().focus().setTextSelection(pos).run()

    // Scroll the heading into view
    const { view } = editor
    const domAtPos = view.domAtPos(pos)
    if (domAtPos.node instanceof Element) {
      domAtPos.node.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  const indentClass: Record<number, string> = {
    1: 'pl-0',
    2: 'pl-3',
    3: 'pl-6',
    4: 'pl-9',
    5: 'pl-12',
    6: 'pl-15',
  }

  const sizeClass: Record<number, string> = {
    1: 'text-sm font-medium',
    2: 'text-sm',
    3: 'text-xs',
    4: 'text-xs',
    5: 'text-xs',
    6: 'text-xs',
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <h2 className="font-medium text-ink">Outline</h2>
        <p className="text-sm text-muted mt-1">
          {headings.length} section{headings.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Outline Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {headings.length === 0 ? (
          <div className="p-4 text-center text-muted text-sm">
            No headings found.
            <br />
            <span className="text-xs">
              Use /h1, /h2, /h3 to add sections
            </span>
          </div>
        ) : (
          <nav>
            <ul className="space-y-1">
              {headings.map((heading) => (
                <li key={heading.id}>
                  <button
                    onClick={() => scrollToHeading(heading.pos)}
                    className={`
                      w-full text-left py-1.5 px-2 rounded
                      hover:bg-bg text-ink
                      ${indentClass[heading.level]}
                      ${sizeClass[heading.level]}
                      truncate
                    `}
                    title={heading.text}
                  >
                    <span className="text-muted mr-1">
                      {'#'.repeat(heading.level)}
                    </span>
                    {heading.text}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </div>

      {/* Document Stats */}
      {editor && (
        <div className="p-3 border-t border-line text-xs text-muted">
          <div className="flex justify-between">
            <span>Words</span>
            <span>
              {editor.storage.characterCount?.words?.() || 0}
            </span>
          </div>
          <div className="flex justify-between mt-1">
            <span>Characters</span>
            <span>
              {editor.storage.characterCount?.characters?.() || 0}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default OutlinePanel
