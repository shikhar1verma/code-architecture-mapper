# Architecture Analysis Tests

This directory contains test scripts for validating the enhanced architecture analysis functionality.

## Test Files

### `test_repo_metrics.py`
Comprehensive testing suite that:
- Clones a real repository for testing
- Tests file scanning, package detection, and dependency analysis
- Validates Grimp analysis for Python packages
- Tests tree-sitter analysis for JS/TS files  
- Validates AST fallback for loose Python files
- Tests the complete MetricsService integration
- Generates JSON output with analysis results

### `test_ast_fallback.py`
Focused test for AST fallback functionality:
- Tests Python import parsing using AST when no packages are detected
- Validates that loose Python files (without `__init__.py`) are properly analyzed
- Shows detailed import statement detection and edge creation

## Running Tests

The tests are designed to work when run from the project root directory:

```bash
# Navigate to project root
cd /path/to/code-architecture-mapper

# Run comprehensive metrics test
python backend/tests/test_repo_metrics.py

# Run focused AST fallback test  
python backend/tests/test_ast_fallback.py
```

**Note**: Both test files automatically detect the project root and set up the correct Python path, so they work seamlessly when run from the root directory.

## Test Repository

Both tests use the [document-ai-chat](https://github.com/shikhar1verma/document-ai-chat/) repository as a test case because it has:
- Loose Python files (no packages with `__init__.py`)
- JavaScript/TypeScript files
- Real import statements and dependencies
- Mixed internal and external dependencies

This makes it perfect for testing our AST fallback functionality for Python files.

## Expected Results

The tests should show:
- ✅ **File Scanning**: Detects Python and JS/TS files correctly
- ✅ **Package Detection**: Shows 0 Python packages (loose files)
- ✅ **AST Fallback**: Successfully parses Python imports using AST
- ✅ **Tree-sitter Analysis**: Parses JS/TS imports correctly
- ✅ **Enhanced Analysis**: Generates comprehensive metrics with both internal and external edges

The AST fallback should find **35+ Python edges** from the 3 Python files, demonstrating that our system correctly handles repositories with loose Python files.
