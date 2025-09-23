OVERVIEW_SYSTEM = (
    "You are summarizing a repository into an Architecture overview. "
    "Use only facts grounded in provided files and metrics. If unsure, say 'unknown'."
)

OVERVIEW_USER_TMPL = (
    "Repo language stats: {language_stats}\n\n"
    "Top files (by centrality):\n{top_files}\n\n"
    "For each listed file, you may see a short excerpt below delimited by <file> tags.\n"
    "Write a clear, senior-level Architecture.md with sections: Overview, Component Map, Data Flow, Risks, How to Extend.\n"
    "Keep it concise and practical."
)

COMPONENT_SYSTEM = (
    "You are a software architect analyzing code to identify architectural components. "
    "Your response must be valid JSON only - no markdown, no explanations, no code blocks. "
    "Analyze the provided files and return a single JSON object representing one architectural component."
)

COMPONENT_USER_TMPL = (
    "Analyze these files to identify ONE architectural component:\n\n"
    "Files: {files}\n\n"
    "Code excerpts:\n{excerpts}\n\n"
    "Return a JSON object with this exact structure:\n"
    "{{\n"
    "  \"name\": \"ComponentName\",\n"
    "  \"purpose\": \"Brief description of what this component does\",\n"
    "  \"key_files\": [\n"
    "    {{\"path\": \"file/path.py\", \"reason\": \"Why this file is important\"}}\n"
    "  ],\n"
    "  \"apis\": [\n"
    "    {{\"name\": \"function_name\", \"file\": \"file/path.py\"}}\n"
    "  ],\n"
    "  \"dependencies\": [\"dependency1\", \"dependency2\"],\n"
    "  \"risks\": [\"potential risk or concern\"],\n"
    "  \"tests\": [\"test_file.py\"]\n"
    "}}\n\n"
    "Respond with ONLY the JSON object, no other text:"
)

# NEW: Dependency Analysis Prompts
DEPENDENCY_ANALYSIS_SYSTEM = (
    "You are an expert software architect analyzing module dependencies. "
    "Your task is to create an intelligent, simplified dependency analysis that groups related modules "
    "and highlights the most important architectural relationships. Focus on clarity and readability."
)

DEPENDENCY_ANALYSIS_USER_TMPL = (
    "Analyze this project's module dependencies and create an intelligent grouping:\n\n"
    "Internal Dependencies (File-to-File):\n{internal_deps}\n\n"
    "External Dependencies by Category:\n{external_deps}\n\n"
    "Project Context:\n"
    "- Language Stats: {language_stats}\n"
    "- Total Files: {file_count}\n"
    "- Key Files: {top_files}\n\n"
    "Create a JSON response with intelligent dependency grouping:\n"
    "{{\n"
    "  \"architectural_layers\": [\n"
    "    {{\n"
    "      \"name\": \"LayerName\",\n"
    "      \"purpose\": \"What this layer does\",\n"
    "      \"modules\": [\"module1\", \"module2\"],\n"
    "      \"dependencies\": [\"layer_it_depends_on\"]\n"
    "    }}\n"
    "  ],\n"
    "  \"key_relationships\": [\n"
    "    {{\n"
    "      \"from\": \"module1\",\n"
    "      \"to\": \"module2\",\n"
    "      \"relationship_type\": \"imports|uses|extends|configures\",\n"
    "      \"importance\": \"high|medium|low\"\n"
    "    }}\n"
    "  ],\n"
    "  \"external_integration\": {{\n"
    "    \"critical_dependencies\": [\"dep1\", \"dep2\"],\n"
    "    \"development_dependencies\": [\"dep1\", \"dep2\"],\n"
    "    \"optional_dependencies\": [\"dep1\", \"dep2\"]\n"
    "  }},\n"
    "  \"simplification_notes\": \"Explanation of how dependencies were grouped and why\"\n"
    "}}\n\n"
    "Respond with ONLY the JSON object:"
)

MERMAID_GENERATION_SYSTEM = (
    "You are an expert at creating clean, readable Mermaid diagrams for software architecture. "
    "Create intelligent, simplified dependency graphs that are easy to understand while showing the most important relationships."
)

# OLD PROMPTS REPLACED BY CHATGPT IMPROVED VERSIONS ABOVE

# OLD BALANCED PROMPTS REMOVED - REPLACED BY CHATGPT IMPROVED VERSIONS

# OLD DETAILED PROMPTS REMOVED - REPLACED BY CHATGPT IMPROVED VERSIONS

MERMAID_GENERATION_USER_TMPL = (
    "Create an intelligent Mermaid diagram using the comprehensive context below:\n\n"
    
    "📁 **PROJECT STRUCTURE:**\n"
    "```mermaid\n{folder_structure}\n```\n\n"
    
    "🏗️ **COMPONENT MAP:**\n"
    "{component_map}\n\n"
    
    "🔄 **DATA FLOW:**\n"
    "{data_flow}\n\n"
    
    "🔗 **INTERNAL DEPENDENCIES:**\n"
    "{internal_dependencies}\n\n"
    
    "📦 **EXTERNAL DEPENDENCIES:**\n"
    "{external_dependencies}\n\n"
    
    "📊 **PROJECT STATS:**\n"
    "- Total Files: {total_files}\n"
    "- Top Files: {top_files}\n"
    "- Dependency Summary: {dependency_summary}\n\n"
    
    "**Visualization Mode: {mode}**\n"
    "- 'overview': High-level architectural overview showing major component groups\n"
    "- 'detailed': Detailed view with individual modules and key relationships\n\n"
    
    "Create a clean Mermaid flowchart that:\n"
    "1. Uses the Component Map and Data Flow for architectural understanding\n"
    "2. References the folder structure for logical groupings\n"
    "3. Shows clear architectural layers based on the context\n"
    "4. Highlights the most important dependencies from the analysis\n"
    "5. Uses appropriate styling and colors\n"
    "6. Is readable and not cluttered\n"
    "7. Reflects the complexity level appropriate for the '{mode}' mode\n\n"
    
    "⚠️ **CRITICAL MERMAID SYNTAX:**\n"
    "- ALWAYS wrap link text in double quotes to prevent parsing errors\n"
    "- Example: FA -- \"2. POST `/upload` document\" --> BA (CORRECT)\n"
    "- Example: FA -- 2. POST `/upload` document --> BA (INCORRECT - can break)\n"
    "- ALWAYS quote node labels with parentheses or special characters\n"
    "- Example: REACT_ICONS[\"React Icons (Io5)\"] (CORRECT)\n"
    "- Example: REACT_ICONS[React Icons (Io5)] (INCORRECT - causes parse errors)\n"
    "- This prevents issues with special characters, spaces, and complex text\n\n"
    
    "Return ONLY the Mermaid diagram code, starting with 'flowchart':"
)

# OLD BALANCED GENERATION PROMPTS - REDUNDANT WITH NEW CHATGPT STRUCTURE

# REMOVED: Old redundant MERMAID_BALANCED_GENERATION_USER_TMPL

# ========= CHATGPT IMPROVED MERMAID PROMPTS =========
# Common system prompt with shared instructions for all modes
MERMAID_COMMON_SYSTEM = (
    "You are a software architect that outputs a Mermaid flowchart showing system architecture. "
    "Audience varies by mode. Optimize for clarity first, detail second. "
    "Work only with the provided repo context. Do not invent components that do not exist."
    "\n\n"
    "OUTPUT RULES\n"
    "- Return ONLY Mermaid code starting with 'flowchart TB'. No backticks. No preface text. "
    "- Use top-to-bottom layout: 'flowchart TB'. "
    "- Prefer short labels. Trim to <= 24 chars. Use Title Case for nodes. "
    "- External systems: rounded nodes (( )), databases: cylinders [( )], queues: subroutine [[ ]], default: [ ] "
    "- Use at most one edge label per link, wrapped in double quotes. Example: A -- \"Auth\" --> B "
    "- Quote any label containing spaces, parentheses, or punctuation inside brackets. Example: SVC[\"Auth Service\"] "
    "- Do not include stray characters after a node definition or edge. No trailing letters. "
    "- No duplicate edges between the same pair. "
    "- If a budget would be exceeded, collapse into 'Other …' nodes and skip low-signal edges."
    "\n\n"
    "GROUPING HEURISTICS\n"
    "- Group by folders or packages into layers: Presentation, API, Services, Domain, Data, Infra, Jobs, Tests. "
    "- JS/TS hints: src/components -> Presentation, src/pages -> Presentation, src/api|controllers -> API, "
    "src/services|usecases -> Services, src/domain|entities -> Domain, src/repositories|db -> Data, "
    "scripts|infra|deploy -> Infra, queue|worker -> Jobs, __tests__|tests -> Tests. "
    "- Python hints: app|api|views -> API, services|use_cases -> Services, domain|models -> Domain, "
    "repo|repository|db|migrations -> Data, cli|scripts|infra -> Infra, tasks|celery|workers -> Jobs, tests -> Tests."
    "\n\n"
    "DEPENDENCY PRUNING\n"
    "- Rank dependencies by frequency or centrality from 'internal_dependencies'. "
    "- Keep only the top K edges per node, where K is set by the mode. "
    "- Prefer cross-layer edges over intra-layer edges. "
    "- Deduplicate and merge parallel edges with a single descriptive label."
    "\n\n"
    "DATA FLOW\n"
    "- Keep one primary path: User -> Presentation -> API -> Services -> Domain -> Data "
    "plus optional External and Jobs. "
    "- Only label major flows like \"HTTP\", \"gRPC\", \"Queue\", \"SQL\", \"Cache\"."
    "\n\n"
    "SELF CHECK\n"
    "- Node count <= mode max_nodes. Edge count <= mode max_edges.\n"
    "- No file paths or file names.\n"
    "- No duplicate edges. No trailing characters after lines.\n"
    "- All labels with spaces or punctuation are quoted."
)

# Common user template with consistent structure
MERMAID_COMMON_USER_TMPL = (
    "Use this repo context:\n"
    "PROJECT STRUCTURE (as Mermaid code block for parsing only):\n"
    "```mermaid\n{folder_structure}\n```\n\n"
    "COMPONENT MAP:\n{component_map}\n\n"
    "DATA FLOW NOTES:\n{data_flow}\n\n"
    "INTERNAL DEPENDENCIES:\n{internal_dependencies}\n\n"
    "EXTERNAL DEPENDENCIES:\n{external_dependencies}\n\n"
    "PROJECT STATS:\n- Total Files: {total_files}\n- Top Files: {top_files}\n- Dependency Summary: {dependency_summary}\n\n"
    "Now generate the diagram for the selected MODE using the MODE POLICY appended below."
)

# ========= MODE POLICIES =========
# Overview: 3-6 coarse components, no subgraphs, only the main flow, zero file-level detail.
MERMAID_OVERVIEW_POLICY = (
    "MODE = OVERVIEW\n"
    "AUDIENCE: Non-technical stakeholders.\n"
    "GOAL: Explain what the system is and how major parts interact.\n"
    "BUDGETS: max_nodes=6, max_edges=7, max_edge_labels=5, edges_per_node=1\n"
    "RULES\n"
    "- Do not use subgraph. "
    "- Only show 3-6 big components: Presentation, API, Services, Data, External, Jobs if present. "
    "- Show a single main path with minimal branching. "
    "- Do not include tests, config, or tooling. "
    "- No file or class names. "
    "OUTPUT: Mermaid starting with 'flowchart TB'."
)

# Balanced: 10-16 components via 3-5 subgraphs, top dependencies only, no file-level nodes.
MERMAID_BALANCED_POLICY = (
    "MODE = BALANCED\n"
    "AUDIENCE: Engineers and technical stakeholders.\n"
    "GOAL: Show layered modules and key integrations without noise.\n"
    "BUDGETS: max_nodes=16, max_edges=18, edges_per_node=2, subgraphs=3..5\n"
    "RULES\n"
    "- Use subgraphs to represent layers. Put 2-4 nodes per subgraph. "
    "- Nodes are modules or folders, never individual files. "
    "- Keep only the top 2 cross-layer dependencies per node. "
    "- Collapse small or niche modules into 'Other Services' or 'Other Data'. "
    "- Include External services as rounded nodes and Database as cylinder. "
    "- Optional small legend subgraph if within budget. "
    "OUTPUT: Mermaid starting with 'flowchart TB'."
)

# Detailed: 18-24 components, stays at module level but adds key intra-layer edges.
# This keeps it readable while being the old "balanced" depth.
MERMAID_DETAILED_POLICY = (
    "MODE = DETAILED\n"
    "AUDIENCE: Senior engineers and leads.\n"
    "GOAL: Expose important module relationships without dropping to file-level.\n"
    "BUDGETS: max_nodes=24, max_edges=28, edges_per_node=3, subgraphs=4..6\n"
    "RULES\n"
    "- Still no file-level nodes. Use modules, packages, or feature folders only. "
    "- Prefer inter-module edges that explain flows. Intra-layer edges allowed but pruned to essentials. "
    "- Keep only high-signal dependencies and collapse low-usage ones into 'Other …'. "
    "- Include CI/CD or Infra only if present and meaningful, keep it compact. "
    "- If node or edge count would exceed budget, raise pruning thresholds and regenerate internally. "
    "OUTPUT: Mermaid starting with 'flowchart TB'."
)

# ========= COMPOSED PROMPTS (drop-in replacements) =========
MERMAID_OVERVIEW_SYSTEM_NEW = MERMAID_COMMON_SYSTEM
MERMAID_OVERVIEW_USER_TMPL_NEW = MERMAID_COMMON_USER_TMPL + "\n" + MERMAID_OVERVIEW_POLICY + "\nReturn ONLY the Mermaid diagram code, starting with 'flowchart TB':"

MERMAID_BALANCED_SYSTEM_NEW = MERMAID_COMMON_SYSTEM
MERMAID_BALANCED_USER_TMPL_NEW = MERMAID_COMMON_USER_TMPL + "\n" + MERMAID_BALANCED_POLICY + "\nReturn ONLY the Mermaid diagram code, starting with 'flowchart TB':"

MERMAID_DETAILED_SYSTEM_NEW = MERMAID_COMMON_SYSTEM
MERMAID_DETAILED_USER_TMPL_NEW = MERMAID_COMMON_USER_TMPL + "\n" + MERMAID_DETAILED_POLICY + "\nReturn ONLY the Mermaid diagram code, starting with 'flowchart TB':"

# NEW: Mermaid Correction Prompts
MERMAID_CORRECTION_SYSTEM = (
    "You are a Mermaid diagram syntax expert. Your ONLY job is to fix the specific syntax error provided. "
    "You MUST return a corrected diagram that renders without errors. "
    "Make MINIMAL changes - only fix what's broken, preserve everything else exactly. "
    "The error message will tell you exactly what's wrong and where."
)

MERMAID_CORRECTION_USER_TMPL = (
    "BROKEN DIAGRAM:\n"
    "```\n{broken_mermaid_code}\n```\n\n"
    "ERROR MESSAGE:\n"
    "{error_message}\n\n"
    "COMMON FIXES FOR SPECIFIC ERRORS:\n\n"
    "🔧 **\"Expecting 'SQE', got 'PS'\" or similar parse errors:**\n"
    "   - CAUSE: Extra content after subgraph declaration OR parentheses in node labels\n"
    "   - FIX: Move content to next line OR quote labels with parentheses\n"
    "   - EXAMPLE: `subgraph Frontend [App]    direction LR` → `subgraph Frontend [App]\\n    direction LR`\n"
    "   - EXAMPLE: `REACT_ICONS[React Icons (Io5)]` → `REACT_ICONS[\"React Icons (Io5)\"]`\n\n"
    "🔧 **\"Unexpected token\" or \"Invalid character\":**\n"
    "   - CAUSE: Special characters in labels without quotes\n"
    "   - FIX: Add quotes around labels with spaces/special chars\n"
    "   - EXAMPLE: `A[My App (v1.0)]` → `A[\"My App (v1.0)\"]`\n\n"
    "🔧 **\"Missing diagram type\":**\n"
    "   - CAUSE: No flowchart declaration\n"
    "   - FIX: Add `flowchart LR` at the beginning\n\n"
    "🔧 **\"Unbalanced subgraph blocks\":**\n"
    "   - CAUSE: Missing `end` statements\n"
    "   - FIX: Add `end` for each `subgraph`\n\n"
    "🔧 **\"Invalid node ID\":**\n"
    "   - CAUSE: Spaces in node IDs\n"
    "   - FIX: Replace spaces with underscores\n"
    "   - EXAMPLE: `FE NAVBAR` → `FE_NAVBAR`\n\n"
    "**COMMON MERMAID PARSE ERROR FIXES:**\n"
    "   - **Invalid characters in labels**: Use quotes around labels with spaces/special chars\n"
    "   - **Wrong node syntax**: Ensure proper node definitions (e.g., A[\"Label\"], B(\"Label\"))\n"
    "   - **Invalid connections**: Use proper arrows (-->, not ->) \n"
    "   - **Unescaped HTML/special chars**: Escape or quote HTML tags like <br/>\n"
    "   - **Missing quotes**: Quote multi-word labels and labels with special characters\n"
    "   - **Invalid node IDs**: Use alphanumeric characters and underscores only\n"
    "   - **Link text issues**: ALWAYS wrap link text in quotes (FA -- \"text\" --> BA)\n\n"
    "INSTRUCTIONS:\n"
    "1. Read the error message carefully\n"
    "2. Find the problematic line/syntax\n"
    "3. Apply the MINIMAL fix needed\n"
    "4. Keep everything else EXACTLY the same\n"
    "5. Return ONLY the corrected diagram code\n\n"
    "CORRECTED DIAGRAM:"
) 