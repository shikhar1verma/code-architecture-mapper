#!/usr/bin/env python3
"""
Simple Requirements Testing Script

Tests different LangChain version combinations to find working ones.
"""

import subprocess
import sys
import tempfile
import os

def test_versions(versions_dict):
    """Test a specific combination of package versions."""
    
    # Create test requirements content
    test_content = [
        "# Test requirements",
        "fastapi==0.115.6",
        "pydantic==2.10.3",
        ""
    ]
    
    # Add LangChain packages
    for package, version in versions_dict.items():
        test_content.append(f"{package}=={version}")
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('\n'.join(test_content))
        temp_file = f.name
    
    try:
        # Test with pip
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--dry-run", "-r", temp_file
        ], capture_output=True, text=True, timeout=60)
        
        success = result.returncode == 0
        message = "✅ Compatible" if success else f"❌ {result.stderr.split('ERROR:')[1].split('To fix')[0].strip() if 'ERROR:' in result.stderr else 'Failed'}"
        
        return success, message
        
    except Exception as e:
        return False, f"❌ Error: {str(e)}"
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def main():
    print("🧪 Testing LangChain Version Combinations")
    print("=" * 50)
    
    # Test combinations from most recent to conservative
    test_cases = [
        ("Current (text-splitters 0.3.0)", {
            "langchain-core": "0.3.15",
            "langchain": "0.3.7",
            "langchain-community": "0.3.7",
            "langchain-text-splitters": "0.3.0",
            "langgraph": "0.2.28"
        }),
        ("LangGraph 0.2.20", {
            "langchain-core": "0.3.15", 
            "langchain": "0.3.7",
            "langchain-community": "0.3.7",
            "langchain-text-splitters": "0.3.0",
            "langgraph": "0.2.20"
        }),
        ("Conservative LangChain", {
            "langchain-core": "0.3.15",
            "langchain": "0.3.0", 
            "langchain-community": "0.3.0",
            "langchain-text-splitters": "0.3.0",
            "langgraph": "0.2.20"
        }),
        ("Very Conservative", {
            "langchain-core": "0.2.38",
            "langchain": "0.2.16",
            "langchain-community": "0.2.16",
            "langchain-text-splitters": "0.2.4", 
            "langgraph": "0.1.19"
        })
    ]
    
    working_combinations = []
    
    for name, versions in test_cases:
        print(f"\n🔍 Testing: {name}")
        success, message = test_versions(versions)
        print(f"   {message}")
        
        if success:
            working_combinations.append((name, versions))
    
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    
    if working_combinations:
        print(f"✅ Found {len(working_combinations)} working combination(s):")
        
        best_name, best_versions = working_combinations[0]
        print(f"\n🎯 RECOMMENDED: {best_name}")
        print("Update your requirements.txt with:")
        
        for package, version in best_versions.items():
            print(f"   {package}=={version}")
            
        print(f"\n📝 Copy these lines to your requirements.txt:")
        for package, version in best_versions.items():
            print(f"{package}=={version}")
    else:
        print("❌ No working combinations found!")
        print("Try Docker build or manual installation.")

if __name__ == "__main__":
    main()
