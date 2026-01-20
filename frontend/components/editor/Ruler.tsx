'use client'

import { useRef, useState, useCallback, useEffect, MouseEvent } from 'react'
import type { PageMargins } from './PagedEditor'

interface RulerProps {
  pageWidth: number
  margins: PageMargins
  onMarginsChange: (margins: Partial<PageMargins>) => void
  /** First-line indent in pixels */
  firstLineIndent?: number
  onFirstLineIndentChange?: (indent: number) => void
  /** Show ruler in inches (true) or centimeters (false) */
  showInches?: boolean
}

/**
 * Horizontal ruler component with draggable margin handles.
 *
 * Features:
 * - Tick marks every 0.5 inches or 1 cm
 * - Draggable left/right margin triangles
 * - Optional first-line indent marker
 * - Visual feedback during drag
 */
export function Ruler({
  pageWidth,
  margins,
  onMarginsChange,
  firstLineIndent = 0,
  onFirstLineIndentChange,
  showInches = true,
}: RulerProps) {
  const rulerRef = useRef<HTMLDivElement>(null)
  const [dragging, setDragging] = useState<'left' | 'right' | 'firstLine' | null>(null)
  const [dragOffset, setDragOffset] = useState(0)

  // Convert pixels to inches/cm for display
  const pixelsPerInch = 96
  const pixelsPerCm = 37.8
  const unit = showInches ? pixelsPerInch : pixelsPerCm
  const unitLabel = showInches ? 'in' : 'cm'

  // Generate tick marks
  const ticks = []
  const tickSpacing = showInches ? pixelsPerInch / 2 : pixelsPerCm // Half inch or 1 cm
  const majorTickInterval = showInches ? 2 : 1 // Every inch or cm

  for (let i = 0; i <= pageWidth / tickSpacing; i++) {
    const position = i * tickSpacing
    const isMajor = i % majorTickInterval === 0
    const number = showInches ? i / 2 : i

    ticks.push(
      <div
        key={i}
        className={`ruler-tick ${isMajor ? 'major' : 'minor'}`}
        style={{ left: `${position}px` }}
      >
        {isMajor && number > 0 && (
          <span className="ruler-number">{number}</span>
        )}
      </div>
    )
  }

  // Handle mouse down on margin handles
  const handleMouseDown = useCallback((
    e: MouseEvent,
    handleType: 'left' | 'right' | 'firstLine'
  ) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(handleType)

    const rect = rulerRef.current?.getBoundingClientRect()
    if (rect) {
      setDragOffset(e.clientX - rect.left)
    }
  }, [])

  // Handle mouse move for dragging
  useEffect(() => {
    if (!dragging) return

    const handleMouseMove = (e: globalThis.MouseEvent) => {
      const rect = rulerRef.current?.getBoundingClientRect()
      if (!rect) return

      const x = e.clientX - rect.left
      const clampedX = Math.max(0, Math.min(pageWidth, x))

      // Snap to nearest 8 pixels (approximately 1/12 inch)
      const snappedX = Math.round(clampedX / 8) * 8

      if (dragging === 'left') {
        // Left margin: can't overlap with content area too much
        const maxLeft = pageWidth - margins.right - 100
        const newLeft = Math.min(snappedX, maxLeft)
        onMarginsChange({ left: Math.max(36, newLeft) })
      } else if (dragging === 'right') {
        // Right margin: measured from right edge
        const newRight = pageWidth - snappedX
        const maxRight = pageWidth - margins.left - 100
        onMarginsChange({ right: Math.max(36, Math.min(newRight, maxRight)) })
      } else if (dragging === 'firstLine') {
        // First-line indent: relative to left margin
        const indent = snappedX - margins.left
        onFirstLineIndentChange?.(Math.max(0, indent))
      }
    }

    const handleMouseUp = () => {
      setDragging(null)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [dragging, pageWidth, margins, onMarginsChange, onFirstLineIndentChange])

  // Calculate handle positions
  const leftHandlePos = margins.left
  const rightHandlePos = pageWidth - margins.right
  const firstLineHandlePos = margins.left + firstLineIndent

  return (
    <div
      ref={rulerRef}
      className={`ruler ${dragging ? 'dragging' : ''}`}
      style={{ width: `${pageWidth}px` }}
    >
      {/* Ruler track with ticks */}
      <div className="ruler-track">
        {ticks}

        {/* Margin shading */}
        <div
          className="ruler-margin-zone left"
          style={{ width: `${margins.left}px` }}
        />
        <div
          className="ruler-margin-zone right"
          style={{ width: `${margins.right}px`, right: 0 }}
        />
      </div>

      {/* Left margin handle */}
      <div
        className={`ruler-handle left-margin ${dragging === 'left' ? 'active' : ''}`}
        style={{ left: `${leftHandlePos}px` }}
        onMouseDown={(e) => handleMouseDown(e, 'left')}
        title={`Left margin: ${(margins.left / unit).toFixed(2)} ${unitLabel}`}
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <polygon points="0,0 12,0 6,10" fill="currentColor" />
        </svg>
      </div>

      {/* First-line indent handle (inverted triangle above) */}
      {onFirstLineIndentChange && (
        <div
          className={`ruler-handle first-line ${dragging === 'firstLine' ? 'active' : ''}`}
          style={{ left: `${firstLineHandlePos}px` }}
          onMouseDown={(e) => handleMouseDown(e, 'firstLine')}
          title={`First-line indent: ${(firstLineIndent / unit).toFixed(2)} ${unitLabel}`}
        >
          <svg width="12" height="12" viewBox="0 0 12 12">
            <polygon points="6,2 0,12 12,12" fill="currentColor" />
          </svg>
        </div>
      )}

      {/* Right margin handle */}
      <div
        className={`ruler-handle right-margin ${dragging === 'right' ? 'active' : ''}`}
        style={{ left: `${rightHandlePos}px` }}
        onMouseDown={(e) => handleMouseDown(e, 'right')}
        title={`Right margin: ${(margins.right / unit).toFixed(2)} ${unitLabel}`}
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <polygon points="0,0 12,0 6,10" fill="currentColor" />
        </svg>
      </div>

      {/* Drag guide line */}
      {dragging && (
        <div
          className="ruler-guide-line"
          style={{
            left: dragging === 'left' ? `${leftHandlePos}px` :
                  dragging === 'right' ? `${rightHandlePos}px` :
                  `${firstLineHandlePos}px`
          }}
        />
      )}
    </div>
  )
}

/**
 * Vertical ruler for page height (optional)
 */
export function VerticalRuler({
  pageHeight,
  margins,
  onMarginsChange,
  showInches = true,
}: {
  pageHeight: number
  margins: Pick<PageMargins, 'top' | 'bottom'>
  onMarginsChange: (margins: Partial<PageMargins>) => void
  showInches?: boolean
}) {
  const rulerRef = useRef<HTMLDivElement>(null)
  const [dragging, setDragging] = useState<'top' | 'bottom' | null>(null)

  const pixelsPerInch = 96
  const pixelsPerCm = 37.8
  const unit = showInches ? pixelsPerInch : pixelsPerCm

  // Generate vertical tick marks
  const ticks = []
  const tickSpacing = showInches ? pixelsPerInch / 2 : pixelsPerCm

  for (let i = 0; i <= pageHeight / tickSpacing; i++) {
    const position = i * tickSpacing
    const isMajor = i % 2 === 0
    const number = showInches ? i / 2 : i

    ticks.push(
      <div
        key={i}
        className={`vruler-tick ${isMajor ? 'major' : 'minor'}`}
        style={{ top: `${position}px` }}
      >
        {isMajor && number > 0 && (
          <span className="vruler-number">{number}</span>
        )}
      </div>
    )
  }

  const handleMouseDown = useCallback((
    e: MouseEvent,
    handleType: 'top' | 'bottom'
  ) => {
    e.preventDefault()
    setDragging(handleType)
  }, [])

  useEffect(() => {
    if (!dragging) return

    const handleMouseMove = (e: globalThis.MouseEvent) => {
      const rect = rulerRef.current?.getBoundingClientRect()
      if (!rect) return

      const y = e.clientY - rect.top
      const clampedY = Math.max(0, Math.min(pageHeight, y))
      const snappedY = Math.round(clampedY / 8) * 8

      if (dragging === 'top') {
        const maxTop = pageHeight - margins.bottom - 200
        onMarginsChange({ top: Math.max(36, Math.min(snappedY, maxTop)) })
      } else if (dragging === 'bottom') {
        const newBottom = pageHeight - snappedY
        const maxBottom = pageHeight - margins.top - 200
        onMarginsChange({ bottom: Math.max(36, Math.min(newBottom, maxBottom)) })
      }
    }

    const handleMouseUp = () => setDragging(null)

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [dragging, pageHeight, margins, onMarginsChange])

  return (
    <div
      ref={rulerRef}
      className={`vruler ${dragging ? 'dragging' : ''}`}
      style={{ height: `${pageHeight}px` }}
    >
      <div className="vruler-track">
        {ticks}
        <div
          className="vruler-margin-zone top"
          style={{ height: `${margins.top}px` }}
        />
        <div
          className="vruler-margin-zone bottom"
          style={{ height: `${margins.bottom}px`, bottom: 0 }}
        />
      </div>

      <div
        className={`vruler-handle top-margin ${dragging === 'top' ? 'active' : ''}`}
        style={{ top: `${margins.top}px` }}
        onMouseDown={(e) => handleMouseDown(e, 'top')}
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <polygon points="0,0 10,6 0,12" fill="currentColor" />
        </svg>
      </div>

      <div
        className={`vruler-handle bottom-margin ${dragging === 'bottom' ? 'active' : ''}`}
        style={{ top: `${pageHeight - margins.bottom}px` }}
        onMouseDown={(e) => handleMouseDown(e, 'bottom')}
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <polygon points="0,0 10,6 0,12" fill="currentColor" />
        </svg>
      </div>
    </div>
  )
}
