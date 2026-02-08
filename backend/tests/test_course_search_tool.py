"""Tests for CourseSearchTool"""
import pytest
from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchToolDefinition:
    """Test tool definition"""

    def test_tool_has_valid_definition(self, test_vector_store):
        """Test that tool has a valid definition"""
        tool = CourseSearchTool(test_vector_store)
        definition = tool.get_tool_definition()

        assert "name" in definition
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition

    def test_tool_definition_has_required_parameters(self, test_vector_store):
        """Test that tool definition includes required parameters"""
        tool = CourseSearchTool(test_vector_store)
        definition = tool.get_tool_definition()

        schema = definition["input_schema"]
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert schema["required"] == ["query"]

    def test_tool_optional_parameters(self, test_vector_store):
        """Test that optional parameters are defined"""
        tool = CourseSearchTool(test_vector_store)
        definition = tool.get_tool_definition()

        schema = definition["input_schema"]
        properties = schema["properties"]
        assert "course_name" in properties
        assert "lesson_number" in properties


class TestCourseSearchToolExecution:
    """Test tool execution"""

    def test_execute_empty_vector_store(self, test_vector_store):
        """Test execution on empty vector store"""
        tool = CourseSearchTool(test_vector_store)
        result = tool.execute(query="Python programming")

        assert isinstance(result, str)
        assert "No relevant content found" in result

    def test_execute_with_results(self, test_vector_store, sample_course, sample_chunks):
        """Test execution with actual search results"""
        # Add data to vector store
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        tool = CourseSearchTool(test_vector_store)
        result = tool.execute(query="Python programming language")

        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message
        assert "No relevant content found" not in result or "Introduction to Python" in result

    def test_execute_with_course_filter(self, test_vector_store, sample_course, sample_chunks):
        """Test execution with course name filter"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        tool = CourseSearchTool(test_vector_store)
        result = tool.execute(query="variables", course_name="Introduction to Python")

        assert isinstance(result, str)

    def test_execute_with_lesson_filter(self, test_vector_store, sample_course, sample_chunks):
        """Test execution with lesson number filter"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        tool = CourseSearchTool(test_vector_store)
        result = tool.execute(query="variables", lesson_number=1)

        assert isinstance(result, str)

    def test_execute_nonexistent_course(self, test_vector_store, sample_course, sample_chunks):
        """Test execution with nonexistent course"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        tool = CourseSearchTool(test_vector_store)
        result = tool.execute(query="test", course_name="Nonexistent Course")

        assert isinstance(result, str)
        assert "No course found" in result

    def test_sources_tracking(self, test_vector_store, sample_course, sample_chunks):
        """Test that sources are properly tracked"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        tool = CourseSearchTool(test_vector_store)
        # Execute search
        result = tool.execute(query="Python")

        # Check that sources are tracked
        assert hasattr(tool, 'last_sources')
        assert isinstance(tool.last_sources, list)

        # If we got results, sources should be populated
        if "No relevant content found" not in result:
            assert len(tool.last_sources) > 0
            # Each source should be a dict with text and url
            for source in tool.last_sources:
                assert isinstance(source, dict)
                assert 'text' in source
                assert 'url' in source


class TestToolManager:
    """Test tool manager"""

    def test_tool_manager_registration(self, test_vector_store):
        """Test tool registration"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)

        manager.register_tool(tool)

        assert "search_course_content" in manager.tools
        assert manager.tools["search_course_content"] == tool

    def test_tool_manager_get_definitions(self, test_vector_store):
        """Test getting tool definitions"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_tool_manager_execute(self, test_vector_store):
        """Test tool execution through manager"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)
        manager.register_tool(tool)

        result = manager.execute_tool("search_course_content", query="test")

        assert isinstance(result, str)

    def test_tool_manager_nonexistent_tool(self, test_vector_store):
        """Test executing nonexistent tool"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)
        manager.register_tool(tool)

        result = manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result.lower()

    def test_tool_manager_get_last_sources(self, test_vector_store, sample_course, sample_chunks):
        """Test getting last sources"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)
        manager.register_tool(tool)

        # Add data and execute
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)
        manager.execute_tool("search_course_content", query="Python")

        sources = manager.get_last_sources()
        assert isinstance(sources, list)

    def test_tool_manager_reset_sources(self, test_vector_store, sample_course, sample_chunks):
        """Test resetting sources"""
        manager = ToolManager()
        tool = CourseSearchTool(test_vector_store)
        manager.register_tool(tool)

        # Add data and execute
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)
        manager.execute_tool("search_course_content", query="Python")

        # Reset sources
        manager.reset_sources()

        sources = manager.get_last_sources()
        assert len(sources) == 0
