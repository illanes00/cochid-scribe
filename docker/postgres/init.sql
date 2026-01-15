-- Scribe Database Schema
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    doc_type VARCHAR(50) NOT NULL DEFAULT 'paper',
    content JSONB DEFAULT '{}',
    markdown TEXT,
    front_matter JSONB DEFAULT '{}',
    version VARCHAR(20) DEFAULT '1.0.0',
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Claims table
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id VARCHAR(50) UNIQUE NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(20) NOT NULL DEFAULT 'MIXED',
    status VARCHAR(20) DEFAULT 'draft',
    section VARCHAR(100),
    evidence JSONB DEFAULT '[]',
    source_sentences TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sentences table (for atomization)
CREATE TABLE IF NOT EXISTS sentences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sentence_id VARCHAR(50) UNIQUE NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    section VARCHAR(100),
    paragraph_id VARCHAR(50),
    position INT,
    sentence_type VARCHAR(50),
    claim_ids TEXT[],
    citation_ids TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bibliography entries table
CREATE TABLE IF NOT EXISTS bibliography_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bib_key VARCHAR(100) UNIQUE NOT NULL,
    entry_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT,
    journal TEXT,
    booktitle TEXT,
    volume VARCHAR(50),
    number VARCHAR(50),
    pages VARCHAR(50),
    publisher TEXT,
    doi TEXT,
    url TEXT,
    abstract TEXT,
    bibtex TEXT,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document citations table
CREATE TABLE IF NOT EXISTS document_citations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    bib_key VARCHAR(100) REFERENCES bibliography_entries(bib_key) ON DELETE CASCADE,
    locator TEXT,
    raw_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, bib_key, locator)
);

-- Notes table (knowledge base)
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content JSONB DEFAULT '{}',
    markdown TEXT,
    note_type VARCHAR(50) DEFAULT 'idea',
    tags TEXT[],
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Links table (knowledge graph)
CREATE TABLE IF NOT EXISTS links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    link_type VARCHAR(50) DEFAULT 'reference',
    context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_type, source_id, target_type, target_id)
);

-- Datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    columns JSONB,
    source_file VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Charts table
CREATE TABLE IF NOT EXISTS charts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    chart_type VARCHAR(50) NOT NULL,
    dataset_id UUID REFERENCES datasets(id) ON DELETE SET NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Document charts relation
CREATE TABLE IF NOT EXISTS document_charts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chart_id UUID REFERENCES charts(id) ON DELETE CASCADE,
    position INT,
    caption TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_slug ON documents(slug);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_claims_document ON claims(document_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_type ON claims(claim_type);

CREATE INDEX IF NOT EXISTS idx_sentences_document ON sentences(document_id);

CREATE INDEX IF NOT EXISTS idx_bib_key ON bibliography_entries(bib_key);
CREATE INDEX IF NOT EXISTS idx_bib_year ON bibliography_entries(year);

CREATE INDEX IF NOT EXISTS idx_notes_slug ON notes(slug);
CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type);

CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_type, target_id);

-- Vector indexes for semantic search
CREATE INDEX IF NOT EXISTS idx_bib_embedding ON bibliography_entries
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_notes_embedding ON notes
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bibliography_entries_updated_at BEFORE UPDATE ON bibliography_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
