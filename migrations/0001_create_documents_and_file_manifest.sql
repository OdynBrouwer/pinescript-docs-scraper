-- Migration: Create documents and file_manifest tables
-- Uses vector(1536) for embeddings (text-embedding-3-small)

-- Ensure pgvector is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source_filename TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    section_heading TEXT,
    token_count INTEGER NOT NULL,
    code_snippet BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_source_filename 
ON documents(source_filename);

CREATE INDEX IF NOT EXISTS idx_documents_code_snippet 
ON documents(code_snippet);

-- Vector index using HNSW for cosine distance
CREATE INDEX IF NOT EXISTS idx_documents_embedding 
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create file_manifest table with FK to documents.id
CREATE TABLE IF NOT EXISTS file_manifest (
    filename TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    last_indexed TIMESTAMP WITH TIME ZONE NOT NULL,
    doc_id TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_file_manifest_content_hash 
ON file_manifest(content_hash);

CREATE INDEX IF NOT EXISTS idx_file_manifest_last_indexed 
ON file_manifest(last_indexed DESC);

-- -----------------------------------------------------------------------------
-- RPC: match_documents
-- Adds a convenience PL/pgSQL function to return documents ordered by
-- similarity to a provided query embedding
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding vector(1536),
    match_threshold DOUBLE PRECISION,
    match_count INTEGER
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    source_filename TEXT,
    chunk_index INTEGER,
    chunk_count INTEGER,
    section_heading TEXT,
    token_count INTEGER,
    code_snippet BOOLEAN,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    similarity DOUBLE PRECISION
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.content,
        d.source_filename,
        d.chunk_index,
        d.chunk_count,
        d.section_heading,
        d.token_count,
        d.code_snippet,
        d.metadata,
        d.embedding,
        d.created_at,
        d.updated_at,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE d.embedding IS NOT NULL
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Notes:
-- - Uses vector cosine distance operator `<=>` (pgvector). Lower distance = more similar.
-- - The `similarity` returned is `1 - distance` which maps distance in [0..1+] to a rough
--   similarity score. You may wish to clamp/normalise this in client code.
-- - `match_threshold` is currently unused by the function body; extend the WHERE clause
--   (e.g. `AND 1 - (d.embedding <=> query_embedding) >= match_threshold`) to filter by
--   similarity within the database if desired.

