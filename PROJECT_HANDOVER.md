# Scribe Project Handover Document

> **Last Updated:** 2026-01-16
> **Status:** Active Development
> **Production URL:** https://scribe.illanes00.cl

---

## 1. Project Overview

### 1.1 What is Scribe?

**Scribe** is an academic writing platform designed for researchers, policy analysts, and think tanks. It combines:

- **Rich text editing** (TipTap/ProseMirror-based)
- **Claims management** (verifiable assertions with evidence tracking)
- **Bibliography management** (BibTeX import/export, inline citations)
- **Presentation authoring** (slide-based editor with PPTX export)
- **AI assistance** (Anthropic Claude for rewriting, claim extraction, hedging)
- **Google Workspace integration** (Docs/Slides import/export)

### 1.2 Target Users

- **Espacio Público** (Chilean think tank) - primary client
- Policy researchers creating policy briefs
- Academics writing papers and presentations

### 1.3 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS |
| Editor | TipTap (ProseMirror) with custom extensions |
| Backend | FastAPI (Python 3.10+), SQLAlchemy, Pydantic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Anthropic Claude API (claude-sonnet-4-20250514) |
| Exports | Pandoc, python-pptx |
| Deployment | Docker, Nginx, Systemd |

---

## 2. Project Structure

```
/srv/projects/illanes00-scribe/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints (15 routers)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   ├── db/                # Database session & migrations
│   │   ├── config.py          # Settings (pydantic-settings)
│   │   └── main.py            # FastAPI app initialization
│   ├── tests/                 # pytest tests
│   ├── uploads/               # Static file uploads
│   ├── requirements.txt       # Python dependencies
│   └── run.py                 # Development server entry
│
├── frontend/                   # Next.js frontend
│   ├── app/                   # App Router pages
│   │   ├── editor/[slug]/     # Document editor
│   │   ├── dashboard/         # Document list
│   │   ├── knowledge/         # Notes/knowledge base
│   │   ├── data/              # Datasets & charts
│   │   └── integrations/      # Google OAuth setup
│   ├── components/
│   │   ├── editor/            # TipTap editor components
│   │   │   ├── TiptapEditor.tsx
│   │   │   ├── SlideEditor.tsx
│   │   │   ├── SlideNavigator.tsx
│   │   │   ├── PresentationView.tsx
│   │   │   └── extensions/    # Custom TipTap extensions
│   │   └── panels/            # Sidebar panels
│   ├── lib/
│   │   ├── api.ts             # API client (typed)
│   │   └── templates.ts       # Document templates
│   ├── hooks/
│   │   └── useDocument.ts     # Document state management
│   └── styles/
│       └── globals.css        # Tailwind + custom styles
│
├── scripts/                    # Utility scripts
│   ├── enrich_and_structure.py  # Claims detection + slides parsing
│   ├── fix_documents.py       # Document migration
│   └── import_bid_notes.py    # Data import
│
├── docs/                       # Source markdown documents
├── docker/                     # Docker configuration
├── deploy/                     # Deployment scripts
└── .env                        # Environment variables
```

---

## 3. Current State & What Works

### 3.1 Fully Implemented Features

| Feature | Status | Notes |
|---------|--------|-------|
| Document CRUD | ✅ Complete | Create, read, update, delete documents |
| TipTap Editor | ✅ Complete | Rich text with headings, lists, formatting |
| Claims Panel | ✅ Complete | View/create claims, link to document |
| Bibliography Panel | ✅ Complete | BibTeX import, search, citations |
| AI Rewriting | ✅ Complete | Anthropic API integration |
| AI Claim Extraction | ✅ Complete | LLM-based extraction endpoint |
| Export (PDF/DOCX/PPTX) | ✅ Complete | Via Pandoc |
| Export (Markdown/LaTeX/HTML) | ✅ Complete | Direct conversion |
| Document Versions | ✅ Complete | Create/restore snapshots |
| Comments | ✅ Complete | Local + Google Docs sync |
| Google Docs Import | ✅ Complete | OAuth + Drive API |
| Google Docs Export | ✅ Complete | Creates Google Doc |
| Google Slides Export | ✅ Complete | Creates Google Slides |
| Knowledge Base (Notes) | ✅ Complete | Wiki-like notes with backlinks |
| Datasets & Charts | ✅ Complete | CSV upload, chart creation |
| Track Changes | ✅ Complete | TipTap extension |

### 3.2 Partially Implemented Features

| Feature | Status | What's Missing |
|---------|--------|----------------|
| Presentation Editor | 🟡 80% | Edit mode needs TipTap integration for slide content editing |
| Claim Marks in Editor | 🟡 70% | Claims created but not visually linked in TipTap JSON |
| Google Slides Import | 🟡 50% | Images not preserved |
| Asset Management | 🟡 40% | Upload works, but no asset model in DB |
| Bidirectional Sync | 🟡 30% | One-way export only |

### 3.3 Not Yet Implemented

| Feature | Priority | Effort |
|---------|----------|--------|
| LLM-based claim extraction on document save | HIGH | 2 days |
| Visual claim highlighting in editor | HIGH | 3 days |
| Asset model for images | MEDIUM | 2 days |
| Slide content editing with TipTap | MEDIUM | 5 days |
| Google → Scribe sync (bidirectional) | MEDIUM | 5 days |
| Real-time collaboration (Yjs) | LOW | 2 weeks |
| Multi-user authentication | LOW | 1 week |

---

## 4. Environment Variables

Located in `/.env`:

```bash
# App
DEBUG=false

# Database
DATABASE_URL=sqlite:///./scribe.db
# For production: DATABASE_URL=postgresql://user:pass@host:5432/scribe

# Authentication
SECRET_KEY=your-secret-key-change-in-production

# Anthropic API (required for AI features)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Google OAuth (required for Google integration)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
GOOGLE_REDIRECT_URI=https://scribe.illanes00.cl/api/v1/integrations/google/callback

# CORS
CORS_ORIGINS=["https://scribe.illanes00.cl"]
```

---

## 5. Running the Project

### 5.1 Development Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py  # Starts on http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev  # Starts on http://localhost:3000
```

### 5.2 Production Deployment

```bash
# Using Docker
docker-compose -f docker-compose.prod.yml up -d

# Or using systemd services (already configured)
sudo systemctl start scribe-backend
sudo systemctl start scribe-frontend
```

### 5.3 Running Tests

```bash
cd backend
pytest -v  # Run all tests
pytest tests/test_documents.py -v  # Specific test file
```

---

## 6. Key Files Reference

### 6.1 Backend Entry Points

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app, router registration |
| `backend/app/config.py` | Environment settings |
| `backend/app/db/session.py` | Database connection |
| `backend/run.py` | Development server launcher |

### 6.2 API Endpoints (backend/app/api/v1/)

| File | Endpoints | Description |
|------|-----------|-------------|
| `documents.py` | `/api/v1/documents/*` | Document CRUD, import, export |
| `claims.py` | `/api/v1/claims/*` | Claims management |
| `bibliography.py` | `/api/v1/bibliography/*` | BibTeX entries |
| `llm.py` | `/api/v1/llm/*` | AI-powered features |
| `google.py` | `/api/v1/google/*` | Google import/export |
| `comments.py` | `/api/v1/comments/*` | Document comments |
| `exports.py` | `/api/v1/exports/*` | Export job management |
| `notes.py` | `/api/v1/notes/*` | Knowledge base notes |
| `datasets.py` | `/api/v1/datasets/*` | Data management |
| `charts.py` | `/api/v1/charts/*` | Chart creation |

### 6.3 Frontend Key Files

| File | Purpose |
|------|---------|
| `frontend/app/editor/[slug]/page.tsx` | Main editor page (751 lines) |
| `frontend/components/editor/TiptapEditor.tsx` | TipTap integration |
| `frontend/components/editor/PresentationView.tsx` | Slide editor |
| `frontend/lib/api.ts` | Typed API client (778 lines) |
| `frontend/hooks/useDocument.ts` | Document state hook |

### 6.4 TipTap Extensions (frontend/components/editor/extensions/)

| File | Extension | Purpose |
|------|-----------|---------|
| `claim.ts` | Claim | Mark text as verifiable claims |
| `citation.ts` | Citation | Inline bibliography references |
| `comment.ts` | Comment | Inline comments with Google sync |
| `track-changes.ts` | TrackChanges | Track insertions/deletions |
| `slash-commands.ts` | SlashCommands | "/" command palette |

---

## 7. Database Schema

### 7.1 Core Tables

```sql
-- Documents
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    doc_type VARCHAR(20) DEFAULT 'paper',  -- paper|thesis|policy|presentation
    content JSON,  -- TipTap JSON + HTML
    markdown TEXT,
    front_matter JSON,  -- Style, slides_data, layout
    version VARCHAR(20) DEFAULT '1.0.0',
    status VARCHAR(20) DEFAULT 'draft',
    source_provider VARCHAR(50),  -- 'google' if imported
    source_id VARCHAR(200),  -- Google file ID
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Claims
CREATE TABLE claims (
    id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(50) UNIQUE NOT NULL,  -- Human-readable: C-abc123
    document_id VARCHAR(36) REFERENCES documents(id),
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(20) DEFAULT 'MIXED',  -- DATA|LITERATURE|MIXED|HYPOTHESIS
    status VARCHAR(20) DEFAULT 'draft',  -- draft|verified|rejected|needs_revision
    section VARCHAR(100),
    evidence JSON DEFAULT '[]',
    source_sentences JSON DEFAULT '[]',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Bibliography
CREATE TABLE bibliography_entries (
    id VARCHAR(36) PRIMARY KEY,
    bib_key VARCHAR(100) UNIQUE NOT NULL,
    entry_type VARCHAR(20) DEFAULT 'misc',
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER,
    journal TEXT,
    booktitle TEXT,
    volume VARCHAR(50),
    pages VARCHAR(50),
    publisher TEXT,
    doi VARCHAR(255),
    url TEXT,
    abstract TEXT,
    bibtex TEXT,
    created_at TIMESTAMP
);

-- Notes (Knowledge Base)
CREATE TABLE notes (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content JSON,
    markdown TEXT,
    note_type VARCHAR(20) DEFAULT 'idea',  -- idea|summary|quote|concept
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Comments
CREATE TABLE comments (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) REFERENCES documents(id),
    parent_id VARCHAR(36),
    anchor_id VARCHAR(100),
    provider VARCHAR(50) DEFAULT 'local',
    external_id VARCHAR(200),
    author VARCHAR(255),
    content TEXT NOT NULL,
    quote TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Document Versions
CREATE TABLE document_versions (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) REFERENCES documents(id),
    label VARCHAR(255),
    content JSON,
    markdown TEXT,
    created_at TIMESTAMP
);
```

---

## 8. API Quick Reference

### 8.1 Documents

```http
GET    /api/v1/documents                  # List documents
POST   /api/v1/documents                  # Create document
GET    /api/v1/documents/{slug}           # Get document
PUT    /api/v1/documents/{slug}           # Update document
DELETE /api/v1/documents/{slug}           # Delete document
POST   /api/v1/documents/import           # Import file (multipart)
POST   /api/v1/documents/{slug}/export    # Start export job
```

### 8.2 Claims

```http
GET    /api/v1/claims/document/{slug}     # List claims for document
POST   /api/v1/claims/document/{slug}     # Create claim
GET    /api/v1/claims/{claim_id}          # Get claim
PUT    /api/v1/claims/{claim_id}          # Update claim
DELETE /api/v1/claims/{claim_id}          # Delete claim
POST   /api/v1/claims/{claim_id}/verify   # Verify claim
```

### 8.3 LLM

```http
POST   /api/v1/llm/rewrite                # Rewrite text
POST   /api/v1/llm/extract-claims         # Extract claims from text
POST   /api/v1/llm/extract-claims-document/{slug}  # Extract + save claims
POST   /api/v1/llm/improve-hedging        # Improve academic hedging
POST   /api/v1/llm/summarize              # Summarize document
```

### 8.4 Google Integration

```http
GET    /api/v1/integrations/google/status      # Check OAuth status
POST   /api/v1/integrations/google/auth-url    # Get OAuth URL
GET    /api/v1/integrations/google/callback    # OAuth callback
POST   /api/v1/google/docs/import              # Import Google Doc
POST   /api/v1/google/docs/export              # Export to Google Docs
POST   /api/v1/google/slides/export            # Export to Google Slides
```

---

## 9. Implementation Priorities

### Phase 1: Claims Enhancement (HIGH PRIORITY)

**Goal:** Make claims visible and editable in the editor.

1. **Automatic claim extraction on save**
   - File: `backend/app/api/v1/documents.py`
   - Add: Call `extract_claims_from_text()` in `update_document()`

2. **Visual claim highlighting**
   - File: `frontend/components/editor/TiptapEditor.tsx`
   - Add: Parse content for `data-claim-id` marks, apply CSS

3. **Click claim → scroll to editor position**
   - File: `frontend/components/panels/ClaimsPanel.tsx`
   - Add: Position tracking in TipTap content

### Phase 2: Presentation Editor (MEDIUM PRIORITY)

**Goal:** Full slide editing with TipTap.

1. **SlideEditor content editing**
   - File: `frontend/components/editor/SlideEditor.tsx`
   - Add: Embed TipTap for editing slide.content

2. **Slide content persistence**
   - File: `frontend/app/editor/[slug]/page.tsx`
   - Add: Save slide content changes to `front_matter.slides_data`

### Phase 3: Asset Management (MEDIUM PRIORITY)

**Goal:** Preserve images from Google Slides imports.

1. **Asset model**
   - Create: `backend/app/models/asset.py`
   - Fields: id, document_id, filename, mime_type, url, source_url

2. **Image extraction from PPTX**
   - Add: python-pptx image extraction in import flow
   - Store: Images as local files, track in assets table

---

## 10. Testing Checklist

### 10.1 Unit Tests (Existing)

```bash
pytest backend/tests/test_documents.py  # Document CRUD
pytest backend/tests/test_claims.py     # Claims management
pytest backend/tests/test_bibliography.py  # Bibliography
pytest backend/tests/test_notes.py      # Knowledge base
```

### 10.2 Integration Tests (To Add)

| Test | Description | Priority |
|------|-------------|----------|
| `test_llm_claim_extraction.py` | Mock Anthropic API, verify claim creation | HIGH |
| `test_google_integration.py` | Mock Google API, verify import/export | MEDIUM |
| `test_export_formats.py` | Verify PDF, DOCX, PPTX generation | MEDIUM |
| `test_presentation_mode.py` | Test slide CRUD operations | LOW |

### 10.3 E2E Tests (Playwright)

| Scenario | Description |
|----------|-------------|
| Document creation | Create doc, edit, save, verify persistence |
| Claim workflow | Extract claims, mark verified, check panel |
| Export flow | Export to PPTX, verify download |
| Google sync | Connect OAuth, import doc, verify content |

---

## 11. Known Issues & Workarounds

### 11.1 PPTX Export Quality

**Issue:** Pandoc-generated PPTX has minimal styling.

**Workaround:** Use `python-pptx` for custom templates.

**Fix Location:** `backend/app/services/conversion.py`

### 11.2 Google Slides Images

**Issue:** Images lost on import.

**Workaround:** None currently.

**Fix:** Implement asset extraction with `python-pptx`.

### 11.3 Claim Position Tracking

**Issue:** Claims in database don't track position in TipTap.

**Workaround:** Pattern matching in `enrich_and_structure.py`.

**Fix:** Store character offsets in claim model.

---

## 12. Contact & Resources

- **Production URL:** https://scribe.illanes00.cl
- **API Docs:** https://scribe.illanes00.cl/api/docs
- **GitHub Actions:** CI/CD in `.github/workflows/`

---

## Appendix A: File Checksums (for verification)

```
frontend/lib/api.ts              - 778 lines, API client
frontend/app/editor/[slug]/page.tsx - 751 lines, main editor
backend/app/api/v1/llm.py        - 336 lines, AI endpoints
scripts/enrich_and_structure.py  - 470 lines, document enrichment
```

---

*This document is the primary reference for continuing development. See related docs:*
- `ARCHITECTURE.md` - Technical architecture details
- `BACKLOG.json` - Machine-readable feature backlog
- `docs/IMPLEMENTATION_GUIDE.md` - Step-by-step implementation
