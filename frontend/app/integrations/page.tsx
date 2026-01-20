'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  FileText,
  BookOpen,
  Database,
  Settings,
  Cloud,
  CheckCircle,
  AlertCircle,
  ExternalLink,
} from 'lucide-react'
import { integrationsApi, googleApi } from '@/lib/api'

export default function IntegrationsPage() {
  const pathname = usePathname()
  const router = useRouter()
  const [googleConnected, setGoogleConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [docId, setDocId] = useState('')
  const [slidesId, setSlidesId] = useState('')
  const [docFormat, setDocFormat] = useState<'html' | 'docx'>('html')
  const [importing, setImporting] = useState(false)

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true)
      const status = await integrationsApi.googleStatus()
      setGoogleConnected(status.connected)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatus()
  }, [loadStatus])

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
      setImporting(true)
      setError(null)
      const doc = await googleApi.importDoc(docId.trim(), undefined, docFormat)
      setSuccess('Document imported successfully!')
      setDocId('')
      setTimeout(() => {
        router.push(`/editor/${doc.slug}`)
      }, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import document')
    } finally {
      setImporting(false)
    }
  }

  async function handleImportSlides() {
    if (!slidesId.trim()) return
    try {
      setImporting(true)
      setError(null)
      const doc = await googleApi.importSlides(slidesId.trim())
      setSuccess('Presentation imported successfully!')
      setSlidesId('')
      setTimeout(() => {
        router.push(`/editor/${doc.slug}`)
      }, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import presentation')
    } finally {
      setImporting(false)
    }
  }

  const navLinks = [
    { href: '/dashboard', label: 'Documents', icon: FileText },
    { href: '/knowledge', label: 'Knowledge', icon: BookOpen },
    { href: '/data', label: 'Data', icon: Database },
    { href: '/integrations', label: 'Integrations', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
                    isActive
                      ? 'bg-bg text-ink font-medium'
                      : 'text-muted hover:text-ink hover:bg-bg/50'
                  }`}
                >
                  <Icon size={14} />
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="container py-8 max-w-2xl">
        <h1 className="text-2xl font-bold mb-6">Integrations</h1>

        {error && (
          <div className="card bg-c-red/10 text-c-red mb-4 flex items-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {success && (
          <div className="card bg-c-green/10 text-c-green mb-4 flex items-center gap-2">
            <CheckCircle size={16} />
            {success}
          </div>
        )}

        <section className="card mb-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-bg rounded-lg">
              <Cloud size={24} className="text-c-blue" />
            </div>
            <div className="flex-1">
              <h2 className="font-medium text-lg mb-1">Google Workspace</h2>
              <p className="text-sm text-muted mb-4">
                Connect your Google account to import and export documents and presentations.
              </p>
              <div className="flex items-center gap-3">
                <button
                  className="btn btn-primary"
                  onClick={handleConnectGoogle}
                  disabled={loading}
                >
                  {googleConnected ? 'Reconnect Google' : 'Connect Google'}
                </button>
                {googleConnected && (
                  <span className="flex items-center gap-1 text-sm text-c-green">
                    <CheckCircle size={14} />
                    Connected
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        {googleConnected && (
          <>
            <section className="card mb-6">
              <h3 className="font-medium mb-3">Import from Google Docs</h3>
              <p className="text-sm text-muted mb-4">
                Enter the Google Doc ID or paste the full URL to import a document.
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  placeholder="Google Doc ID or URL"
                  className="input flex-1"
                />
                <select
                  className="input w-28"
                  value={docFormat}
                  onChange={(e) => setDocFormat(e.target.value as 'html' | 'docx')}
                  title="Import format"
                >
                  <option value="html">HTML</option>
                  <option value="docx">DOCX</option>
                </select>
                <button
                  className="btn"
                  onClick={handleImportDoc}
                  disabled={!docId.trim() || importing}
                >
                  {importing ? 'Importing...' : 'Import'}
                </button>
              </div>
            </section>

            <section className="card">
              <h3 className="font-medium mb-3">Import from Google Slides</h3>
              <p className="text-sm text-muted mb-4">
                Enter the Google Slides ID or paste the full URL to import a presentation.
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={slidesId}
                  onChange={(e) => setSlidesId(e.target.value)}
                  placeholder="Google Slides ID or URL"
                  className="input flex-1"
                />
                <button
                  className="btn"
                  onClick={handleImportSlides}
                  disabled={!slidesId.trim() || importing}
                >
                  {importing ? 'Importing...' : 'Import'}
                </button>
              </div>
            </section>
          </>
        )}

        {!googleConnected && !loading && (
          <div className="card text-center py-8">
            <Cloud size={48} className="mx-auto mb-4 text-muted" />
            <p className="text-muted mb-4">
              Connect your Google account to import documents and presentations.
            </p>
            <button className="btn btn-primary" onClick={handleConnectGoogle}>
              Connect Google
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
