# Scribe

Academic writing platform for creating, editing, and compiling academic documents with claim verification and AI assistance.

## Features

- **Rich Text Editor**: Tiptap-based editor similar to Google Docs
- **Claim Management**: Track and verify claims in your academic writing
- **Bibliography**: BibTeX import, Zotero integration, semantic search
- **AI Assistance**: Claude-powered rewriting and claim extraction
- **Multi-format Export**: PDF, HTML, Word, LaTeX via Quarto
- **Knowledge Base**: Obsidian-like notes with backlinks and graph view

## Quick Start

```bash
# Install dependencies
make setup

# Start development servers
make dev
```

Frontend runs at http://localhost:3000
Backend API at http://localhost:8000

## Project Structure

```
scribe/
├── frontend/          # Next.js 14 + TypeScript + Tailwind
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   │   └── editor/    # Tiptap editor
│   └── lib/           # Utilities
│
├── backend/           # FastAPI + Python
│   ├── app/
│   │   ├── api/v1/    # API endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   └── tests/         # Pytest tests
│
└── docs/              # Documentation
```

## Development

```bash
# Run tests
make test

# Run linters
make lint

# Format code
make format

# Reset database
make db-reset
```

## API Endpoints

- `GET/POST /api/v1/documents` - List/create documents
- `GET/PUT/DELETE /api/v1/documents/{slug}` - Document CRUD
- `GET/POST /api/v1/claims/document/{slug}` - Document claims
- `GET/PUT/DELETE /api/v1/claims/{claim_id}` - Claim CRUD
- `GET/POST /api/v1/bibliography` - Bibliography entries
- `POST /api/v1/llm/rewrite` - AI rewriting
- `POST /api/v1/llm/extract-claims` - AI claim extraction

## Environment Variables

```bash
DATABASE_URL=sqlite:///./scribe.db  # or postgresql://...
ANTHROPIC_API_KEY=your_key          # For LLM features
```

## Deployment

See [DEPLOY.md](DEPLOY.md) for production deployment instructions.

## Design System

Uses [illanes v3 design system](https://static.illanes00.cl):
- Typography: IBM Plex Sans, JetBrains Mono
- Colors: Minimal palette with semantic colors
- No shadows, gradients, or border-radius

## License

Private - All rights reserved
