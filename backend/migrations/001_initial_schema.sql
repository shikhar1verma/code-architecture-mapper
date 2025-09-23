-- Initial schema for Code Architecture Mapper
-- Creates core tables for MVP functionality with intelligent dependency diagrams
-- Updated: 2025-09-23 - Added async analysis support with progress tracking

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
    status TEXT NOT NULL DEFAULT 'pending', -- pending | started | completed | failed
    progress_status TEXT, -- Human-readable progress description for UI display
    message TEXT, -- last progress/error message
    language_stats JSONB, -- {"python": 62.3, "ts": 37.7}
    loc_total INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    metrics JSONB, -- {"central_files":[...], "graph": {"nodes":..., "edges":...}}
    components JSONB DEFAULT '[]'::jsonb, -- component analysis results
    architecture_md TEXT,
    
    -- Original diagrams
    mermaid_modules TEXT,
    mermaid_folders TEXT,
    
    -- Intelligent dependency diagrams (LLM-powered)
    mermaid_modules_simple TEXT,
    mermaid_modules_balanced TEXT,
    mermaid_modules_detailed TEXT,
    
    token_budget JSONB DEFAULT '{"embed_calls":0,"gen_calls":0,"chunks":0}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Examples table - stores complete example analysis data (independent copy)
CREATE TABLE examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE, -- Human readable name for dropdown
    repo_url TEXT NOT NULL,
    repo_owner TEXT,
    repo_name TEXT,
    default_branch TEXT,
    commit_sha TEXT,
    status TEXT NOT NULL DEFAULT 'complete',
    message TEXT,
    language_stats JSONB,
    loc_total INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    metrics JSONB,
    components JSONB DEFAULT '[]'::jsonb,
    architecture_md TEXT,
    
    -- Original diagrams
    mermaid_modules TEXT,
    mermaid_folders TEXT,
    
    -- Intelligent dependency diagrams
    mermaid_modules_simple TEXT,
    mermaid_modules_balanced TEXT,
    mermaid_modules_detailed TEXT,
    
    token_budget JSONB DEFAULT '{"embed_calls":0,"gen_calls":0,"chunks":0}',
    description TEXT, -- Description for the example
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance (minimal set to avoid slowing down writes)
CREATE INDEX idx_analyses_repo_url ON analyses(repo_url);
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

CREATE TRIGGER update_examples_updated_at 
    BEFORE UPDATE ON examples 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Example data will be loaded from fixtures during Docker startup

-- Comments for documentation
COMMENT ON TABLE analyses IS 'Stores repository analysis results and metadata';
COMMENT ON TABLE examples IS 'Stores complete example analysis data (independent, static examples)';

COMMENT ON COLUMN analyses.status IS 'Analysis status: pending, started, completed, failed';
COMMENT ON COLUMN analyses.progress_status IS 'Human-readable description of current analysis progress for UI display';
COMMENT ON COLUMN analyses.metrics IS 'JSON containing central files list and graph data';
COMMENT ON COLUMN analyses.components IS 'JSON array containing component analysis results';

-- Original diagram columns
COMMENT ON COLUMN analyses.mermaid_modules IS 'Basic module dependency diagram (rule-based)';
COMMENT ON COLUMN analyses.mermaid_folders IS 'Project folder structure diagram';

-- Intelligent dependency diagram columns
COMMENT ON COLUMN analyses.mermaid_modules_simple IS 'Simplified overview diagram showing major component groups';
COMMENT ON COLUMN analyses.mermaid_modules_balanced IS 'Balanced diagram with grouped modules and categorized dependencies';
COMMENT ON COLUMN analyses.mermaid_modules_detailed IS 'Detailed diagram showing individual modules and relationships'; 