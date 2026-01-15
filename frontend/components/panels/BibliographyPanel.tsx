'use client'

import { useState, useEffect, useCallback } from 'react'
import { BibEntry, bibliographyApi } from '@/lib/api'

interface BibliographyPanelProps {
  onCite?: (bibKey: string) => void
}

export function BibliographyPanel({ onCite }: BibliographyPanelProps) {
  const [entries, setEntries] = useState<BibEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showImport, setShowImport] = useState(false)
  const [bibtexInput, setBibtexInput] = useState('')
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    loadEntries()
  }, [])

  async function loadEntries() {
    try {
      setLoading(true)
      setError(null)
      const data = await bibliographyApi.list()
      setEntries(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bibliography')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = useCallback(
    async (query: string) => {
      if (query.length < 2) {
        loadEntries()
        return
      }
      try {
        setLoading(true)
        const results = await bibliographyApi.search(query)
        setEntries(results)
      } catch (err) {
        console.error('Search failed:', err)
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, handleSearch])

  async function handleImport() {
    if (!bibtexInput.trim()) return
    try {
      setImporting(true)
      const imported = await bibliographyApi.importBibtex(bibtexInput)
      setEntries((prev) => [...imported, ...prev])
      setBibtexInput('')
      setShowImport(false)
    } catch (err) {
      console.error('Import failed:', err)
      alert('Failed to import BibTeX')
    } finally {
      setImporting(false)
    }
  }

  async function handleDelete(bibKey: string) {
    if (!confirm(`Delete ${bibKey}?`)) return
    try {
      await bibliographyApi.delete(bibKey)
      setEntries((prev) => prev.filter((e) => e.bib_key !== bibKey))
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  function formatAuthors(author: string): string {
    const authors = author.split(' and ')
    if (authors.length <= 2) return author
    return `${authors[0]} et al.`
  }

  if (loading && entries.length === 0) {
    return <div className="p-4 text-muted">Loading bibliography...</div>
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <h2 className="font-medium text-ink">Bibliography</h2>
        <p className="text-sm text-muted mt-1">{entries.length} entries</p>
      </div>

      {/* Search */}
      <div className="p-2 border-b border-line">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by title, author, key..."
          className="w-full px-3 py-2 text-sm border border-line bg-paper focus:outline-none focus:border-ink"
        />
      </div>

      {/* Import Section */}
      {showImport && (
        <div className="p-3 border-b border-line bg-bg">
          <textarea
            value={bibtexInput}
            onChange={(e) => setBibtexInput(e.target.value)}
            placeholder="Paste BibTeX here..."
            className="w-full h-32 p-2 text-xs font-mono border border-line bg-paper resize-none focus:outline-none focus:border-ink"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleImport}
              disabled={importing}
              className="px-3 py-1 text-sm bg-ink text-paper hover:opacity-90 disabled:opacity-50"
            >
              {importing ? 'Importing...' : 'Import'}
            </button>
            <button
              onClick={() => setShowImport(false)}
              className="px-3 py-1 text-sm border border-line hover:bg-paper"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Entries List */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="p-4 text-c-red">
            {error}
            <button onClick={loadEntries} className="ml-2 underline">
              Retry
            </button>
          </div>
        )}

        {entries.length === 0 && !loading ? (
          <div className="p-4 text-center text-muted">
            {searchQuery ? 'No results found' : 'No bibliography entries'}
          </div>
        ) : (
          <ul className="divide-y divide-line">
            {entries.map((entry) => (
              <li
                key={entry.bib_key}
                className="p-3 hover:bg-bg"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-c-blue">
                        @{entry.bib_key}
                      </span>
                      <span className="text-xs text-muted">
                        {entry.entry_type}
                      </span>
                    </div>
                    <p className="text-sm text-ink font-medium line-clamp-2">
                      {entry.title}
                    </p>
                    <p className="text-xs text-muted mt-1">
                      {formatAuthors(entry.author)}
                      {entry.year && ` (${entry.year})`}
                    </p>
                    {entry.journal && (
                      <p className="text-xs text-muted italic">
                        {entry.journal}
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-2">
                  {onCite && (
                    <button
                      onClick={() => onCite(entry.bib_key)}
                      className="text-xs text-c-blue hover:underline"
                    >
                      Cite
                    </button>
                  )}
                  {entry.doi && (
                    <a
                      href={`https://doi.org/${entry.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-muted hover:underline"
                    >
                      DOI
                    </a>
                  )}
                  {entry.url && (
                    <a
                      href={entry.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-muted hover:underline"
                    >
                      URL
                    </a>
                  )}
                  <button
                    onClick={() => handleDelete(entry.bib_key)}
                    className="text-xs text-c-red hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add/Import Button */}
      <div className="p-3 border-t border-line flex gap-2">
        <button
          onClick={() => setShowImport(!showImport)}
          className="flex-1 py-2 text-sm text-center border border-line hover:bg-bg"
        >
          {showImport ? 'Cancel Import' : '+ Import BibTeX'}
        </button>
      </div>
    </div>
  )
}

export default BibliographyPanel
