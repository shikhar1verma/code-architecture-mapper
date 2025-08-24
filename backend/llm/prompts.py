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
    "- This prevents issues with special characters, spaces, and complex text\n\n"
    
    "Return ONLY the Mermaid diagram code, starting with 'flowchart':"
)

# Dedicated template for balanced diagram - the best architectural representation
MERMAID_BALANCED_GENERATION_SYSTEM = (
    "You are a senior software architect creating the BEST possible dependency diagram for a codebase. "
    "This diagram will be the primary architectural view that developers and stakeholders see first. "
    "Focus on creating an intuitive, comprehensive yet clean representation that tells the story of how the system works."
)

MERMAID_BALANCED_GENERATION_USER_TMPL = (
    "Create the BEST architectural dependency diagram for this project using the comprehensive context below:\n\n"
    
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
    
    "This is the PRIMARY architectural view - make it exceptional by:\n\n"
    "🎯 **ARCHITECTURAL CLARITY:**\n"
    "- Use the Component Map to understand logical groupings\n"
    "- Follow the Data Flow to show system interactions\n"
    "- Reference the folder structure for organizational context\n"
    "- Group modules into logical architectural layers (Frontend, Backend, Services, Data, etc.)\n\n"
    
    "📊 **BALANCED DETAIL:**\n"
    "- More detail than a simple overview, but cleaner than individual modules\n"
    "- Show component groups rather than every single file\n"
    "- Include the most critical external dependencies from the analysis\n"
    "- Focus on relationships that define the architecture\n\n"
    
    "🎨 **VISUAL EXCELLENCE:**\n"
    "- Use subgraphs to group related components based on the folder structure\n"
    "- Apply consistent styling with meaningful colors\n"
    "- Ensure the diagram flows logically following the data flow patterns\n"
    "- Keep it readable - avoid overcrowding\n\n"
    
    "🏗️ **STORYTELLING:**\n"
    "- The diagram should tell the story of how this system works\n"
    "- Someone should be able to understand the architecture at a glance\n"
    "- Show both internal structure and external integrations\n"
    "- Reflect the architectural insights from the Component Map and Data Flow\n\n"
    
    "⚠️ **CRITICAL MERMAID SYNTAX:**\n"
    "- ALWAYS wrap link text in double quotes to prevent parsing errors\n"
    "- Example: FA -- \"2. POST `/upload` document\" --> BA (CORRECT)\n"
    "- Example: FA -- 2. POST `/upload` document --> BA (INCORRECT - can break)\n"
    "- This prevents issues with special characters, spaces, and complex text\n\n"
    
    "Return ONLY the Mermaid diagram code, starting with 'flowchart':"
)

# NEW: Mermaid Correction Prompts
MERMAID_CORRECTION_SYSTEM = (
    "You are an expert at fixing Mermaid diagram syntax errors. "
    "You will receive a broken Mermaid diagram and a concise error message that typically includes line numbers and specific syntax issues. "
    "Your task is to fix the syntax error while preserving the diagram's structure and meaning. "
    "Focus on the specific error mentioned and make minimal, targeted changes."
)

MERMAID_CORRECTION_USER_TMPL = (
    "Fix this broken Mermaid diagram:\n\n"
    "```mermaid\n{broken_mermaid_code}\n```\n\n"
    "**Error:** {error_message}\n\n"
    "**Instructions:**\n"
    "1. **Analyze the error**: The error above shows the exact line and position where parsing failed\n"
    "   - Look for the line number mentioned\n"
    "   - The '^' pointer shows the exact character position\n"
    "   - 'Expecting X got Y' tells you what syntax was expected\n\n"
    "2. **Common Mermaid parse error fixes:**\n"
    "   - **Invalid characters in labels**: Use quotes around labels with spaces/special chars\n"
    "   - **Wrong node syntax**: Ensure proper node definitions (e.g., A[\"Label\"], B(\"Label\"))\n"
    "   - **Invalid connections**: Use proper arrows (-->, not ->) \n"
    "   - **Unescaped HTML/special chars**: Escape or quote HTML tags like <br/>\n"
    "   - **Missing quotes**: Quote multi-word labels and labels with special characters\n"
    "   - **Invalid node IDs**: Use alphanumeric characters and underscores only\n"
    "   - **Link text issues**: ALWAYS wrap link text in quotes (FA -- \"text\" --> BA)\n\n"
    "3. **Step-by-step fix:**\n"
    "   - Go to the line number mentioned in the error. Line number may mismatch sometimes.\n"
    "   - Look at the character position indicated by '^'\n"
    "   - Check what the parser expected vs what it got\n"
    "   - Apply the minimal fix (usually adding quotes or fixing syntax)\n"
    "   - Ensure the fix doesn't break the diagram's meaning\n\n"
    "Return ONLY the corrected Mermaid diagram code, starting with 'flowchart':"
) 