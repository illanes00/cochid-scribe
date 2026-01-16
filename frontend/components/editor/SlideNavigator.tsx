'use client'

import { useCallback } from 'react'
import { ChevronLeft, ChevronRight, Plus, Trash2, Layout } from 'lucide-react'

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
  readOnly?: boolean
}

export function SlideNavigator({
  slides,
  currentSlide,
  onSlideSelect,
  onAddSlide,
  onDeleteSlide,
  onLayoutChange,
  readOnly = false,
}: SlideNavigatorProps) {
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
            className={`
              slide-thumbnail w-full text-left p-2 border transition-colors
              ${index === currentSlide
                ? 'border-c-blue bg-blue-50/50'
                : 'border-line hover:border-line-strong bg-paper'
              }
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
                  {slide.content.replace(/[#*_\-]/g, '').slice(0, 100)}
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
