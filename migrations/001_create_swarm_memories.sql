-- Migration: 001_create_swarm_memories
-- Description: Create the swarm_memories table for storing agent memories
-- Created: 2024-04-04
-- Author: Heretek Swarm

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the main memories table
CREATE TABLE IF NOT EXISTS swarm_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,  -- 'episodic', 'semantic', 'working'
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI embedding dimension (text-embedding-3-small)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_swarm_memories_agent ON swarm_memories(agent_id);
CREATE INDEX idx_swarm_memories_type ON swarm_memories(memory_type);
CREATE INDEX idx_swarm_memories_created ON swarm_memories(created_at DESC);
CREATE INDEX idx_swarm_memories_expires ON swarm_memories(expires_at) 
    WHERE expires_at IS NOT NULL;

-- Vector index for semantic similarity search (IVFFlat for approximate search)
-- Note: This requires pgvector extension
CREATE INDEX IF NOT EXISTS idx_swarm_memories_embedding 
    ON swarm_memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Add comments for documentation
COMMENT ON TABLE swarm_memories IS 'Stores agent memories with semantic embeddings';
COMMENT ON COLUMN swarm_memories.agent_id IS 'Unique identifier for the agent';
COMMENT ON COLUMN swarm_memories.memory_type IS 'Type: episodic, semantic, or working memory';
COMMENT ON COLUMN swarm_memories.content IS 'The actual memory content (text)';
COMMENT ON COLUMN swarm_memories.embedding IS 'Vector embedding for semantic search (1536-dim for text-embedding-3-small)';
COMMENT ON COLUMN swarm_memories.metadata IS 'Additional metadata as key-value pairs';