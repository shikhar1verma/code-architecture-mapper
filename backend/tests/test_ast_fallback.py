#!/usr/bin/env python3
"""
Test to verify hybrid parsing approach (AST + Grimp for Python, AST + tree-sitter for JS)
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Handle imports for both running from root and from tests directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_hybrid_parsing():
    """Test hybrid parsing functionality for both Python and JavaScript"""
    
    print("🧪 Testing Hybrid Parsing (AST + Grimp/tree-sitter)")
    print("=" * 60)
    
    # Clone the repo temporarily
    test_dir = Path("/tmp/ast_test")
    repo_path = test_dir / "document-ai-chat"
    
    try:
        # Clean up and clone
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True)
        
        print("📥 Cloning test repository...")
        result = subprocess.run([
            "git", "clone", "https://github.com/shikhar1verma/document-ai-chat.git", str(repo_path)
        ], capture_output=True, text=True, cwd=test_dir)
        
        if result.returncode != 0:
            raise Exception(f"Clone failed: {result.stderr}")
        
        # Test direct import
        from backend.services.analysis.archmap_enhanced import EnhancedArchMapper
        
        print("✅ Repository cloned and mapper imported")
        
        # Test the enhanced mapper
        mapper = EnhancedArchMapper(str(repo_path))
        
        # Test file scanning
        files = mapper.scan_repo()
        py_files = [f for f in files if f['language'] == 'python']
        js_files = [f for f in files if f['language'] in ['javascript', 'jsx', 'typescript', 'tsx']]
        
        print(f"📁 Found {len(py_files)} Python files and {len(js_files)} JS/TS files")
        for pf in py_files[:3]:
            print(f"   Python: {pf['path']}")
        for jf in js_files[:3]:
            print(f"   JS/TS: {jf['path']}")
        
        # Test individual parsing methods
        print("\n🐍 Testing Python hybrid parsing...")
        
        # Test Grimp analysis
        grimp_edges = mapper.py_edges_grimp()
        print(f"   Grimp edges: {len(grimp_edges)}")
        
        # Test AST analysis on all files
        ast_edges = mapper.py_edges_ast_all_files(files)
        print(f"   AST edges: {len(ast_edges)}")
        
        # Test hybrid Python analysis
        hybrid_py_edges = mapper.py_edges_hybrid(files)
        print(f"   Hybrid Python edges: {len(hybrid_py_edges)}")
        
        # Count edge types
        py_edge_types = {}
        for edge in hybrid_py_edges:
            edge_type = edge.get('via', 'unknown')
            py_edge_types[edge_type] = py_edge_types.get(edge_type, 0) + 1
        print(f"   Python edge types: {py_edge_types}")
        
        # Test JavaScript/TypeScript hybrid parsing
        print("\n📜 Testing JS/TS hybrid parsing...")
        
        tsconf = mapper.load_tsconfig()
        all_js_edges = []
        
        for js_file in js_files[:3]:  # Test first 3 files
            print(f"\n   Testing: {js_file['path']}")
            
            # Test tree-sitter
            ts_edges = mapper.js_ts_imports_treesitter(js_file['path'], js_file['content'], tsconf)
            print(f"      Tree-sitter: {len(ts_edges)} edges")
            
            # Test AST regex
            ast_js_edges = mapper.js_ts_imports_ast(js_file['path'], js_file['content'], tsconf)
            print(f"      AST regex: {len(ast_js_edges)} edges")
            
            # Test hybrid
            hybrid_js_edges = mapper.js_ts_imports_hybrid(js_file['path'], js_file['content'], tsconf)
            print(f"      Hybrid: {len(hybrid_js_edges)} edges")
            
            all_js_edges.extend(hybrid_js_edges)
        
        # Count JS edge types
        js_edge_types = {}
        for edge in all_js_edges:
            edge_type = edge.get('via', 'unknown')
            js_edge_types[edge_type] = js_edge_types.get(edge_type, 0) + 1
        print(f"   JS/TS edge types: {js_edge_types}")
        
        # Test full hybrid analysis
        print(f"\n🔬 Testing full hybrid analysis...")
        result = mapper.analyze_repository()
        
        dep_analysis = result['dependencies']['dependency_analysis']
        print(f"✅ Full hybrid analysis completed:")
        print(f"   Total edges: {dep_analysis['total_edges']}")
        print(f"   Internal edges: {dep_analysis['summary']['internal_count']}")
        print(f"   External edges: {dep_analysis['summary']['external_count']}")
        print(f"   Edge types: {dep_analysis.get('edge_types', {})}")
        print(f"   Categories: {len(dep_analysis['summary']['categories'])} categories")
        
        # Verify hybrid approach found more edges
        total_individual = len(hybrid_py_edges) + len(all_js_edges)
        print(f"\n📊 Edge comparison:")
        print(f"   Individual parsing total: {total_individual}")
        print(f"   Full analysis total: {dep_analysis['total_edges']}")
        
        # Success criteria: hybrid should find edges and full analysis should work
        # Allow for some deduplication in hybrid approach
        py_expected = max(len(grimp_edges), len(ast_edges))
        py_success = len(hybrid_py_edges) >= (py_expected * 0.9)  # Allow 10% reduction due to deduplication
        js_success = len(all_js_edges) > 0 if js_files else True
        full_success = dep_analysis['total_edges'] > 0
        
        # Check edge types are present (showing hybrid approach worked)
        edge_types = dep_analysis.get('edge_types', {})
        hybrid_indicators = any(
            edge_type in ['ast', 'grimp', 'tree-sitter', 'ast-regex', 'grimp-preferred', 'tree-sitter-preferred']
            for edge_type in edge_types.keys()
        )
        
        print(f"\n✅ Validation results:")
        print(f"   Python hybrid success: {py_success}")
        print(f"   JS/TS hybrid success: {js_success}")
        print(f"   Full analysis success: {full_success}")
        print(f"   Hybrid indicators present: {hybrid_indicators}")
        
        return py_success and js_success and full_success and hybrid_indicators
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print(f"🧹 Cleaned up test directory")


if __name__ == "__main__":
    success = test_hybrid_parsing()
    if success:
        print(f"\n🎉 Hybrid parsing test passed!")
    else:
        print(f"\n💥 Hybrid parsing test failed!")
    
    sys.exit(0 if success else 1)
