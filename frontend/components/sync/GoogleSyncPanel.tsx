'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Cloud,
  CloudOff,
  Upload,
  Download,
  RefreshCw,
  AlertTriangle,
  Check,
  Link,
  Unlink,
  X,
  ExternalLink,
} from 'lucide-react'
import {
  googleSyncApi,
  SyncStatus,
  SyncStatusType,
  ResolveStrategy,
} from '@/lib/api'

interface GoogleSyncPanelProps {
  documentSlug: string
  documentType: 'paper' | 'thesis' | 'policy' | 'presentation'
  sourceProvider?: string | null
  sourceId?: string | null
  onSyncComplete?: () => void
}

const STATUS_CONFIG: Record<
  SyncStatusType,
  { color: string; icon: React.ReactNode; label: string }
> = {
  none: {
    color: 'text-muted',
    icon: <CloudOff size={14} />,
    label: 'Not linked',
  },
  synced: {
    color: 'text-c-green',
    icon: <Check size={14} />,
    label: 'Synced',
  },
  local_changed: {
    color: 'text-c-amber',
    icon: <Upload size={14} />,
    label: 'Local changes',
  },
  remote_changed: {
    color: 'text-c-blue',
    icon: <Download size={14} />,
    label: 'Remote changes',
  },
  conflict: {
    color: 'text-c-red',
    icon: <AlertTriangle size={14} />,
    label: 'Conflict',
  },
}

export function GoogleSyncPanel({
  documentSlug,
  documentType,
  sourceProvider,
  sourceId,
  onSyncComplete,
}: GoogleSyncPanelProps) {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showLinkDialog, setShowLinkDialog] = useState(false)
  const [showConflictDialog, setShowConflictDialog] = useState(false)
  const [linkDocId, setLinkDocId] = useState('')
  const [driveUrl, setDriveUrl] = useState<string | null>(null)

  const isPresentation = documentType === 'presentation'

  const fetchStatus = useCallback(async () => {
    if (!documentSlug || documentSlug === 'new') return

    try {
      setLoading(true)
      setError(null)

      const status = isPresentation
        ? await googleSyncApi.getSlidesStatus(documentSlug)
        : await googleSyncApi.getStatus(documentSlug)

      setSyncStatus(status)

      if (status.sync_status === 'conflict') {
        setShowConflictDialog(true)
      }

      // Fetch drive URL if linked
      if (status.linked) {
        try {
          const urlResponse = await googleSyncApi.getDriveUrl(documentSlug)
          setDriveUrl(urlResponse.url)
        } catch {
          setDriveUrl(null)
        }
      } else {
        setDriveUrl(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sync status')
    } finally {
      setLoading(false)
    }
  }, [documentSlug, isPresentation])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  const handleLink = async () => {
    if (!linkDocId.trim()) return

    try {
      setLoading(true)
      setError(null)

      // Extract Google Doc/Slides ID from URL if a full URL was pasted
      let docId = linkDocId.trim()

      // Match both document and presentation URLs
      const docMatch = docId.match(/\/document\/d\/([a-zA-Z0-9_-]+)/)
      const slideMatch = docId.match(/\/presentation\/d\/([a-zA-Z0-9_-]+)/)

      if (docMatch) {
        docId = docMatch[1]
      } else if (slideMatch) {
        docId = slideMatch[1]
      }

      if (isPresentation) {
        await googleSyncApi.linkSlides(documentSlug, docId)
      } else {
        await googleSyncApi.link(documentSlug, docId)
      }

      setShowLinkDialog(false)
      setLinkDocId('')
      await fetchStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link')
    } finally {
      setLoading(false)
    }
  }

  const handleUnlink = async () => {
    const confirmMsg = isPresentation
      ? 'Are you sure you want to unlink this presentation from Google Slides?'
      : 'Are you sure you want to unlink this document from Google Docs?'

    if (!confirm(confirmMsg)) {
      return
    }

    try {
      setLoading(true)
      setError(null)

      if (isPresentation) {
        await googleSyncApi.unlinkSlides(documentSlug)
      } else {
        await googleSyncApi.unlink(documentSlug)
      }

      await fetchStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unlink')
    } finally {
      setLoading(false)
    }
  }

  const handlePush = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = isPresentation
        ? await googleSyncApi.pushSlides(documentSlug)
        : await googleSyncApi.push(documentSlug)

      if (!result.success) {
        setError(result.error || 'Push failed')
        return
      }

      if (result.warnings.length > 0) {
        console.warn('Push warnings:', result.warnings)
      }

      await fetchStatus()
      onSyncComplete?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to push changes')
    } finally {
      setLoading(false)
    }
  }

  const handlePull = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = isPresentation
        ? await googleSyncApi.pullSlides(documentSlug)
        : await googleSyncApi.pull(documentSlug)

      if (!result.success) {
        setError(result.error || 'Pull failed')
        return
      }

      if (result.warnings.length > 0) {
        console.warn('Pull warnings:', result.warnings)
      }

      await fetchStatus()
      onSyncComplete?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pull changes')
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async (strategy: ResolveStrategy) => {
    try {
      setLoading(true)
      setError(null)

      const result = isPresentation
        ? await googleSyncApi.resolveSlides(documentSlug, strategy)
        : await googleSyncApi.resolve(documentSlug, strategy)

      if (!result.success) {
        setError(result.message || 'Failed to resolve conflict')
        return
      }

      setShowConflictDialog(false)
      await fetchStatus()
      onSyncComplete?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve conflict')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenInDrive = () => {
    if (driveUrl) {
      window.open(driveUrl, '_blank', 'noopener,noreferrer')
    }
  }

  const statusConfig = syncStatus
    ? STATUS_CONFIG[syncStatus.sync_status]
    : STATUS_CONFIG.none

  const googleServiceName = isPresentation ? 'Google Slides' : 'Google Docs'
  const linkPlaceholder = isPresentation
    ? 'Google Slides ID or URL'
    : 'Google Doc ID or URL'

  return (
    <div className="relative">
      {/* Sync Status Badge */}
      <div className="flex items-center gap-2">
        <button
          onClick={fetchStatus}
          disabled={loading}
          className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded-md border border-line hover:bg-bg ${statusConfig.color}`}
          title="Click to refresh sync status"
        >
          {loading ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            statusConfig.icon
          )}
          <span>{statusConfig.label}</span>
        </button>

        {/* Action buttons based on status */}
        {syncStatus?.linked && (
          <div className="flex items-center gap-1">
            {/* View in Drive button */}
            {driveUrl && (
              <button
                onClick={handleOpenInDrive}
                className="btn btn-sm text-c-blue"
                title={`Open in ${googleServiceName}`}
              >
                <ExternalLink size={12} />
              </button>
            )}

            {(syncStatus.sync_status === 'local_changed' ||
              syncStatus.sync_status === 'synced') && (
              <button
                onClick={handlePush}
                disabled={loading}
                className="btn btn-sm"
                title={`Push to ${googleServiceName}`}
              >
                <Upload size={12} />
              </button>
            )}
            {(syncStatus.sync_status === 'remote_changed' ||
              syncStatus.sync_status === 'synced') && (
              <button
                onClick={handlePull}
                disabled={loading}
                className="btn btn-sm"
                title={`Pull from ${googleServiceName}`}
              >
                <Download size={12} />
              </button>
            )}
            {syncStatus.sync_status === 'conflict' && (
              <button
                onClick={() => setShowConflictDialog(true)}
                className="btn btn-sm text-c-red"
                title="Resolve conflict"
              >
                <AlertTriangle size={12} />
              </button>
            )}
            <button
              onClick={handleUnlink}
              disabled={loading}
              className="btn btn-sm text-muted hover:text-c-red"
              title={`Unlink from ${googleServiceName}`}
            >
              <Unlink size={12} />
            </button>
          </div>
        )}

        {!syncStatus?.linked && (
          <button
            onClick={() => setShowLinkDialog(true)}
            className="btn btn-sm"
            title={`Link to ${googleServiceName}`}
          >
            <Link size={12} className="mr-1" />
            Link
          </button>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="absolute top-full left-0 mt-1 p-2 text-xs text-c-red bg-paper border border-c-red rounded-md shadow-sm z-10 max-w-xs">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-muted hover:text-ink"
          >
            <X size={12} />
          </button>
        </div>
      )}

      {/* Link Dialog */}
      {showLinkDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper border border-line rounded-lg shadow-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Link to {googleServiceName}</h3>
            <p className="text-sm text-muted mb-4">
              Enter the {googleServiceName} ID or paste the full URL.
            </p>
            <input
              type="text"
              value={linkDocId}
              onChange={(e) => setLinkDocId(e.target.value)}
              placeholder={linkPlaceholder}
              className="input w-full mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowLinkDialog(false)
                  setLinkDocId('')
                }}
                className="btn btn-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleLink}
                disabled={!linkDocId.trim() || loading}
                className="btn btn-sm btn-primary"
              >
                {loading ? 'Linking...' : 'Link'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conflict Resolution Dialog */}
      {showConflictDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-paper border border-line rounded-lg shadow-lg p-6 w-96">
            <div className="flex items-center gap-2 text-c-red mb-4">
              <AlertTriangle size={20} />
              <h3 className="text-lg font-semibold">Sync Conflict</h3>
            </div>
            <p className="text-sm text-muted mb-4">
              Both the local {isPresentation ? 'presentation' : 'document'} and {googleServiceName} have been modified since
              the last sync. Choose how to resolve this conflict:
            </p>
            <div className="space-y-2 mb-4">
              <button
                onClick={() => handleResolve('keep_local')}
                disabled={loading}
                className="w-full flex items-center gap-3 p-3 border border-line rounded-md hover:bg-bg text-left"
              >
                <Upload size={20} className="text-c-amber" />
                <div>
                  <div className="font-medium">Keep Local</div>
                  <div className="text-xs text-muted">
                    Push your local changes to {googleServiceName}, overwriting remote
                    changes
                  </div>
                </div>
              </button>
              <button
                onClick={() => handleResolve('keep_remote')}
                disabled={loading}
                className="w-full flex items-center gap-3 p-3 border border-line rounded-md hover:bg-bg text-left"
              >
                <Download size={20} className="text-c-blue" />
                <div>
                  <div className="font-medium">Keep Remote</div>
                  <div className="text-xs text-muted">
                    Pull {googleServiceName} changes, overwriting local changes
                  </div>
                </div>
              </button>
            </div>
            <button
              onClick={() => setShowConflictDialog(false)}
              className="w-full btn btn-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
