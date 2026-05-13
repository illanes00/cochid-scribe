'use client'

import { LockKeyhole, LogIn } from 'lucide-react'
import { useAuth } from '@/lib/auth'

interface WorkspaceGateProps {
  title?: string
  description?: string
}

export function WorkspaceGate({
  title = 'Workspace protegido',
  description = 'Inicia sesión para continuar.',
}: WorkspaceGateProps) {
  const { loginWithSSO, loading } = useAuth()

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      <div className="border border-line bg-paper p-6 w-full max-w-md text-center">
        <div className="flex items-center justify-center gap-2 mb-3">
          <LockKeyhole size={18} />
          <h1 className="text-xl font-bold">{title}</h1>
        </div>
        <p className="text-sm text-muted mb-5">{description}</p>
        <button
          type="button"
          onClick={loginWithSSO}
          disabled={loading}
          className="btn btn-primary w-full"
        >
          <LogIn size={14} className="mr-2" />
          Iniciar sesión con Cochid
        </button>
      </div>
    </div>
  )
}
