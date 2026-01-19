'use client'

import { useCallback, useState, type DragEvent } from 'react'
import { ChevronLeft, ChevronRight, Plus, Trash2 } from 'lucide-react'

export interface Slide {
  id: string
  slideNumber: number
  layout: 'title' | 'content' | 'two-column' | 'image-full' | 'blank'
  title: string
  content: string
  notes?: string
}

interface SlideNavigatorProps {
  slides: Slide[]
  currentSlide: number
  onSlideSelect: (index: number) => void
  onAddSlide?: () => void
  onDeleteSlide?: (index: number) => void
  onLayoutChange?: (index: number, layout: Slide['layout']) => void
  onReorderSlide?: (fromIndex: number, toIndex: number) => void
  readOnly?: boolean
}

export function SlideNavigator({
  slides,
  currentSlide,
  onSlideSelect,
  onAddSlide,
  onDeleteSlide,
  onLayoutChange,
  onReorderSlide,
  readOnly = false,
}: SlideNavigatorProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  const getPreviewText = useCallback((content: string) => {
    const withoutHtml = content.replace(/<[^>]+>/g, '')
    return withoutHtml.replace(/[#*_\-]/g, '').slice(0, 100)
  }, [])

  const handleDragStart = useCallback(
    (index: number, event: DragEvent<HTMLButtonElement>) => {
      if (readOnly) return
      setDraggedIndex(index)
      setDragOverIndex(null)
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', String(index))
    },
    [readOnly]
  )

  const handleDragOver = useCallback(
    (index: number, event: DragEvent<HTMLButtonElement>) => {
      if (readOnly) return
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      if (dragOverIndex !== index) {
        setDragOverIndex(index)
      }
    },
    [dragOverIndex, readOnly]
  )

  const cleanupDrag = useCallback(() => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [])

  const handleDrop = useCallback(
    (toIndex: number, event: DragEvent<HTMLButtonElement>) => {
      if (readOnly) return
      event.preventDefault()
      const raw = event.dataTransfer.getData('text/plain')
      const fromIndex = Number(raw)
      if (!Number.isFinite(fromIndex)) {
        cleanupDrag()
        return
      }
      if (fromIndex !== toIndex) {
        onReorderSlide?.(fromIndex, toIndex)
      }
      cleanupDrag()
    },
    [cleanupDrag, onReorderSlide, readOnly]
  )

  const handleDragEnd = useCallback(() => {
    cleanupDrag()
  }, [cleanupDrag])

  const handlePrevious = useCallback(() => {
    if (currentSlide > 0) {
      onSlideSelect(currentSlide - 1)
    }
  }, [currentSlide, onSlideSelect])

  const handleNext = useCallback(() => {
    if (currentSlide < slides.length - 1) {
      onSlideSelect(currentSlide + 1)
    }
  }, [currentSlide, slides.length, onSlideSelect])

  const getLayoutIcon = (layout: Slide['layout']) => {
    switch (layout) {
      case 'title':
        return 'T'
      case 'content':
        return 'C'
      case 'two-column':
        return '||'
      case 'image-full':
        return 'I'
      case 'blank':
        return 'B'
      default:
        return 'C'
    }
  }

  return (
    <div className="slide-navigator h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-line">
        <span className="text-xs font-semibold text-muted uppercase tracking-wide">
          Slides
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={handlePrevious}
            disabled={currentSlide === 0}
            className="p-1 text-muted hover:text-ink disabled:opacity-30"
            title="Previous slide"
          >
            <ChevronLeft size={14} />
          </button>
          <span className="text-xs text-muted px-1">
            {currentSlide + 1} / {slides.length}
          </span>
          <button
            onClick={handleNext}
            disabled={currentSlide === slides.length - 1}
            className="p-1 text-muted hover:text-ink disabled:opacity-30"
            title="Next slide"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Slide thumbnails */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {slides.map((slide, index) => (
          <button
            key={slide.id}
            onClick={() => onSlideSelect(index)}
            draggable={!readOnly}
            onDragStart={(e) => handleDragStart(index, e)}
            onDragOver={(e) => handleDragOver(index, e)}
            onDrop={(e) => handleDrop(index, e)}
            onDragEnd={handleDragEnd}
            className={`
              slide-thumbnail w-full text-left p-2 border transition-colors
              ${index === currentSlide
                ? 'border-c-blue bg-blue-50/50'
                : 'border-line hover:border-line-strong bg-paper'
              }
              ${draggedIndex === index ? 'opacity-60' : ''}
              ${dragOverIndex === index && draggedIndex !== null && draggedIndex !== index ? 'border-c-blue' : ''}
            `}
          >
            {/* Slide number and layout */}
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-muted">
                {index + 1}
              </span>
              <span className="text-[10px] px-1 py-0.5 bg-bg text-muted font-mono">
                {getLayoutIcon(slide.layout)}
              </span>
            </div>

            {/* Slide preview */}
            <div className={`
              slide-preview aspect-[16/9] bg-paper border border-line mb-1 p-1 overflow-hidden
              ${slide.layout === 'title' ? 'flex items-center justify-center' : ''}
            `}>
              {slide.title ? (
                <div className={`
                  text-[8px] leading-tight
                  ${slide.layout === 'title'
                    ? 'text-center font-bold text-[10px]'
                    : 'font-semibold'
                  }
                `}>
                  {slide.title.slice(0, 50)}
                  {slide.title.length > 50 && '...'}
                </div>
              ) : (
                <div className="text-[8px] text-muted italic">Empty slide</div>
              )}
              {slide.layout !== 'title' && slide.content && (
                <div className="text-[6px] text-muted mt-0.5 line-clamp-3">
                  {getPreviewText(slide.content)}
                </div>
              )}
            </div>

            {/* Actions */}
            {!readOnly && index === currentSlide && (
              <div className="flex items-center gap-1 mt-1">
                <select
                  className="text-[10px] px-1 py-0.5 border border-line bg-paper flex-1"
                  value={slide.layout}
                  onChange={(e) => onLayoutChange?.(index, e.target.value as Slide['layout'])}
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value="title">Title</option>
                  <option value="content">Content</option>
                  <option value="two-column">Two Column</option>
                  <option value="image-full">Image</option>
                  <option value="blank">Blank</option>
                </select>
                {slides.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSlide?.(index)
                    }}
                    className="p-0.5 text-muted hover:text-c-red"
                    title="Delete slide"
                  >
                    <Trash2 size={10} />
                  </button>
                )}
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Add slide button */}
      {!readOnly && (
        <div className="p-2 border-t border-line">
          <button
            onClick={onAddSlide}
            className="w-full btn btn-sm flex items-center justify-center gap-1"
          >
            <Plus size={12} />
            <span className="text-xs">Add Slide</span>
          </button>
        </div>
      )}
    </div>
  )
}

export default SlideNavigator
