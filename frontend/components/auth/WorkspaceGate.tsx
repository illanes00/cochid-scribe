'use client'

import { FormEvent, useState } from 'react'
import { LockKeyhole } from 'lucide-react'
import { useAuth } from '@/lib/auth'

interface WorkspaceGateProps {
  title?: string
  description?: string
}

export function WorkspaceGate({
  title = 'Workspace protegido',
  description = 'Este workspace requiere autenticación antes de mostrar el informe y sus fuentes.',
}: WorkspaceGateProps) {
  const { loginToWorkspace, loading } = useAuth()
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await loginToWorkspace(password)
      setPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo autenticar')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="border border-line bg-paper p-6 w-full max-w-md">
        <div className="flex items-center gap-2 mb-3">
          <LockKeyhole size={18} />
          <h1 className="text-xl font-bold">{title}</h1>
        </div>
        <p className="text-sm text-muted mb-4">{description}</p>
        <label className="block text-sm font-medium mb-2">Contraseña</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="input w-full mb-3"
          placeholder="Ingresa la clave del workspace"
          autoFocus
        />
        {error && <div className="text-xs text-c-red mb-3">{error}</div>}
        <button className="btn btn-primary w-full" disabled={submitting || loading}>
          {submitting ? 'Entrando...' : 'Entrar al workspace'}
        </button>
      </form>
    </div>
  )
}
