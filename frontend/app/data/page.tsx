'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Plus,
  Database,
  Search,
  RefreshCw,
  Trash2,
  Upload,
  Table,
  FileSpreadsheet,
} from 'lucide-react'
import { Dataset, datasetsApi } from '@/lib/api'

export default function DataPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const perPage = 20

  useEffect(() => {
    loadDatasets()
  }, [page])

  async function loadDatasets() {
    try {
      setLoading(true)
      setError(null)
      const result = await datasetsApi.list(page, perPage, searchQuery || undefined)
      setDatasets(result.datasets)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load datasets')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(slug: string, e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('Delete this dataset? This cannot be undone.')) return

    try {
      await datasetsApi.delete(slug)
      setDatasets((prev) => prev.filter((d) => d.slug !== slug))
      setTotal((prev) => prev - 1)
    } catch (err) {
      alert('Failed to delete dataset')
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      setError(null)
      const dataset = await datasetsApi.upload(file)
      router.push(`/data/${dataset.slug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setPage(1)
    loadDatasets()
  }

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
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
            <Link href="/data" className="text-sm text-ink font-medium">
              Data
            </Link>
            <Link href="/integrations" className="text-sm text-muted hover:text-ink">
              Integrations
            </Link>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="container py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold mb-1">Data</h1>
            <p className="text-sm text-muted">
              {total} dataset{total !== 1 ? 's' : ''} - Upload and visualize data
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadDatasets}
              className="btn"
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              onChange={handleUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-primary"
              disabled={uploading}
            >
              <Upload size={16} className="mr-2" />
              {uploading ? 'Uploading...' : 'Upload Data'}
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-4 mb-6">
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              type="text"
              placeholder="Search datasets..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
        </div>

        {/* Error state */}
        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadDatasets} className="text-sm underline">
              Retry
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && datasets.length === 0 && (
          <div className="card text-center py-12">
            <RefreshCw size={24} className="mx-auto mb-4 text-muted animate-spin" />
            <p className="text-muted">Loading datasets...</p>
          </div>
        )}

        {/* Dataset grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map((dataset) => (
              <DatasetCard
                key={dataset.slug}
                dataset={dataset}
                onDelete={(e) => handleDelete(dataset.slug, e)}
              />
            ))}

            {datasets.length === 0 && (
              <div className="col-span-full card text-center py-12">
                <Database size={48} className="mx-auto mb-4 text-muted" />
                <p className="text-muted mb-2">
                  {searchQuery ? 'No datasets match your search' : 'No datasets yet'}
                </p>
                <p className="text-sm text-muted mb-4">
                  Upload CSV or JSON files to get started
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn btn-primary"
                >
                  Upload your first dataset
                </button>
              </div>
            )}
          </div>
        )}

        {/* Pagination */}
        {total > perPage && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn btn-sm"
            >
              Previous
            </button>
            <span className="text-sm text-muted">
              Page {page} of {Math.ceil(total / perPage)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / perPage)}
              className="btn btn-sm"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

function DatasetCard({
  dataset,
  onDelete,
}: {
  dataset: Dataset
  onDelete: (e: React.MouseEvent) => void
}) {
  const typeIcons: Record<string, React.ReactNode> = {
    csv: <FileSpreadsheet size={16} />,
    json: <Database size={16} />,
    manual: <Table size={16} />,
  }

  const updatedDate = new Date(dataset.updated_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })

  return (
    <Link href={`/data/${dataset.slug}`}>
      <div className="card h-full flex flex-col hover:border-line-strong transition-colors">
        <div className="flex items-start justify-between mb-2">
          <span className="p-2 bg-bg text-muted">
            {typeIcons[dataset.data_type] || <Database size={16} />}
          </span>
          <button
            className="p-1 hover:bg-bg text-muted hover:text-c-red"
            onClick={onDelete}
            title="Delete dataset"
          >
            <Trash2 size={14} />
          </button>
        </div>

        <h3 className="font-semibold mb-1 line-clamp-2">{dataset.name}</h3>

        {dataset.description && (
          <p className="text-sm text-muted mb-2 line-clamp-2">
            {dataset.description}
          </p>
        )}

        <div className="mt-auto flex items-center justify-between text-xs text-muted">
          <span>{dataset.row_count} rows</span>
          <span>{dataset.columns.length} columns</span>
          <span>{updatedDate}</span>
        </div>
      </div>
    </Link>
  )
}
