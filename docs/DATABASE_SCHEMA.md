# Scribe Database Schema

> Database: SQLite (development) / PostgreSQL (production)
> ORM: SQLAlchemy 2.0
> Location: `backend/scribe.db`

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐         │
│    │  documents  │────────▶│   claims    │         │    notes    │         │
│    └─────────────┘         └─────────────┘         └─────────────┘         │
│          │                                                                  │
│          │         ┌─────────────────────┐                                 │
│          ├────────▶│ document_versions   │                                 │
│          │         └─────────────────────┘                                 │
│          │                                                                  │
│          │         ┌─────────────┐                                         │
│          ├────────▶│  comments   │◀───────┐ (self-reference for replies)  │
│          │         └─────────────┘────────┘                                │
│          │                                                                  │
│          │         ┌─────────────┐                                         │
│          └────────▶│   assets    │  (TODO: needs implementation)           │
│                    └─────────────┘                                         │
│                                                                             │
│    ┌─────────────────────┐    ┌─────────────┐    ┌─────────────┐           │
│    │ bibliography_entries│    │  datasets   │    │   charts    │           │
│    └─────────────────────┘    └─────────────┘    └─────────────┘           │
│                                      │                  │                   │
│                                      └──────────────────┘                   │
│                                                                             │
│    ┌─────────────┐         ┌─────────────┐                                 │
│    │ integrations│         │ export_jobs │                                 │
│    └─────────────┘         └─────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables

### documents

Primary table for all document types (papers, presentations, policy briefs).

```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    doc_type VARCHAR(20) DEFAULT 'paper',
    content TEXT,  -- JSON: {"json": TiptapJSON, "html": string}
    markdown TEXT,
    front_matter TEXT,  -- JSON: style settings, slides_data, etc.
    version VARCHAR(20) DEFAULT '1.0.0',
    status VARCHAR(20) DEFAULT 'draft',
    source_provider VARCHAR(50),  -- 'google' if imported from Google
    source_id VARCHAR(200),  -- Google file ID for imported docs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_documents_slug ON documents(slug);
CREATE INDEX idx_documents_doc_type ON documents(doc_type);
CREATE INDEX idx_documents_status ON documents(status);
```

**doc_type values:**
- `paper` - Academic paper
- `thesis` - Thesis/dissertation
- `policy` - Policy brief
- `presentation` - Slide presentation

**status values:**
- `draft` - Work in progress
- `review` - Under review
- `final` - Finalized

**content JSON structure:**
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

**front_matter JSON structure:**
```json
{
  "style": "classic",
  "layout": "a4",
  "font": "serif",
  "slides_data": {
    "slides": [
      {
        "id": "slide-1",
        "slideNumber": 1,
        "layout": "title",
        "title": "Slide Title",
        "content": "Markdown content",
        "notes": "Speaker notes"
      }
    ],
    "theme": {
      "primaryColor": "#1a365d",
      "secondaryColor": "#c53030",
      "fontFamily": "IBM Plex Sans"
    }
  }
}
```

---

### claims

Stores verifiable claims extracted from documents.

```sql
CREATE TABLE claims (
    id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(50) UNIQUE NOT NULL,  -- Human-readable: C-abc123
    document_id VARCHAR(36) NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(20) DEFAULT 'MIXED',
    status VARCHAR(20) DEFAULT 'draft',
    section VARCHAR(100),
    evidence TEXT DEFAULT '[]',  -- JSON array
    source_sentences TEXT DEFAULT '[]',  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_claims_document_id ON claims(document_id);
CREATE INDEX idx_claims_claim_id ON claims(claim_id);
CREATE INDEX idx_claims_status ON claims(status);
```

**claim_type values:**
- `DATA` - Numeric data, statistics
- `LITERATURE` - Academic citation
- `MIXED` - Combination
- `HYPOTHESIS` - Unverified hypothesis

**status values:**
- `draft` - Not yet verified
- `verified` - Verified with evidence
- `rejected` - Found to be false
- `needs_revision` - Requires changes

**evidence JSON structure:**
```json
[
  {
    "source": "BID Report 2024",
    "url": "https://publications.iadb.org/...",
    "quote": "Supporting quote from source",
    "verified_at": "2026-01-16T12:00:00"
  }
]
```

---

### bibliography_entries

BibTeX bibliography entries for citations.

```sql
CREATE TABLE bibliography_entries (
    id VARCHAR(36) PRIMARY KEY,
    bib_key VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "smith2024"
    entry_type VARCHAR(20) DEFAULT 'misc',
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER,
    journal TEXT,
    booktitle TEXT,
    volume VARCHAR(50),
    number VARCHAR(50),
    pages VARCHAR(50),
    publisher TEXT,
    address TEXT,
    doi VARCHAR(255),
    url TEXT,
    abstract TEXT,
    keywords TEXT,
    bibtex TEXT,  -- Original BibTeX string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_bib_bib_key ON bibliography_entries(bib_key);
CREATE INDEX idx_bib_year ON bibliography_entries(year);
CREATE UNIQUE INDEX idx_bib_doi ON bibliography_entries(doi) WHERE doi IS NOT NULL;
```

**entry_type values:**
- `article` - Journal article
- `book` - Book
- `inproceedings` - Conference paper
- `techreport` - Technical report
- `misc` - Miscellaneous

---

### comments

Document comments with threading support.

```sql
CREATE TABLE comments (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    parent_id VARCHAR(36),  -- For replies
    anchor_id VARCHAR(100),  -- Position in document
    provider VARCHAR(50) DEFAULT 'local',
    external_id VARCHAR(200),  -- Google Docs comment ID
    author VARCHAR(255),
    content TEXT NOT NULL,
    quote TEXT,  -- Selected text
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_comments_document_id ON comments(document_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_anchor_id ON comments(anchor_id);
```

**provider values:**
- `local` - Created in Scribe
- `google` - Synced from Google Docs

---

### document_versions

Version snapshots for documents.

```sql
CREATE TABLE document_versions (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    label VARCHAR(255),  -- e.g., "v1.0", "Before review"
    content TEXT,  -- JSON snapshot
    markdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_versions_document_id ON document_versions(document_id);
CREATE INDEX idx_versions_created_at ON document_versions(created_at);
```

---

### notes

Knowledge base notes (wiki-like).

```sql
CREATE TABLE notes (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,  -- JSON TipTap content
    markdown TEXT,
    note_type VARCHAR(20) DEFAULT 'idea',
    tags TEXT DEFAULT '[]',  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notes_slug ON notes(slug);
CREATE INDEX idx_notes_note_type ON notes(note_type);
```

**note_type values:**
- `idea` - Raw idea
- `summary` - Summary of source
- `quote` - Important quote
- `concept` - Concept definition

---

### datasets

Uploaded data files for charts.

```sql
CREATE TABLE datasets (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) DEFAULT 'text/csv',
    row_count INTEGER DEFAULT 0,
    columns TEXT DEFAULT '[]',  -- JSON: column names and types
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_datasets_name ON datasets(name);
```

**columns JSON structure:**
```json
[
  { "name": "year", "type": "integer" },
  { "name": "value", "type": "float" },
  { "name": "category", "type": "string" }
]
```

---

### charts

Chart configurations linked to datasets.

```sql
CREATE TABLE charts (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    chart_type VARCHAR(50) DEFAULT 'bar',
    config TEXT DEFAULT '{}',  -- JSON chart configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_charts_dataset_id ON charts(dataset_id);
```

**chart_type values:**
- `bar` - Bar chart
- `line` - Line chart
- `pie` - Pie chart
- `scatter` - Scatter plot
- `area` - Area chart

**config JSON structure:**
```json
{
  "x_column": "year",
  "y_column": "value",
  "color_column": "category",
  "x_label": "Year",
  "y_label": "Value ($)",
  "legend": true,
  "stacked": false
}
```

---

### export_jobs

Background export job tracking.

```sql
CREATE TABLE export_jobs (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    format VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    output_path VARCHAR(500),
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_exports_document_id ON export_jobs(document_id);
CREATE INDEX idx_exports_status ON export_jobs(status);
```

**status values:**
- `pending` - Queued
- `processing` - In progress
- `complete` - Done
- `failed` - Error occurred

---

### integrations

OAuth tokens for external services.

```sql
CREATE TABLE integrations (
    id VARCHAR(36) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,  -- 'google'
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope TEXT,
    user_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_integrations_provider ON integrations(provider);
CREATE UNIQUE INDEX idx_integrations_provider_unique ON integrations(provider);
```

---

### assets (TODO - Not Yet Implemented)

Storage for document images and files.

```sql
CREATE TABLE assets (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36),
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    url VARCHAR(500) NOT NULL,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_assets_document_id ON assets(document_id);
CREATE INDEX idx_assets_mime_type ON assets(mime_type);
```

---

## Migration Scripts

### Initial Schema

```sql
-- Run from backend/ directory
sqlite3 scribe.db < docker/postgres/init.sql
```

### Add Assets Table

```sql
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36),
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    url VARCHAR(500) NOT NULL,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);
```

### Add Sync Fields to Documents

```sql
ALTER TABLE documents ADD COLUMN google_revision_id VARCHAR(200);
ALTER TABLE documents ADD COLUMN last_synced_at TIMESTAMP;
ALTER TABLE documents ADD COLUMN sync_status VARCHAR(20) DEFAULT 'synced';
```

### Add Position Fields to Claims

```sql
ALTER TABLE claims ADD COLUMN start_offset INTEGER;
ALTER TABLE claims ADD COLUMN end_offset INTEGER;
```

---

## Query Examples

### Get Document with Claims Count

```sql
SELECT
    d.*,
    COUNT(c.id) as claim_count,
    SUM(CASE WHEN c.status = 'verified' THEN 1 ELSE 0 END) as verified_count
FROM documents d
LEFT JOIN claims c ON d.id = c.document_id
WHERE d.slug = 'my-document'
GROUP BY d.id;
```

### Get Comments with Replies

```sql
WITH RECURSIVE comment_tree AS (
    SELECT c.*, 0 as depth
    FROM comments c
    WHERE c.document_id = 'doc-id' AND c.parent_id IS NULL

    UNION ALL

    SELECT c.*, ct.depth + 1
    FROM comments c
    JOIN comment_tree ct ON c.parent_id = ct.id
)
SELECT * FROM comment_tree ORDER BY created_at;
```

### Search Bibliography

```sql
SELECT * FROM bibliography_entries
WHERE title LIKE '%search term%'
   OR author LIKE '%search term%'
ORDER BY year DESC;
```

### Get Knowledge Graph Edges

```sql
-- Find notes that reference other notes via [[wiki-links]]
SELECT
    n1.id as source,
    n2.id as target,
    'references' as type
FROM notes n1
CROSS JOIN notes n2
WHERE n1.id != n2.id
  AND n1.markdown LIKE '%[[' || n2.slug || ']]%';
```

---

## Backup and Restore

### Backup

```bash
# SQLite
sqlite3 backend/scribe.db ".backup backup.db"

# Or dump to SQL
sqlite3 backend/scribe.db ".dump" > backup.sql
```

### Restore

```bash
# From backup file
cp backup.db backend/scribe.db

# From SQL dump
sqlite3 backend/scribe.db < backup.sql
```

---

## PostgreSQL Migration

For production, use PostgreSQL:

```python
# backend/app/config.py
DATABASE_URL=postgresql://scribe:password@localhost:5432/scribe
```

Key differences:
- Use `UUID` type instead of `VARCHAR(36)`
- Use `JSONB` instead of `TEXT` for JSON columns
- Use `SERIAL` for auto-increment IDs (if needed)
