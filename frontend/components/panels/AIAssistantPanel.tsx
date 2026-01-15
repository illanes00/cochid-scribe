'use client'

import { useState } from 'react'
import { llmApi } from '@/lib/api'

interface AIAssistantPanelProps {
  selectedText?: string
  onApplyRewrite?: (text: string) => void
}

type AssistantMode = 'rewrite' | 'hedging' | 'claims'

export function AIAssistantPanel({
  selectedText = '',
  onApplyRewrite,
}: AIAssistantPanelProps) {
  const [mode, setMode] = useState<AssistantMode>('rewrite')
  const [instruction, setInstruction] = useState('')
  const [tone, setTone] = useState('academic')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    original?: string
    rewritten?: string
    improved?: string
    changes?: string[]
    claims?: Record<string, unknown>[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit() {
    if (!selectedText.trim()) {
      setError('Please select some text in the editor first')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      switch (mode) {
        case 'rewrite': {
          if (!instruction.trim()) {
            setError('Please enter an instruction')
            setLoading(false)
            return
          }
          const response = await llmApi.rewrite({
            text: selectedText,
            instruction,
            tone,
          })
          setResult(response)
          break
        }
        case 'hedging': {
          const response = await llmApi.improveHedging(selectedText)
          setResult(response)
          break
        }
        case 'claims': {
          const response = await llmApi.extractClaims(selectedText)
          setResult({ claims: response.claims })
          break
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  function handleApply() {
    if (!result) return
    const text = result.rewritten || result.improved
    if (text && onApplyRewrite) {
      onApplyRewrite(text)
      setResult(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <h2 className="font-medium text-ink">AI Assistant</h2>
        <p className="text-sm text-muted mt-1">
          Powered by Claude
        </p>
      </div>

      {/* Mode Selector */}
      <div className="p-2 border-b border-line flex gap-1">
        {[
          { id: 'rewrite', label: 'Rewrite' },
          { id: 'hedging', label: 'Hedging' },
          { id: 'claims', label: 'Extract Claims' },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setMode(m.id as AssistantMode)
              setResult(null)
              setError(null)
            }}
            className={`px-2 py-1 text-xs rounded ${
              mode === m.id
                ? 'bg-ink text-paper'
                : 'text-muted hover:bg-bg'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Input Section */}
      <div className="p-3 border-b border-line">
        {/* Selected Text Preview */}
        <div className="mb-3">
          <label className="text-xs text-muted block mb-1">
            Selected Text
          </label>
          <div className="p-2 bg-bg text-sm text-ink max-h-24 overflow-y-auto">
            {selectedText || (
              <span className="text-muted italic">
                Select text in the editor...
              </span>
            )}
          </div>
        </div>

        {/* Mode-specific inputs */}
        {mode === 'rewrite' && (
          <>
            <div className="mb-3">
              <label className="text-xs text-muted block mb-1">
                Instruction
              </label>
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="e.g., Make it more concise, Add more detail, Simplify the language..."
                className="w-full p-2 text-sm border border-line bg-paper resize-none h-20 focus:outline-none focus:border-ink"
              />
            </div>
            <div className="mb-3">
              <label className="text-xs text-muted block mb-1">
                Tone
              </label>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full p-2 text-sm border border-line bg-paper focus:outline-none focus:border-ink"
              >
                <option value="academic">Academic</option>
                <option value="formal">Formal</option>
                <option value="casual">Casual</option>
                <option value="technical">Technical</option>
              </select>
            </div>
          </>
        )}

        {mode === 'hedging' && (
          <p className="text-xs text-muted">
            Improves hedging by replacing absolute statements with tentative
            language, adding qualifiers, and using passive voice where
            appropriate.
          </p>
        )}

        {mode === 'claims' && (
          <p className="text-xs text-muted">
            Extracts verifiable claims from the text, identifying the type
            (DATA, LITERATURE, MIXED, HYPOTHESIS) and what evidence would
            verify each claim.
          </p>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading || !selectedText.trim()}
          className="w-full mt-3 py-2 text-sm bg-ink text-paper hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Processing...' : mode === 'claims' ? 'Extract Claims' : 'Generate'}
        </button>
      </div>

      {/* Results Section */}
      <div className="flex-1 overflow-y-auto p-3">
        {error && (
          <div className="p-3 mb-3 bg-c-red/10 text-c-red text-sm">
            {error}
          </div>
        )}

        {result && (
          <div>
            {/* Rewrite/Hedging Result */}
            {(result.rewritten || result.improved) && (
              <>
                <div className="mb-3">
                  <label className="text-xs text-muted block mb-1">
                    Result
                  </label>
                  <div className="p-2 bg-bg text-sm text-ink">
                    {result.rewritten || result.improved}
                  </div>
                </div>

                {result.changes && result.changes.length > 0 && (
                  <div className="mb-3">
                    <label className="text-xs text-muted block mb-1">
                      Changes Made
                    </label>
                    <ul className="text-xs text-muted space-y-1">
                      {result.changes.map((change, i) => (
                        <li key={i}>• {change}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={handleApply}
                  className="w-full py-2 text-sm border border-c-green text-c-green hover:bg-c-green/10"
                >
                  Apply to Document
                </button>
              </>
            )}

            {/* Claims Result */}
            {result.claims && (
              <div>
                <label className="text-xs text-muted block mb-2">
                  Extracted Claims ({result.claims.length})
                </label>
                <ul className="space-y-2">
                  {result.claims.map((claim, i) => (
                    <li key={i} className="p-2 bg-bg text-xs">
                      <p className="text-ink font-medium">
                        {String(claim.claim_text || claim.text || '')}
                      </p>
                      <div className="flex gap-2 mt-1">
                        <span className="text-c-blue">
                          {String(claim.claim_type || claim.type || 'MIXED')}
                        </span>
                        {claim.evidence_needed ? (
                          <span className="text-muted">
                            Needs: {String(claim.evidence_needed)}
                          </span>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default AIAssistantPanel
