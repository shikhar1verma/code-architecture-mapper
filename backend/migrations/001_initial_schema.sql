-- Initial schema for Code Architecture Mapper
-- Creates core tables for MVP functionality

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Analyses table - stores repository analysis results
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_url TEXT NOT NULL,
    repo_owner TEXT,
    repo_name TEXT,
    default_branch TEXT,
    commit_sha TEXT,
    status TEXT NOT NULL DEFAULT 'queued', -- queued | running | complete | error
    message TEXT, -- last progress/error message
    language_stats JSONB, -- {"python": 62.3, "ts": 37.7}
    loc_total INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    metrics JSONB, -- {"central_files":[...], "graph": {"nodes":..., "edges":...}}
    architecture_md TEXT,
    mermaid_modules TEXT,
    mermaid_folders TEXT,
    token_budget JSONB DEFAULT '{"embed_calls":0,"gen_calls":0,"chunks":0}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table - stores individual file metrics and information
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    language TEXT,
    loc INTEGER DEFAULT 0,
    fan_in INTEGER DEFAULT 0,
    fan_out INTEGER DEFAULT 0,
    centrality FLOAT8 DEFAULT 0.0,
    hash TEXT, -- file hash for change detection
    snippet TEXT, -- first N lines or salient excerpt
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Examples table - stores example repositories for the examples endpoint
CREATE TABLE examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_url TEXT NOT NULL UNIQUE,
    analysis_id UUID REFERENCES analyses(id),
    label TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_analyses_repo_url ON analyses(repo_url);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);

CREATE INDEX idx_files_analysis_id ON files(analysis_id);
CREATE INDEX idx_files_centrality ON files(centrality DESC);
CREATE INDEX idx_files_path ON files(path);

CREATE INDEX idx_examples_repo_url ON examples(repo_url);

-- Trigger to update updated_at on analyses table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_analyses_updated_at 
    BEFORE UPDATE ON analyses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some example repositories for demo purposes
INSERT INTO examples (repo_url, label, description) VALUES
    ('https://github.com/encode/uvicorn', 'Uvicorn', 'Lightning-fast ASGI server implementation'),
    ('https://github.com/tiangolo/fastapi', 'FastAPI', 'Modern, fast web framework for building APIs'),
    ('https://github.com/psf/requests', 'Requests', 'Simple HTTP library for Python');

-- Comments for documentation
COMMENT ON TABLE analyses IS 'Stores repository analysis results and metadata';
COMMENT ON TABLE files IS 'Stores individual file metrics and centrality data';
COMMENT ON TABLE examples IS 'Stores example repositories for the examples endpoint';

COMMENT ON COLUMN analyses.status IS 'Analysis status: queued, running, complete, error';
COMMENT ON COLUMN analyses.metrics IS 'JSON containing central files list and graph data';
COMMENT ON COLUMN files.centrality IS 'Degree centrality score (0.0 to 1.0)';
COMMENT ON COLUMN files.fan_in IS 'Number of files that import this file';
COMMENT ON COLUMN files.fan_out IS 'Number of files this file imports'; 