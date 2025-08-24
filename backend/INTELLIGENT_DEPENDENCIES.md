# Intelligent Dependency Graph System

## Overview

The code architecture mapper now includes an advanced intelligent dependency graph system that addresses the common problem of overwhelming dependency visualizations in complex projects.

## Problem Solved

**Before**: Traditional dependency graphs become cluttered and unreadable when projects have many packages and dependencies, creating "dependency spaghetti" that obscures architectural insights.

**After**: Intelligent filtering, grouping, and multi-level visualization that maintains clarity while preserving important architectural relationships.

## Features

### 1. **Rule-Based Intelligent Filtering**

Automatically categorizes and filters dependencies:

- **Internal Dependencies**: File-to-file relationships within your project
- **External Categories**: 
  - Frontend/UI (React, Vue, CSS frameworks)
  - Backend/API (Express, FastAPI, server frameworks)  
  - Database (SQL, MongoDB, ORMs)
  - Testing (Jest, PyTest, testing frameworks)
  - Build/Config (Webpack, Babel, config files)
  - Utilities (Lodash, Date libraries, helpers)
  - Standard Library (Built-in language libraries)

### 2. **Multi-Level Visualization Modes**

#### Simple Mode (`mode: 'simple'`)
- High-level architectural overview
- Shows only major component groups
- Perfect for executive summaries and initial understanding

#### Balanced Mode (`mode: 'balanced'`) - **Default**
- Groups internal modules by directory/component
- Shows categorized external dependencies
- Optimal balance of detail and clarity

#### Detailed Mode (`mode: 'detailed'`)  
- Individual modules and relationships
- Top external dependencies per category
- For deep architectural analysis

#### Focused Mode (`mode: 'focused'`)
- Centers on a specific module
- Shows direct dependencies and dependents
- Interactive drill-down capability

### 3. **Smart Grouping Logic**

**Internal Module Grouping**:
- Directory-based organization (frontend/, backend/, services/)
- Semantic grouping (components, utilities, tests)
- Configurable group names and relationships

**External Dependency Filtering**:
- De-prioritizes standard library imports
- Groups related packages (all React-related together)
- Limits noise while preserving important relationships

## API Endpoints

### Basic Analysis
```bash
POST /analysis/start
{
    "repo_url": "https://github.com/user/repo",
    "force_refresh": false
}
```

### Focused Analysis
```bash
GET /analysis/{analysis_id}/focus/src/components/Button.tsx
```

Returns focused dependency graph and connection metrics for specific module.

### Dependency Insights
```bash
GET /analysis/{analysis_id}/dependency-insights
```

Returns:
- Most connected modules
- External dependency statistics  
- Architectural recommendations
- Connection metrics

## Frontend Integration

### Diagram Mode Selector
Users can switch between visualization modes:
- **Overview**: High-level architecture 
- **Grouped**: Organized modules with categories
- **Detailed**: Individual module relationships
- **Structure**: Project folder hierarchy

### Interactive Features
- Click-to-focus on specific modules
- Download diagrams in different modes
- Real-time dependency insights
- Architectural recommendations

## Configuration Options

### Complexity Levels
```python
# In build_graph()
filter_and_group_dependencies(edges, complexity_level="balanced")

# Options:
# - "simple": Major categories only, minimal external deps
# - "balanced": Categorized externals, grouped internals  
# - "detailed": Most deps with smart grouping
```

### Customization
```python
# Add new dependency categories
def categorize_dependency(dep: str) -> str:
    # Add your custom categorization logic
    if 'your-framework' in dep.lower():
        return "Your Framework"
    # ...
```

## Advanced Features

### LLM-Powered Enhancement (Optional)
Uses Gemini to create even more intelligent groupings:

```python
enhanced_analysis = enhance_dependency_analysis_with_llm(
    dependency_analysis, language_stats, file_count, top_files
)
```

Benefits:
- Semantic understanding of relationships
- Context-aware grouping
- Architectural layer identification
- Custom simplification strategies

### Architectural Recommendations
Automatically suggests improvements:
- "High external/internal dependency ratio detected"
- "Consider grouping similar dependencies"
- "Review development vs production dependencies"

## Usage Examples

### Simple Project Overview
```javascript
// Frontend: Select 'Overview' mode
// Shows: ProjectModules -> [Frontend/UI, Backend/API, Database]
```

### Complex Microservices Analysis  
```javascript
// Frontend: Select 'Grouped' mode  
// Shows: Services, Components, Utilities grouped with categorized externals
```

### Module-Specific Investigation
```javascript
// Frontend: Click on specific module in Files table
// API: GET /analysis/{id}/focus/src/services/auth.py
// Shows: Just that module and its direct connections
```

## Benefits

1. **Clarity**: Complex projects remain readable
2. **Scalability**: Handles large codebases gracefully  
3. **Actionable**: Provides architectural insights and recommendations
4. **Interactive**: Multiple views for different audiences
5. **Intelligent**: Uses both rules and AI for optimal grouping

## Best Practices

1. **Start with 'Balanced' mode** for most analyses
2. **Use 'Simple' for stakeholder presentations**
3. **Switch to 'Detailed' for architectural reviews**  
4. **Use 'Focused' to investigate specific modules**
5. **Review dependency insights for optimization opportunities**

This intelligent system transforms overwhelming dependency graphs into clear, actionable architectural insights while maintaining the flexibility to drill down when needed. 