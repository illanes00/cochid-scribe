'use client'

import { useCallback, useEffect, useState } from 'react'
import { Claim, claimsApi, llmApi } from '@/lib/api'

interface ClaimsPanelProps {
  documentSlug: string
  onClaimClick?: (
    claimId: string,
    claimText?: string,
    startOffset?: number | null,
    endOffset?: number | null
  ) => void
  activeClaimId?: string | null
}

const claimTypeColors: Record<string, string> = {
  DATA: 'bg-blue-100 text-blue-800',
  LITERATURE: 'bg-purple-100 text-purple-800',
  MIXED: 'bg-amber-100 text-amber-800',
  HYPOTHESIS: 'bg-green-100 text-green-800',
}

const statusIcons: Record<string, string> = {
  draft: '○',
  verified: '✓',
  rejected: '✗',
  needs_revision: '⟳',
}

const statusColors: Record<string, string> = {
  draft: 'text-muted',
  verified: 'text-c-green',
  rejected: 'text-c-red',
  needs_revision: 'text-c-amber',
}

export function ClaimsPanel({
  documentSlug,
  onClaimClick,
  activeClaimId = null,
}: ClaimsPanelProps) {
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [extracting, setExtracting] = useState(false)
  const [extractError, setExtractError] = useState<string | null>(null)

  const loadClaims = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await claimsApi.listByDocument(documentSlug)
      setClaims(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims')
    } finally {
      setLoading(false)
    }
  }, [documentSlug])

  useEffect(() => {
    loadClaims()
  }, [loadClaims])

  async function handleVerify(claimId: string) {
    try {
      const updated = await claimsApi.verify(claimId)
      setClaims((prev) =>
        prev.map((c) => (c.claim_id === claimId ? updated : c))
      )
    } catch (err) {
      console.error('Failed to verify claim:', err)
    }
  }

  async function handleDelete(claimId: string) {
    if (!confirm('Delete this claim?')) return
    try {
      await claimsApi.delete(claimId)
      setClaims((prev) => prev.filter((c) => c.claim_id !== claimId))
    } catch (err) {
      console.error('Failed to delete claim:', err)
    }
  }

  async function handleExtractClaims() {
    try {
      if (!documentSlug || documentSlug === 'new') return
      setExtracting(true)
      setExtractError(null)
      await llmApi.extractClaimsForDocument(documentSlug)
      await loadClaims()
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Failed to extract claims')
    } finally {
      setExtracting(false)
    }
  }

  const filteredClaims =
    filter === 'all'
      ? claims
      : claims.filter((c) => c.status === filter)

  const stats = {
    total: claims.length,
    verified: claims.filter((c) => c.status === 'verified').length,
    draft: claims.filter((c) => c.status === 'draft').length,
    rejected: claims.filter((c) => c.status === 'rejected').length,
  }

  if (loading) {
    return (
      <div className="p-4 text-muted">
        Loading claims...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-c-red">
        {error}
        <button onClick={loadClaims} className="ml-2 underline">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <h2 className="font-medium text-ink">Claims</h2>
        <div className="flex gap-2 mt-2 text-sm">
          <span className="text-c-green">{stats.verified} verified</span>
          <span className="text-muted">·</span>
          <span className="text-muted">{stats.draft} draft</span>
          <span className="text-muted">·</span>
          <span className="text-c-red">{stats.rejected} rejected</span>
        </div>
        {extractError && (
          <div className="text-xs text-c-red mt-2">{extractError}</div>
        )}
      </div>

      {/* Filter */}
      <div className="p-2 border-b border-line flex gap-1">
        {['all', 'draft', 'verified', 'rejected'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-1 text-xs rounded ${
              filter === f
                ? 'bg-ink text-paper'
                : 'text-muted hover:bg-bg'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Claims List */}
      <div className="flex-1 overflow-y-auto">
        {filteredClaims.length === 0 ? (
          <div className="p-4 text-center text-muted">
            No claims found
          </div>
        ) : (
          <ul className="divide-y divide-line">
            {filteredClaims.map((claim) => (
              <li
                key={claim.claim_id}
                className={`p-3 hover:bg-bg cursor-pointer ${
                  claim.claim_id === activeClaimId
                    ? 'bg-blue-50 border-l-2 border-blue-500'
                    : ''
                }`}
                onClick={() => {
                  onClaimClick?.(
                    claim.claim_id,
                    claim.claim_text,
                    claim.start_offset ?? null,
                    claim.end_offset ?? null
                  )
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-lg ${statusColors[claim.status]}`}
                        title={claim.status}
                      >
                        {statusIcons[claim.status]}
                      </span>
                      <span className="text-xs text-muted font-mono">
                        {claim.claim_id}
                      </span>
                    </div>
                    <p className="text-sm text-ink line-clamp-2">
                      {claim.claim_text}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          claimTypeColors[claim.claim_type]
                        }`}
                      >
                        {claim.claim_type}
                      </span>
                      {claim.section && (
                        <span className="text-xs text-muted">
                          {claim.section}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-2">
                  {claim.status === 'draft' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleVerify(claim.claim_id)
                      }}
                      className="text-xs text-c-green hover:underline"
                    >
                      Verify
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(claim.claim_id)
                    }}
                    className="text-xs text-c-red hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add Claim Button */}
      <div className="p-3 border-t border-line">
        <div className="flex flex-col gap-2">
          <button
            className="w-full py-2 text-sm text-center border border-line hover:bg-bg"
            onClick={handleExtractClaims}
            disabled={extracting}
          >
            {extracting ? 'Extracting...' : 'Extract Claims'}
          </button>
          <button className="w-full py-2 text-sm text-center border border-line hover:bg-bg">
            + Add Claim
          </button>
        </div>
      </div>
    </div>
  )
}

export default ClaimsPanel
