"""
Test script to verify LangGraph integration and basic functionality.

Run this script to test the LangGraph workflow without running a full analysis.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Test LangGraph imports (v0.2.x)
    from langgraph.graph import StateGraph, END, START
    print("✅ LangGraph import successful")
    
    # Test workflow imports
    from backend.workflows.state import AnalysisState, DiagramState, AnalysisConfig
    from backend.workflows.nodes import (
        core_analysis_node, 
        architecture_overview_node,
        components_extraction_node,
        diagram_generation_node,
        central_file_summary_node
    )
    from backend.workflows.graph import AnalysisWorkflow, create_analysis_graph
    print("✅ Workflow imports successful")
    
    # Test basic graph creation
    graph = create_analysis_graph()
    print("✅ Analysis graph creation successful")
    
    # Test workflow initialization
    workflow = AnalysisWorkflow()
    print("✅ Workflow initialization successful")
    
    print("\n🎉 All LangGraph integration tests passed!")
    print("\nNext steps:")
    print("1. Run: pip install -r requirements.txt (to install LangGraph dependencies)")
    print("2. Start the backend server to test with actual repository analysis")
    print("3. The workflow is now ready to replace the existing pipeline")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTo fix this, run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
