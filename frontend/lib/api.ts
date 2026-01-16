/**
 * Scribe API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface DocumentContent {
  html?: string
  json?: Record<string, unknown>
}

export interface Document {
  id: string
  slug: string
  title: string
  doc_type: 'paper' | 'thesis' | 'policy'
  content: DocumentContent
  markdown?: string
  front_matter: Record<string, unknown>
  source_provider?: string | null
  source_id?: string | null
  status: 'draft' | 'review' | 'final'
  version: string
  created_at: string
  updated_at: string
  claim_count: number
  verified_count: number
}

export interface DocumentCreate {
  title: string
  doc_type?: 'paper' | 'thesis' | 'policy'
  content?: DocumentContent
  markdown?: string
  front_matter?: Record<string, unknown>
  slug?: string
}

export interface DocumentUpdate {
  title?: string
  content?: DocumentContent
  markdown?: string
  front_matter?: Record<string, unknown>
  status?: 'draft' | 'review' | 'final'
}

export interface DocumentList {
  documents: Document[]
  total: number
  page: number
  per_page: number
}

export interface Claim {
  id: string
  claim_id: string
  document_id: string
  claim_text: string
  claim_type: 'DATA' | 'LITERATURE' | 'MIXED' | 'HYPOTHESIS'
  status: 'draft' | 'verified' | 'rejected' | 'needs_revision'
  section?: string
  evidence: Evidence[]
  source_sentences: string[]
  created_at: string
  updated_at: string
}

export interface Evidence {
  type: string
  source: string
  description?: string
}

export interface ClaimCreate {
  claim_text: string
  claim_type: 'DATA' | 'LITERATURE' | 'MIXED' | 'HYPOTHESIS'
  section?: string
  evidence?: Evidence[]
}

export interface ClaimUpdate {
  claim_text?: string
  claim_type?: 'DATA' | 'LITERATURE' | 'MIXED' | 'HYPOTHESIS'
  status?: 'draft' | 'verified' | 'rejected' | 'needs_revision'
  section?: string
  evidence?: Evidence[]
}

export interface BibEntry {
  id: string
  bib_key: string
  entry_type: string
  title: string
  author: string
  year?: number
  journal?: string
  booktitle?: string
  volume?: string
  number?: string
  pages?: string
  publisher?: string
  doi?: string
  url?: string
  abstract?: string
  bibtex?: string
  created_at: string
}

export interface BibEntryCreate {
  bib_key: string
  entry_type: string
  title: string
  author: string
  year?: number
  journal?: string
  booktitle?: string
  volume?: string
  number?: string
  pages?: string
  publisher?: string
  doi?: string
  url?: string
  abstract?: string
}

export interface RewriteRequest {
  text: string
  instruction: string
  tone?: string
}

export interface RewriteResponse {
  original: string
  rewritten: string
}

// Knowledge Base Types
export interface Note {
  id: string
  slug: string
  title: string
  content: DocumentContent
  markdown: string
  note_type: 'idea' | 'summary' | 'quote' | 'concept'
  tags: string[]
  created_at: string
  updated_at: string
  backlink_count: number
}

export interface NoteCreate {
  title: string
  slug?: string
  content?: DocumentContent
  markdown?: string
  note_type?: 'idea' | 'summary' | 'quote' | 'concept'
  tags?: string[]
}

export interface NoteUpdate {
  title?: string
  content?: DocumentContent
  markdown?: string
  note_type?: 'idea' | 'summary' | 'quote' | 'concept'
  tags?: string[]
}

export interface NoteList {
  notes: Note[]
  total: number
  page: number
  per_page: number
}

export interface GraphNode {
  id: string
  type: 'note' | 'document' | 'claim' | 'bib'
  label: string
  metadata: Record<string, unknown>
}

export interface GraphEdge {
  source: string
  target: string
  type: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Data Types
export interface ColumnInfo {
  name: string
  type: 'string' | 'number' | 'date' | 'boolean'
  sample_values: unknown[]
}

export interface Dataset {
  id: string
  slug: string
  name: string
  description: string
  data_type: 'csv' | 'json' | 'manual'
  data: Record<string, unknown>[]
  columns: ColumnInfo[]
  row_count: number
  source_file: string
  created_at: string
  updated_at: string
}

export interface DatasetCreate {
  name: string
  slug?: string
  description?: string
  data_type?: 'csv' | 'json' | 'manual'
  data?: Record<string, unknown>[]
  columns?: ColumnInfo[]
}

export interface DatasetList {
  datasets: Dataset[]
  total: number
  page: number
  per_page: number
}

export interface ChartConfig {
  x_column?: string
  y_column?: string
  color_column?: string
  size_column?: string
  title?: string
  x_label?: string
  y_label?: string
  legend?: boolean
  grid?: boolean
  colors?: string[]
}

export interface Chart {
  id: string
  slug: string
  title: string
  chart_type: 'bar' | 'line' | 'scatter' | 'pie' | 'table' | 'area'
  dataset_id: string | null
  config: ChartConfig
  created_at: string
  updated_at: string
}

export interface ChartCreate {
  title: string
  slug?: string
  chart_type: Chart['chart_type']
  dataset_id?: string
  config?: ChartConfig
}

export interface ChartList {
  charts: Chart[]
  total: number
  page: number
  per_page: number
}

export type ExportFormat = 'markdown' | 'html' | 'docx' | 'pptx' | 'latex' | 'pdf'

export interface ExportJob {
  id: string
  document_id: string
  format: ExportFormat
  status: 'pending' | 'running' | 'done' | 'failed'
  output_path?: string | null
  error?: string | null
  created_at: string
  updated_at: string
}

export interface IntegrationStatus {
  provider: string
  connected: boolean
  expires_at?: string | null
}

export interface Comment {
  id: string
  document_id: string
  parent_id?: string | null
  anchor_id?: string | null
  provider: string
  external_id?: string | null
  author?: string | null
  content: string
  quote?: string | null
  resolved: boolean
  created_at: string
  updated_at: string
}

export interface CommentCreate {
  content: string
  quote?: string
  parent_id?: string | null
  anchor_id?: string | null
}

export interface CommentUpdate {
  resolved?: boolean
}

export interface DocumentVersion {
  id: string
  document_id: string
  label?: string | null
  created_at: string
}

export interface DocumentVersionDetail extends DocumentVersion {
  content: Record<string, unknown>
  markdown?: string | null
}

export interface DocumentVersionCreate {
  label?: string | null
}

// API Error
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

// Helper function for API calls
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

// Documents API
export const documentsApi = {
  list: (page = 1, perPage = 20): Promise<DocumentList> =>
    fetchApi(`/api/v1/documents?page=${page}&per_page=${perPage}`),

  get: (slug: string): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}`),

  create: (data: DocumentCreate): Promise<Document> =>
    fetchApi('/api/v1/documents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: DocumentUpdate): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/documents/${slug}`, {
      method: 'DELETE',
    }),

  import: async (file: File, title?: string, docType?: string): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    if (docType) formData.append('doc_type', docType)

    const response = await fetch(`${API_BASE}/api/v1/documents/import`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Import failed' }))
      throw new ApiError(response.status, error.detail || 'Import failed')
    }

    return response.json()
  },

  export: (slug: string, format: ExportFormat): Promise<ExportJob> =>
    fetchApi(`/api/v1/documents/${slug}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    }),
}

// Claims API
export const claimsApi = {
  listByDocument: (slug: string, status?: string): Promise<Claim[]> => {
    const params = status ? `?status=${status}` : ''
    return fetchApi(`/api/v1/claims/document/${slug}${params}`)
  },

  get: (claimId: string): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}`),

  create: (slug: string, data: ClaimCreate): Promise<Claim> =>
    fetchApi(`/api/v1/claims/document/${slug}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (claimId: string, data: ClaimUpdate): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (claimId: string): Promise<void> =>
    fetchApi(`/api/v1/claims/${claimId}`, {
      method: 'DELETE',
    }),

  verify: (claimId: string): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}/verify`, {
      method: 'POST',
    }),
}

// Bibliography API
export const bibliographyApi = {
  list: (limit = 100, offset = 0): Promise<BibEntry[]> =>
    fetchApi(`/api/v1/bibliography?limit=${limit}&offset=${offset}`),

  search: (query: string, limit = 20): Promise<BibEntry[]> =>
    fetchApi(`/api/v1/bibliography/search?q=${encodeURIComponent(query)}&limit=${limit}`),

  get: (bibKey: string): Promise<BibEntry> =>
    fetchApi(`/api/v1/bibliography/${bibKey}`),

  create: (data: BibEntryCreate): Promise<BibEntry> =>
    fetchApi('/api/v1/bibliography', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  delete: (bibKey: string): Promise<void> =>
    fetchApi(`/api/v1/bibliography/${bibKey}`, {
      method: 'DELETE',
    }),

  importBibtex: (bibtex: string): Promise<BibEntry[]> =>
    fetchApi('/api/v1/bibliography/import', {
      method: 'POST',
      body: JSON.stringify(bibtex),
    }),
}

// LLM API
export const llmApi = {
  rewrite: (data: RewriteRequest): Promise<RewriteResponse> =>
    fetchApi('/api/v1/llm/rewrite', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  extractClaims: (text: string): Promise<{ claims: Record<string, unknown>[] }> =>
    fetchApi('/api/v1/llm/extract-claims', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  improveHedging: (
    text: string
  ): Promise<{ original: string; improved: string; changes: string[] }> =>
    fetchApi('/api/v1/llm/improve-hedging', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  extractClaimsForDocument: (slug: string): Promise<{ created: number }> =>
    fetchApi(`/api/v1/llm/extract-claims-document/${slug}`, {
      method: 'POST',
    }),
}

// Notes API (Knowledge Base)
export const notesApi = {
  list: (page = 1, perPage = 20, search?: string, noteType?: string, tag?: string): Promise<NoteList> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (search) params.append('search', search)
    if (noteType) params.append('note_type', noteType)
    if (tag) params.append('tag', tag)
    return fetchApi(`/api/v1/notes?${params}`)
  },

  get: (slug: string): Promise<Note> =>
    fetchApi(`/api/v1/notes/${slug}`),

  create: (data: NoteCreate): Promise<Note> =>
    fetchApi('/api/v1/notes', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: NoteUpdate): Promise<Note> =>
    fetchApi(`/api/v1/notes/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/notes/${slug}`, {
      method: 'DELETE',
    }),

  getBacklinks: (slug: string): Promise<{ id: string; source_type: string; source_id: string }[]> =>
    fetchApi(`/api/v1/notes/${slug}/backlinks`),
}

// Graph API
export const graphApi = {
  getFullGraph: (includeDocuments = true, includeClaims = false, includeBib = true): Promise<GraphData> => {
    const params = new URLSearchParams({
      include_documents: String(includeDocuments),
      include_claims: String(includeClaims),
      include_bib: String(includeBib),
    })
    return fetchApi(`/api/v1/graph?${params}`)
  },

  getLocalGraph: (entityType: string, entityId: string, depth = 1): Promise<GraphData> =>
    fetchApi(`/api/v1/graph/local/${entityType}/${entityId}?depth=${depth}`),

  search: (query: string): Promise<GraphData> =>
    fetchApi(`/api/v1/graph/search?query=${encodeURIComponent(query)}`),
}

// Datasets API
export const datasetsApi = {
  list: (page = 1, perPage = 20, search?: string): Promise<DatasetList> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (search) params.append('search', search)
    return fetchApi(`/api/v1/datasets?${params}`)
  },

  get: (slug: string): Promise<Dataset> =>
    fetchApi(`/api/v1/datasets/${slug}`),

  create: (data: DatasetCreate): Promise<Dataset> =>
    fetchApi('/api/v1/datasets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  upload: async (file: File, name?: string): Promise<Dataset> => {
    const formData = new FormData()
    formData.append('file', file)
    if (name) formData.append('name', name)

    const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, error.detail || 'Upload failed')
    }

    return response.json()
  },

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/datasets/${slug}`, {
      method: 'DELETE',
    }),
}

// Charts API
export const chartsApi = {
  list: (page = 1, perPage = 20, search?: string, chartType?: string): Promise<ChartList> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (search) params.append('search', search)
    if (chartType) params.append('chart_type', chartType)
    return fetchApi(`/api/v1/charts?${params}`)
  },

  get: (slug: string): Promise<Chart> =>
    fetchApi(`/api/v1/charts/${slug}`),

  create: (data: ChartCreate): Promise<Chart> =>
    fetchApi('/api/v1/charts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: Partial<ChartCreate>): Promise<Chart> =>
    fetchApi(`/api/v1/charts/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/charts/${slug}`, {
      method: 'DELETE',
    }),
}

// Exports API
export const exportsApi = {
  get: (jobId: string): Promise<ExportJob> =>
    fetchApi(`/api/v1/exports/${jobId}`),

  downloadUrl: (jobId: string): string =>
    `${API_BASE}/api/v1/exports/${jobId}/download`,
}

// Assets API
export const assetsApi = {
  upload: async (file: File): Promise<{ url: string; name: string }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/api/v1/assets/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, error.detail || 'Upload failed')
    }

    return response.json()
  },
}

// Integrations API
export const integrationsApi = {
  googleStatus: (): Promise<IntegrationStatus> =>
    fetchApi('/api/v1/integrations/google/status'),

  googleAuthUrl: (): Promise<{ url: string }> =>
    fetchApi('/api/v1/integrations/google/auth-url', { method: 'POST' }),
}

// Google import/export API
export const googleApi = {
  importDoc: (
    fileId: string,
    title?: string,
    format?: 'html' | 'docx'
  ): Promise<{ slug: string; title: string }> =>
    fetchApi('/api/v1/google/docs/import', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId, title, format }),
    }),

  exportDoc: (slug: string, folderId?: string): Promise<{ file_id: string; url?: string }> =>
    fetchApi('/api/v1/google/docs/export', {
      method: 'POST',
      body: JSON.stringify({ slug, folder_id: folderId }),
    }),

  exportSlides: (slug: string, folderId?: string): Promise<{ file_id: string; url?: string }> =>
    fetchApi('/api/v1/google/slides/export', {
      method: 'POST',
      body: JSON.stringify({ slug, folder_id: folderId }),
    }),

  importSlides: (
    fileId: string,
    title?: string,
    format?: 'pptx'
  ): Promise<{ slug: string; title: string }> =>
    fetchApi('/api/v1/google/slides/import', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId, title, format }),
    }),
}

// Comments API
export const commentsApi = {
  list: (slug: string): Promise<Comment[]> =>
    fetchApi(`/api/v1/comments/document/${slug}`),

  create: (slug: string, data: CommentCreate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/document/${slug}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  syncGoogle: (slug: string): Promise<{ created: number }> =>
    fetchApi(`/api/v1/comments/document/${slug}/sync`, {
      method: 'POST',
    }),

  createGoogle: (slug: string, data: CommentCreate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/document/${slug}/google`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (commentId: string, data: CommentUpdate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/${commentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}

// Versions API
export const versionsApi = {
  list: (slug: string): Promise<DocumentVersion[]> =>
    fetchApi(`/api/v1/documents/${slug}/versions`),

  create: (slug: string, data: DocumentVersionCreate): Promise<DocumentVersion> =>
    fetchApi(`/api/v1/documents/${slug}/versions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  restore: (slug: string, versionId: string): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}/versions/${versionId}/restore`, {
      method: 'POST',
    }),

  get: (slug: string, versionId: string): Promise<DocumentVersionDetail> =>
    fetchApi(`/api/v1/documents/${slug}/versions/${versionId}`),
}

// Export all APIs
export const api = {
  documents: documentsApi,
  claims: claimsApi,
  bibliography: bibliographyApi,
  llm: llmApi,
  notes: notesApi,
  graph: graphApi,
  datasets: datasetsApi,
  charts: chartsApi,
  exports: exportsApi,
  assets: assetsApi,
  integrations: integrationsApi,
  google: googleApi,
  comments: commentsApi,
  versions: versionsApi,
}

export default api
