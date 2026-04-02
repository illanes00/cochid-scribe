'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, BookOpen, CheckCircle, MessageCircle } from 'lucide-react'
import { renderMarkdown } from '@/lib/markdown'

interface ChatPanelProps {
  documentSlug: string
  documentTitle?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

const SYSTEM_CONTEXT_PROMPT = `Eres un asistente de investigación senior especializado en política pública chilena.
Tienes acceso al documento completo, sus claims verificados, la bibliografía, y los comentarios de revisión.
Responde en español. Sé factual, cita evidencia del documento cuando sea relevante.
Cuando el usuario pregunte sobre comentarios de CIF o directores, analiza si la evidencia del documento soporta o contradice el comentario.`

export function ChatPanel({ documentSlug, documentTitle }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState<{
    document?: string
    claims?: number
    comments?: number
    bibliography?: number
  } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadContext()
  }, [documentSlug])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function loadContext() {
    try {
      const [docRes, commentsRes, claimsRes, bibRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/documents/${documentSlug}`).then((r) => r.json()),
        fetch(`${API_BASE}/api/v1/comments/document/${documentSlug}`).then((r) => r.json()),
        fetch(`${API_BASE}/api/v1/claims/document/${documentSlug}`).then((r) => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/v1/bibliography`).then((r) => r.json()).catch(() => []),
      ])

      setContext({
        document: docRes.markdown?.slice(0, 200) + '...',
        claims: claimsRes?.length || docRes.claim_count || 0,
        comments: Array.isArray(commentsRes) ? commentsRes.length : 0,
        bibliography: Array.isArray(bibRes) ? bibRes.length : 0,
      })

      // Add welcome message
      if (messages.length === 0) {
        setMessages([
          {
            id: 'welcome',
            role: 'system',
            content: `Documento cargado: **${docRes.title}**\n\n${Array.isArray(commentsRes) ? commentsRes.length : 0} comentarios · ${docRes.claim_count || 0} claims · ${Array.isArray(bibRes) ? bibRes.length : 0} refs bibliográficas\n\nPregúntame sobre el documento, los comentarios de CIF/directores, o pídeme que analice alguna sección.`,
            timestamp: new Date(),
          },
        ])
      }
    } catch {
      // Context load failed silently
    }
  }

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      // Build context-aware prompt by fetching relevant data
      const [docRes, commentsRes, claimsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/documents/${documentSlug}`).then((r) => r.json()),
        fetch(`${API_BASE}/api/v1/comments/document/${documentSlug}`).then((r) => r.json()),
        fetch(`${API_BASE}/api/v1/claims/document/${documentSlug}`).then((r) => r.json()).catch(() => []),
      ])

      const docMarkdown = docRes.markdown || ''
      const commentsText = Array.isArray(commentsRes)
        ? commentsRes
            .filter((c: { parent_id: string | null }) => !c.parent_id)
            .map((c: { author: string; content: string }, i: number) => `${i + 1}. [${c.author || 'Anon'}]: ${c.content}`)
            .join('\n')
        : ''
      const claimsText = Array.isArray(claimsRes)
        ? claimsRes
            .map((c: { claim_text: string; claim_type: string; status: string }) => `- [${c.claim_type}/${c.status}] ${c.claim_text}`)
            .join('\n')
        : ''

      // Use Claude CLI subprocess endpoint with full document context
      const response = await fetch(`${API_BASE}/api/v1/chat/${documentSlug}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          include_document: true,
          include_comments: true,
          include_claims: true,
          include_bibliography: true,
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Error del servidor')
      }

      const data = await response.json()

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || 'Sin respuesta.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `Error: ${err instanceof Error ? err.message : 'Error desconocido'}. Verifica que la API key de Anthropic esté configurada.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function clearChat() {
    setMessages([])
    loadContext()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with context stats */}
      <div className="px-4 py-3 border-b border-line">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Chat con IA</h3>
          <button onClick={clearChat} className="text-muted hover:text-ink" title="Limpiar chat">
            <Trash2 size={14} />
          </button>
        </div>
        {context && (
          <div className="flex gap-3 mt-1.5 text-[10px] text-muted">
            <span className="flex items-center gap-1">
              <CheckCircle size={10} /> {context.claims} claims
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle size={10} /> {context.comments} comentarios
            </span>
            <span className="flex items-center gap-1">
              <BookOpen size={10} /> {context.bibliography} refs
            </span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`leading-relaxed ${
              msg.role === 'user'
                ? 'bg-bg text-ink p-2.5 ml-6 text-sm'
                : msg.role === 'system'
                  ? 'bg-bg text-muted p-2.5 italic text-xs'
                  : 'text-ink p-2.5 text-sm'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="provider-badge ai mb-1.5">Scribe AI</div>
            )}
            <div className="comment-content" style={{ lineHeight: '1.6' }}>
              {renderMarkdown(msg.content)}
            </div>
            <div className="text-[9px] text-muted mt-1">
              {msg.timestamp.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-xs text-muted animate-pulse p-2.5">
            Analizando con contexto del documento...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-line">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pregunta sobre el documento..."
            rows={2}
            className="flex-1 text-xs p-2 border border-line resize-none bg-paper focus:outline-none focus:border-ink"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="self-end px-3 py-2 bg-ink text-paper hover:opacity-90 disabled:opacity-50"
          >
            <Send size={14} />
          </button>
        </div>
        <div className="text-[9px] text-muted mt-1">
          Enter para enviar · Shift+Enter para nueva línea
        </div>
      </div>
    </div>
  )
}
