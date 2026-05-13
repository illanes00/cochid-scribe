'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LogIn, PenLine } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const router = useRouter()
  const { authenticated, loading, loginWithSSO } = useAuth()

  useEffect(() => {
    if (!loading && authenticated) {
      router.replace('/dashboard')
    }
  }, [authenticated, loading, router])

  // Don't flash the landing while we're checking the session, or right after
  // detecting an authenticated user (the redirect is about to fire).
  if (loading || authenticated) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-sm text-muted">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-bg flex items-center justify-center p-6 overflow-hidden">
      <div className="max-w-md w-full text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <PenLine size={22} className="text-c-blue" />
          <span className="text-2xl font-bold text-ink">Cochid · Scribe</span>
        </div>
        <p className="text-sm text-muted leading-relaxed mb-8">
          Escritura colaborativa con IA · claims verificables · bibliografía APA.
        </p>
        <button
          type="button"
          onClick={loginWithSSO}
          className="btn btn-primary w-full"
        >
          <LogIn size={14} className="mr-2" />
          Iniciar sesión
        </button>
        <p className="text-[11px] text-muted mt-6">
          Acceso vía Cochid SSO · Authentik
        </p>
      </div>
    </div>
  )
}
