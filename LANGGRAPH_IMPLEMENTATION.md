# LangGraph Implementation for Code Architecture Analysis

## Overview

This document describes the LangGraph implementation that replaces the linear pipeline with a structured, node-based workflow for code architecture analysis.

## Architecture

### Workflow Structure

The LangGraph workflow follows this structure:

```
START → Core Analysis → Architecture Overview → [Components Extraction || Diagram Generation] → Final Summary → END
```

### Node Types

1. **Sequential Nodes**:
   - Core Analysis (Static analysis)
   - Architecture Overview (LLM-powered)
   - Final Summary (Rule-based)

2. **Parallel Nodes**:
   - Components Extraction (Rule-based + LLM)
   - Diagram Generation (LLM with self-correction subgraph)

3. **Sub-graphs**:
   - Diagram Self-Correction (Validates and corrects Mermaid diagrams)

### Key Features

#### 1. Core Analysis Node
- **Type**: Static analysis
- **Functions**: Repository cloning, file scanning, dependency extraction, metrics calculation
- **Output**: Core repository data, metrics, and dependency analysis

#### 2. Architecture Overview Node  
- **Type**: LLM-powered
- **Functions**: Generates architectural markdown overview
- **Dependencies**: Requires core analysis completion

#### 3. Components Extraction Node
- **Type**: Rule-based + LLM
- **Functions**: Groups files by components (rule-based) + extracts component details (LLM)
- **Execution**: Runs in parallel with diagram generation

#### 4. Diagram Generation Node + Subgraph
- **Type**: LLM with self-correction
- **Functions**: Creates intelligent Mermaid diagrams with validation
- **Self-Correction**: 3-attempt loop with syntax validation and error correction
- **Fallback**: Rule-based diagram generation if LLM fails
- **Execution**: Runs in parallel with component extraction

#### 5. Final Summary Node
- **Type**: Rule-based
- **Functions**: Prepares final response with all analysis results
- **Dependencies**: Requires both parallel nodes to complete

## State Management

### AnalysisState
Main state object passed between nodes containing:
- Input parameters (analysis_id, repo_url, force_refresh)
- Intermediate results (core analysis, architecture overview)
- Parallel processing results (components, diagrams) 
- Final results (summary, central files)
- Error tracking and processing status

### DiagramState (Subgraph)
Specialized state for diagram generation subgraph:
- Diagram generation attempts and validation
- Error tracking and correction history
- Final validated diagrams

## Implementation Files

### Core Files
- `backend/workflows/state.py` - State models and configuration
- `backend/workflows/nodes.py` - All node implementations  
- `backend/workflows/graph.py` - Main graph orchestrator
- `backend/workflows/diagram_subgraph.py` - Self-correcting diagram generation
- `backend/workflows/__init__.py` - Package exports

### Integration
- Updated `backend/routes/analysis/operations.py` - Main analysis endpoints
- Updated `backend/routes/analysis/diagrams.py` - Diagram generation endpoints
- Updated `backend/requirements.txt` - Added LangGraph dependencies

## Benefits Over Previous Pipeline

### 1. **Clear Separation of Concerns**
- Each node has a single, well-defined responsibility
- Easy to understand, test, and maintain individual components

### 2. **Parallel Processing**
- Components extraction and diagram generation run simultaneously
- Improved performance and resource utilization

### 3. **Self-Correcting Diagrams** 
- 3-attempt validation and correction loop for Mermaid diagrams
- Automatic syntax checking and error correction
- Fallback mechanisms for robust operation

### 4. **Better Error Handling**
- Granular error tracking at each node
- Failed nodes don't prevent other nodes from completing
- Graceful fallbacks maintain system functionality

### 5. **Extensibility**
- Easy to add new nodes or modify existing ones
- Clear interfaces for integrating new analysis types
- Subgraphs enable complex workflows within nodes

### 6. **Monitoring and Observability**
- State tracking shows exactly where processing is
- Detailed logging at each node
- Easy to identify bottlenecks and failures

## Usage

### Basic Analysis
```python
from backend.workflows import run_analysis_with_langgraph

result = run_analysis_with_langgraph(analysis_id, repo_url, force_refresh=False)
```

### On-Demand Diagram Generation
```python
from backend.workflows import generate_diagram_on_demand

diagram = generate_diagram_on_demand(
    analysis_id, mode, dependency_analysis, json_graph, file_infos, architecture_md
)
```

### Direct Workflow Usage
```python
from backend.workflows import AnalysisWorkflow

workflow = AnalysisWorkflow()
result = workflow.run_analysis(analysis_id, repo_url)
```

## Testing

Run the test script to verify installation and basic functionality:

```bash
cd backend
python workflows/test_langgraph.py
```

## Migration Path

The new LangGraph implementation is designed as a drop-in replacement:

1. **API Compatibility**: All existing API endpoints work unchanged
2. **Response Format**: Maintains identical response structure  
3. **Database Storage**: Uses same storage mechanisms
4. **Configuration**: Respects all existing configuration settings

## Configuration

The workflow respects all existing configuration:
- `USE_LLM_FOR_DIAGRAMS`: Controls LLM vs rule-based diagram generation
- `USE_LLM_FOR_DEPENDENCY_ANALYSIS`: Controls dependency analysis enhancement
- `TOP_FILES`, `COMPONENT_COUNT`: Controls processing limits

## Error Recovery

The LangGraph implementation includes robust error recovery:

1. **Node-Level Recovery**: Failed nodes don't crash the entire workflow
2. **LLM Fallbacks**: Rule-based alternatives when LLM calls fail
3. **Diagram Correction**: Multiple attempts with validation and correction
4. **Graceful Degradation**: Partial results when some components fail

This implementation provides a more robust, maintainable, and extensible foundation for the code architecture analysis system.
