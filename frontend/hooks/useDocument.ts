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
    if (Object.keys(pendingUpdates.current).length === 0) return

    try {
      setSaving(true)
      const updates = { ...pendingUpdates.current }
      pendingUpdates.current = {}

      const updated = await documentsApi.update(slug, updates)
      setDocument(updated)
      setLastSaved(new Date())
      setHasUnsavedChanges(false)
      onSaveSuccess?.()
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Save failed')
      onSaveError?.(error)
      // Restore pending updates on failure
      pendingUpdates.current = {
        ...pendingUpdates.current,
      }
      setHasUnsavedChanges(true)
    } finally {
      setSaving(false)
    }
  }, [document, slug, onSaveSuccess, onSaveError])

  // Update document (queues for auto-save)
  const updateDocument = useCallback(
    (updates: DocumentUpdate) => {
      pendingUpdates.current = {
        ...pendingUpdates.current,
        ...updates,
      }
      setHasUnsavedChanges(true)

      // Clear existing timer
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }

      // Set new auto-save timer
      autoSaveTimer.current = setTimeout(() => {
        saveDocument()
      }, autoSaveDelay)
    },
    [autoSaveDelay, saveDocument]
  )

  // Initial load
  useEffect(() => {
    loadDocument()
  }, [loadDocument])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current)
      }
      // Save any pending changes before unmount
      if (Object.keys(pendingUpdates.current).length > 0) {
        saveDocument()
      }
    }
  }, [saveDocument])

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
