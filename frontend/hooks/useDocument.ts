'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Document, documentsApi, DocumentUpdate } from '@/lib/api'

interface UseDocumentOptions {
  autoSaveDelay?: number
  onSaveSuccess?: () => void
  onSaveError?: (error: Error) => void
}

interface UseDocumentReturn {
  document: Document | null
  loading: boolean
  error: string | null
  saving: boolean
  lastSaved: Date | null
  hasUnsavedChanges: boolean
  updateDocument: (updates: DocumentUpdate) => void
  saveDocument: () => Promise<void>
  reloadDocument: () => Promise<void>
}

function mergePendingUpdates(
  current: DocumentUpdate,
  updates: DocumentUpdate
): DocumentUpdate {
  return {
    ...current,
    ...updates,
    content: updates.content
      ? {
          ...(current.content || {}),
          ...updates.content,
        }
      : current.content,
    front_matter: updates.front_matter
      ? {
          ...(current.front_matter || {}),
          ...updates.front_matter,
        }
      : current.front_matter,
  }
}

function applyUpdatesToDocument(
  document: Document | null,
  updates: DocumentUpdate
): Document | null {
  if (!document) return document

  return {
    ...document,
    ...updates,
    content: updates.content
      ? {
          ...(document.content || {}),
          ...updates.content,
        }
      : document.content,
    front_matter: updates.front_matter
      ? {
          ...(document.front_matter || {}),
          ...updates.front_matter,
        }
      : document.front_matter,
  }
}

export function useDocument(
  slug: string,
  options: UseDocumentOptions = {}
): UseDocumentReturn {
  const { autoSaveDelay = 3000, onSaveSuccess, onSaveError } = options

  const [document, setDocument] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const pendingUpdates = useRef<DocumentUpdate>({})
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null)
  const saveInFlight = useRef<Promise<void> | null>(null)
  const saveDocumentRef = useRef<() => Promise<void>>(async () => {})
  const isMounted = useRef(true)

  const clearAutoSaveTimer = useCallback(() => {
    if (autoSaveTimer.current) {
      clearTimeout(autoSaveTimer.current)
      autoSaveTimer.current = null
    }
  }, [])

  const scheduleAutoSave = useCallback(
    (delay = autoSaveDelay) => {
      clearAutoSaveTimer()

      if (!slug || slug === 'new') return
      if (Object.keys(pendingUpdates.current).length === 0) return

      autoSaveTimer.current = setTimeout(() => {
        void saveDocumentRef.current()
      }, delay)
    },
    [autoSaveDelay, clearAutoSaveTimer, slug]
  )

  // Load document
  const loadDocument = useCallback(async () => {
    if (!slug || slug === 'new') {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const doc = await documentsApi.get(slug)
      setDocument(doc)
      setLastSaved(new Date(doc.updated_at))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }, [slug])

  // Save document
  const saveDocument = useCallback(async () => {
    if (!document || !slug || slug === 'new') return
    if (saveInFlight.current) return saveInFlight.current
    if (Object.keys(pendingUpdates.current).length === 0) return

    clearAutoSaveTimer()

    const updates = pendingUpdates.current
    pendingUpdates.current = {}

    const savePromise = (async () => {
      try {
        if (isMounted.current) {
          setSaving(true)
        }

        const updated = await documentsApi.update(slug, updates)
        const hasPendingUpdates = Object.keys(pendingUpdates.current).length > 0

        if (isMounted.current) {
          setDocument(
            hasPendingUpdates
              ? applyUpdatesToDocument(updated, pendingUpdates.current)
              : updated
          )
          setLastSaved(new Date(updated.updated_at))
          setHasUnsavedChanges(hasPendingUpdates)
        }

        onSaveSuccess?.()

        if (hasPendingUpdates) {
          scheduleAutoSave(0)
        }
      } catch (err) {
        pendingUpdates.current = mergePendingUpdates(updates, pendingUpdates.current)

        if (isMounted.current) {
          setHasUnsavedChanges(true)
        }

        const error = err instanceof Error ? err : new Error('Save failed')
        onSaveError?.(error)
        scheduleAutoSave()
      } finally {
        saveInFlight.current = null

        if (isMounted.current) {
          setSaving(false)
        }
      }
    })()

    saveInFlight.current = savePromise
    return savePromise
  }, [document, slug, onSaveSuccess, onSaveError, clearAutoSaveTimer, scheduleAutoSave])

  saveDocumentRef.current = saveDocument

  // Update document (queues for auto-save)
  const updateDocument = useCallback(
    (updates: DocumentUpdate) => {
      pendingUpdates.current = mergePendingUpdates(pendingUpdates.current, updates)
      setDocument((current) => applyUpdatesToDocument(current, updates))
      setHasUnsavedChanges(true)

      scheduleAutoSave()
    },
    [scheduleAutoSave]
  )

  // Initial load
  useEffect(() => {
    loadDocument()
  }, [loadDocument])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMounted.current = false
      clearAutoSaveTimer()
      // Save any pending changes before unmount
      if (Object.keys(pendingUpdates.current).length > 0) {
        void saveDocumentRef.current()
      }
    }
  }, [clearAutoSaveTimer])

  // Save on page unload
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  return {
    document,
    loading,
    error,
    saving,
    lastSaved,
    hasUnsavedChanges,
    updateDocument,
    saveDocument,
    reloadDocument: loadDocument,
  }
}

export default useDocument
