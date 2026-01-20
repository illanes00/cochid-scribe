'use client'

import { useState, useEffect, useCallback } from 'react'
import { Check, X, Clock, CheckCircle, XCircle, RefreshCw, Filter } from 'lucide-react'
import { TrackChange, TrackChangesListResponse, ChangeStatus, trackChangesApi } from '@/lib/api'

interface TrackChangesPanelProps {
  documentSlug: string
  onChangeResolved?: () => void
}

export function TrackChangesPanel({ documentSlug, onChangeResolved }: TrackChangesPanelProps) {
  const [data, setData] = useState<TrackChangesListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<ChangeStatus | 'all'>('all')
  const [resolving, setResolving] = useState<string | null>(null)

  const loadChanges = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const status = statusFilter === 'all' ? undefined : statusFilter
      const result = await trackChangesApi.list(documentSlug, status)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load changes')
    } finally {
      setLoading(false)
    }
  }, [documentSlug, statusFilter])

  useEffect(() => {
    loadChanges()
  }, [loadChanges])

  const handleResolve = async (changeId: string, action: 'accept' | 'reject') => {
    setResolving(changeId)
    try {
      await trackChangesApi.resolve(documentSlug, changeId, action)
      await loadChanges()
      onChangeResolved?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve change')
    } finally {
      setResolving(null)
    }
  }

  const handleAcceptAll = async () => {
    if (!confirm('Accept all pending changes?')) return
    setLoading(true)
    try {
      await trackChangesApi.acceptAll(documentSlug)
      await loadChanges()
      onChangeResolved?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept all changes')
    } finally {
      setLoading(false)
    }
  }

  const handleRejectAll = async () => {
    if (!confirm('Reject all pending changes?')) return
    setLoading(true)
    try {
      await trackChangesApi.rejectAll(documentSlug)
      await loadChanges()
      onChangeResolved?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject all changes')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: ChangeStatus) => {
    switch (status) {
      case 'pending':
        return <Clock size={14} className="text-c-amber" />
      case 'accepted':
        return <CheckCircle size={14} className="text-c-green" />
      case 'rejected':
        return <XCircle size={14} className="text-c-red" />
    }
  }

  const getChangeTypeStyle = (type: string) => {
    return type === 'insert'
      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
      : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 line-through'
  }

  if (loading && !data) {
    return (
      <div className="p-4 text-center text-muted">
        <RefreshCw size={20} className="animate-spin mx-auto mb-2" />
        Loading changes...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-c-red text-sm mb-2">{error}</div>
        <button onClick={loadChanges} className="btn btn-sm">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-sm">Track Changes</h3>
          <button onClick={loadChanges} className="p-1 hover:bg-bg rounded" title="Refresh">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Status counts */}
        {data && (
          <div className="flex gap-3 text-xs text-muted">
            <span className="flex items-center gap-1">
              <Clock size={12} className="text-c-amber" />
              {data.pending_count} pending
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle size={12} className="text-c-green" />
              {data.accepted_count} accepted
            </span>
            <span className="flex items-center gap-1">
              <XCircle size={12} className="text-c-red" />
              {data.rejected_count} rejected
            </span>
          </div>
        )}
      </div>

      {/* Filter */}
      <div className="p-2 border-b border-line flex items-center gap-2">
        <Filter size={14} className="text-muted" />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ChangeStatus | 'all')}
          className="input text-xs py-1 flex-1"
        >
          <option value="all">All changes</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Bulk actions */}
      {data && data.pending_count > 0 && (
        <div className="p-2 border-b border-line flex gap-2">
          <button
            onClick={handleAcceptAll}
            className="btn btn-sm btn-success flex-1 text-xs"
            disabled={loading}
          >
            <Check size={12} className="mr-1" />
            Accept All
          </button>
          <button
            onClick={handleRejectAll}
            className="btn btn-sm btn-danger flex-1 text-xs"
            disabled={loading}
          >
            <X size={12} className="mr-1" />
            Reject All
          </button>
        </div>
      )}

      {/* Changes list */}
      <div className="flex-1 overflow-auto">
        {data?.changes.length === 0 ? (
          <div className="p-4 text-center text-muted text-sm">
            No tracked changes
          </div>
        ) : (
          <div className="divide-y divide-line">
            {data?.changes.map((change) => (
              <div key={change.change_id} className="p-3 hover:bg-bg/50">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(change.status)}
                    <span className="text-xs font-medium uppercase">
                      {change.change_type}
                    </span>
                  </div>
                  <span className="text-xs text-muted">
                    {new Date(change.created_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Content preview */}
                {change.content && (
                  <div
                    className={`text-sm px-2 py-1 rounded mt-1 ${getChangeTypeStyle(change.change_type)}`}
                  >
                    {change.content.length > 100
                      ? `${change.content.substring(0, 100)}...`
                      : change.content}
                  </div>
                )}

                {/* Author */}
                {change.author_name && (
                  <div className="text-xs text-muted mt-1">
                    by {change.author_name}
                  </div>
                )}

                {/* Resolution info */}
                {change.status !== 'pending' && change.resolved_at && (
                  <div className="text-xs text-muted mt-1">
                    {change.status === 'accepted' ? 'Accepted' : 'Rejected'}{' '}
                    {change.resolved_by && `by ${change.resolved_by}`}{' '}
                    on {new Date(change.resolved_at).toLocaleDateString()}
                  </div>
                )}

                {/* Actions for pending changes */}
                {change.status === 'pending' && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => handleResolve(change.change_id, 'accept')}
                      className="btn btn-xs btn-success"
                      disabled={resolving === change.change_id}
                    >
                      <Check size={12} className="mr-1" />
                      Accept
                    </button>
                    <button
                      onClick={() => handleResolve(change.change_id, 'reject')}
                      className="btn btn-xs btn-danger"
                      disabled={resolving === change.change_id}
                    >
                      <X size={12} className="mr-1" />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
