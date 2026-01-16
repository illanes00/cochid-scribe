# FOR CODEX: Scribe Project Instructions

> **STOP AND READ THIS FIRST**
>
> You are taking over an active project. This document tells you everything you need to know.

---

## Quick Start (Read These Files)

1. **PROJECT_HANDOVER.md** - Complete project overview
2. **BACKLOG.json** - Machine-readable feature list (parse this!)
3. **ARCHITECTURE.md** - System architecture and data flows
4. **docs/IMPLEMENTATION_GUIDE.md** - Step-by-step implementation instructions

---

## What is Scribe?

An academic writing platform for policy researchers. Think Google Docs + Notion + academic features:

- Rich text editor (TipTap/ProseMirror)
- Claims management (verifiable assertions)
- Bibliography (BibTeX import, citations)
- Presentations (slide editor)
- AI assistance (Anthropic Claude)
- Google Workspace integration

**Production URL:** https://scribe.illanes00.cl

---

## Tech Stack

```
Frontend: Next.js 14 + React 18 + TailwindCSS + TipTap
Backend:  FastAPI + SQLAlchemy + Pydantic
Database: SQLite (dev) / PostgreSQL (prod)
AI:       Anthropic Claude API
```

---

## What's Working (Don't Break These)

- Document CRUD ✅
- TipTap editor ✅
- Claims panel ✅
- Bibliography panel ✅
- Export (PDF, DOCX, PPTX) ✅
- Google Docs import/export ✅
- AI rewriting ✅
- Knowledge base ✅
- Version history ✅

---

## What Needs To Be Done (Priority Order)

### Priority 1: Claims Enhancement
1. **Auto-extract claims on document save**
   - File: `backend/app/api/v1/documents.py`
   - In `update_document()`, call LLM extraction when content changes
   - Create claim records automatically

2. **Visual claim highlighting**
   - File: `frontend/components/editor/TiptapEditor.tsx`
   - File: `frontend/styles/globals.css`
   - Highlight claim marks with blue background
   - Click claim → scroll to position

### Priority 2: Presentation Editor
1. **TipTap in SlideEditor**
   - File: `frontend/components/editor/SlideEditor.tsx`
   - Replace textarea with TipTap instance
   - Persist slide content changes

### Priority 3: Asset Management
1. **Create Asset model**
   - New file: `backend/app/models/asset.py`
   - Track images and files in database

### Priority 4: Professional PPTX Export
1. **python-pptx export**
   - New file: `backend/app/services/slides_export.py`
   - Use python-pptx instead of Pandoc
   - Apply Espacio Público branding

---

## Running the Project

```bash
# Backend
cd backend
source .venv/bin/activate
python run.py  # http://localhost:8000

# Frontend
cd frontend
npm run dev    # http://localhost:3000
```

---

## Environment Variables

Create `backend/.env`:
```
DATABASE_URL=sqlite:///./scribe.db
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
```

---

## Tests

```bash
cd backend
pytest -v
```

---

## Key Files Quick Reference

| What | Where |
|------|-------|
| Main editor page | `frontend/app/editor/[slug]/page.tsx` |
| TipTap setup | `frontend/components/editor/TiptapEditor.tsx` |
| Claim extension | `frontend/components/editor/extensions/claim.ts` |
| API client | `frontend/lib/api.ts` |
| Document API | `backend/app/api/v1/documents.py` |
| Claims API | `backend/app/api/v1/claims.py` |
| LLM API | `backend/app/api/v1/llm.py` |
| Document model | `backend/app/models/document.py` |
| Claim model | `backend/app/models/claim.py` |

---

## Database

SQLite at `backend/scribe.db`. Schema in `docs/DATABASE_SCHEMA.md`.

Main tables:
- `documents` - All document types
- `claims` - Verifiable claims
- `bibliography_entries` - BibTeX entries
- `comments` - Document comments
- `notes` - Knowledge base

---

## API Base

- Dev: `http://localhost:8000/api/v1`
- Prod: `https://scribe.illanes00.cl/api/v1`

Full reference: `docs/API_REFERENCE.md`

---

## Espacio Público Theme Colors

```css
--ep-primary: #1a365d;    /* Dark blue */
--ep-secondary: #c53030;  /* Red */
--ep-accent: #2b6cb0;     /* Medium blue */
```

---

## Tips

1. **Parse BACKLOG.json** - It has structured feature data
2. **Read Implementation Guide** - Has exact code snippets
3. **Test changes** - `pytest -v` for backend
4. **Check existing patterns** - Look at similar files before creating new ones
5. **Keep it simple** - Don't over-engineer

---

## Questions?

Read the docs first. Everything is documented.

Good luck, Codex. The project is in your hands now.
