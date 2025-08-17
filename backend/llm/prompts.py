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
    "You extract stable 'Component Cards' from code hints. Output STRICT JSON only, matching the schema: "
    "{\"name\": str, \"purpose\": str, \"key_files\":[{\"path\":str,\"reason\":str}], "
    "\"apis\":[{\"name\":str,\"file\":str}], \"dependencies\":[str], \"risks\":[str], \"tests\":[str]}"
)

COMPONENT_USER_TMPL = (
    "Given these files and excerpts, propose ONE component card grounded in facts.\n"
    "Files: {files}\n\n"
    "Excerpts (truncated):\n{excerpts}\n"
    "Return ONLY the JSON."
) 