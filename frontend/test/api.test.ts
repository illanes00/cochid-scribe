import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { documentsApi, claimsApi, ApiError } from '@/lib/api'

const mockFetch = global.fetch as ReturnType<typeof vi.fn>

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  describe('documentsApi', () => {
    const mockDocument = {
      id: '123',
      slug: 'test-doc',
      title: 'Test Document',
      doc_type: 'document',
      content: { json: {}, html: '' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    it('should fetch document by slug', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockDocument),
      })

      const result = await documentsApi.get('test-doc')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/documents/test-doc',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockDocument)
    })

    it('should list documents with pagination', async () => {
      const mockList = {
        documents: [mockDocument],
        total: 1,
        page: 1,
        per_page: 20,
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockList),
      })

      const result = await documentsApi.list(1, 20)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/documents?page=1&per_page=20',
        expect.anything()
      )
      expect(result).toEqual(mockList)
    })

    it('should create document with POST', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve(mockDocument),
      })

      const newDoc = { title: 'New Document', doc_type: 'paper' as const }
      const result = await documentsApi.create(newDoc)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/documents',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newDoc),
        })
      )
      expect(result).toEqual(mockDocument)
    })

    it('should update document with PUT', async () => {
      const updatedDoc = { ...mockDocument, title: 'Updated Title' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(updatedDoc),
      })

      const result = await documentsApi.update('test-doc', { title: 'Updated Title' })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/documents/test-doc',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ title: 'Updated Title' }),
        })
      )
      expect(result.title).toBe('Updated Title')
    })

    it('should delete document with DELETE', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.reject('No content'),
      })

      await documentsApi.delete('test-doc')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/documents/test-doc',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should throw ApiError on 404', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Document not found' }),
      })

      await expect(documentsApi.get('nonexistent')).rejects.toThrow('Document not found')
    })

    it('should throw ApiError on 500', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Internal server error' }),
      })

      await expect(documentsApi.get('test-doc')).rejects.toThrow('Internal server error')
    })

    it('should handle malformed error response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.reject('Invalid JSON'),
      })

      await expect(documentsApi.get('test-doc')).rejects.toThrow('Unknown error')
    })

    it('should include status code in ApiError', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      })

      try {
        await documentsApi.get('test-doc')
        expect.fail('Should have thrown')
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect((error as ApiError).status).toBe(401)
        expect((error as ApiError).message).toBe('Unauthorized')
      }
    })
  })

  describe('claimsApi', () => {
    const mockClaim = {
      id: 'claim-123',
      claim_id: 'C-abc123',
      document_id: 'doc-123',
      claim_text: 'Test claim',
      claim_type: 'DATA',
      status: 'draft',
      evidence: [],
      source_sentences: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    it('should fetch claims for document', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve([mockClaim]),
      })

      const result = await claimsApi.listByDocument('test-doc')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/claims/document/test-doc',
        expect.anything()
      )
      expect(result).toEqual([mockClaim])
    })

    it('should update claim status', async () => {
      const updatedClaim = { ...mockClaim, status: 'verified' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(updatedClaim),
      })

      const result = await claimsApi.update('claim-123', { status: 'verified' })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/claims/claim-123',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ status: 'verified' }),
        })
      )
      expect(result.status).toBe('verified')
    })
  })
})
