'use client'

import { useState, useCallback, useEffect, useMemo } from 'react'
import { Maximize2, Minimize2, Play, ChevronLeft, ChevronRight, Edit3, Eye, ExternalLink } from 'lucide-react'
import { SlideNavigator, Slide } from './SlideNavigator'
import { SlideEditor } from './SlideEditor'

interface SlidesData {
  slides: Slide[]
  theme: {
    primaryColor: string
    secondaryColor: string
    fontFamily: string
    logoUrl?: string
  }
}

interface PresentationViewProps {
  slidesData: SlidesData
  documentTitle?: string
  onSlidesChange?: (slides: Slide[]) => void
  readOnly?: boolean
  googleSlidesUrl?: string
}

// Default Espacio Publico theme
const DEFAULT_THEME = {
  primaryColor: '#1a365d',
  secondaryColor: '#c53030',
  fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
  logoUrl: undefined,
}

export function PresentationView({
  slidesData,
  documentTitle,
  onSlidesChange,
  readOnly = false,
  googleSlidesUrl,
}: PresentationViewProps) {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isPresenting, setIsPresenting] = useState(false)
  const [isEditMode, setIsEditMode] = useState(true)

  const slides = useMemo(() => slidesData?.slides || [], [slidesData])
  const theme = useMemo(() => slidesData?.theme || DEFAULT_THEME, [slidesData])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isPresenting || isFullscreen) {
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') {
          e.preventDefault()
          setCurrentSlide((prev) => Math.min(prev + 1, slides.length - 1))
        } else if (e.key === 'ArrowLeft' || e.key === 'Backspace') {
          e.preventDefault()
          setCurrentSlide((prev) => Math.max(prev - 1, 0))
        } else if (e.key === 'Escape') {
          e.preventDefault()
          setIsFullscreen(false)
          setIsPresenting(false)
        } else if (e.key === 'Home') {
          e.preventDefault()
          setCurrentSlide(0)
        } else if (e.key === 'End') {
          e.preventDefault()
          setCurrentSlide(slides.length - 1)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isPresenting, isFullscreen, slides.length])

  const handleSlideSelect = useCallback((index: number) => {
    setCurrentSlide(index)
  }, [])

  const handleAddSlide = useCallback(() => {
    if (readOnly) return

    const newSlide: Slide = {
      id: `slide-${Date.now()}`,
      slideNumber: slides.length + 1,
      layout: 'content',
      title: 'New Slide',
      content: '',
      notes: '',
    }

    const updatedSlides = [...slides, newSlide]
    onSlidesChange?.(updatedSlides)
    setCurrentSlide(updatedSlides.length - 1)
  }, [slides, onSlidesChange, readOnly])

  const handleDeleteSlide = useCallback(
    (index: number) => {
      if (readOnly || slides.length <= 1) return

      const updatedSlides = slides
        .filter((_, i) => i !== index)
        .map((slide, i) => ({
          ...slide,
          slideNumber: i + 1,
          id: `slide-${i + 1}`,
        }))

      onSlidesChange?.(updatedSlides)
      setCurrentSlide(Math.min(currentSlide, updatedSlides.length - 1))
    },
    [slides, currentSlide, onSlidesChange, readOnly]
  )

  const handleLayoutChange = useCallback(
    (index: number, layout: Slide['layout']) => {
      if (readOnly) return

      const updatedSlides = slides.map((slide, i) =>
        i === index ? { ...slide, layout } : slide
      )
      onSlidesChange?.(updatedSlides)
    },
    [slides, onSlidesChange, readOnly]
  )

  const handleSlideChange = useCallback(
    (updatedSlide: Slide) => {
      if (readOnly) return
      const updatedSlides = slides.map((slide) =>
        slide.id === updatedSlide.id ? { ...updatedSlide } : slide
      )
      onSlidesChange?.(updatedSlides)
    },
    [slides, onSlidesChange, readOnly]
  )

  const handleReorderSlide = useCallback(
    (fromIndex: number, toIndex: number) => {
      if (readOnly) return
      if (fromIndex === toIndex) return
      if (fromIndex < 0 || toIndex < 0) return
      if (fromIndex >= slides.length || toIndex >= slides.length) return

      const nextSlides = [...slides]
      const [moved] = nextSlides.splice(fromIndex, 1)
      if (!moved) return
      nextSlides.splice(toIndex, 0, moved)

      const normalized = nextSlides.map((slide, idx) => ({
        ...slide,
        slideNumber: idx + 1,
      }))

      // Keep current selection stable relative to reorder
      let nextCurrent = currentSlide
      if (fromIndex === currentSlide) {
        nextCurrent = toIndex
      } else if (fromIndex < currentSlide && toIndex >= currentSlide) {
        nextCurrent = currentSlide - 1
      } else if (fromIndex > currentSlide && toIndex <= currentSlide) {
        nextCurrent = currentSlide + 1
      }

      onSlidesChange?.(normalized)
      setCurrentSlide(nextCurrent)
    },
    [currentSlide, onSlidesChange, readOnly, slides]
  )

  const handleStartPresentation = useCallback(() => {
    setIsPresenting(true)
    setIsFullscreen(true)

    // Request fullscreen if available
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(() => {
        // Fullscreen might be blocked, continue anyway
      })
    }
  }, [])

  const handleExitPresentation = useCallback(() => {
    setIsPresenting(false)
    setIsFullscreen(false)

    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {})
    }
  }, [])

  const currentSlideData = slides[currentSlide]

  if (!slides.length) {
    return (
      <div className="h-full flex items-center justify-center text-muted">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <p>No slides found in this presentation</p>
        </div>
      </div>
    )
  }

  // Fullscreen presentation mode
  if (isFullscreen) {
    return (
      <div className="presentation-mode">
        {currentSlideData && (
          <div className="slide-container" style={{ maxWidth: '1200px' }}>
            <SlideEditor slide={currentSlideData} theme={theme} />
          </div>
        )}

        {/* Navigation controls */}
        <div className="slide-nav-controls">
          <button
            onClick={() => setCurrentSlide((prev) => Math.max(prev - 1, 0))}
            disabled={currentSlide === 0}
            className="btn btn-sm"
          >
            <ChevronLeft size={16} />
          </button>

          <span className="text-sm font-medium">
            {currentSlide + 1} / {slides.length}
          </span>

          <button
            onClick={() =>
              setCurrentSlide((prev) => Math.min(prev + 1, slides.length - 1))
            }
            disabled={currentSlide === slides.length - 1}
            className="btn btn-sm"
          >
            <ChevronRight size={16} />
          </button>

          <div className="w-px h-4 bg-line mx-2" />

          <button
            onClick={handleExitPresentation}
            className="btn btn-sm"
            title="Exit presentation (Esc)"
          >
            <Minimize2 size={14} />
          </button>
        </div>
      </div>
    )
  }

  // Normal editor view
  return (
    <div className="presentation-view h-full">
      {/* Left sidebar - Slide navigator */}
      <aside className="w-56 border-r border-line bg-paper flex-shrink-0 overflow-hidden">
        <SlideNavigator
          slides={slides}
          currentSlide={currentSlide}
          onSlideSelect={handleSlideSelect}
          onAddSlide={handleAddSlide}
          onDeleteSlide={handleDeleteSlide}
          onLayoutChange={handleLayoutChange}
          onReorderSlide={handleReorderSlide}
          readOnly={readOnly}
        />
      </aside>

      {/* Main slide area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="slide-toolbar">
          <span className="text-xs font-semibold text-muted flex-1">
            Slide {currentSlide + 1}: {currentSlideData?.title || 'Untitled'}
          </span>

          <button
            onClick={() => setIsEditMode(!isEditMode)}
            className={`btn btn-sm ${isEditMode ? 'btn-primary' : ''}`}
            title={isEditMode ? 'Preview mode' : 'Edit mode'}
          >
            {isEditMode ? <Eye size={14} /> : <Edit3 size={14} />}
            <span className="ml-1">{isEditMode ? 'Preview' : 'Edit'}</span>
          </button>

          {googleSlidesUrl && (
            <a
              href={googleSlidesUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-sm bg-blue-600 text-white hover:bg-blue-700"
              title="Open in Google Slides"
            >
              <ExternalLink size={14} />
              <span className="ml-1">Google Slides</span>
            </a>
          )}

          <button
            onClick={handleStartPresentation}
            className="btn btn-sm btn-primary"
            title="Start presentation"
          >
            <Play size={14} />
            <span className="ml-1">Present</span>
          </button>

          <button
            onClick={() => setIsFullscreen(true)}
            className="btn btn-sm"
            title="Fullscreen"
          >
            <Maximize2 size={14} />
          </button>
        </div>

        {/* Slide view */}
        <div className="slide-area">
          <div className="slide-container">
            {currentSlideData && (
              <SlideEditor
                slide={currentSlideData}
                theme={theme}
                isEditing={isEditMode}
                onSlideChange={handleSlideChange}
              />
            )}
          </div>
        </div>

        {/* Speaker notes */}
        {currentSlideData?.notes && (
          <div className="speaker-notes">
            <div className="text-xs font-semibold text-muted mb-2">
              Speaker Notes
            </div>
            <div className="text-sm text-ink">{currentSlideData.notes}</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PresentationView
