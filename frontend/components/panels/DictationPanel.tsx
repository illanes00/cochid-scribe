'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Mic, PauseCircle, ClipboardPaste, FileUp, RefreshCw, Waves, Wand2 } from 'lucide-react'
import { dictationApi, DictationSession } from '@/lib/api'

interface DictationPanelProps {
  documentSlug: string
  onInsertText?: (text: string) => void
  showCanvas?: boolean
}

const STORAGE_PREFIX = 'scribe-dictation-session'

export function DictationPanel({
  documentSlug,
  onInsertText,
  showCanvas = true,
}: DictationPanelProps) {
  const canInsert = typeof onInsertText === 'function'
  const [session, setSession] = useState<DictationSession | null>(null)
  const [recording, setRecording] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastChunk, setLastChunk] = useState('')
  const [canvasText, setCanvasText] = useState('')
  const [autoAppend, setAutoAppend] = useState(true)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunkCounterRef = useRef(0)
  const sessionSlugRef = useRef<string | null>(null)

  useEffect(() => {
    const storageKey = `${STORAGE_PREFIX}:${documentSlug}`
    const existingSlug = typeof window !== 'undefined' ? localStorage.getItem(storageKey) : null

    async function bootstrap() {
      try {
        setBusy(true)
        if (existingSlug) {
          const existing = await dictationApi.getSession(existingSlug)
          setSession(existing)
          sessionSlugRef.current = existing.slug
          chunkCounterRef.current = existing.chunk_count
          return
        }

        const created = await dictationApi.createSession(documentSlug)
        setSession(created)
        sessionSlugRef.current = created.slug
        chunkCounterRef.current = created.chunk_count
        if (typeof window !== 'undefined') {
          localStorage.setItem(storageKey, created.slug)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'No se pudo iniciar el dictado')
      } finally {
        setBusy(false)
      }
    }

    bootstrap()

    return () => {
      stopRecording()
    }
  }, [documentSlug])

  async function uploadChunk(blob: Blob) {
    if (!sessionSlugRef.current) return

    const chunkIndex = chunkCounterRef.current + 1
    chunkCounterRef.current = chunkIndex
    setBusy(true)
    setError(null)

    try {
      const file = new File([blob], `chunk-${chunkIndex}.webm`, { type: blob.type || 'audio/webm' })
      const response = await dictationApi.transcribeChunk(sessionSlugRef.current, file, chunkIndex)
      setSession(response.session)
      setLastChunk(response.transcript)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falló la transcripción del chunk')
    } finally {
      setBusy(false)
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType =
        MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm'

      const recorder = new MediaRecorder(stream, { mimeType })
      recorder.ondataavailable = async (event) => {
        if (event.data && event.data.size > 0) {
          await uploadChunk(event.data)
        }
      }
      recorder.start(20000)

      recorderRef.current = recorder
      streamRef.current = stream
      setRecording(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo acceder al micrófono')
    }
  }

  function stopRecording() {
    recorderRef.current?.stop()
    recorderRef.current = null
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setRecording(false)
  }

  useEffect(() => {
    if (!showCanvas || !session?.transcript) return
    setCanvasText((current) => (current.trim() ? current : session.transcript))
  }, [session?.transcript, showCanvas])

  useEffect(() => {
    if (!showCanvas || !autoAppend || !lastChunk.trim()) return
    setCanvasText((current) => `${current}${current.trim() ? '\n\n' : ''}${lastChunk}`.trim())
  }, [autoAppend, lastChunk, showCanvas])

  const chunkLog = useMemo(() => session?.chunk_log || [], [session])
  const transcriptLength = session?.transcript?.trim().length || 0
  const canvasLength = canvasText.trim().length
  const effectiveDraft = showCanvas ? canvasText.trim() : session?.transcript?.trim() || ''

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-4 border-b border-line bg-paper space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted">Voz central</div>
          <h3 className="text-base font-semibold mt-1">Dictado y reescritura</h3>
          <p className="text-xs text-muted mt-1">
            Graba por chunks, corrige el borrador al centro del flujo y envialo al documento cuando el bloque ya esté limpio.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2 text-[11px]">
          <div className="cif-kpi">
            <div className="text-muted">Sesión</div>
            <div className="font-medium truncate">{session?.slug || '...'}</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Chunks</div>
            <div className="font-medium">{session?.chunk_count || 0}</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Estado</div>
            <div className="font-medium flex items-center gap-1">
              {busy && <RefreshCw size={12} className="animate-spin" />}
              {recording ? 'grabando' : session?.status || 'idle'}
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 border-b border-line space-y-4 bg-bg">
        <div className="flex flex-wrap gap-2">
          {!recording ? (
            <button className="btn btn-primary btn-sm" onClick={startRecording} disabled={busy || !session}>
              <Mic size={14} className="mr-1" />
              Empezar dictado
            </button>
          ) : (
            <button className="btn btn-sm" onClick={stopRecording}>
              <PauseCircle size={14} className="mr-1" />
              Pausar captura
            </button>
          )}
          {showCanvas && (
            <button
              className="btn btn-sm"
              onClick={() => setCanvasText(session?.transcript || '')}
              disabled={!session?.transcript}
            >
              <RefreshCw size={14} className="mr-1" />
              Rehidratar borrador
            </button>
          )}
          <button
            className="btn btn-sm"
            onClick={() => lastChunk && onInsertText?.(lastChunk)}
            disabled={!canInsert || !lastChunk}
          >
            <ClipboardPaste size={14} className="mr-1" />
            Insertar último chunk
          </button>
          <button
            className="btn btn-sm"
            onClick={() => session?.transcript && onInsertText?.(session.transcript)}
            disabled={!canInsert || !session?.transcript}
          >
            <FileUp size={14} className="mr-1" />
            Insertar transcript
          </button>
          {showCanvas && (
            <button
              className="btn btn-sm"
              onClick={() => canvasText && onInsertText?.(canvasText)}
              disabled={!canInsert || !canvasText.trim()}
            >
              <Wand2 size={14} className="mr-1" />
              Insertar borrador
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px]">
          <div className="cif-kpi">
            <div className="text-muted">Transcript acumulado</div>
            <div className="font-medium">{transcriptLength} caracteres</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Borrador editable</div>
            <div className="font-medium">{showCanvas ? canvasLength : transcriptLength} caracteres</div>
          </div>
          <div className="cif-kpi">
            <div className="text-muted">Último chunk</div>
            <div className="font-medium truncate">{lastChunk.trim() ? 'listo para revisar' : 'sin cambios'}</div>
          </div>
        </div>

        {!canInsert && (
          <div className="text-[11px] text-muted">
            Este modo está en canvas de trabajo. Para insertar texto al documento, abre el editor completo.
          </div>
        )}

        {showCanvas && (
          <div className="flex items-center justify-between text-[11px] text-muted">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoAppend}
                onChange={(event) => setAutoAppend(event.target.checked)}
              />
              Autoagregar cada chunk al canvas
            </label>
            <button
              className="text-c-blue hover:underline"
              onClick={() => setCanvasText('')}
              disabled={!canvasText}
            >
              Limpiar canvas
            </button>
          </div>
        )}

        {error && <div className="text-xs text-c-red">{error}</div>}
      </div>

      <div className={`grid ${showCanvas ? 'grid-rows-[1.1fr,0.8fr]' : 'grid-rows-[1fr]'} flex-1 min-h-0`}>
        <div className="border-b border-line overflow-y-auto p-3 bg-paper">
          <div className="flex items-center justify-between gap-3 mb-2">
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted">
                {showCanvas ? 'Borrador de reescritura' : 'Transcript acumulado'}
              </div>
              <div className="text-[11px] text-muted mt-1">
                {showCanvas
                  ? 'Consolida acá el texto que sí debería entrar al informe. La idea es limpiar repeticiones antes de insertar.'
                  : 'Transcripción acumulada por chunks.'}
              </div>
            </div>
            {showCanvas && (
              <button
                className="text-[11px] text-c-blue hover:underline"
                onClick={() => setCanvasText((current) => `${current}${current ? '\n\n' : ''}${lastChunk}`)}
                disabled={!lastChunk}
              >
                Añadir último chunk
              </button>
            )}
          </div>
          {showCanvas && (
            <div className="mb-3 border border-line bg-bg px-3 py-2 text-[11px] text-muted flex items-start gap-2">
              <Waves size={14} className="mt-0.5 flex-shrink-0 text-c-blue" />
              Trabaja en bloques cortos: dicta, deja que cierre el chunk, corrige el borrador y luego inserta solo la versión ya reescrita.
            </div>
          )}
          {showCanvas ? (
            <textarea
              value={canvasText}
              onChange={(event) => setCanvasText(event.target.value)}
              placeholder="Empieza a hablar. La transcripción irá llegando acá y puedes reordenarla o resumirla antes de mandarla al documento."
              className="w-full min-h-full h-full resize-none border border-line bg-bg p-3 text-[12px] leading-6 outline-none"
            />
          ) : (
            <pre className="text-[11px] leading-5 whitespace-pre-wrap break-words bg-bg border border-line p-3 min-h-full">
              {session?.transcript || 'Todavía no hay transcripción.'}
            </pre>
          )}
        </div>
        <div className="overflow-y-auto p-3 bg-bg">
          <div className="flex items-center justify-between gap-3 mb-2">
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted">Chunks auditables</div>
              <div className="text-[11px] text-muted mt-1">
                Contrasta el borrador contra cada captura cuando dudes de una frase.
              </div>
            </div>
            {effectiveDraft && canInsert && (
              <button
                className="btn btn-sm"
                onClick={() => onInsertText?.(effectiveDraft)}
              >
                <ClipboardPaste size={14} className="mr-1" />
                Insertar bloque activo
              </button>
            )}
          </div>
          <div className="space-y-2">
            {chunkLog.length === 0 && <div className="text-xs text-muted">Aún no hay chunks guardados.</div>}
            {[...chunkLog].reverse().map((chunk: any) => (
              <div key={`${chunk.chunk_index}-${chunk.created_at}`} className="border border-line p-2 bg-bg">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-medium">Chunk {chunk.chunk_index}</span>
                  <span className="text-muted">{chunk.file_name}</span>
                </div>
                <div className="text-xs mt-2 whitespace-pre-wrap">{chunk.transcript || '(vacío)'}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
