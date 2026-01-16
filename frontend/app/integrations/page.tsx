'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { integrationsApi, googleApi } from '@/lib/api'

export default function IntegrationsPage() {
  const [googleConnected, setGoogleConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [docId, setDocId] = useState('')
  const [slidesId, setSlidesId] = useState('')
  const [docFormat, setDocFormat] = useState<'html' | 'docx'>('html')

  async function loadStatus() {
    try {
      setLoading(true)
      const status = await integrationsApi.googleStatus()
      setGoogleConnected(status.connected)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  async function handleConnectGoogle() {
    try {
      const { url } = await integrationsApi.googleAuthUrl()
      window.location.href = url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start OAuth')
    }
  }

  async function handleImportDoc() {
    if (!docId.trim()) return
    try {
      await googleApi.importDoc(docId.trim(), undefined, docFormat)
      alert('Documento importado.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import doc')
    }
  }

  async function handleImportSlides() {
    if (!slidesId.trim()) return
    try {
      await googleApi.importSlides(slidesId.trim())
      alert('Slides importadas.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import slides')
    }
  }

  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-muted hover:text-ink">
              Documents
            </Link>
            <Link href="/knowledge" className="text-sm text-muted hover:text-ink">
              Knowledge Base
            </Link>
            <Link href="/integrations" className="text-sm text-ink font-medium">
              Integrations
            </Link>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <h1 className="text-2xl font-bold mb-4">Integrations</h1>
        {error && (
          <div className="card bg-c-red/10 text-c-red mb-4">{error}</div>
        )}

        <section className="card mb-6">
          <h2 className="font-medium text-lg mb-2">Google Docs & Slides</h2>
          <p className="text-sm text-muted mb-4">
            Conecta tu cuenta para importar y exportar documentos.
          </p>
          <button
            className="btn btn-primary"
            onClick={handleConnectGoogle}
            disabled={loading}
          >
            {googleConnected ? 'Re-connect Google' : 'Connect Google'}
          </button>
        </section>

        <section className="card mb-6">
          <h3 className="font-medium mb-2">Importar Google Docs</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
              placeholder="Google Doc file ID"
              className="input flex-1"
            />
            <select
              className="input w-28"
              value={docFormat}
              onChange={(e) => setDocFormat(e.target.value as 'html' | 'docx')}
            >
              <option value="html">HTML</option>
              <option value="docx">DOCX</option>
            </select>
            <button className="btn" onClick={handleImportDoc} disabled={!googleConnected}>
              Importar
            </button>
          </div>
        </section>

        <section className="card">
          <h3 className="font-medium mb-2">Importar Google Slides</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={slidesId}
              onChange={(e) => setSlidesId(e.target.value)}
              placeholder="Google Slides file ID"
              className="input flex-1"
            />
            <button className="btn" onClick={handleImportSlides} disabled={!googleConnected}>
              Importar
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
