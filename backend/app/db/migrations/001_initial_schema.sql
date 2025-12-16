-- Initial schema for RAG Chatbot
-- Creates chapters and chunks tables with proper indexes and triggers

-- Chapters table: stores chapter-level metadata
CREATE TABLE IF NOT EXISTS chapters (
    chapter_id VARCHAR(50) PRIMARY KEY,
    chapter_title TEXT NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Index on ingestion timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_chapters_ingestion ON chapters(ingestion_timestamp DESC);

-- Chunks table: stores individual text chunks with embeddings
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id VARCHAR(50) NOT NULL REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK (token_count > 0 AND token_count <= 700),
    embedding_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_chapter_chunks ON chunks(chapter_id);
CREATE INDEX IF NOT EXISTS idx_embedding_id ON chunks(embedding_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON chunks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_count ON chunks(token_count);

-- Trigger function to auto-update chapter.total_chunks
CREATE OR REPLACE FUNCTION update_chapter_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE chapters
        SET total_chunks = (
            SELECT COUNT(*) FROM chunks WHERE chapter_id = NEW.chapter_id
        )
        WHERE chapter_id = NEW.chapter_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE chapters
        SET total_chunks = (
            SELECT COUNT(*) FROM chunks WHERE chapter_id = OLD.chapter_id
        )
        WHERE chapter_id = OLD.chapter_id;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_chunk_count ON chunks;
CREATE TRIGGER trigger_update_chunk_count
AFTER INSERT OR DELETE ON chunks
FOR EACH ROW
EXECUTE FUNCTION update_chapter_chunk_count();

-- Verification query (commented out, uncomment to verify schema)
-- SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;
