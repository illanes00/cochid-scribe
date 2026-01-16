# Scribe Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              SCRIBE SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │   Browser    │────▶│   Nginx      │────▶│   Next.js Frontend       │ │
│  │   (User)     │     │   Proxy      │     │   Port 8132              │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│                              │                        │                  │
│                              │                        │ API Calls        │
│                              ▼                        ▼                  │
│                       ┌──────────────────────────────────┐              │
│                       │       FastAPI Backend            │              │
│                       │       Port 8000                  │              │
│                       └──────────────────────────────────┘              │
│                              │              │           │                │
│              ┌───────────────┼──────────────┼───────────┼───────────┐   │
│              ▼               ▼              ▼           ▼           │   │
│       ┌──────────┐    ┌──────────┐   ┌──────────┐ ┌──────────┐     │   │
│       │ SQLite   │    │ Anthropic│   │ Google   │ │  Pandoc  │     │   │
│       │ Database │    │ Claude   │   │ APIs     │ │  Export  │     │   │
│       └──────────┘    └──────────┘   └──────────┘ └──────────┘     │   │
│                                                                      │   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Frontend Architecture (Next.js 14)

```
frontend/
├── app/                          # App Router (Next.js 14)
│   ├── layout.tsx               # Root layout with global styles
│   ├── page.tsx                 # Landing page (redirects to /dashboard)
│   ├── dashboard/
│   │   └── page.tsx             # Document list, create new docs
│   ├── editor/
│   │   └── [slug]/
│   │       └── page.tsx         # MAIN EDITOR PAGE (751 lines)
│   │                            # - TipTap integration
│   │                            # - Sidebar panels
│   │                            # - Export controls
│   │                            # - Presentation mode toggle
│   ├── knowledge/
│   │   ├── page.tsx             # Notes list
│   │   ├── [slug]/page.tsx      # Note editor
│   │   └── graph/page.tsx       # Knowledge graph visualization
│   ├── data/
│   │   ├── page.tsx             # Datasets list
│   │   └── [slug]/page.tsx      # Dataset viewer + chart builder
│   └── integrations/
│       └── page.tsx             # Google OAuth connection UI
│
├── components/
│   ├── editor/
│   │   ├── TiptapEditor.tsx     # Core TipTap wrapper
│   │   │                        # - Configures all extensions
│   │   │                        # - Handles content changes
│   │   │                        # - Bubble menu for formatting
│   │   │
│   │   ├── SlideEditor.tsx      # Individual slide editor
│   │   │                        # - Layout selection
│   │   │                        # - Background controls
│   │   │                        # - Content area (TODO: TipTap)
│   │   │
│   │   ├── SlideNavigator.tsx   # Slide thumbnails sidebar
│   │   │                        # - Drag-drop reordering
│   │   │                        # - Add/delete slides
│   │   │                        # - Quick navigation
│   │   │
│   │   ├── PresentationView.tsx # Full presentation view
│   │   │                        # - Slide navigation
│   │   │                        # - Fullscreen mode
│   │   │                        # - Keyboard controls
│   │   │
│   │   └── extensions/          # TipTap Extensions
│   │       ├── claim.ts         # Claim mark (highlights claims)
│   │       ├── citation.ts      # Citation mark [@author2024]
│   │       ├── comment.ts       # Comment marks + threads
│   │       ├── track-changes.ts # Insert/delete tracking
│   │       └── slash-commands.ts# "/" command palette
│   │
│   └── panels/
│       ├── ClaimsPanel.tsx      # List claims, verify status
│       ├── BibliographyPanel.tsx# Search, import BibTeX
│       ├── CommentsPanel.tsx    # Comment threads
│       ├── VersionsPanel.tsx    # Version history
│       ├── OutlinePanel.tsx     # Document structure nav
│       └── AIAssistantPanel.tsx # AI rewriting interface
│
├── lib/
│   ├── api.ts                   # Typed API client (778 lines)
│   │                            # - All endpoint functions
│   │                            # - TypeScript interfaces
│   │                            # - Error handling
│   └── templates.ts             # Document templates
│
├── hooks/
│   └── useDocument.ts           # Document state management
│                                # - Fetch, save, autosave
│                                # - Optimistic updates
│
└── styles/
    └── globals.css              # Tailwind + custom styles
                                 # - Editor theme
                                 # - Espacio Público colors
```

### 2. Backend Architecture (FastAPI)

```
backend/app/
├── main.py                      # FastAPI app initialization
│                                # - CORS configuration
│                                # - Router registration
│                                # - Middleware setup
│
├── config.py                    # Settings (pydantic-settings)
│                                # - Environment variables
│                                # - Default values
│
├── db/
│   └── session.py               # Database session management
│                                # - SQLAlchemy engine
│                                # - Session dependency
│
├── models/                      # SQLAlchemy ORM Models
│   ├── document.py              # Document model
│   ├── claim.py                 # Claim model
│   ├── bibliography.py          # BibliographyEntry model
│   ├── comment.py               # Comment model
│   ├── note.py                  # Note model
│   ├── dataset.py               # Dataset model
│   ├── document_version.py      # DocumentVersion model
│   ├── export.py                # ExportJob model
│   └── integration.py           # Integration model (OAuth tokens)
│
├── schemas/                     # Pydantic Schemas (Request/Response)
│   ├── document.py              # DocumentCreate, DocumentResponse
│   ├── claim.py                 # ClaimCreate, ClaimResponse
│   ├── bibliography.py          # BibEntryCreate, BibEntryResponse
│   └── ... (mirrors models)
│
├── api/v1/                      # API Routers
│   ├── documents.py             # /api/v1/documents/*
│   │                            # - CRUD operations
│   │                            # - Import (file upload)
│   │                            # - Export (start job)
│   │
│   ├── claims.py                # /api/v1/claims/*
│   │                            # - Claim CRUD
│   │                            # - Verify/reject claims
│   │
│   ├── bibliography.py          # /api/v1/bibliography/*
│   │                            # - BibTeX import
│   │                            # - Search entries
│   │
│   ├── llm.py                   # /api/v1/llm/*
│   │                            # - Rewrite text
│   │                            # - Extract claims (AI)
│   │                            # - Improve hedging
│   │                            # - Summarize
│   │
│   ├── google.py                # /api/v1/google/*
│   │                            # - Import from Google Docs
│   │                            # - Export to Google Docs/Slides
│   │
│   ├── integrations.py          # /api/v1/integrations/*
│   │                            # - OAuth flow
│   │                            # - Token management
│   │
│   ├── comments.py              # /api/v1/comments/*
│   ├── exports.py               # /api/v1/exports/*
│   ├── notes.py                 # /api/v1/notes/*
│   ├── datasets.py              # /api/v1/datasets/*
│   ├── charts.py                # /api/v1/charts/*
│   ├── graph.py                 # /api/v1/graph/*
│   └── assets.py                # /api/v1/assets/* (partial)
│
└── services/                    # Business Logic
    ├── conversion.py            # Markdown ↔ TipTap ↔ exports
    ├── content_links.py         # Detect internal links
    ├── google.py                # Google API client wrapper
    ├── llm/                     # LLM service (Anthropic)
    ├── importer/                # File import logic
    ├── compiler/                # Export compilation
    ├── graph/                   # Knowledge graph builder
    └── data/                    # Dataset processing
```

---

## Data Flow Diagrams

### 1. Document Save Flow

```
User Edits in TipTap
        │
        ▼
TiptapEditor.tsx (onUpdate)
        │
        ▼
useDocument.ts (debouncedSave)
        │
        ▼
api.ts → PUT /api/v1/documents/{slug}
        │
        ▼
documents.py (update_document)
        │
        ├─────────────────────────────────┐
        ▼                                 ▼
Update DB                        [TODO] Extract Claims
(SQLAlchemy)                     via LLM if content changed
        │
        ▼
Return DocumentResponse
```

### 2. Claim Extraction Flow

```
POST /api/v1/llm/extract-claims-document/{slug}
        │
        ▼
llm.py (extract_claims_from_document)
        │
        ├─── Get document markdown
        │
        ▼
Anthropic API Call
(claude-sonnet-4-20250514)
        │
Prompt: "Analyze text, identify
verifiable claims with types"
        │
        ▼
Parse JSON Response
[{text, type, section}, ...]
        │
        ▼
Create Claim records in DB
        │
        ▼
[TODO] Update TipTap content
with claim marks
        │
        ▼
Return ClaimResponse[]
```

### 3. Google Docs Import Flow

```
POST /api/v1/google/docs/import
{file_id: "Google Doc ID"}
        │
        ▼
google.py (import_google_doc)
        │
        ├─── Check OAuth token valid
        │
        ▼
Google Docs API
→ documents.get()
→ Export as HTML
        │
        ▼
services/conversion.py
HTML → Markdown → TipTap JSON
        │
        ▼
Create/Update Document
with source_provider="google"
source_id=file_id
        │
        ▼
[TODO] Sync comments from
Google Docs
        │
        ▼
Return DocumentResponse
```

### 4. Export to PPTX Flow

```
POST /api/v1/documents/{slug}/export
{format: "pptx"}
        │
        ▼
exports.py (start_export)
        │
Create ExportJob (status=pending)
        │
        ▼
Background Task
        │
        ├─── Get document content
        │
        ▼
services/conversion.py
TipTap JSON → Markdown
        │
        ▼
Pandoc subprocess
pandoc -t pptx -o output.pptx
        │
        ▼
Save to uploads/exports/
Update ExportJob (status=complete)
        │
        ▼
GET /api/v1/exports/{job_id}/download
        │
        ▼
Return file response
```

---

## TipTap Extension Architecture

### Claim Extension (claim.ts)

```typescript
// Mark schema
{
  name: 'claim',
  type: 'mark',
  attrs: {
    claimId: { default: null }  // Links to claims table
  }
}

// Rendered as:
<span class="claim-highlight" data-claim-id="C-abc123">
  El gasto aumentó 23%
</span>

// CSS styling:
.claim-highlight {
  background: rgba(59, 130, 246, 0.2);
  border-bottom: 2px solid #3b82f6;
}
```

### Citation Extension (citation.ts)

```typescript
// Node schema
{
  name: 'citation',
  type: 'node',
  inline: true,
  attrs: {
    bibKey: { default: '' }  // e.g., "smith2024"
  }
}

// Rendered as:
<span class="citation" data-bib-key="smith2024">
  [Smith, 2024]
</span>
```

### Slash Commands Extension (slash-commands.ts)

```typescript
// Available commands
const commands = [
  { title: 'Heading 1', command: 'heading', attrs: { level: 1 } },
  { title: 'Heading 2', command: 'heading', attrs: { level: 2 } },
  { title: 'Bullet List', command: 'bulletList' },
  { title: 'Numbered List', command: 'orderedList' },
  { title: 'Quote', command: 'blockquote' },
  { title: 'Code Block', command: 'codeBlock' },
  { title: 'Horizontal Rule', command: 'horizontalRule' },
  { title: 'Add Citation', command: 'citation' },
  { title: 'Mark as Claim', command: 'claim' },
]
```

---

## Database Entity Relationships

```
┌─────────────────┐       ┌─────────────────┐
│    documents    │       │     claims      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ document_id (FK)│
│ slug            │       │ id (PK)         │
│ title           │       │ claim_id        │
│ doc_type        │       │ claim_text      │
│ content (JSON)  │       │ claim_type      │
│ markdown        │       │ status          │
│ front_matter    │       │ evidence (JSON) │
│ version         │       └─────────────────┘
│ status          │
│ source_provider │       ┌─────────────────┐
│ source_id       │       │    comments     │
└─────────────────┘       ├─────────────────┤
        │                 │ document_id (FK)│──►
        │                 │ id (PK)         │
        │                 │ anchor_id       │
        │                 │ content         │
        │                 │ resolved        │
        │                 └─────────────────┘
        │
        │                 ┌─────────────────┐
        │                 │document_versions│
        ├────────────────►├─────────────────┤
        │                 │ document_id (FK)│
        │                 │ id (PK)         │
        │                 │ label           │
        │                 │ content (JSON)  │
        │                 └─────────────────┘
        │
        │                 ┌─────────────────┐
        │                 │  integrations   │
        └────────────────►├─────────────────┤
                          │ id (PK)         │
                          │ provider        │
                          │ access_token    │
                          │ refresh_token   │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│bibliography_    │       │     notes       │
│entries          │       ├─────────────────┤
├─────────────────┤       │ id (PK)         │
│ id (PK)         │       │ slug            │
│ bib_key         │       │ title           │
│ entry_type      │       │ content (JSON)  │
│ title           │       │ note_type       │
│ author          │       │ tags (JSON)     │
│ year            │       └─────────────────┘
│ bibtex          │
└─────────────────┘
```

---

## Security Architecture

### Current State

```
┌─────────────────────────────────────────────────┐
│               SECURITY MODEL                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  Authentication: NONE (single-user app)         │
│                                                  │
│  OAuth: Google OAuth 2.0 for Drive access       │
│         - Tokens stored in integrations table   │
│         - Refresh handled automatically         │
│                                                  │
│  CORS: Configured in main.py                    │
│        - Origins: from CORS_ORIGINS env var     │
│                                                  │
│  API: No rate limiting                          │
│       No API keys                               │
│                                                  │
│  Database: SQLite (no encryption)               │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Future Considerations

For multi-user deployment:
1. Add JWT authentication
2. Add user model and document ownership
3. Add API rate limiting
4. Use PostgreSQL with encryption
5. Add RBAC (role-based access control)

---

## Environment Configuration

### Development (.env)

```bash
DEBUG=true
DATABASE_URL=sqlite:///./scribe.db
SECRET_KEY=dev-secret-key
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback
CORS_ORIGINS=["http://localhost:3000"]
```

### Production (.env)

```bash
DEBUG=false
DATABASE_URL=postgresql://scribe:password@localhost:5432/scribe
SECRET_KEY=production-secure-key-change-this
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=https://scribe.illanes00.cl/api/v1/integrations/google/callback
CORS_ORIGINS=["https://scribe.illanes00.cl"]
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION SERVER                         │
│                    scribe.illanes00.cl                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                      Nginx                              │ │
│  │  - SSL termination (Let's Encrypt)                     │ │
│  │  - Proxy to frontend (port 8132)                       │ │
│  │  - Proxy /api/* to backend (port 8000)                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│          ┌──────────────┴──────────────┐                    │
│          ▼                              ▼                    │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │ scribe-frontend  │          │ scribe-backend   │         │
│  │ (systemd)        │          │ (systemd)        │         │
│  │                  │          │                  │         │
│  │ next start       │          │ uvicorn          │         │
│  │ port 8132        │          │ port 8000        │         │
│  └──────────────────┘          └──────────────────┘         │
│                                        │                     │
│                                        ▼                     │
│                                ┌──────────────────┐         │
│                                │ SQLite Database  │         │
│                                │ /backend/scribe.db│        │
│                                └──────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Current Bottlenecks

1. **Large documents**: TipTap JSON can grow large for 50+ page documents
2. **LLM calls**: Anthropic API calls take 2-5 seconds
3. **Export generation**: Pandoc subprocess can take 10+ seconds for PPTX

### Optimization Strategies

1. **Document chunking**: Split large docs into sections
2. **Background tasks**: Use Celery/Redis for long-running exports
3. **Caching**: Redis cache for repeated bibliography lookups
4. **CDN**: Serve static assets from CDN

---

## Module Interaction Summary

```
Frontend (Next.js)
    │
    ├── TiptapEditor ──── Extensions (claim, citation, comment)
    │       │
    │       └── useDocument hook ──── api.ts
    │                                    │
    │                                    ▼
    │                              Backend API
    │                                    │
    ├── Panels ────────────────────────┼─── claims.py
    │   (Claims, Bib, Comments)        │    bibliography.py
    │                                   │    comments.py
    │                                   │
    ├── PresentationView ──────────────┼─── documents.py (slides_data)
    │                                   │
    └── Export buttons ────────────────┼─── exports.py
                                        │    google.py
                                        │
                                        ▼
                                   Services Layer
                                        │
                                        ├── conversion.py
                                        ├── google.py (API client)
                                        └── llm/ (Anthropic)
```
