# Scribe API Reference

> Base URL: `http://localhost:8000` (dev) | `https://scribe.illanes00.cl` (prod)
> API Version: v1
> Prefix: `/api/v1`

---

## Table of Contents

1. [Documents](#documents)
2. [Claims](#claims)
3. [Bibliography](#bibliography)
4. [LLM (AI Features)](#llm-ai-features)
5. [Google Integration](#google-integration)
6. [Comments](#comments)
7. [Exports](#exports)
8. [Notes (Knowledge Base)](#notes-knowledge-base)
9. [Datasets](#datasets)
10. [Charts](#charts)
11. [Integrations (OAuth)](#integrations-oauth)

---

## Documents

### List Documents

```http
GET /api/v1/documents
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 20 | Items per page |
| doc_type | string | null | Filter by type (paper, thesis, policy, presentation) |

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "slug": "document-slug",
      "title": "Document Title",
      "doc_type": "paper",
      "status": "draft",
      "version": "1.0.0",
      "claim_count": 5,
      "verified_count": 2,
      "created_at": "2026-01-16T12:00:00",
      "updated_at": "2026-01-16T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

### Get Document

```http
GET /api/v1/documents/{slug}
```

**Response:**
```json
{
  "id": "uuid",
  "slug": "document-slug",
  "title": "Document Title",
  "doc_type": "paper",
  "content": {
    "json": { "type": "doc", "content": [...] },
    "html": "<p>...</p>"
  },
  "markdown": "# Document\n\nContent...",
  "front_matter": {
    "style": "classic",
    "slides_data": {...}
  },
  "source_provider": "google",
  "source_id": "google-file-id",
  "status": "draft",
  "version": "1.0.0",
  "claim_count": 5,
  "verified_count": 2,
  "created_at": "2026-01-16T12:00:00",
  "updated_at": "2026-01-16T12:00:00"
}
```

### Create Document

```http
POST /api/v1/documents
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "New Document",
  "doc_type": "paper",
  "content": { "json": { "type": "doc", "content": [] } },
  "markdown": "",
  "front_matter": {},
  "slug": "new-document"  // Optional, auto-generated if omitted
}
```

**Response:** Same as Get Document

### Update Document

```http
PUT /api/v1/documents/{slug}
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": { "json": {...} },
  "markdown": "...",
  "status": "review"
}
```

### Delete Document

```http
DELETE /api/v1/documents/{slug}
```

**Response:**
```json
{ "status": "deleted" }
```

### Import Document

```http
POST /api/v1/documents/import
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Markdown, DOCX, or HTML file |
| title | string | No | Override title |
| doc_type | string | No | Document type |

**Response:** Created document object

---

## Claims

### List Claims for Document

```http
GET /api/v1/claims/document/{slug}
```

**Response:**
```json
{
  "claims": [
    {
      "id": "uuid",
      "claim_id": "C-abc123",
      "claim_text": "El gasto aumentó 23%",
      "claim_type": "DATA",
      "status": "draft",
      "section": "Resumen",
      "evidence": [],
      "source_sentences": [],
      "created_at": "2026-01-16T12:00:00"
    }
  ],
  "total": 10
}
```

### Create Claim

```http
POST /api/v1/claims/document/{slug}
Content-Type: application/json
```

**Request Body:**
```json
{
  "claim_text": "New claim text",
  "claim_type": "DATA",
  "section": "Introduction"
}
```

### Get Claim

```http
GET /api/v1/claims/{claim_id}
```

### Update Claim

```http
PUT /api/v1/claims/{claim_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "claim_text": "Updated claim",
  "claim_type": "LITERATURE",
  "status": "verified",
  "evidence": [
    { "source": "BID Report 2024", "url": "https://..." }
  ]
}
```

### Delete Claim

```http
DELETE /api/v1/claims/{claim_id}
```

### Verify Claim

```http
POST /api/v1/claims/{claim_id}/verify
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "verified",
  "evidence": [...]
}
```

---

## Bibliography

### List Entries

```http
GET /api/v1/bibliography
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| search | string | Search in title/author |
| entry_type | string | Filter by type (article, book, etc.) |

**Response:**
```json
{
  "entries": [
    {
      "id": "uuid",
      "bib_key": "smith2024",
      "entry_type": "article",
      "title": "Study Title",
      "author": "Smith, John",
      "year": 2024,
      "journal": "Nature",
      "doi": "10.1000/xyz",
      "bibtex": "@article{smith2024,...}"
    }
  ]
}
```

### Import BibTeX

```http
POST /api/v1/bibliography/import
Content-Type: application/json
```

**Request Body:**
```json
{
  "bibtex": "@article{smith2024,\n  title={...},\n  author={...}\n}"
}
```

**Response:**
```json
{
  "imported": 3,
  "entries": [...]
}
```

### Get Entry

```http
GET /api/v1/bibliography/{bib_key}
```

### Delete Entry

```http
DELETE /api/v1/bibliography/{bib_key}
```

---

## LLM (AI Features)

### Rewrite Text

```http
POST /api/v1/llm/rewrite
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Original text to rewrite",
  "style": "academic",  // Options: academic, concise, formal, simple
  "language": "es"      // Optional, default: auto-detect
}
```

**Response:**
```json
{
  "original": "Original text...",
  "rewritten": "Rewritten text in academic style...",
  "changes": ["Made more formal", "Added hedging"]
}
```

### Extract Claims from Text

```http
POST /api/v1/llm/extract-claims
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "El gasto aumentó 23% según datos del BID...",
  "doc_type": "policy"  // Optional context
}
```

**Response:**
```json
{
  "claims": [
    {
      "text": "El gasto aumentó 23%",
      "type": "DATA",
      "section": null,
      "confidence": 0.95
    }
  ]
}
```

### Extract Claims from Document

```http
POST /api/v1/llm/extract-claims-document/{slug}
```

**Response:**
```json
{
  "claims": [...],
  "created": 5,
  "existing": 2
}
```

### Improve Hedging

```http
POST /api/v1/llm/improve-hedging
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "This proves that X causes Y."
}
```

**Response:**
```json
{
  "original": "This proves that X causes Y.",
  "improved": "The evidence suggests that X may contribute to Y.",
  "changes": ["Added 'suggests'", "Changed 'proves' to hedged language"]
}
```

### Summarize Document

```http
POST /api/v1/llm/summarize
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Long document text...",
  "max_length": 500,
  "format": "bullets"  // Options: paragraph, bullets
}
```

**Response:**
```json
{
  "summary": "• Key point 1\n• Key point 2\n• Key point 3"
}
```

---

## Google Integration

### Import from Google Docs

```http
POST /api/v1/google/docs/import
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_id": "1abc123...",  // Google Drive file ID
  "doc_type": "policy"
}
```

**Response:** Created document object

### Export to Google Docs

```http
POST /api/v1/google/docs/export
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_slug": "my-document",
  "folder_id": "1xyz..."  // Optional, defaults to root
}
```

**Response:**
```json
{
  "file_id": "1abc...",
  "url": "https://docs.google.com/document/d/1abc.../edit"
}
```

### Export to Google Slides

```http
POST /api/v1/google/slides/export
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_slug": "my-presentation",
  "folder_id": "1xyz..."
}
```

**Response:**
```json
{
  "file_id": "1def...",
  "url": "https://docs.google.com/presentation/d/1def.../edit"
}
```

---

## Comments

### List Comments for Document

```http
GET /api/v1/comments/document/{slug}
```

**Response:**
```json
{
  "comments": [
    {
      "id": "uuid",
      "anchor_id": "comment-anchor-1",
      "author": "User",
      "content": "Comment text",
      "quote": "Quoted text from document",
      "resolved": false,
      "replies": [...],
      "created_at": "2026-01-16T12:00:00"
    }
  ]
}
```

### Create Comment

```http
POST /api/v1/comments/document/{slug}
Content-Type: application/json
```

**Request Body:**
```json
{
  "anchor_id": "unique-anchor-id",
  "content": "Comment text",
  "quote": "Selected text",
  "parent_id": null  // For replies
}
```

### Update Comment

```http
PUT /api/v1/comments/{comment_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Updated comment",
  "resolved": true
}
```

### Delete Comment

```http
DELETE /api/v1/comments/{comment_id}
```

---

## Exports

### Start Export Job

```http
POST /api/v1/documents/{slug}/export
Content-Type: application/json
```

**Request Body:**
```json
{
  "format": "pdf",  // Options: pdf, docx, pptx, md, html, latex
  "options": {
    "template": "academic",
    "include_bibliography": true
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "format": "pdf",
  "created_at": "2026-01-16T12:00:00"
}
```

### Get Export Job Status

```http
GET /api/v1/exports/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "complete",  // pending, processing, complete, failed
  "format": "pdf",
  "download_url": "/api/v1/exports/{job_id}/download",
  "error": null
}
```

### Download Export

```http
GET /api/v1/exports/{job_id}/download
```

**Response:** Binary file stream with appropriate Content-Type

---

## Notes (Knowledge Base)

### List Notes

```http
GET /api/v1/notes
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| search | string | Search in title/content |
| note_type | string | Filter by type |
| tags | string | Comma-separated tag filter |

**Response:**
```json
{
  "notes": [
    {
      "id": "uuid",
      "slug": "note-slug",
      "title": "Note Title",
      "note_type": "concept",
      "tags": ["research", "policy"],
      "created_at": "2026-01-16T12:00:00"
    }
  ]
}
```

### Create Note

```http
POST /api/v1/notes
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "New Note",
  "content": { "json": {...} },
  "markdown": "...",
  "note_type": "idea",
  "tags": ["tag1", "tag2"]
}
```

### Get Note

```http
GET /api/v1/notes/{slug}
```

### Update Note

```http
PUT /api/v1/notes/{slug}
Content-Type: application/json
```

### Delete Note

```http
DELETE /api/v1/notes/{slug}
```

### Get Knowledge Graph

```http
GET /api/v1/graph
```

**Response:**
```json
{
  "nodes": [
    { "id": "note-1", "label": "Note Title", "type": "concept" }
  ],
  "edges": [
    { "source": "note-1", "target": "note-2", "type": "references" }
  ]
}
```

---

## Datasets

### List Datasets

```http
GET /api/v1/datasets
```

### Upload Dataset

```http
POST /api/v1/datasets/upload
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Description |
|-------|------|-------------|
| file | file | CSV file |
| name | string | Dataset name |

### Get Dataset

```http
GET /api/v1/datasets/{id}
```

### Query Dataset

```http
POST /api/v1/datasets/{id}/query
Content-Type: application/json
```

**Request Body:**
```json
{
  "columns": ["year", "value"],
  "filters": [
    { "column": "year", "op": ">=", "value": 2020 }
  ],
  "group_by": ["year"],
  "aggregations": [
    { "column": "value", "function": "sum" }
  ]
}
```

---

## Charts

### Create Chart

```http
POST /api/v1/charts
Content-Type: application/json
```

**Request Body:**
```json
{
  "dataset_id": "uuid",
  "chart_type": "bar",  // bar, line, pie, scatter
  "title": "Chart Title",
  "config": {
    "x_column": "year",
    "y_column": "value",
    "color_column": "category"
  }
}
```

### Get Chart

```http
GET /api/v1/charts/{id}
```

### Export Chart as Image

```http
GET /api/v1/charts/{id}/export?format=png
```

---

## Integrations (OAuth)

### Check Integration Status

```http
GET /api/v1/integrations/google/status
```

**Response:**
```json
{
  "connected": true,
  "email": "user@example.com",
  "expires_at": "2026-01-16T12:00:00"
}
```

### Get OAuth URL

```http
POST /api/v1/integrations/google/auth-url
```

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### OAuth Callback (Internal)

```http
GET /api/v1/integrations/google/callback?code=xxx
```

Handles OAuth callback and stores tokens.

### Disconnect Integration

```http
DELETE /api/v1/integrations/google
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field": "field_name"  // Optional, for validation errors
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## Rate Limits

Currently no rate limiting is implemented. For production:

- Recommended: 100 requests/minute per IP
- LLM endpoints: 10 requests/minute (expensive)

---

## Health Check

### Simple Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Scribe API",
  "host": "hostname"
}
```

### API Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Scribe API",
  "host": "hostname",
  "environment": "production"
}
```

### Detailed Health Check

```http
GET /api/v1/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Scribe API",
  "environment": "production",
  "host": "hostname",
  "timestamp": "2026-01-20T12:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.5,
      "message": "Connected"
    },
    "google_integration": {
      "status": "healthy",
      "message": "OAuth credentials configured"
    },
    "llm_service": {
      "status": "healthy",
      "message": "Anthropic API key configured"
    }
  }
}
```

Status values: `healthy`, `degraded`, `unhealthy`

---

## Assets

### Upload Asset

```http
POST /api/v1/assets/upload
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Description |
|-------|------|-------------|
| file | file | Image or file to upload |

**Response:**
```json
{
  "filename": "uuid.png",
  "url": "/uploads/uuid.png",
  "content_type": "image/png",
  "size": 12345
}
```

### Get Asset

```http
GET /api/v1/assets/{filename}
```

**Response:** Binary file stream

### Delete Asset

```http
DELETE /api/v1/assets/{filename}
```

**Response:**
```json
{
  "status": "deleted"
}
```

---

## Document Versions

### List Versions

```http
GET /api/v1/documents/{slug}/versions
```

**Response:**
```json
{
  "versions": [
    {
      "id": "uuid",
      "label": "Draft 1",
      "created_at": "2026-01-16T12:00:00"
    }
  ]
}
```

### Create Version (Snapshot)

```http
POST /api/v1/documents/{slug}/versions
Content-Type: application/json
```

**Request Body:**
```json
{
  "label": "Before major changes"
}
```

### Get Version

```http
GET /api/v1/documents/{slug}/versions/{version_id}
```

**Response:** Full document content at that version

### Restore Version

```http
POST /api/v1/documents/{slug}/versions/{version_id}/restore
```

Restores document to this version (creates new version first).

---

## Authentication

Currently single-user, no authentication required.

For future multi-user support:
- JWT tokens in `Authorization: Bearer <token>` header
- OAuth2 with Google for social login
