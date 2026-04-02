'use client'

import { useState, useEffect } from 'react'
import {
  ReviewAnalysis,
  ReviewCommentResponse,
  ReviewStatus,
  ApplyItem,
  reviewApi,
  commentsApi,
} from '@/lib/api'
import { renderMarkdown } from '@/lib/markdown'

interface ReviewPanelProps {
  documentSlug: string
  sourceProvider?: string | null
}

const RESPONSE_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  agree: { label: 'De acuerdo', color: 'text-green-700 bg-green-50' },
  partial: { label: 'Parcial', color: 'text-yellow-700 bg-yellow-50' },
  disagree: { label: 'No concuerda', color: 'text-red-700 bg-red-50' },
  clarification: { label: 'Aclaración', color: 'text-blue-700 bg-blue-50' },
  editorial: { label: 'Editorial', color: 'text-gray-700 bg-gray-50' },
}

type Step = 'status' | 'analyzing' | 'review' | 'applying' | 'done'

export function ReviewPanel({ documentSlug, sourceProvider }: ReviewPanelProps) {
  const [step, setStep] = useState<Step>('status')
  const [status, setStatus] = useState<ReviewStatus | null>(null)
  const [analysis, setAnalysis] = useState<ReviewAnalysis | null>(null)
  const [approvals, setApprovals] = useState<Record<string, boolean>>({})
  const [editedResponses, setEditedResponses] = useState<Record<string, string>>({})
  const [pushToGoogle, setPushToGoogle] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<{ applied_replies: number; applied_edits: number; errors: string[] } | null>(null)

  useEffect(() => {
    loadStatus()
  }, [documentSlug])

  async function loadStatus() {
    try {
      setLoading(true)
      setError(null)
      const data = await reviewApi.status(documentSlug)
      setStatus(data)
      setStep('status')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load status')
    } finally {
      setLoading(false)
    }
  }

  async function handleSyncComments() {
    try {
      setSyncing(true)
      setError(null)
      await commentsApi.syncGoogle(documentSlug)
      await loadStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  async function handleAnalyze() {
    try {
      setStep('analyzing')
      setError(null)
      const data = await reviewApi.analyze(documentSlug)
      setAnalysis(data)

      // Default: approve all, push to Google if linked
      const defaults: Record<string, boolean> = {}
      const googleDefaults: Record<string, boolean> = {}
      for (const r of data.responses) {
        defaults[r.comment_id] = true
        googleDefaults[r.comment_id] = status?.has_google_link ?? false
      }
      setApprovals(defaults)
      setPushToGoogle(googleDefaults)
      setEditedResponses({})
      setStep('review')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setStep('status')
    }
  }

  async function handleApply() {
    if (!analysis) return
    try {
      setStep('applying')
      setError(null)

      const items: ApplyItem[] = analysis.responses
        .filter((r) => approvals[r.comment_id])
        .map((r) => ({
          comment_id: r.comment_id,
          response_text: editedResponses[r.comment_id] || r.response_text,
          apply_edit: !!r.suggested_edit,
          push_to_google: pushToGoogle[r.comment_id] ?? false,
        }))

      const data = await reviewApi.apply(documentSlug, items)
      setResult(data)
      setStep('done')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Apply failed')
      setStep('review')
    }
  }

  function toggleApproval(commentId: string) {
    setApprovals((prev) => ({ ...prev, [commentId]: !prev[commentId] }))
  }

  function toggleGooglePush(commentId: string) {
    setPushToGoogle((prev) => ({ ...prev, [commentId]: !prev[commentId] }))
  }

  function updateResponse(commentId: string, text: string) {
    setEditedResponses((prev) => ({ ...prev, [commentId]: text }))
  }

  if (loading && step === 'status') {
    return <div className="p-4 text-sm text-muted">Cargando estado...</div>
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-line">
        <h3 className="text-sm font-semibold">AI Review & Respond</h3>
        {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Step 1: Status */}
        {step === 'status' && status && (
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-bg">
                <div className="text-2xl font-bold">{status.pending_comments}</div>
                <div className="text-xs text-muted">Pendientes</div>
              </div>
              <div className="p-3 bg-bg">
                <div className="text-2xl font-bold">{status.resolved_comments}</div>
                <div className="text-xs text-muted">Resueltos</div>
              </div>
            </div>

            {sourceProvider === 'google' && (
              <button
                onClick={handleSyncComments}
                disabled={syncing}
                className="w-full px-3 py-2 text-sm bg-bg border border-line hover:bg-line/30 disabled:opacity-50"
              >
                {syncing ? 'Sincronizando...' : 'Sync comentarios de Google'}
              </button>
            )}

            {status.pending_comments > 0 ? (
              <button
                onClick={handleAnalyze}
                className="w-full px-3 py-2 text-sm font-medium bg-ink text-paper hover:opacity-90"
              >
                Analizar {status.pending_comments} comentarios con IA
              </button>
            ) : (
              <p className="text-sm text-muted text-center py-4">
                No hay comentarios pendientes.
              </p>
            )}
          </div>
        )}

        {/* Step 2: Analyzing */}
        {step === 'analyzing' && (
          <div className="p-4 text-center space-y-3">
            <div className="animate-pulse text-sm text-muted">
              Analizando comentarios con IA...
            </div>
            <div className="text-xs text-muted">
              Generando respuestas factuales y argumentadas.
              <br />
              Esto puede tomar 30-60 segundos.
            </div>
          </div>
        )}

        {/* Step 3: Review responses */}
        {step === 'review' && analysis && (
          <div className="divide-y divide-line">
            {/* Summary */}
            {analysis.summary && (
              <div className="p-4 bg-blue-50">
                <div className="text-xs font-semibold text-blue-800 mb-1">Resumen</div>
                <p className="text-xs text-blue-900">{analysis.summary}</p>
              </div>
            )}

            {/* Each response */}
            {analysis.responses.map((r, idx) => (
              <ResponseCard
                key={r.comment_id}
                index={idx + 1}
                response={r}
                approved={approvals[r.comment_id] ?? true}
                pushGoogle={pushToGoogle[r.comment_id] ?? false}
                editedText={editedResponses[r.comment_id]}
                hasGoogleLink={status?.has_google_link ?? false}
                onToggleApproval={() => toggleApproval(r.comment_id)}
                onToggleGoogle={() => toggleGooglePush(r.comment_id)}
                onUpdateResponse={(text) => updateResponse(r.comment_id, text)}
              />
            ))}
          </div>
        )}

        {/* Step 4: Applying */}
        {step === 'applying' && (
          <div className="p-4 text-center space-y-3">
            <div className="animate-pulse text-sm text-muted">
              Aplicando respuestas...
            </div>
          </div>
        )}

        {/* Step 5: Done */}
        {step === 'done' && result && (
          <div className="p-4 space-y-4">
            <div className="p-3 border-l-3 border-l-c-green bg-bg">
              <div className="text-sm font-medium text-green-800">Completado</div>
              <div className="text-xs text-green-700 mt-1">
                {result.applied_edits} respuestas aplicadas
                {result.applied_replies > 0 && `, ${result.applied_replies} enviadas a Google Docs`}
              </div>
            </div>
            {result.errors.length > 0 && (
              <div className="p-3 border-l-3 border-l-c-red bg-bg">
                <div className="text-xs font-medium text-red-800">Errores:</div>
                {result.errors.map((e, i) => (
                  <div key={i} className="text-xs text-red-700">{e}</div>
                ))}
              </div>
            )}
            <button
              onClick={loadStatus}
              className="w-full px-3 py-2 text-sm bg-bg border border-line hover:bg-line/30"
            >
              Volver al estado
            </button>
          </div>
        )}
      </div>

      {/* Bottom action bar */}
      {step === 'review' && analysis && (
        <div className="px-4 py-3 border-t border-line bg-paper">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted">
              {Object.values(approvals).filter(Boolean).length}/{analysis.responses.length} aprobadas
            </span>
            <button
              onClick={() => setStep('status')}
              className="text-xs text-muted hover:text-ink"
            >
              Cancelar
            </button>
          </div>
          <button
            onClick={handleApply}
            disabled={Object.values(approvals).filter(Boolean).length === 0}
            className="w-full px-3 py-2 text-sm font-medium bg-ink text-paper hover:opacity-90 disabled:opacity-50"
          >
            Aplicar respuestas aprobadas
          </button>
        </div>
      )}
    </div>
  )
}

// ── Response Card ──────────────────────────────────────────

interface ResponseCardProps {
  index: number
  response: ReviewCommentResponse
  approved: boolean
  pushGoogle: boolean
  editedText?: string
  hasGoogleLink: boolean
  onToggleApproval: () => void
  onToggleGoogle: () => void
  onUpdateResponse: (text: string) => void
}

function ResponseCard({
  index,
  response,
  approved,
  pushGoogle,
  editedText,
  hasGoogleLink,
  onToggleApproval,
  onToggleGoogle,
  onUpdateResponse,
}: ResponseCardProps) {
  const [editing, setEditing] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const typeInfo = RESPONSE_TYPE_LABELS[response.response_type] || RESPONSE_TYPE_LABELS.clarification

  return (
    <div className={`p-3 ${approved ? '' : 'opacity-50'}`}>
      {/* Comment header */}
      <div className="flex items-start gap-2 mb-2">
        <input
          type="checkbox"
          checked={approved}
          onChange={onToggleApproval}
          className="mt-1 flex-shrink-0"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium">#{index}</span>
            <span className={`text-[10px] px-1.5 py-0.5 border border-line ${typeInfo.color}`}>
              {typeInfo.label}
            </span>
            {response.comment_author && (
              <span className="text-[10px] text-muted">{response.comment_author}</span>
            )}
          </div>

          {/* Original comment */}
          <div className="comment-bubble mb-2">
            <div className="comment-content text-sm text-ink">
              {renderMarkdown(
                response.comment_content.length > 250
                  ? response.comment_content.slice(0, 250) + '...'
                  : response.comment_content,
              )}
            </div>
          </div>

          {/* AI response */}
          {editing ? (
            <textarea
              value={editedText ?? response.response_text}
              onChange={(e) => onUpdateResponse(e.target.value)}
              rows={4}
              className="w-full text-xs p-2 border border-line resize-y bg-paper"
            />
          ) : (
            <div
              className="comment-content text-sm cursor-pointer hover:bg-bg p-1"
              onClick={() => setEditing(true)}
              title="Click para editar"
            >
              {renderMarkdown(
                (editedText ?? response.response_text).length > 200 && !expanded
                  ? (editedText ?? response.response_text).slice(0, 200) + '...'
                  : editedText ?? response.response_text,
              )}
            </div>
          )}

          <div className="flex flex-row items-center gap-3 mt-1">
            {editing && (
              <button
                onClick={() => setEditing(false)}
                className="text-[10px] text-c-blue"
              >
                Listo
              </button>
            )}

            {(editedText ?? response.response_text).length > 200 && !editing && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-[10px] text-muted hover:text-ink"
              >
                {expanded ? 'Menos' : 'Mas'}
              </button>
            )}
          </div>

          {/* Suggested edit */}
          {response.suggested_edit && (
            <div className="mt-2 p-2 bg-bg text-[10px] space-y-1">
              <div className="font-medium">Edición sugerida:</div>
              <div className="text-red-700 line-through">
                {response.suggested_edit.original_text.slice(0, 100)}
                {response.suggested_edit.original_text.length > 100 && '...'}
              </div>
              <div className="text-green-700">
                {response.suggested_edit.replacement_text.slice(0, 100)}
                {response.suggested_edit.replacement_text.length > 100 && '...'}
              </div>
              <div className="text-muted italic">{response.suggested_edit.rationale}</div>
            </div>
          )}

          {/* Google push toggle */}
          {hasGoogleLink && approved && (
            <label className="flex items-center gap-1.5 mt-2 text-[10px] text-muted cursor-pointer">
              <input
                type="checkbox"
                checked={pushGoogle}
                onChange={onToggleGoogle}
                className="scale-75"
              />
              Enviar a Google Docs
            </label>
          )}
        </div>
      </div>
    </div>
  )
}
