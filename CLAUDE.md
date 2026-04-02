# CLAUDE.md - Development Instructions for AI Assistants

> This file provides context for AI assistants (Claude, Codex, etc.) working on the Scribe project.

## Project Summary

**Scribe** is a multi-tenant academic collaboration platform for policy researchers, think tanks, universities, and government. It features:
- Rich text editing (TipTap/ProseMirror) with inline claims, comments, track changes
- AI Review & Respond (Claude CLI subprocess — analyzes reviewer comments, generates argued responses)
- AI Chat panel with full document context (claims, comments, bibliography)
- Claims management (verifiable assertions with evidence strength indicators)
- Bibliography management (BibTeX, 17+ verified sources)
- Knowledge graph (D3 force simulation, interactive)
- Google Workspace integration (bidirectional sync, comment replies)
- Multi-user support (User, Project, ProjectMember models, Authentik SSO ready)
- MCP server (19 tools for Claude Code CLI integration)
- Presentation authoring (slides with PPTX export)

**Production:** https://scribe.illanes00.cl

## Quick Reference

### Key Documentation Files

| File | Purpose |
|------|---------|
| `PROJECT_HANDOVER.md` | Complete project overview |
| `ARCHITECTURE.md` | System architecture |
| `BACKLOG.json` | Machine-readable feature list |
| `docs/IMPLEMENTATION_GUIDE.md` | Step-by-step implementation |
| `docs/API_REFERENCE.md` | API documentation |
| `docs/DATABASE_SCHEMA.md` | Database schema |
| `docs/TESTING_PLAN.md` | Test specifications |
| `.claude/project_context.json` | Machine-readable context |

### Running the Project

```bash
# Backend (Terminal 1)
cd backend
source .venv/bin/activate
python run.py  # http://localhost:8000

# Frontend (Terminal 2)
cd frontend
npm run dev    # http://localhost:3000
```

### Running Tests

```bash
cd backend
pytest -v
```

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints for all functions
- Use Pydantic for validation
- Async functions for I/O operations
- Example:

```python
async def get_document(slug: str, db: Session) -> Document | None:
    """Get document by slug."""
    return db.query(Document).filter(Document.slug == slug).first()
```

### TypeScript (Frontend)

- Use functional components with hooks
- Use TypeScript interfaces for props
- Use TailwindCSS for styling
- Example:

```typescript
interface ClaimsPanelProps {
  documentId: string
  onClaimClick: (claimId: string) => void
}

export default function ClaimsPanel({ documentId, onClaimClick }: ClaimsPanelProps) {
  // ...
}
```

### TipTap Extensions

- Extend from `@tiptap/core` classes
- Use `addAttributes()` for custom data
- Use `parseHTML()` and `renderHTML()` for serialization
- Example in `frontend/components/editor/extensions/claim.ts`

## Current Priorities

1. **Auto claim extraction on save** - `backend/app/api/v1/documents.py`
2. **Visual claim highlighting** - `frontend/components/editor/TiptapEditor.tsx`
3. **Asset model for images** - Create `backend/app/models/asset.py`
4. **Professional PPTX export** - Create `backend/app/services/slides_export.py`
5. **TipTap in SlideEditor** - `frontend/components/editor/SlideEditor.tsx`

## Important Patterns

### Document Content Structure

Documents store TipTap JSON in `content`:

```json
{
  "json": {
    "type": "doc",
    "content": [
      { "type": "heading", "attrs": { "level": 1 }, "content": [...] },
      { "type": "paragraph", "content": [...] }
    ]
  },
  "html": "<h1>Title</h1><p>Content</p>"
}
```

### Slides Data Structure

Presentations store slides in `front_matter.slides_data`:

```json
{
  "slides": [
    {
      "id": "slide-1",
      "slideNumber": 1,
      "layout": "title",
      "title": "Title",
      "content": "Markdown content",
      "notes": ""
    }
  ],
  "theme": {
    "primaryColor": "#1a365d",
    "secondaryColor": "#c53030"
  }
}
```

### Claims in TipTap

Claims are marks with `claimId` attribute:

```json
{
  "type": "text",
  "text": "El gasto aumentó 23%",
  "marks": [
    { "type": "claim", "attrs": { "claimId": "C-abc123" } }
  ]
}
```

## Environment Variables

Required:
- `DATABASE_URL` - Database connection string
- `ANTHROPIC_API_KEY` - For AI features

Optional:
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - For Google integration
- `SECRET_KEY` - For token signing
- `CORS_ORIGINS` - Allowed origins

## Common Tasks

### Adding a New API Endpoint

1. Create/update router in `backend/app/api/v1/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Register router in `backend/app/main.py`
4. Add API client function in `frontend/lib/api.ts`

### Adding a TipTap Extension

1. Create extension in `frontend/components/editor/extensions/`
2. Register in `TiptapEditor.tsx` extensions array
3. Add CSS in `frontend/styles/globals.css`

### Adding a Database Table

1. Create model in `backend/app/models/`
2. Add to `backend/app/models/__init__.py`
3. Create schema in `backend/app/schemas/`
4. Run migration or create table manually

## Theme Colors

Espacio Público institutional colors:

```css
--ep-primary: #1a365d;    /* Dark blue */
--ep-secondary: #c53030;  /* Red */
--ep-accent: #2b6cb0;     /* Medium blue */
```

## Useful Commands

```bash
# Database queries
sqlite3 backend/scribe.db "SELECT * FROM documents LIMIT 5;"

# Check API docs
open http://localhost:8000/docs

# Build frontend for production
cd frontend && npm run build

# Run specific test
pytest backend/tests/test_documents.py -v
```

## Deployment Architecture

**IMPORTANT:** This project uses a two-server deployment model:

| Server | Hostname | Purpose |
|--------|----------|---------|
| **vps-dev** | Development | Development, testing, CI. Does NOT deploy to production. |
| **vps-deploy** | Production | Runs production services. Deployment via GitHub Actions CD. |

### How to Deploy

1. **Make changes** on vps-dev (this server)
2. **Run tests** to verify changes work:
   ```bash
   cd backend && pytest -v
   cd frontend && npm test
   ```
3. **Commit and push** to `main` branch:
   ```bash
   git add -A
   git commit -m "feat: description of changes"
   git push origin main
   ```
4. **CD automatically triggers** on vps-deploy via GitHub Actions (`.github/workflows/cd.yml`)
5. **Verify deployment** at https://scribe.illanes00.cl

### CD Pipeline Steps (on vps-deploy)

1. Pull latest code from `origin/main`
2. Install backend dependencies
3. Run database migrations
4. Build frontend (`npm run build`)
5. Restart services (`sudo systemctl restart illanes00-scribe-backend illanes00-scribe-frontend`)
6. Health check

### Common Deployment Issues

- **Stale cache:** If Cloudflare caches old assets, toggle Development Mode or purge cache
- **Environment variables:** `NEXT_PUBLIC_*` vars are baked into the frontend at build time
- **Service not restarting:** Check `sudo systemctl status illanes00-scribe-frontend`

## Don't Forget

- Parse `BACKLOG.json` for structured task data
- Check existing code patterns before creating new files
- Run tests after changes
- Keep code simple and focused
- **Push to main to deploy** - vps-dev does NOT deploy to production
