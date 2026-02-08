# RAG Chatbot Testing Guide

## Quick Start

### Run All Tests
```bash
uv run pytest backend/tests/ -v
```

### Run Specific Test Categories
```bash
# Course search tool tests
uv run pytest backend/tests/test_course_search_tool.py -v

# AI generator tests
uv run pytest backend/tests/test_ai_generator.py -v

# RAG system integration tests
uv run pytest backend/tests/test_rag_system_integration.py -v

# Vector store tests
uv run pytest backend/tests/test_vector_store.py -v
```

### Run Specific Test
```bash
uv run pytest backend/tests/test_course_search_tool.py::TestCourseSearchToolExecution::test_execute_nonexistent_course -v
```

---

## Test Organization

### Test Files

#### 1. `test_course_search_tool.py` (15 tests)
Tests the `CourseSearchTool` - the tool Claude uses to search for course content.

**Key Test Classes**:
- `TestCourseSearchToolDefinition`: Validates tool definition format
- `TestCourseSearchToolExecution`: Tests tool execution with various parameters
- `TestToolManager`: Tests tool registration and execution management

**Critical Tests**:
- `test_execute_nonexistent_course`: Ensures nonexistent courses return errors (not wrong courses)
- `test_sources_tracking`: Validates that sources are properly tracked for display

#### 2. `test_ai_generator.py` (10 tests)
Tests the `AIGenerator` - handles Claude API integration and tool execution.

**Key Test Classes**:
- `TestAIGeneratorInitialization`: Validates configuration
- `TestAIGeneratorResponseGeneration`: Tests response generation with/without tools
- `TestAIGeneratorToolExecution`: Tests tool calling and execution flow
- `TestAIGeneratorEdgeCases`: Tests error scenarios

**Critical Tests**:
- `test_handle_tool_execution_flow`: Validates tool calls are properly executed
- `test_tool_execution_constructs_messages_correctly`: Ensures message structure is correct

#### 3. `test_rag_system_integration.py` (15 tests)
End-to-end tests of the complete RAG system.

**Key Test Classes**:
- `TestRAGSystemInitialization`: Validates all components are set up
- `TestRAGSystemDocumentProcessing`: Tests loading courses from documents
- `TestRAGSystemQueryProcessing`: Tests the full query→answer flow
- `TestRAGSystemSourceTracking`: Tests source extraction and tracking
- `TestRAGSystemErrorHandling`: Tests error scenarios

**Critical Tests**:
- `test_query_tool_execution_flow`: Full end-to-end test with tool execution
- `test_query_without_tool_call`: Tests general knowledge questions without searching

#### 4. `test_vector_store.py` (27 tests)
Tests the `VectorStore` - ChromaDB integration and semantic search.

**Key Test Classes**:
- `TestSearchResultsDataclass`: Tests result container
- `TestVectorStoreInitialization`: Tests setup
- `TestVectorStoreAddContent`: Tests adding courses/chunks
- `TestVectorStoreSearch`: Tests search with filters
- `TestVectorStoreResolveCourseNames`: Tests course name resolution (the main fix)
- `TestVectorStoreClearData`: Tests data clearing
- `TestVectorStoreMetadata`: Tests metadata retrieval

**Critical Tests**:
- `test_search_nonexistent_course`: Validates course similarity threshold (MAIN FIX)
- `test_search_with_course_name_filter`: Validates filtering works correctly
- `test_resolve_nonexistent_course`: Ensures bad matches return None

---

## The Main Fix: Course Similarity Threshold

### What Was Broken
Before the fix, when a user asked about "Advanced Machine Learning" course (which doesn't exist), the system would:
1. Search for semantically similar courses
2. Find "Introduction to Machine Learning"
3. Return content from that course WITHOUT telling the user
4. Claude would get wrong content and return confusing answers

### The Fix
Added a similarity threshold check in `VectorStore._resolve_course_name()`:
```python
distance = results['distances'][0][0]  # Get similarity score
if distance > 1.5:  # If too dissimilar
    return None  # Course doesn't exist
```

### Validation
The test `test_search_nonexistent_course` validates this:
```python
def test_search_nonexistent_course(self, test_vector_store, sample_course, sample_chunks):
    # Add a course to the vector store
    test_vector_store.add_course_metadata(sample_course)
    test_vector_store.add_course_content(sample_chunks)

    # Try to search for a completely different course
    results = test_vector_store.search(query="test", course_name="Nonexistent Course")

    # Should fail gracefully
    assert results.is_empty()
    assert "No course found" in results.error
```

---

## Running Tests During Development

### Before Making Changes
```bash
# Run tests to establish baseline
uv run pytest backend/tests/ -v
```

### After Making Changes
```bash
# Quick test
uv run pytest backend/tests/ -x -v

# With coverage report
uv run pytest backend/tests/ --cov=backend --cov-report=html

# Specific test for your change
uv run pytest backend/tests/test_vector_store.py::TestVectorStoreSearch -v
```

### Test Driven Development
```bash
# 1. Write test first
# 2. Run test (should fail)
uv run pytest backend/tests/test_feature.py -v

# 3. Implement feature
# 4. Run test again (should pass)
uv run pytest backend/tests/test_feature.py -v

# 5. Run all tests (no regressions)
uv run pytest backend/tests/ -v
```

---

## Test Fixtures

All test fixtures are defined in `conftest.py`:

### `test_config`
Configuration object for tests with temporary ChromaDB database.

### `test_vector_store`
Fresh vector store instance for each test.

### `test_document_processor`
Document processor instance.

### `sample_course`
Sample course with lessons for testing.

### `sample_chunks`
Sample course chunks ready for vector storage.

### `sample_document_text`
Raw course document text.

### `temp_document_file`
Temporary file with sample course content.

### Usage Example
```python
def test_something(self, test_vector_store, sample_course, sample_chunks):
    # Fixtures are automatically provided
    test_vector_store.add_course_metadata(sample_course)
    test_vector_store.add_course_content(sample_chunks)
    # ... test code
```

---

## Understanding Test Failures

### Common Failure Patterns

**If SearchResults Tests Fail**
- Check if ChromaDB is working properly
- Verify embeddings are being generated
- Ensure similarity threshold logic is correct

**If AIGenerator Tests Fail**
- Verify Anthropic API is configured (ANTHROPIC_API_KEY env var)
- Check if mocking is working (check patch paths)
- Ensure tool definitions are valid JSON

**If RAG System Tests Fail**
- Run document processing tests first
- Then vector store tests
- Then individual component tests
- Finally integration tests

**If VectorStore Tests Fail**
- Might indicate issues with:
  - ChromaDB connection
  - Embedding model loading
  - Filter building logic
  - Similarity calculations

### Debug a Failing Test
```bash
# Run with more verbose output
uv run pytest backend/tests/test_file.py::TestClass::test_method -vv

# Run with print statements shown
uv run pytest backend/tests/test_file.py::TestClass::test_method -vv -s

# Run with full traceback
uv run pytest backend/tests/test_file.py::TestClass::test_method -vv --tb=long
```

---

## Test Coverage

### Current Coverage
- **CourseSearchTool**: 100% (15/15 tests)
- **AIGenerator**: 100% (10/10 tests)
- **RAGSystem**: 100% (15/15 tests)
- **VectorStore**: 100% (27/27 tests)
- **Total**: 68/68 tests passing

### Generate Coverage Report
```bash
uv run pytest backend/tests/ --cov=backend --cov-report=term-missing
uv run pytest backend/tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Continuous Integration

### Recommended CI Setup
```yaml
# GitHub Actions example
- name: Run tests
  run: |
    uv sync
    uv run pytest backend/tests/ -v --tb=short

- name: Check coverage
  run: uv run pytest backend/tests/ --cov=backend --cov-fail-under=80
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
uv run pytest backend/tests/ -v || exit 1
```

---

## Key Testing Concepts

### Mocking in Tests
Tests use mocking to avoid actual API calls:
```python
@patch('ai_generator.anthropic.Anthropic')
def test_api_call(self, mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    # Now mock_client.messages.create() is under our control
```

### Fixtures
Fixtures are reusable test components:
```python
def test_with_fixtures(self, test_vector_store, sample_course):
    # test_vector_store and sample_course are automatically set up
```

### Parametrized Tests
For testing multiple scenarios:
```python
@pytest.mark.parametrize("course_name,expected", [
    ("Python", "Introduction to Python"),
    ("Advanced", "Advanced Topics"),
])
def test_course_matching(self, course_name, expected):
    # Test runs twice with different parameters
```

---

## Troubleshooting

### Tests Won't Run
```bash
# Make sure dependencies are installed
uv sync

# Make sure pytest is available
uv run pytest --version

# Check Python version
uv run python --version
```

### ChromaDB Errors
```bash
# ChromaDB persists data - clear it if corrupted
rm -rf backend/chroma_db

# Re-run tests (will recreate fresh DB)
uv run pytest backend/tests/ -v
```

### API Key Not Found
```bash
# Make sure .env file exists with API key
echo "ANTHROPIC_API_KEY=your-key-here" > backend/.env

# Or set environment variable
export ANTHROPIC_API_KEY=your-key-here
uv run pytest backend/tests/ -v
```

### Import Errors
```bash
# Make sure you're running from project root
cd /Users/sz/Desktop/starting-ragchatbot-codebase

# Run pytest
uv run pytest backend/tests/ -v
```

---

## Adding New Tests

### Template for New Test
```python
# backend/tests/test_new_feature.py
import pytest
from new_module import NewClass

class TestNewFeature:
    def test_basic_functionality(self, test_config):
        """Test description"""
        instance = NewClass(test_config)
        result = instance.do_something()
        assert result == expected

    def test_error_handling(self, test_config):
        """Test error cases"""
        instance = NewClass(test_config)
        with pytest.raises(ValueError):
            instance.do_something_bad()
```

### Run New Tests
```bash
uv run pytest backend/tests/test_new_feature.py -v
```

---

## Summary

The test suite provides:
✅ **Comprehensive coverage** of all RAG system components
✅ **Quick feedback** during development (run in seconds)
✅ **Clear validation** that the course similarity fix works
✅ **Regression prevention** from future changes
✅ **Documentation** via test names and fixtures

Use the tests to:
- Verify your changes don't break existing functionality
- Validate new features work as expected
- Document expected behavior
- Debug issues faster
