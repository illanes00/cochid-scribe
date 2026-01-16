'use client'

import { useEffect, useState } from 'react'
import { DocumentVersion, DocumentVersionDetail, versionsApi } from '@/lib/api'

interface VersionsPanelProps {
  documentSlug: string
  onRestore?: () => void
  currentMarkdown?: string
}

interface DiffLine {
  left: string
  right: string
  status: 'same' | 'add' | 'remove'
}

export function VersionsPanel({ documentSlug, onRestore, currentMarkdown = '' }: VersionsPanelProps) {
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [restoring, setRestoring] = useState<string | null>(null)
  const [diffVersion, setDiffVersion] = useState<DocumentVersionDetail | null>(null)
  const [diffLines, setDiffLines] = useState<DiffLine[]>([])

  const loadVersions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await versionsApi.list(documentSlug)
      setVersions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!documentSlug || documentSlug === 'new') {
      setLoading(false)
      return
    }
    loadVersions()
  }, [documentSlug])

  const handleCreate = async () => {
    const label = window.prompt('Version label (optional)')
    try {
      setCreating(true)
      await versionsApi.create(documentSlug, { label: label || undefined })
      await loadVersions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create version')
    } finally {
      setCreating(false)
    }
  }

  const handleRestore = async (versionId: string) => {
    if (!confirm('Restore this version? Current changes will be overwritten.')) return
    try {
      setRestoring(versionId)
      await versionsApi.restore(documentSlug, versionId)
      await loadVersions()
      onRestore?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore version')
    } finally {
      setRestoring(null)
    }
  }

  const handleDiff = async (versionId: string) => {
    try {
      setError(null)
      const detail = await versionsApi.get(documentSlug, versionId)
      setDiffVersion(detail)
      const left = (detail.markdown || '').split('\n')
      const right = (currentMarkdown || '').split('\n')
      setDiffLines(buildDiff(left, right))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load diff')
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-ink">Versions</h2>
          <button className="btn btn-sm" onClick={handleCreate} disabled={creating}>
            {creating ? 'Saving...' : 'Save snapshot'}
          </button>
        </div>
        {error && <div className="text-xs text-c-red mt-2">{error}</div>}
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-muted">Loading versions...</div>
        ) : versions.length === 0 ? (
          <div className="p-4 text-center text-muted">No snapshots yet</div>
        ) : (
          <ul className="divide-y divide-line">
            {versions.map((version) => (
              <li key={version.id} className="p-3 flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm text-ink">
                    {version.label || 'Untitled snapshot'}
                  </div>
                  <div className="text-xs text-muted">
                    {new Date(version.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="btn btn-sm"
                    onClick={() => handleDiff(version.id)}
                  >
                    Diff
                  </button>
                  <button
                    className="btn btn-sm"
                    onClick={() => handleRestore(version.id)}
                    disabled={restoring === version.id}
                  >
                    {restoring === version.id ? 'Restoring...' : 'Restore'}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {diffVersion && (
        <div className="border-t border-line bg-paper">
          <div className="p-3 flex items-center justify-between">
            <div className="text-xs text-muted">
              Diff: {diffVersion.label || 'Snapshot'} → Current
            </div>
            <button className="text-xs underline" onClick={() => setDiffVersion(null)}>
              Close
            </button>
          </div>
          <div className="diff-grid">
            <div className="diff-col">
              <div className="diff-title">Snapshot</div>
              <div className="diff-body">
                {diffLines.map((line, idx) => (
                  <div
                    key={`left-${idx}`}
                    className={`diff-line ${
                      line.status === 'remove' ? 'diff-removed' : line.status === 'same' ? '' : 'diff-muted'
                    }`}
                  >
                    {line.left || ' '}
                  </div>
                ))}
              </div>
            </div>
            <div className="diff-col">
              <div className="diff-title">Current</div>
              <div className="diff-body">
                {diffLines.map((line, idx) => (
                  <div
                    key={`right-${idx}`}
                    className={`diff-line ${
                      line.status === 'add' ? 'diff-added' : line.status === 'same' ? '' : 'diff-muted'
                    }`}
                  >
                    {line.right || ' '}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function buildDiff(left: string[], right: string[]): DiffLine[] {
  const maxCells = 200000
  if (left.length * right.length > maxCells) {
    const max = Math.max(left.length, right.length)
    const lines: DiffLine[] = []
    for (let i = 0; i < max; i += 1) {
      const l = left[i] ?? ''
      const r = right[i] ?? ''
      lines.push({
        left: l,
        right: r,
        status: l === r ? 'same' : l ? 'remove' : 'add',
      })
    }
    return lines
  }

  const dp: number[][] = Array.from({ length: left.length + 1 }, () =>
    Array(right.length + 1).fill(0)
  )

  for (let i = left.length - 1; i >= 0; i -= 1) {
    for (let j = right.length - 1; j >= 0; j -= 1) {
      if (left[i] === right[j]) {
        dp[i][j] = dp[i + 1][j + 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
      }
    }
  }

  const lines: DiffLine[] = []
  let i = 0
  let j = 0
  while (i < left.length && j < right.length) {
    if (left[i] === right[j]) {
      lines.push({ left: left[i], right: right[j], status: 'same' })
      i += 1
      j += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      lines.push({ left: left[i], right: '', status: 'remove' })
      i += 1
    } else {
      lines.push({ left: '', right: right[j], status: 'add' })
      j += 1
    }
  }

  while (i < left.length) {
    lines.push({ left: left[i], right: '', status: 'remove' })
    i += 1
  }
  while (j < right.length) {
    lines.push({ left: '', right: right[j], status: 'add' })
    j += 1
  }

  return lines
}

export default VersionsPanel
