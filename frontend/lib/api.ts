/**
 * Scribe API Client
 * Handles all communication with the FastAPI backend
 */

// Use relative path so Next.js rewrites work in production
// The rewrites in next.config.mjs handle proxying to the correct backend port
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// Types
export interface DocumentContent {
  html?: string;
  json?: Record<string, unknown>;
}

export interface Document {
  id: string;
  slug: string;
  title: string;
  doc_type: "paper" | "thesis" | "policy" | "presentation";
  content: DocumentContent;
  markdown?: string;
  front_matter: Record<string, unknown>;
  source_provider?: string | null;
  source_id?: string | null;
  status: "draft" | "review" | "final";
  version: string;
  created_at: string;
  updated_at: string;
  claim_count: number;
  verified_count: number;
}

export interface DocumentCreate {
  title: string;
  doc_type?: "paper" | "thesis" | "policy" | "presentation";
  content?: DocumentContent;
  markdown?: string;
  front_matter?: Record<string, unknown>;
  slug?: string;
}

export interface DocumentUpdate {
  title?: string;
  content?: DocumentContent;
  markdown?: string;
  front_matter?: Record<string, unknown>;
  status?: "draft" | "review" | "final";
}

export interface DocumentList {
  documents: Document[];
  total: number;
  page: number;
  per_page: number;
}

export interface Claim {
  id: string;
  claim_id: string;
  document_id: string;
  claim_text: string;
  claim_type: "DATA" | "LITERATURE" | "MIXED" | "HYPOTHESIS";
  status: "draft" | "verified" | "rejected" | "needs_revision";
  section?: string;
  start_offset?: number | null;
  end_offset?: number | null;
  evidence: Evidence[];
  source_sentences: string[];
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  type: string;
  source: string;
  description?: string;
}

export interface ClaimCreate {
  claim_text: string;
  claim_type: "DATA" | "LITERATURE" | "MIXED" | "HYPOTHESIS";
  section?: string;
  evidence?: Evidence[];
}

export interface ClaimUpdate {
  claim_text?: string;
  claim_type?: "DATA" | "LITERATURE" | "MIXED" | "HYPOTHESIS";
  status?: "draft" | "verified" | "rejected" | "needs_revision";
  section?: string;
  evidence?: Evidence[];
}

export interface BibEntry {
  id: string;
  bib_key: string;
  entry_type: string;
  title: string;
  author: string;
  year?: number;
  journal?: string;
  booktitle?: string;
  volume?: string;
  number?: string;
  pages?: string;
  publisher?: string;
  doi?: string;
  url?: string;
  abstract?: string;
  bibtex?: string;
  created_at: string;
}

export interface BibEntryCreate {
  bib_key: string;
  entry_type: string;
  title: string;
  author: string;
  year?: number;
  journal?: string;
  booktitle?: string;
  volume?: string;
  number?: string;
  pages?: string;
  publisher?: string;
  doi?: string;
  url?: string;
  abstract?: string;
}

export interface RewriteRequest {
  text: string;
  instruction: string;
  tone?: string;
}

export interface RewriteResponse {
  original: string;
  rewritten: string;
}

// Knowledge Base Types
export interface Note {
  id: string;
  slug: string;
  title: string;
  content: DocumentContent;
  markdown: string;
  note_type: "idea" | "summary" | "quote" | "concept";
  tags: string[];
  created_at: string;
  updated_at: string;
  backlink_count: number;
}

export interface NoteCreate {
  title: string;
  slug?: string;
  content?: DocumentContent;
  markdown?: string;
  note_type?: "idea" | "summary" | "quote" | "concept";
  tags?: string[];
}

export interface NoteUpdate {
  title?: string;
  content?: DocumentContent;
  markdown?: string;
  note_type?: "idea" | "summary" | "quote" | "concept";
  tags?: string[];
}

export interface NoteList {
  notes: Note[];
  total: number;
  page: number;
  per_page: number;
}

export interface GraphNode {
  id: string;
  type: "note" | "document" | "claim" | "bib";
  label: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Data Types
export interface ColumnInfo {
  name: string;
  type: "string" | "number" | "date" | "boolean";
  sample_values: unknown[];
}

export interface Dataset {
  id: string;
  slug: string;
  name: string;
  description: string;
  data_type: "csv" | "json" | "manual";
  data: Record<string, unknown>[];
  columns: ColumnInfo[];
  row_count: number;
  source_file: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetCreate {
  name: string;
  slug?: string;
  description?: string;
  data_type?: "csv" | "json" | "manual";
  data?: Record<string, unknown>[];
  columns?: ColumnInfo[];
}

export interface DatasetList {
  datasets: Dataset[];
  total: number;
  page: number;
  per_page: number;
}

export interface ChartConfig {
  x_column?: string;
  y_column?: string;
  color_column?: string;
  size_column?: string;
  title?: string;
  x_label?: string;
  y_label?: string;
  legend?: boolean;
  grid?: boolean;
  colors?: string[];
}

export interface Chart {
  id: string;
  slug: string;
  title: string;
  chart_type: "bar" | "line" | "scatter" | "pie" | "table" | "area";
  dataset_id: string | null;
  config: ChartConfig;
  created_at: string;
  updated_at: string;
}

export interface ChartCreate {
  title: string;
  slug?: string;
  chart_type: Chart["chart_type"];
  dataset_id?: string;
  config?: ChartConfig;
}

export interface ChartList {
  charts: Chart[];
  total: number;
  page: number;
  per_page: number;
}

export type ExportFormat =
  | "markdown"
  | "html"
  | "docx"
  | "pptx"
  | "latex"
  | "pdf";

export interface ExportJob {
  id: string;
  document_id: string;
  format: ExportFormat;
  status: "pending" | "running" | "done" | "failed";
  output_path?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationStatus {
  provider: string;
  connected: boolean;
  expires_at?: string | null;
}

export interface Comment {
  id: string;
  document_id: string;
  parent_id?: string | null;
  anchor_id?: string | null;
  provider: string;
  external_id?: string | null;
  author?: string | null;
  content: string;
  quote?: string | null;
  resolved: boolean;
  comment_scope?: string; // general | section | inline
  section?: string | null; // section name
  created_at: string;
  updated_at: string;
}

export interface CommentCreate {
  content: string;
  quote?: string;
  parent_id?: string | null;
  anchor_id?: string | null;
}

export interface CommentUpdate {
  resolved?: boolean;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  label?: string | null;
  created_at: string;
}

export interface DocumentVersionDetail extends DocumentVersion {
  content: Record<string, unknown>;
  markdown?: string | null;
}

export interface DocumentVersionCreate {
  label?: string | null;
}

// Google Sync Types
export type SyncStatusType =
  | "none"
  | "synced"
  | "local_changed"
  | "remote_changed"
  | "conflict";
export type ResolveStrategy = "keep_local" | "keep_remote";

export interface SyncStatus {
  linked: boolean;
  google_doc_id?: string | null;
  sync_status: SyncStatusType;
  last_synced_at?: string | null;
  google_revision_id?: string | null;
  local_version_hash?: string | null;
  warnings: string[];
}

export interface LinkResponse {
  success: boolean;
  google_doc_id: string;
  google_revision_id?: string | null;
  message?: string | null;
}

export interface PushResponse {
  success: boolean;
  new_revision_id?: string | null;
  claims_preserved: number;
  citations_preserved: number;
  warnings: string[];
  error?: string | null;
}

export interface PullResponse {
  success: boolean;
  claims_restored: number;
  citations_restored: number;
  warnings: string[];
  error?: string | null;
}

export interface ResolveResponse {
  success: boolean;
  new_sync_status: SyncStatusType;
  message?: string | null;
}

export interface DriveUrlResponse {
  url: string;
  file_type: "document" | "presentation";
}

// API Error
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

// Helper function for API calls
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers = new Headers(options.headers || {});

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Documents API
export const documentsApi = {
  list: (page = 1, perPage = 20): Promise<DocumentList> =>
    fetchApi(`/api/v1/documents?page=${page}&per_page=${perPage}`),

  get: (slug: string): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}`),

  create: (data: DocumentCreate): Promise<Document> =>
    fetchApi("/api/v1/documents", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: DocumentUpdate): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/documents/${slug}`, {
      method: "DELETE",
    }),

  import: async (
    file: File,
    title?: string,
    docType?: string,
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    if (docType) formData.append("doc_type", docType);

    const response = await fetch(`${API_BASE}/api/v1/documents/import`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Import failed" }));
      throw new ApiError(response.status, error.detail || "Import failed");
    }

    return response.json();
  },

  export: (slug: string, format: ExportFormat): Promise<ExportJob> =>
    fetchApi(`/api/v1/documents/${slug}/export`, {
      method: "POST",
      body: JSON.stringify({ format }),
    }),
};

// Claims API
export const claimsApi = {
  listByDocument: (slug: string, status?: string): Promise<Claim[]> => {
    const params = status ? `?status=${status}` : "";
    return fetchApi(`/api/v1/claims/document/${slug}${params}`);
  },

  get: (claimId: string): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}`),

  create: (slug: string, data: ClaimCreate): Promise<Claim> =>
    fetchApi(`/api/v1/claims/document/${slug}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (claimId: string, data: ClaimUpdate): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (claimId: string): Promise<void> =>
    fetchApi(`/api/v1/claims/${claimId}`, {
      method: "DELETE",
    }),

  verify: (claimId: string): Promise<Claim> =>
    fetchApi(`/api/v1/claims/${claimId}/verify`, {
      method: "POST",
    }),
};

// Bibliography API
export const bibliographyApi = {
  list: (limit = 100, offset = 0): Promise<BibEntry[]> =>
    fetchApi(`/api/v1/bibliography?limit=${limit}&offset=${offset}`),

  search: (query: string, limit = 20): Promise<BibEntry[]> =>
    fetchApi(
      `/api/v1/bibliography/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ),

  get: (bibKey: string): Promise<BibEntry> =>
    fetchApi(`/api/v1/bibliography/${bibKey}`),

  create: (data: BibEntryCreate): Promise<BibEntry> =>
    fetchApi("/api/v1/bibliography", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  delete: (bibKey: string): Promise<void> =>
    fetchApi(`/api/v1/bibliography/${bibKey}`, {
      method: "DELETE",
    }),

  importBibtex: (bibtex: string): Promise<BibEntry[]> =>
    fetchApi("/api/v1/bibliography/import", {
      method: "POST",
      body: JSON.stringify(bibtex),
    }),
};

// LLM API
export const llmApi = {
  rewrite: (data: RewriteRequest): Promise<RewriteResponse> =>
    fetchApi("/api/v1/llm/rewrite", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  extractClaims: (
    text: string,
  ): Promise<{ claims: Record<string, unknown>[] }> =>
    fetchApi("/api/v1/llm/extract-claims", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  improveHedging: (
    text: string,
  ): Promise<{ original: string; improved: string; changes: string[] }> =>
    fetchApi("/api/v1/llm/improve-hedging", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  extractClaimsForDocument: (slug: string): Promise<{ created: number }> =>
    fetchApi(`/api/v1/llm/extract-claims-document/${slug}`, {
      method: "POST",
    }),
};

// Notes API (Knowledge Base)
export const notesApi = {
  list: (
    page = 1,
    perPage = 20,
    search?: string,
    noteType?: string,
    tag?: string,
  ): Promise<NoteList> => {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
    });
    if (search) params.append("search", search);
    if (noteType) params.append("note_type", noteType);
    if (tag) params.append("tag", tag);
    return fetchApi(`/api/v1/notes?${params}`);
  },

  get: (slug: string): Promise<Note> => fetchApi(`/api/v1/notes/${slug}`),

  create: (data: NoteCreate): Promise<Note> =>
    fetchApi("/api/v1/notes", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: NoteUpdate): Promise<Note> =>
    fetchApi(`/api/v1/notes/${slug}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/notes/${slug}`, {
      method: "DELETE",
    }),

  getBacklinks: (
    slug: string,
  ): Promise<{ id: string; source_type: string; source_id: string }[]> =>
    fetchApi(`/api/v1/notes/${slug}/backlinks`),
};

// Graph API
export const graphApi = {
  getFullGraph: (
    includeDocuments = true,
    includeClaims = false,
    includeBib = true,
  ): Promise<GraphData> => {
    const params = new URLSearchParams({
      include_documents: String(includeDocuments),
      include_claims: String(includeClaims),
      include_bib: String(includeBib),
    });
    return fetchApi(`/api/v1/graph?${params}`);
  },

  getLocalGraph: (
    entityType: string,
    entityId: string,
    depth = 1,
  ): Promise<GraphData> =>
    fetchApi(`/api/v1/graph/local/${entityType}/${entityId}?depth=${depth}`),

  search: (query: string): Promise<GraphData> =>
    fetchApi(`/api/v1/graph/search?query=${encodeURIComponent(query)}`),
};

// Datasets API
export const datasetsApi = {
  list: (page = 1, perPage = 20, search?: string): Promise<DatasetList> => {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
    });
    if (search) params.append("search", search);
    return fetchApi(`/api/v1/datasets?${params}`);
  },

  get: (slug: string): Promise<Dataset> => fetchApi(`/api/v1/datasets/${slug}`),

  create: (data: DatasetCreate): Promise<Dataset> =>
    fetchApi("/api/v1/datasets", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  upload: async (file: File, name?: string): Promise<Dataset> => {
    const formData = new FormData();
    formData.append("file", file);
    if (name) formData.append("name", name);

    const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(response.status, error.detail || "Upload failed");
    }

    return response.json();
  },

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/datasets/${slug}`, {
      method: "DELETE",
    }),
};

// Charts API
export const chartsApi = {
  list: (
    page = 1,
    perPage = 20,
    search?: string,
    chartType?: string,
  ): Promise<ChartList> => {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
    });
    if (search) params.append("search", search);
    if (chartType) params.append("chart_type", chartType);
    return fetchApi(`/api/v1/charts?${params}`);
  },

  get: (slug: string): Promise<Chart> => fetchApi(`/api/v1/charts/${slug}`),

  create: (data: ChartCreate): Promise<Chart> =>
    fetchApi("/api/v1/charts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (slug: string, data: Partial<ChartCreate>): Promise<Chart> =>
    fetchApi(`/api/v1/charts/${slug}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (slug: string): Promise<void> =>
    fetchApi(`/api/v1/charts/${slug}`, {
      method: "DELETE",
    }),
};

// Exports API
export const exportsApi = {
  get: (jobId: string): Promise<ExportJob> =>
    fetchApi(`/api/v1/exports/${jobId}`),

  downloadUrl: (jobId: string): string =>
    `${API_BASE}/api/v1/exports/${jobId}/download`,
};

// Assets API
export interface AssetResponse {
  id: string;
  document_id?: string | null;
  filename: string;
  mime_type: string;
  size_bytes: number;
  url: string;
  source_url?: string | null;
  created_at: string;
}

export const assetsApi = {
  upload: async (file: File): Promise<AssetResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/v1/assets/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(response.status, error.detail || "Upload failed");
    }

    return response.json();
  },
};

// Integrations API
export const integrationsApi = {
  googleStatus: (): Promise<IntegrationStatus> =>
    fetchApi("/api/v1/integrations/google/status"),

  googleAuthUrl: (): Promise<{ url: string }> =>
    fetchApi("/api/v1/integrations/google/auth-url", { method: "POST" }),
};

// Google import/export API
export const googleApi = {
  importDoc: (
    fileId: string,
    title?: string,
    format?: "html" | "docx",
  ): Promise<{ slug: string; title: string }> =>
    fetchApi("/api/v1/google/docs/import", {
      method: "POST",
      body: JSON.stringify({ file_id: fileId, title, format }),
    }),

  exportDoc: (
    slug: string,
    folderId?: string,
  ): Promise<{ file_id: string; url?: string }> =>
    fetchApi("/api/v1/google/docs/export", {
      method: "POST",
      body: JSON.stringify({ slug, folder_id: folderId }),
    }),

  exportSlides: (
    slug: string,
    folderId?: string,
  ): Promise<{ file_id: string; url?: string }> =>
    fetchApi("/api/v1/google/slides/export", {
      method: "POST",
      body: JSON.stringify({ slug, folder_id: folderId }),
    }),

  importSlides: (
    fileId: string,
    title?: string,
    format?: "pptx",
  ): Promise<{ slug: string; title: string }> =>
    fetchApi("/api/v1/google/slides/import", {
      method: "POST",
      body: JSON.stringify({ file_id: fileId, title, format }),
    }),
};

// Google Docs Sync API
export const googleSyncApi = {
  // Documents
  link: (slug: string, googleDocId: string): Promise<LinkResponse> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/link`, {
      method: "POST",
      body: JSON.stringify({ google_doc_id: googleDocId }),
    }),

  unlink: (slug: string): Promise<{ success: boolean; message: string }> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/link`, {
      method: "DELETE",
    }),

  getStatus: (slug: string): Promise<SyncStatus> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/status`),

  push: (slug: string): Promise<PushResponse> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/push`, {
      method: "POST",
    }),

  pull: (slug: string): Promise<PullResponse> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/pull`, {
      method: "POST",
    }),

  resolve: (
    slug: string,
    strategy: ResolveStrategy,
  ): Promise<ResolveResponse> =>
    fetchApi(`/api/v1/google-sync/docs/${slug}/resolve`, {
      method: "POST",
      body: JSON.stringify({ strategy }),
    }),

  // Presentations (Google Slides)
  linkSlides: (slug: string, googleSlidesId: string): Promise<LinkResponse> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/link`, {
      method: "POST",
      body: JSON.stringify({ google_doc_id: googleSlidesId }),
    }),

  unlinkSlides: (
    slug: string,
  ): Promise<{ success: boolean; message: string }> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/link`, {
      method: "DELETE",
    }),

  getSlidesStatus: (slug: string): Promise<SyncStatus> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/status`),

  pushSlides: (slug: string): Promise<PushResponse> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/push`, {
      method: "POST",
    }),

  pullSlides: (slug: string): Promise<PullResponse> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/pull`, {
      method: "POST",
    }),

  resolveSlides: (
    slug: string,
    strategy: ResolveStrategy,
  ): Promise<ResolveResponse> =>
    fetchApi(`/api/v1/google-sync/slides/${slug}/resolve`, {
      method: "POST",
      body: JSON.stringify({ strategy }),
    }),

  // Common
  getDriveUrl: (slug: string): Promise<DriveUrlResponse> =>
    fetchApi(`/api/v1/google-sync/${slug}/drive-url`),
};

// Comments API
export const commentsApi = {
  list: (slug: string): Promise<Comment[]> =>
    fetchApi(`/api/v1/comments/document/${slug}`),

  create: (slug: string, data: CommentCreate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/document/${slug}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  syncGoogle: (slug: string): Promise<{ created: number }> =>
    fetchApi(`/api/v1/comments/document/${slug}/sync`, {
      method: "POST",
    }),

  createGoogle: (slug: string, data: CommentCreate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/document/${slug}/google`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (commentId: string, data: CommentUpdate): Promise<Comment> =>
    fetchApi(`/api/v1/comments/${commentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};

// Versions API
export const versionsApi = {
  list: (slug: string): Promise<DocumentVersion[]> =>
    fetchApi(`/api/v1/documents/${slug}/versions`),

  create: (
    slug: string,
    data: DocumentVersionCreate,
  ): Promise<DocumentVersion> =>
    fetchApi(`/api/v1/documents/${slug}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  restore: (slug: string, versionId: string): Promise<Document> =>
    fetchApi(`/api/v1/documents/${slug}/versions/${versionId}/restore`, {
      method: "POST",
    }),

  get: (slug: string, versionId: string): Promise<DocumentVersionDetail> =>
    fetchApi(`/api/v1/documents/${slug}/versions/${versionId}`),
};

// Track Changes types
export type ChangeType = "insert" | "delete";
export type ChangeStatus = "pending" | "accepted" | "rejected";

export interface TrackChange {
  id: number;
  document_id: string;
  change_id: string;
  change_type: ChangeType;
  content: string | null;
  position_start: number | null;
  position_end: number | null;
  author_name: string | null;
  author_email: string | null;
  status: ChangeStatus;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_comment: string | null;
}

export interface TrackChangesListResponse {
  changes: TrackChange[];
  total: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
}

export interface TrackChangeCreate {
  change_id: string;
  change_type: ChangeType;
  content?: string;
  position_start?: number;
  position_end?: number;
  author_name?: string;
  author_email?: string;
}

// Track Changes API
export const trackChangesApi = {
  list: (
    slug: string,
    status?: ChangeStatus,
  ): Promise<TrackChangesListResponse> => {
    const params = status ? `?status=${status}` : "";
    return fetchApi(`/api/v1/documents/${slug}/changes${params}`);
  },

  create: (slug: string, change: TrackChangeCreate): Promise<TrackChange> =>
    fetchApi(`/api/v1/documents/${slug}/changes`, {
      method: "POST",
      body: JSON.stringify(change),
    }),

  get: (slug: string, changeId: string): Promise<TrackChange> =>
    fetchApi(`/api/v1/documents/${slug}/changes/${changeId}`),

  resolve: (
    slug: string,
    changeId: string,
    action: "accept" | "reject",
    comment?: string,
    resolvedBy?: string,
  ): Promise<{ success: boolean; change: TrackChange; message: string }> =>
    fetchApi(`/api/v1/documents/${slug}/changes/${changeId}/resolve`, {
      method: "POST",
      body: JSON.stringify({ action, comment, resolved_by: resolvedBy }),
    }),

  bulkResolve: (
    slug: string,
    changeIds: string[],
    action: "accept" | "reject",
    comment?: string,
    resolvedBy?: string,
  ): Promise<{ success: boolean; resolved_count: number; message: string }> =>
    fetchApi(`/api/v1/documents/${slug}/changes/bulk-resolve`, {
      method: "POST",
      body: JSON.stringify({
        change_ids: changeIds,
        action,
        comment,
        resolved_by: resolvedBy,
      }),
    }),

  acceptAll: (
    slug: string,
    resolvedBy?: string,
  ): Promise<{ success: boolean; resolved_count: number; message: string }> =>
    fetchApi(`/api/v1/documents/${slug}/changes/accept-all`, {
      method: "POST",
      body: JSON.stringify({ resolved_by: resolvedBy }),
    }),

  rejectAll: (
    slug: string,
    resolvedBy?: string,
  ): Promise<{ success: boolean; resolved_count: number; message: string }> =>
    fetchApi(`/api/v1/documents/${slug}/changes/reject-all`, {
      method: "POST",
      body: JSON.stringify({ resolved_by: resolvedBy }),
    }),

  delete: (
    slug: string,
    changeId: string,
  ): Promise<{ success: boolean; message: string }> =>
    fetchApi(`/api/v1/documents/${slug}/changes/${changeId}`, {
      method: "DELETE",
    }),

  extractFromContent: (
    slug: string,
    content: Record<string, unknown>,
    authorName?: string,
    authorEmail?: string,
  ): Promise<TrackChangesListResponse> =>
    fetchApi(`/api/v1/documents/${slug}/changes/extract`, {
      method: "POST",
      body: JSON.stringify({
        content,
        author_name: authorName,
        author_email: authorEmail,
      }),
    }),
};

// Review types
export interface SuggestedEdit {
  original_text: string;
  replacement_text: string;
  rationale: string;
}

export interface ReviewCommentResponse {
  comment_id: string;
  comment_content: string;
  comment_author: string | null;
  response_type:
    | "agree"
    | "disagree"
    | "partial"
    | "clarification"
    | "editorial";
  response_text: string;
  suggested_edit: SuggestedEdit | null;
}

export interface ReviewAnalysis {
  document_slug: string;
  total_comments: number;
  responses: ReviewCommentResponse[];
  summary: string;
}

export interface ReviewStatus {
  document_slug: string;
  total_comments: number;
  pending_comments: number;
  resolved_comments: number;
  has_google_link: boolean;
}

export interface WorkspaceFile {
  name: string;
  relative_path: string;
  category: string;
  kind: "text" | "image" | "binary";
  size_bytes: number;
  preview_url: string;
}

export interface WorkspaceBundle {
  workspace: {
    slug: string;
    title: string;
    description: string;
    recommended_document_slug: string;
  };
  report: {
    title: string;
    relative_path: string;
    preview_url: string;
    sections: { level: number; title: string }[];
    excerpt: string;
  };
  sources: {
    report_files: WorkspaceFile[];
    review_files: WorkspaceFile[];
    verification_files: WorkspaceFile[];
    figure_files: WorkspaceFile[];
  };
}

export interface DictationSession {
  id: string;
  slug: string;
  title: string;
  workspace_slug: string;
  document_slug?: string | null;
  status: string;
  transcript: string;
  notes: string;
  chunk_count: number;
  chunk_log: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

export interface DictationChunkResponse {
  chunk_index: number;
  transcript: string;
  session: DictationSession;
}

export interface WorkspaceLoginResponse {
  ok: boolean;
  authenticated: boolean;
  user: {
    email: string;
    name?: string;
    role?: string;
  };
}

export interface ApplyItem {
  comment_id: string;
  response_text: string;
  apply_edit?: boolean;
  push_to_google?: boolean;
}

// Review API
export const reviewApi = {
  status: (slug: string): Promise<ReviewStatus> =>
    fetchApi(`/api/v1/review/${slug}/status`),

  analyze: (slug: string): Promise<ReviewAnalysis> =>
    fetchApi(`/api/v1/review/${slug}/analyze`, { method: "POST" }),

  apply: (
    slug: string,
    items: ApplyItem[],
  ): Promise<{
    applied_replies: number;
    applied_edits: number;
    errors: string[];
  }> =>
    fetchApi(`/api/v1/review/${slug}/apply`, {
      method: "POST",
      body: JSON.stringify({ items }),
    }),

  importFeedback: (
    slug: string,
    items: {
      author: string;
      content: string;
      quote?: string;
      feedback_type?: string;
    }[],
    source?: string,
  ): Promise<{ created: number }> =>
    fetchApi(`/api/v1/comments/document/${slug}/import-feedback`, {
      method: "POST",
      body: JSON.stringify({ items, source: source || "email" }),
    }),
};

export const workspacesApi = {
  getCifMedicamentos: (): Promise<WorkspaceBundle> =>
    fetchApi("/api/v1/workspaces/cif-medicamentos"),
};

export const dictationApi = {
  seedCifWorkspace: (): Promise<{ slug: string; title: string; workspace_slug: string }> =>
    fetchApi("/api/v1/dictation/workspace/cif-medicamentos/seed", {
      method: "POST",
    }),

  createSession: (documentSlug: string): Promise<DictationSession> => {
    const form = new FormData();
    form.append("title", `Dictado ${documentSlug}`);
    form.append("workspace_slug", "cif-medicamentos");
    form.append("document_slug", documentSlug);
    return fetchApi("/api/v1/dictation/sessions", {
      method: "POST",
      body: form,
      headers: undefined,
    });
  },

  getSession: (slug: string): Promise<DictationSession> =>
    fetchApi(`/api/v1/dictation/sessions/${slug}`),

  transcribeChunk: (
    slug: string,
    audioFile: File,
    chunkIndex: number,
  ): Promise<DictationChunkResponse> => {
    const form = new FormData();
    form.append("audio", audioFile);
    form.append("chunk_index", String(chunkIndex));
    return fetchApi(`/api/v1/dictation/sessions/${slug}/chunks`, {
      method: "POST",
      body: form,
      headers: undefined,
    });
  },
};

export const authApi = {
  workspaceLogin: (password: string): Promise<WorkspaceLoginResponse> =>
    fetchApi("/api/v1/auth/workspace-login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
};

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
  googleSync: googleSyncApi,
  comments: commentsApi,
  versions: versionsApi,
  trackChanges: trackChangesApi,
  review: reviewApi,
  workspaces: workspacesApi,
  dictation: dictationApi,
  auth: authApi,
};

export default api;
