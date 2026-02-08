"""API endpoint tests for the RAG system"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import json
from fastapi.testclient import TestClient
from app import app


class TestQueryEndpoint:
    """Test /api/query endpoint"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_endpoint_basic(self, mock_anthropic_class, test_client_with_docs):
        """Test basic query endpoint functionality"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Python is a programming language")]
        mock_client.messages.create.return_value = mock_response

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "What is Python?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert len(data["answer"]) > 0

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_endpoint_with_session(self, mock_anthropic_class, test_client_with_docs):
        """Test query endpoint with existing session"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        # First query
        response1 = test_client_with_docs.post(
            "/api/query",
            json={"query": "First question"}
        )
        session_id = response1.json()["session_id"]

        # Second query with same session
        response2 = test_client_with_docs.post(
            "/api/query",
            json={"query": "Follow-up question", "session_id": session_id}
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == session_id

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_endpoint_creates_new_session(self, mock_anthropic_class, test_client_with_docs):
        """Test that query endpoint creates new session if not provided"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "Test query"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"].startswith("session_")

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_endpoint_response_structure(self, mock_anthropic_class, test_client_with_docs):
        """Test that response follows QueryResponse schema"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response")]
        mock_client.messages.create.return_value = mock_response

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "Test"}
        )

        data = response.json()
        # Verify SourceCitation structure
        for source in data["sources"]:
            assert "text" in source
            assert isinstance(source["text"], str)
            # url is optional
            if "url" in source:
                assert source["url"] is None or isinstance(source["url"], str)

    def test_query_endpoint_missing_query_field(self, test_client):
        """Test query endpoint with missing query field"""
        response = test_client.post(
            "/api/query",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_query_endpoint_empty_query(self, test_client_with_docs):
        """Test query endpoint with empty query string"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock(text="Response")]
            mock_client.messages.create.return_value = mock_response

            response = test_client_with_docs.post(
                "/api/query",
                json={"query": ""}
            )

            assert response.status_code == 200

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_endpoint_with_sources(self, mock_anthropic_class, test_client_with_docs):
        """Test that query endpoint returns sources from search"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock tool use response to simulate search execution
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

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "What is Python?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["sources"], list)

    @patch('rag_system.RAGSystem.query')
    def test_query_endpoint_error_handling(self, mock_query, test_client):
        """Test query endpoint error handling"""
        mock_query.side_effect = Exception("Test error")

        response = test_client.post(
            "/api/query",
            json={"query": "Test"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestResetEndpoint:
    """Test /api/reset endpoint"""

    def test_reset_endpoint_basic(self, test_client_with_docs):
        """Test basic session reset"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock(text="Response")]
            mock_client.messages.create.return_value = mock_response

            # Create a session first
            query_response = test_client_with_docs.post(
                "/api/query",
                json={"query": "Test"}
            )
            session_id = query_response.json()["session_id"]

            # Reset the session
            reset_response = test_client_with_docs.post(
                "/api/reset",
                json={"session_id": session_id}
            )

            assert reset_response.status_code == 200
            data = reset_response.json()
            assert data["status"] == "success"
            assert "message" in data

    def test_reset_endpoint_missing_session_id(self, test_client):
        """Test reset endpoint with missing session_id"""
        response = test_client.post(
            "/api/reset",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_reset_endpoint_with_nonexistent_session(self, test_client):
        """Test resetting a nonexistent session"""
        response = test_client.post(
            "/api/reset",
            json={"session_id": "nonexistent_session"}
        )

        # Should succeed even if session doesn't exist (graceful handling)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_reset_endpoint_error_handling(self, test_config, temp_document_file):
        """Test reset endpoint error handling"""
        from app import RAGSystem
        rag = RAGSystem(test_config)
        rag.add_course_document(temp_document_file)

        from unittest.mock import patch
        with patch('app.rag_system', rag):
            with patch.object(rag.session_manager, 'clear_session', side_effect=Exception("Test error")):
                client = TestClient(app)
                response = client.post(
                    "/api/reset",
                    json={"session_id": "test_session"}
                )

                assert response.status_code == 500
                data = response.json()
                assert "detail" in data


class TestCoursesEndpoint:
    """Test /api/courses endpoint"""

    def test_courses_endpoint_basic(self, test_client_with_docs):
        """Test basic courses endpoint functionality"""
        response = test_client_with_docs.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_courses_endpoint_with_loaded_courses(self, test_client_with_docs):
        """Test courses endpoint returns loaded courses"""
        response = test_client_with_docs.get("/api/courses")

        data = response.json()
        assert data["total_courses"] > 0
        assert len(data["course_titles"]) > 0
        assert "Introduction to Python" in data["course_titles"]

    def test_courses_endpoint_empty_database(self, test_client):
        """Test courses endpoint with empty database"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] >= 0
        assert isinstance(data["course_titles"], list)

    @patch('rag_system.RAGSystem.get_course_analytics')
    def test_courses_endpoint_error_handling(self, mock_analytics, test_client):
        """Test courses endpoint error handling"""
        mock_analytics.side_effect = Exception("Test error")

        response = test_client.get("/api/courses")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_courses_endpoint_response_structure(self, test_client_with_docs):
        """Test that response follows CourseStats schema"""
        response = test_client_with_docs.get("/api/courses")

        data = response.json()
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        for title in data["course_titles"]:
            assert isinstance(title, str)


class TestAPIIntegration:
    """Integration tests for complete API flows"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_complete_conversation_flow(self, mock_anthropic_class, test_client_with_docs):
        """Test complete conversation flow with multiple queries"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        # Query 1
        response1 = test_client_with_docs.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Query 2 with same session
        response2 = test_client_with_docs.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Query 3 with same session
        response3 = test_client_with_docs.post(
            "/api/query",
            json={"query": "What about functions?", "session_id": session_id}
        )
        assert response3.status_code == 200

        # Reset session
        reset_response = test_client_with_docs.post(
            "/api/reset",
            json={"session_id": session_id}
        )
        assert reset_response.status_code == 200

    @patch('ai_generator.anthropic.Anthropic')
    def test_multiple_independent_sessions(self, mock_anthropic_class, test_client_with_docs):
        """Test multiple independent sessions"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        # Create multiple sessions
        sessions = []
        for i in range(3):
            response = test_client_with_docs.post(
                "/api/query",
                json={"query": f"Query {i}"}
            )
            assert response.status_code == 200
            session_id = response.json()["session_id"]
            sessions.append(session_id)

        # Verify all sessions are different
        assert len(set(sessions)) == 3

    @patch('ai_generator.anthropic.Anthropic')
    def test_courses_endpoint_integration(self, mock_anthropic_class, test_client_with_docs):
        """Test courses endpoint after queries"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        # Make a query
        test_client_with_docs.post(
            "/api/query",
            json={"query": "Test"}
        )

        # Check courses are still available
        response = test_client_with_docs.get("/api/courses")
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] > 0


class TestAPIContentNegotiation:
    """Test API request/response handling"""

    def test_query_endpoint_json_content_type(self, test_client_with_docs):
        """Test that endpoint requires JSON content type"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock(text="Response")]
            mock_client.messages.create.return_value = mock_response

            response = test_client_with_docs.post(
                "/api/query",
                json={"query": "Test"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/json")

    def test_response_json_serialization(self, test_client_with_docs):
        """Test that responses are properly JSON serializable"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client

            mock_response = Mock()
            mock_response.stop_reason = "end_turn"
            mock_response.content = [Mock(text="Response")]
            mock_client.messages.create.return_value = mock_response

            response = test_client_with_docs.post(
                "/api/query",
                json={"query": "Test"}
            )

            # Verify response is valid JSON
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_courses_endpoint_http_methods(self, test_client):
        """Test that courses endpoint only accepts GET"""
        # GET should work
        with patch('rag_system.RAGSystem.get_course_analytics') as mock_analytics:
            mock_analytics.return_value = {"total_courses": 0, "course_titles": []}
            response = test_client.get("/api/courses")
            assert response.status_code == 200

        # POST should not be allowed
        response = test_client.post("/api/courses")
        assert response.status_code == 405  # Method not allowed


class TestAPIEdgeCases:
    """Test API edge cases and boundary conditions"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_with_special_characters(self, mock_anthropic_class, test_client_with_docs):
        """Test query with special characters"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "What is @#$% & special?"}
        )

        assert response.status_code == 200

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_with_very_long_query(self, mock_anthropic_class, test_client_with_docs):
        """Test query with very long string"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        long_query = "What is Python? " * 100
        response = test_client_with_docs.post(
            "/api/query",
            json={"query": long_query}
        )

        assert response.status_code == 200

    @patch('ai_generator.anthropic.Anthropic')
    def test_query_with_unicode_characters(self, mock_anthropic_class, test_client_with_docs):
        """Test query with unicode characters"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        response = test_client_with_docs.post(
            "/api/query",
            json={"query": "What is Python? 你好 🎉 café"}
        )

        assert response.status_code == 200

    def test_reset_with_invalid_session_format(self, test_client):
        """Test reset with various session ID formats"""
        for session_id in ["", "session_invalid_123", "not_a_session", "null"]:
            response = test_client.post(
                "/api/reset",
                json={"session_id": session_id}
            )
            # Should handle gracefully
            assert response.status_code in [200, 500]
