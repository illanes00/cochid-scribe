'use client'

import { useRef, useState, useCallback, useEffect, useMemo, ReactNode } from 'react'
import { Editor } from '@tiptap/core'
import { Ruler, VerticalRuler } from './Ruler'
import { HeaderFooterEditor, HeaderFooterContent } from './HeaderFooterEditor'

/**
 * Page format dimensions at 96 DPI
 * These match standard print sizes for accurate WYSIWYG editing
 */
export const PAGE_FORMATS = {
  A4: { width: 794, height: 1123, name: 'A4 (210mm x 297mm)' },
  Letter: { width: 816, height: 1056, name: 'Letter (8.5" x 11")' },
  Legal: { width: 816, height: 1344, name: 'Legal (8.5" x 14")' },
} as const

export type PageFormat = keyof typeof PAGE_FORMATS

export interface PageMargins {
  top: number
  right: number
  bottom: number
  left: number
}

export interface PageLayoutConfig {
  format: PageFormat
  margins: PageMargins
  showRuler: boolean
  showVerticalRuler: boolean
  showPageBreaks: boolean
  showHeaderFooter: boolean
  headerContent?: HeaderFooterContent
  footerContent?: HeaderFooterContent
}

const DEFAULT_MARGINS: PageMargins = {
  top: 72,    // 1 inch
  right: 72,
  bottom: 72,
  left: 72,
}

const DEFAULT_LAYOUT: PageLayoutConfig = {
  format: 'A4',
  margins: DEFAULT_MARGINS,
  showRuler: true,
  showVerticalRuler: false,
  showPageBreaks: true,
  showHeaderFooter: false,
}

interface PagedEditorProps {
  children: ReactNode
  editor: Editor | null
  layout?: Partial<PageLayoutConfig>
  documentTitle?: string
  onLayoutChange?: (layout: PageLayoutConfig) => void
  className?: string
}

/**
 * PagedEditor wraps the TipTap editor with visual pagination.
 *
 * This uses CSS-based pagination (no document mutation) for stability:
 * - Visual page breaks are rendered as overlays
 * - The document model remains unchanged
 * - Cursor and selection behavior is preserved
 * - Header/footer are separate mini-editors outside main content
 */
export function PagedEditor({
  children,
  editor,
  layout: layoutProp,
  documentTitle = 'Untitled',
  onLayoutChange,
  className = '',
}: PagedEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const [pageCount, setPageCount] = useState(1)

  // Merge provided layout with defaults (memoized to prevent unnecessary re-renders)
  const layout: PageLayoutConfig = useMemo(() => ({
    ...DEFAULT_LAYOUT,
    ...layoutProp,
    margins: { ...DEFAULT_MARGINS, ...layoutProp?.margins },
  }), [layoutProp])

  const pageFormat = PAGE_FORMATS[layout.format]
  const contentHeight = pageFormat.height - layout.margins.top - layout.margins.bottom
  const contentWidth = pageFormat.width - layout.margins.left - layout.margins.right

  // Calculate number of pages based on content height
  const calculatePageCount = useCallback(() => {
    if (!contentRef.current) return 1
    const scrollHeight = contentRef.current.scrollHeight
    // Account for header/footer space if enabled
    const headerFooterSpace = layout.showHeaderFooter ? 80 : 0
    const effectiveContentHeight = contentHeight - headerFooterSpace
    return Math.max(1, Math.ceil(scrollHeight / effectiveContentHeight))
  }, [contentHeight, layout.showHeaderFooter])

  // Update page count when content changes
  useEffect(() => {
    if (!editor) return

    const updatePageCount = () => {
      // Delay slightly to let DOM update
      requestAnimationFrame(() => {
        setPageCount(calculatePageCount())
      })
    }

    updatePageCount()

    editor.on('update', updatePageCount)
    editor.on('transaction', updatePageCount)

    // Also update on window resize
    window.addEventListener('resize', updatePageCount)

    return () => {
      editor.off('update', updatePageCount)
      editor.off('transaction', updatePageCount)
      window.removeEventListener('resize', updatePageCount)
    }
  }, [editor, calculatePageCount])

  // Handle margin changes from ruler
  const handleMarginsChange = useCallback((newMargins: Partial<PageMargins>) => {
    const updatedLayout = {
      ...layout,
      margins: { ...layout.margins, ...newMargins },
    }
    onLayoutChange?.(updatedLayout)
  }, [layout, onLayoutChange])

  // Handle header/footer content changes
  const handleHeaderChange = useCallback((content: HeaderFooterContent) => {
    onLayoutChange?.({
      ...layout,
      headerContent: content,
    })
  }, [layout, onLayoutChange])

  const handleFooterChange = useCallback((content: HeaderFooterContent) => {
    onLayoutChange?.({
      ...layout,
      footerContent: content,
    })
  }, [layout, onLayoutChange])

  // Generate page break indicators
  const pageBreaks = []
  if (layout.showPageBreaks && pageCount > 1) {
    for (let i = 1; i < pageCount; i++) {
      pageBreaks.push(
        <div
          key={`page-break-${i}`}
          className="page-break-indicator"
          style={{
            top: `${i * contentHeight}px`,
          }}
        >
          <span className="page-break-label">Page {i + 1}</span>
        </div>
      )
    }
  }

  return (
    <div
      ref={containerRef}
      className={`paged-editor-wrapper ${className}`}
      style={{
        '--page-width': `${pageFormat.width}px`,
        '--page-height': `${pageFormat.height}px`,
        '--margin-top': `${layout.margins.top}px`,
        '--margin-right': `${layout.margins.right}px`,
        '--margin-bottom': `${layout.margins.bottom}px`,
        '--margin-left': `${layout.margins.left}px`,
        '--content-width': `${contentWidth}px`,
        '--content-height': `${contentHeight}px`,
      } as React.CSSProperties}
    >
      {/* Ruler */}
      {layout.showRuler && (
        <Ruler
          pageWidth={pageFormat.width}
          margins={layout.margins}
          onMarginsChange={handleMarginsChange}
        />
      )}

      {/* Page container */}
      <div className="paged-editor-scroll">
        <div className="paged-editor-pages-wrapper">
          {/* Vertical ruler */}
          {layout.showVerticalRuler && (
            <VerticalRuler
              pageHeight={pageFormat.height}
              margins={{ top: layout.margins.top, bottom: layout.margins.bottom }}
              onMarginsChange={handleMarginsChange}
            />
          )}

          <div className="paged-editor-pages">
            {/* Paper visual */}
            <div className="page-paper">
            {/* Header */}
            {layout.showHeaderFooter && (
              <div className="page-header">
                <HeaderFooterEditor
                  type="header"
                  content={layout.headerContent}
                  onChange={handleHeaderChange}
                  variables={{
                    pageNumber: 1,
                    totalPages: pageCount,
                    documentTitle,
                  }}
                />
              </div>
            )}

            {/* Content area */}
            <div className="page-content" ref={contentRef}>
              {children}
              {pageBreaks}
            </div>

            {/* Footer */}
            {layout.showHeaderFooter && (
              <div className="page-footer">
                <HeaderFooterEditor
                  type="footer"
                  content={layout.footerContent}
                  onChange={handleFooterChange}
                  variables={{
                    pageNumber: 1,
                    totalPages: pageCount,
                    documentTitle,
                  }}
                />
              </div>
            )}
          </div>
        </div>
        </div>

        {/* Page count indicator */}
        <div className="page-count-indicator">
          {pageCount} {pageCount === 1 ? 'page' : 'pages'}
        </div>
      </div>
    </div>
  )
}

/**
 * Utility hook to manage page layout state
 */
export function usePageLayout(initialLayout?: Partial<PageLayoutConfig>) {
  const [layout, setLayout] = useState<PageLayoutConfig>({
    ...DEFAULT_LAYOUT,
    ...initialLayout,
    margins: { ...DEFAULT_MARGINS, ...initialLayout?.margins },
  })

  const updateLayout = useCallback((updates: Partial<PageLayoutConfig>) => {
    setLayout(prev => ({
      ...prev,
      ...updates,
      margins: updates.margins ? { ...prev.margins, ...updates.margins } : prev.margins,
    }))
  }, [])

  const toggleRuler = useCallback(() => {
    setLayout(prev => ({ ...prev, showRuler: !prev.showRuler }))
  }, [])

  const togglePageBreaks = useCallback(() => {
    setLayout(prev => ({ ...prev, showPageBreaks: !prev.showPageBreaks }))
  }, [])

  const toggleHeaderFooter = useCallback(() => {
    setLayout(prev => ({ ...prev, showHeaderFooter: !prev.showHeaderFooter }))
  }, [])

  const setFormat = useCallback((format: PageFormat) => {
    setLayout(prev => ({ ...prev, format }))
  }, [])

  return {
    layout,
    updateLayout,
    toggleRuler,
    togglePageBreaks,
    toggleHeaderFooter,
    setFormat,
  }
}
