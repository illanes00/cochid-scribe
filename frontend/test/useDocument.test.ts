import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useDocument } from '@/hooks/useDocument'

// Mock the API module
vi.mock('@/lib/api', () => ({
  documentsApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
  Document: {},
  DocumentUpdate: {},
}))

import { documentsApi } from '@/lib/api'

const mockDocument = {
  id: '123',
  slug: 'test-doc',
  title: 'Test Document',
  content: { json: { type: 'doc', content: [] }, html: '<p></p>' },
  doc_type: 'document',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('useDocument', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(documentsApi.get).mockResolvedValue(mockDocument)
    vi.mocked(documentsApi.update).mockResolvedValue({
      ...mockDocument,
      title: 'Updated Title',
    })
  })

  it('should load document on mount', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    expect(result.current.loading).toBe(true)
    expect(result.current.document).toBe(null)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(documentsApi.get).toHaveBeenCalledWith('test-doc')
    expect(result.current.document).toEqual(mockDocument)
    expect(result.current.error).toBe(null)
  })

  it('should not load document for "new" slug', async () => {
    const { result } = renderHook(() => useDocument('new'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(documentsApi.get).not.toHaveBeenCalled()
    expect(result.current.document).toBe(null)
  })

  it('should handle load errors gracefully', async () => {
    vi.mocked(documentsApi.get).mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.document).toBe(null)
  })

  it('should mark document as having unsaved changes on update', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.hasUnsavedChanges).toBe(false)

    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })

    expect(result.current.hasUnsavedChanges).toBe(true)
  })

  it('should allow manual save via saveDocument', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })

    // Call saveDocument directly
    await act(async () => {
      await result.current.saveDocument()
    })

    expect(documentsApi.update).toHaveBeenCalledWith('test-doc', { title: 'New Title' })
  })

  it('should call onSaveSuccess callback after successful save', async () => {
    const onSaveSuccess = vi.fn()
    const { result } = renderHook(() =>
      useDocument('test-doc', { onSaveSuccess })
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })

    await act(async () => {
      await result.current.saveDocument()
    })

    expect(onSaveSuccess).toHaveBeenCalled()
  })

  it('should call onSaveError callback on save failure', async () => {
    const onSaveError = vi.fn()
    vi.mocked(documentsApi.update).mockRejectedValue(new Error('Save failed'))

    const { result } = renderHook(() =>
      useDocument('test-doc', { onSaveError })
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })

    await act(async () => {
      await result.current.saveDocument()
    })

    expect(onSaveError).toHaveBeenCalledWith(expect.any(Error))
    // Should still have unsaved changes after failure
    expect(result.current.hasUnsavedChanges).toBe(true)
  })

  it('should clear hasUnsavedChanges after successful save', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })

    expect(result.current.hasUnsavedChanges).toBe(true)

    await act(async () => {
      await result.current.saveDocument()
    })

    expect(result.current.hasUnsavedChanges).toBe(false)
  })

  it('should merge multiple updates before saving', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Multiple rapid updates
    act(() => {
      result.current.updateDocument({ title: 'New Title' })
    })
    act(() => {
      result.current.updateDocument({ markdown: 'New content' })
    })

    await act(async () => {
      await result.current.saveDocument()
    })

    expect(documentsApi.update).toHaveBeenCalledWith('test-doc', {
      title: 'New Title',
      markdown: 'New content',
    })
    expect(documentsApi.update).toHaveBeenCalledTimes(1)
  })

  it('should not save if no pending updates', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Try to save without any updates
    await act(async () => {
      await result.current.saveDocument()
    })

    expect(documentsApi.update).not.toHaveBeenCalled()
  })

  it('should reload document via reloadDocument', async () => {
    const { result } = renderHook(() => useDocument('test-doc'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(documentsApi.get).toHaveBeenCalledTimes(1)

    await act(async () => {
      await result.current.reloadDocument()
    })

    expect(documentsApi.get).toHaveBeenCalledTimes(2)
  })
})
