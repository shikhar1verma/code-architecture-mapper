export interface AnalysisRequest {
  repo_url: string;
  force_refresh?: boolean;
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string; // "pending" | "started" | "completed" | "failed"
  cached?: boolean;
  cached_at?: string;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: string; // "pending" | "started" | "completed" | "failed"  
  progress_status?: string; // Human-readable progress description
  message?: string;
}

export interface RefreshAnalysisRequest {
  repo_url: string;
  force_refresh?: boolean;
}

export interface Component {
  name: string;
  purpose: string;
  key_files: { path: string; reason: string }[];
  apis: { name: string; file: string }[];
  dependencies: string[];
  risks: string[];
  tests: string[];
}

export interface CentralFile {
  path: string;
  fan_in: number;
  fan_out: number;
  degree_centrality: number;
}

export interface DependencyAnalysis {
  internal_edges: { src: string; dst: string }[];
  external_groups: Record<string, [string, string][]>;
  summary: {
    internal_count: number;
    external_count: number;
    categories: string[];
  };
}

export interface Metrics {
  central_files: CentralFile[];
  graph: {
    nodes: { id: string; fan_in: number; fan_out: number }[];
    edges: { source: string; target: string }[];
  };
  dependency_analysis: DependencyAnalysis;
}

export interface AnalysisResult {
  status: string;
  repo: {
    url: string;
    commit_sha: string;
  };
  language_stats: Record<string, number>;
  loc_total: number;
  file_count: number;
  metrics: Metrics;
  components: Component[];
  artifacts: {
    architecture_md: string;
    mermaid_modules: string;
    mermaid_modules_simple: string;
    mermaid_modules_balanced: string;
    mermaid_modules_detailed: string;
    mermaid_folders: string;
  };
  token_budget: {
    embed_calls: number;
    gen_calls: number;
    chunks: number;
  };
}

export type DiagramMode = 'simple' | 'balanced' | 'detailed' | 'folders';

export interface DiagramOption {
  mode: DiagramMode;
  label: string;
  description: string;
  diagram_key: keyof AnalysisResult['artifacts'];
}

export interface DiagramGenerationResponse {
  mode: string;
  diagram: string;
  status: string; // "generated" | "generated_rule_based"
  message?: string;
}

// Example-related types
export interface ExampleSummary {
  id: string;
  name: string;
  description: string;
  repo_url: string;
  repo_name: string;
  language_stats: Record<string, number>;
  loc_total: number;
  file_count: number;
}

export interface ExampleData {
  status: string;
  repo: {
    url: string;
    commit_sha: string;
    owner: string;
    name: string;
    default_branch: string;
  };
  language_stats: Record<string, number>;
  loc_total: number;
  file_count: number;
  metrics: Metrics;
  components: Component[];
  artifacts: {
    architecture_md: string;
    mermaid_modules: string;
    mermaid_modules_simple: string;
    mermaid_modules_balanced: string;
    mermaid_modules_detailed: string;
    mermaid_folders: string;
  };
  token_budget: {
    embed_calls: number;
    gen_calls: number;
    chunks: number;
  };
} 