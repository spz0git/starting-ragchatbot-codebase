"""Integration tests for the RAG system"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rag_system import RAGSystem


class TestRAGSystemInitialization:
    """Test RAGSystem initialization"""

    def test_initialization(self, test_config):
        """Test RAGSystem can be initialized"""
        rag = RAGSystem(test_config)

        assert rag.config == test_config
        assert rag.document_processor is not None
        assert rag.vector_store is not None
        assert rag.ai_generator is not None
        assert rag.session_manager is not None
        assert rag.tool_manager is not None
        assert rag.search_tool is not None

    def test_tool_registration(self, test_config):
        """Test that search tool is registered"""
        rag = RAGSystem(test_config)

        tool_defs = rag.tool_manager.get_tool_definitions()
        assert len(tool_defs) > 0
        assert tool_defs[0]["name"] == "search_course_content"


class TestRAGSystemDocumentProcessing:
    """Test document processing"""

    def test_add_single_document(self, test_config, temp_document_file):
        """Test adding a single course document"""
        rag = RAGSystem(test_config)
        course, chunks = rag.add_course_document(temp_document_file)

        assert course is not None
        assert course.title == "Introduction to Python"
        assert chunks > 0
        assert len(course.lessons) > 0

    def test_add_nonexistent_document(self, test_config):
        """Test adding a nonexistent document"""
        rag = RAGSystem(test_config)
        course, chunks = rag.add_course_document("/nonexistent/path.txt")

        assert course is None
        assert chunks == 0

    def test_add_course_folder(self, test_config, temp_document_file):
        """Test adding courses from a folder"""
        import os
        import tempfile

        # Create a temporary folder with a document
        temp_dir = tempfile.mkdtemp()
        import shutil
        shutil.copy(temp_document_file, os.path.join(temp_dir, "course.txt"))

        rag = RAGSystem(test_config)
        courses, chunks = rag.add_course_folder(temp_dir, clear_existing=True)

        assert courses > 0
        assert chunks > 0

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_get_course_analytics(self, test_config, temp_document_file):
        """Test getting course analytics"""
        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        analytics = rag.get_course_analytics()

        assert "total_courses" in analytics
        assert "course_titles" in analytics
        assert analytics["total_courses"] > 0


class TestRAGSystemQueryProcessing:
    """Test query processing"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_without_session(self, mock_anthropic_class, test_config, temp_document_file):
        """Test query processing without session"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock the API response
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="This is a response about the course")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        response, sources = rag.query("What is Python?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(sources, list)

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_with_session(self, mock_anthropic_class, test_config, temp_document_file):
        """Test query processing with session"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with context")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        # Create a session
        session_id = rag.session_manager.create_session()

        # Make a query
        response, sources = rag.query("What is Python?", session_id)

        assert isinstance(response, str)
        assert isinstance(sources, list)

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_tool_execution_flow(self, mock_anthropic_class, test_config, temp_document_file):
        """Test that tool execution flows correctly"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock tool use response
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.id = "tool_123"
        tool_use_block.input = {"query": "Python"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [tool_use_block]

        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Python is a programming language")]

        mock_client.messages.create.side_effect = [initial_response, final_response]

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        response, sources = rag.query("What is Python?")

        assert isinstance(response, str)
        # Tool should have been called
        assert mock_client.messages.create.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_without_tool_call(self, mock_anthropic_class, test_config):
        """Test query that doesn't use tools"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="General knowledge response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)

        response, sources = rag.query("What is artificial intelligence?")

        assert isinstance(response, str)
        # Only one API call should be made (no tool execution)
        assert mock_client.messages.create.call_count == 1

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_preserves_session_history(self, mock_anthropic_class, test_config, temp_document_file):
        """Test that session history is preserved"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        session_id = rag.session_manager.create_session()

        # Make multiple queries
        rag.query("What is Python?", session_id)
        rag.query("Tell me more", session_id)

        # Check history is stored
        history = rag.session_manager.get_conversation_history(session_id)
        assert history is not None
        # History should contain both exchanges
        assert "Python" in history or len(history) > 0


class TestRAGSystemSourceTracking:
    """Test source tracking"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_sources_returned_from_query(self, mock_anthropic_class, test_config, temp_document_file):
        """Test that sources are returned from queries"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        response, sources = rag.query("Python content")

        assert isinstance(sources, list)

    @patch('ai_generator.anthropic.Anthropic')
    def test_sources_reset_after_query(self, mock_anthropic_class, test_config, temp_document_file):
        """Test that sources are reset after query"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        # First query
        rag.query("Query 1")
        sources_after_first = rag.tool_manager.get_last_sources()

        # Second query
        rag.query("Query 2")
        sources_after_second = rag.tool_manager.get_last_sources()

        # Sources should be reset
        assert isinstance(sources_after_first, list)
        assert isinstance(sources_after_second, list)


class TestRAGSystemErrorHandling:
    """Test error handling"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_with_invalid_session(self, mock_anthropic_class, test_config, temp_document_file):
        """Test query with invalid session ID"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        # This should still work (creates new history or uses None)
        response, sources = rag.query("Test", "invalid_session_id")

        assert isinstance(response, str)

    @patch('ai_generator.anthropic.Anthropic')
    def test_empty_query(self, mock_anthropic_class, test_config, temp_document_file):
        """Test empty query"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        response, sources = rag.query("")

        assert isinstance(response, str)
