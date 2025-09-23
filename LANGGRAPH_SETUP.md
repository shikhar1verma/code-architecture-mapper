# LangGraph Setup and Installation Guide

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `langgraph==0.2.45`
- `langchain==0.3.7`
- `langchain-core==0.3.15`

### 2. Test Installation
```bash
python workflows/test_langgraph.py
```

### 3. Start the Server
```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## What Changed

### New Features
✅ **LangGraph Workflow** - Structured node-based analysis pipeline
✅ **Parallel Processing** - Components + diagrams run simultaneously  
✅ **Self-Correcting Diagrams** - 3-attempt validation and correction loop
✅ **Better Error Handling** - Granular error tracking and recovery
✅ **Extensible Architecture** - Easy to add new analysis nodes

### API Compatibility
✅ **All existing endpoints work unchanged**
✅ **Same response format**  
✅ **Same database storage**
✅ **Same configuration settings**

## File Structure

```
backend/
├── workflows/              # New LangGraph implementation
│   ├── __init__.py         # Package exports
│   ├── state.py            # State models
│   ├── nodes.py            # Node implementations  
│   ├── graph.py            # Main workflow orchestrator
│   ├── diagram_subgraph.py # Self-correcting diagrams
│   └── test_langgraph.py   # Installation test
├── requirements.txt        # Updated with LangGraph
└── routes/analysis/
    ├── operations.py       # Updated to use LangGraph
    └── diagrams.py         # Updated diagram generation
```

## How It Works

### Original Flow (Linear)
```
Repository → Analysis → LLM Content → Diagrams → Response
```

### New LangGraph Flow (Structured)
```
START
  ↓
Core Analysis (Static)
  ↓  
Architecture Overview (LLM)
  ↓
┌─────────────────────┬─────────────────────┐
│ Components (LLM)    │ Diagrams (LLM Sub) │
│                     │   ↓ Validation      │
│                     │   ↓ Correction      │
│                     │   ↓ Retry (3x)      │
└─────────────────────┴─────────────────────┘
  ↓
Final Summary
  ↓
END
```

## Self-Correcting Diagrams

The diagram generation now includes intelligent validation:

1. **Generate** - Create Mermaid diagram using LLM
2. **Validate** - Check syntax, rendering issues, conventions
3. **Correct** - Apply automatic corrections for common errors
4. **Retry** - Up to 3 attempts with improvements
5. **Finalize** - Use best result or fallback to rule-based

Common corrections applied:
- Missing diagram type declarations
- Unbalanced brackets
- Overly long node labels  
- Problematic characters
- Complex diagram simplification

## Benefits

### For Developers
- **Clearer Code**: Each node has single responsibility
- **Better Testing**: Individual nodes can be tested in isolation
- **Easier Debugging**: State tracking shows exact failure points
- **Extensible**: Add new analysis types as new nodes

### For Users  
- **More Reliable**: Better error recovery and fallbacks
- **Better Diagrams**: Self-correction reduces rendering issues
- **Faster Analysis**: Parallel processing improves performance
- **Same Experience**: All existing functionality preserved

## Troubleshooting

### Import Errors
If you see `Unable to import 'langgraph.graph'`:
```bash
pip install -r requirements.txt
```

### Test Failures
Run the test script to diagnose issues:
```bash
python workflows/test_langgraph.py
```

### API Errors  
The LangGraph implementation maintains full API compatibility. If you see different responses, check logs for specific node failures.

## Next Steps

1. **Run Tests**: Verify the installation works correctly
2. **Start Server**: Test with actual repository analysis
3. **Monitor Logs**: Check for any issues during analysis
4. **Optimize**: Adjust configuration based on performance needs

The LangGraph implementation is now ready to handle your code architecture analysis with improved reliability and extensibility!
