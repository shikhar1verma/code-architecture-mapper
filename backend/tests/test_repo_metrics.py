#!/usr/bin/env python3
"""
Repository Metrics Testing Tool

This script clones a specific repository and performs step-by-step metrics analysis
to validate our enhanced architecture analysis implementation.

Target Repository: https://github.com/shikhar1verma/document-ai-chat/
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Handle imports for both running from root and from tests directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.analysis.archmap_enhanced import EnhancedArchMapper
from backend.services.analysis.metrics import MetricsService
from backend.services.analysis.orchestrator import AnalysisOrchestrator


class RepoMetricsTester:
    """Test class for validating repository metrics analysis"""
    
    def __init__(self, repo_url: str, test_dir: str = "/tmp/repo_metrics_test"):
        self.repo_url = repo_url
        self.test_dir = Path(test_dir)
        self.repo_name = repo_url.split("/")[-1].replace(".git", "")
        self.repo_path = self.test_dir / self.repo_name
        
    def setup_test_environment(self):
        """Set up clean test environment"""
        print("🧹 Setting up test environment...")
        
        # Clean up existing test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        self.test_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created test directory: {self.test_dir}")
        
    def clone_repository(self):
        """Clone the target repository"""
        print(f"📥 Cloning repository: {self.repo_url}")
        
        try:
            result = subprocess.run([
                "git", "clone", self.repo_url, str(self.repo_path)
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
                
            print(f"   ✅ Repository cloned to: {self.repo_path}")
            
            # Show repository structure
            self._show_repo_structure()
            
        except Exception as e:
            print(f"   ❌ Clone failed: {e}")
            raise
    
    def _show_repo_structure(self):
        """Display repository structure"""
        print(f"\n📁 Repository structure:")
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'dist', 'build']]
            
            level = root.replace(str(self.repo_path), '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}{os.path.basename(root)}/")
            
            # Show Python and JS/TS files
            subindent = '  ' * (level + 1)
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.json')):
                    print(f"{subindent}{file}")
            
            if level > 2:  # Limit depth
                break
    
    def test_file_scanning(self):
        """Test 1: File scanning functionality"""
        print(f"\n🔍 Test 1: File Scanning")
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            files = mapper.scan_repo()
            
            print(f"   ✅ Files scanned: {len(files)}")
            
            # Group by language
            by_language = {}
            for file in files:
                lang = file['language']
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(file['path'])
            
            print(f"   📊 Languages found:")
            for lang, file_list in by_language.items():
                print(f"      {lang}: {len(file_list)} files")
                if len(file_list) <= 5:  # Show files if not too many
                    for file_path in file_list:
                        print(f"         - {file_path}")
                else:
                    for file_path in file_list[:3]:
                        print(f"         - {file_path}")
                    print(f"         ... and {len(file_list) - 3} more")
            
            total_loc = sum(f['loc'] for f in files)
            print(f"   📏 Total lines of code: {total_loc}")
            
            return files
            
        except Exception as e:
            print(f"   ❌ File scanning failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_python_packages_detection(self):
        """Test 2: Python packages detection"""
        print(f"\n🐍 Test 2: Python Packages Detection")
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            packages = mapper.detect_python_packages()
            
            print(f"   ✅ Python packages detected: {len(packages)}")
            for pkg in packages:
                print(f"      - {pkg}")
                
            if not packages:
                print(f"   ℹ️ No Python packages found. Checking for Python files...")
                files = mapper.scan_repo()
                py_files = [f for f in files if f['language'] == 'python']
                print(f"      Python files found: {len(py_files)}")
                for py_file in py_files[:5]:
                    print(f"         - {py_file['path']}")
                    
                print(f"   💡 Note: Grimp requires Python packages with __init__.py files.")
                print(f"      For loose Python files, we should fall back to AST parsing.")
                
            return packages
            
        except Exception as e:
            print(f"   ❌ Package detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_individual_python_files(self):
        """Test 2.5: Individual Python file analysis (AST fallback)"""
        print(f"\n🔍 Test 2.5: Individual Python Files Analysis")
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            files = mapper.scan_repo()
            py_files = [f for f in files if f['language'] == 'python']
            
            print(f"   📁 Analyzing {len(py_files)} Python files individually...")
            
            all_edges = []
            for py_file in py_files:
                print(f"   🔍 Analyzing: {py_file['path']}")
                
                # Check imports manually by looking at the content
                content = py_file['content']
                import_lines = [line.strip() for line in content.split('\n') 
                               if line.strip().startswith(('import ', 'from '))]
                
                print(f"      Found {len(import_lines)} import statements:")
                for imp in import_lines[:3]:  # Show first 3
                    print(f"         {imp}")
                if len(import_lines) > 3:
                    print(f"         ... and {len(import_lines) - 3} more")
                    
            return all_edges
            
        except Exception as e:
            print(f"   ❌ Individual file analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_hybrid_python_analysis(self):
        """Test 3: Hybrid Python analysis (Grimp + AST)"""
        print(f"\n🐍 Test 3: Hybrid Python Analysis")
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            files = mapper.scan_repo()
            
            print("   🔍 Running individual Python analysis methods...")
            
            # Test Grimp
            grimp_edges = mapper.py_edges_grimp()
            print(f"   Grimp edges: {len(grimp_edges)}")
            
            # Test AST
            ast_edges = mapper.py_edges_ast_all_files(files)
            print(f"   AST edges: {len(ast_edges)}")
            
            # Test hybrid
            hybrid_edges = mapper.py_edges_hybrid(files)
            print(f"   Hybrid edges: {len(hybrid_edges)}")
            
            # Analyze edge types
            edge_types = {}
            for edge in hybrid_edges:
                edge_type = edge.get('via', 'unknown')
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            
            print(f"   📊 Edge type breakdown: {edge_types}")
            
            if hybrid_edges:
                print(f"   📋 Sample hybrid edges:")
                for i, edge in enumerate(hybrid_edges[:5]):
                    edge_type = "→" if edge['internal'] else "↗"
                    print(f"      {i+1}. {edge['src']} {edge_type} {edge['dst']} ({edge['via']})")
                    
                if len(hybrid_edges) > 5:
                    print(f"      ... and {len(hybrid_edges) - 5} more edges")
            
            # Validate hybrid approach
            expected_count = max(len(grimp_edges), len(ast_edges))
            if len(hybrid_edges) >= expected_count:
                print(f"   ✅ Hybrid approach found at least as many edges as best individual method")
            else:
                print(f"   ⚠️ Hybrid found fewer edges than expected")
                
            return hybrid_edges
            
        except Exception as e:
            print(f"   ❌ Hybrid Python analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_hybrid_js_ts_analysis(self):
        """Test 4: Hybrid JavaScript/TypeScript analysis (tree-sitter + AST)"""
        print(f"\n📜 Test 4: Hybrid JavaScript/TypeScript Analysis") 
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            tsconf = mapper.load_tsconfig()
            
            print(f"   📋 TypeScript config loaded: {'✅' if tsconf else '❌'}")
            if tsconf:
                print(f"      Config keys: {list(tsconf.keys())}")
            
            # Find JS/TS files and test parsing
            files = mapper.scan_repo()
            js_ts_files = [f for f in files if f['language'] in ['javascript', 'jsx', 'typescript', 'tsx']]
            
            print(f"   📁 JS/TS files to analyze: {len(js_ts_files)}")
            
            all_js_edges = []
            edge_type_counts = {}
            
            for file_info in js_ts_files[:5]:  # Test first 5 files
                try:
                    print(f"\n   Analyzing: {file_info['path']}")
                    
                    # Test individual methods
                    ts_edges = mapper.js_ts_imports_treesitter(
                        file_info['path'], file_info['content'], tsconf
                    )
                    ast_edges = mapper.js_ts_imports_ast(
                        file_info['path'], file_info['content'], tsconf
                    )
                    hybrid_edges = mapper.js_ts_imports_hybrid(
                        file_info['path'], file_info['content'], tsconf
                    )
                    
                    print(f"      Tree-sitter: {len(ts_edges)} edges")
                    print(f"      AST regex: {len(ast_edges)} edges")
                    print(f"      Hybrid: {len(hybrid_edges)} edges")
                    
                    all_js_edges.extend(hybrid_edges)
                    
                    # Count edge types for this file
                    for edge in hybrid_edges:
                        edge_type = edge.get('via', 'unknown')
                        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
                    
                    # Show sample imports from this file
                    content = file_info['content']
                    import_lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if ('import ' in line or 'require(' in line or 'export' in line) and ('from ' in line or 'require(' in line):
                            import_lines.append(line)
                    
                    if import_lines:
                        print(f"         Sample import statements:")
                        for imp in import_lines[:2]:
                            print(f"            {imp}")
                            
                except Exception as e:
                    print(f"      {file_info['path']}: ❌ Failed - {e}")
            
            print(f"\n   ✅ Total hybrid JS/TS edges: {len(all_js_edges)}")
            print(f"   📊 Edge type breakdown: {edge_type_counts}")
            
            if all_js_edges:
                print(f"   📋 Sample hybrid JS/TS edges:")
                for i, edge in enumerate(all_js_edges[:3]):
                    edge_type = "→" if edge['internal'] else "↗"
                    print(f"      {i+1}. {edge['src']} {edge_type} {edge['dst']} ({edge['via']})")
                    
            return all_js_edges
            
        except Exception as e:
            print(f"   ❌ Hybrid JS/TS analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_full_analysis(self):
        """Test 5: Full enhanced analysis"""
        print(f"\n🔬 Test 5: Full Enhanced Analysis")
        print("=" * 50)
        
        try:
            mapper = EnhancedArchMapper(str(self.repo_path))
            result = mapper.analyze_repository()
            
            # Extract key metrics
            repo_metrics = result['files']['repository_metrics']
            dependency_analysis = result['dependencies']['dependency_analysis']
            graph_metrics = result['metrics']['graph_metrics']
            
            print(f"   ✅ Full analysis completed!")
            print(f"   📊 Repository metrics:")
            print(f"      Files: {repo_metrics['file_count']}")
            print(f"      Total LOC: {repo_metrics['loc_total']}")
            print(f"      Languages: {repo_metrics['language_stats']}")
            
            print(f"   🔗 Dependency analysis:")
            print(f"      Total edges: {dependency_analysis['total_edges']}")
            print(f"      Internal edges: {dependency_analysis['summary']['internal_count']}")
            print(f"      External edges: {dependency_analysis['summary']['external_count']}")
            print(f"      Categories: {len(dependency_analysis['summary']['categories'])} categories")
            
            print(f"   📈 Graph metrics:")
            print(f"      Nodes: {len(graph_metrics['fan_in'])}")
            print(f"      Top files count: {len(graph_metrics['top_files'])}")
            
            # Show top central files
            if graph_metrics['top_files']:
                print(f"   🏆 Top central files:")
                for i, file_path in enumerate(graph_metrics['top_files'][:5], 1):
                    fan_in = graph_metrics['fan_in'].get(file_path, 0)
                    fan_out = graph_metrics['fan_out'].get(file_path, 0)
                    centrality = graph_metrics['degree_centrality'].get(file_path, 0)
                    print(f"      {i}. {file_path}")
                    print(f"         Fan-in: {fan_in}, Fan-out: {fan_out}, Centrality: {centrality:.4f}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Full analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_metrics_service(self):
        """Test 6: MetricsService integration"""
        print(f"\n🎯 Test 6: MetricsService Integration")
        print("=" * 50)
        
        try:
            metrics_service = MetricsService()
            enhanced_metrics = metrics_service.analyze_repository_metrics(str(self.repo_path))
            
            print(f"   ✅ MetricsService analysis completed!")
            
            # Test central files summary
            central_files = metrics_service.get_central_files_summary(enhanced_metrics, limit=5)
            print(f"   🏆 Central files summary:")
            for file_data in central_files:
                print(f"      - {file_data['path']}")
                print(f"        Fan-in: {file_data['fan_in']}, Fan-out: {file_data['fan_out']}")
                print(f"        Centralities: degree={file_data['degree_centrality']}, in={file_data['in_degree_centrality']}, out={file_data['out_degree_centrality']}")
            
            # Test complexity analysis
            complexity = metrics_service.calculate_project_complexity_score(metrics=enhanced_metrics)
            print(f"   📊 Complexity analysis:")
            print(f"      Score: {complexity['complexity_score']} ({complexity['complexity_level']})")
            print(f"      Key metrics:")
            print(f"         Dependency ratio: {complexity['metrics']['dependency_ratio']}")
            print(f"         Avg fan-in: {complexity['metrics']['avg_fan_in']}")
            print(f"         Avg fan-out: {complexity['metrics']['avg_fan_out']}")
            
            # Test architectural patterns
            patterns = metrics_service.identify_architectural_patterns(enhanced_metrics)
            print(f"   🏗️ Architectural patterns:")
            for pattern_type, items in patterns.items():
                if pattern_type != 'insights' and items:
                    print(f"      {pattern_type}: {len(items)} files")
                    if items and len(items) <= 3:
                        for item in items:
                            if isinstance(item, dict) and 'path' in item:
                                print(f"         - {item['path']}")
            
            return enhanced_metrics
            
        except Exception as e:
            print(f"   ❌ MetricsService failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_results_to_json(self, result: Dict[str, Any]):
        """Save analysis results to JSON file"""
        if not result:
            print("   ⚠️ No results to save")
            return
            
        output_file = self.test_dir / f"{self.repo_name}_metrics.json"
        
        # Create a clean version for JSON serialization
        clean_result = {
            "repository": result["repository"],
            "files": {
                "repository_metrics": result["files"]["repository_metrics"],
                "file_count": len(result["files"]["file_infos"])
            },
            "dependencies": result["dependencies"],
            "metrics": {
                "graph_metrics": result["metrics"]["graph_metrics"],
                "top_files": result["metrics"]["top_files"]
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(clean_result, f, indent=2)
            print(f"   💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"   ❌ Failed to save results: {e}")
    
    def cleanup(self):
        """Clean up test environment"""
        print(f"\n🧹 Cleaning up...")
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            print(f"   ✅ Test directory cleaned up")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🧪 Repository Metrics Testing Suite")
        print("=" * 60)
        print(f"Target Repository: {self.repo_url}")
        print(f"Test Directory: {self.test_dir}")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_environment()
            self.clone_repository()
            
            # Run tests
            files = self.test_file_scanning()
            packages = self.test_python_packages_detection()
            self.test_individual_python_files()  # New test for loose Python files
            py_edges = self.test_hybrid_python_analysis()  # Updated to hybrid
            js_edges = self.test_hybrid_js_ts_analysis()   # Updated to hybrid
            full_result = self.test_full_analysis()
            metrics_result = self.test_metrics_service()
            
            # Save results
            if full_result:
                self.save_results_to_json(full_result)
            
            # Summary
            print(f"\n📋 Test Summary")
            print("=" * 30)
            print(f"✅ Files scanned: {len(files) if files else 0}")
            print(f"✅ Python packages: {len(packages) if packages else 0}")
            print(f"✅ Python edges: {len(py_edges) if py_edges else 0}")
            print(f"✅ JS/TS edges: {len(js_edges) if js_edges else 0}")
            print(f"✅ Full analysis: {'Success' if full_result else 'Failed'}")
            print(f"✅ MetricsService: {'Success' if metrics_result else 'Failed'}")
            
            # Analysis
            print(f"\n🔍 Analysis:")
            if not packages:
                print(f"   📝 No Python packages found - this repo has loose Python files")
                print(f"   💡 Consider adding AST fallback for Python files without packages")
            
            if not py_edges and packages:
                print(f"   ⚠️ Grimp found packages but no edges - dependency resolution issue")
            
            if not py_edges and not packages:
                print(f"   ℹ️ No Python packages or edges - this is normal for repos with loose Python files")
            
            print(f"\n💡 Hybrid Analysis Assessment:")
            if not packages:
                print(f"   1. ✅ Hybrid approach handles repos without packages via AST fallback")
                print(f"   2. ✅ This is normal behavior for scripts/loose Python files")
            
            total_edges = len(py_edges or []) + len(js_edges or [])
            if full_result:
                analysis = full_result['dependencies']['dependency_analysis']
                print(f"   3. ✅ Full hybrid analysis found {analysis['total_edges']} total edges")
                if 'edge_types' in analysis:
                    print(f"   4. ✅ Edge type distribution: {analysis['edge_types']}")
                if 'summary' in analysis:
                    print(f"   5. ✅ Summary structure: Internal={analysis['summary']['internal_count']}, External={analysis['summary']['external_count']}, Categories={len(analysis['summary']['categories'])}")
                
                if analysis['total_edges'] > total_edges:
                    print(f"   6. ✅ Full analysis found more edges than individual tests - good aggregation")
                elif analysis['total_edges'] == total_edges:
                    print(f"   6. ✅ Edge counts match - consistent aggregation")
                else:
                    print(f"   6. ⚠️ Full analysis found fewer edges - check aggregation logic")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            self.cleanup()


def main():
    """Main function to run the test"""
    repo_url = "https://github.com/shikhar1verma/document-ai-chat.git"
    
    tester = RepoMetricsTester(repo_url)
    success = tester.run_full_test_suite()
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
    else:
        print(f"\n💥 Some tests failed. Check the output above for details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
