"""Tests for AIGenerator"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from ai_generator import AIGenerator
import anthropic


class TestAIGeneratorInitialization:
    """Test AIGenerator initialization"""

    def test_initialization(self, test_config):
        """Test AIGenerator can be initialized"""
        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        assert generator.model == test_config.ANTHROPIC_MODEL
        assert generator.client is not None
        assert hasattr(generator, 'base_params')

    def test_base_params_config(self, test_config):
        """Test base parameters are properly configured"""
        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        assert generator.base_params["model"] == test_config.ANTHROPIC_MODEL
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800

    def test_system_prompt_exists(self, test_config):
        """Test that system prompt is defined"""
        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        assert hasattr(generator, 'SYSTEM_PROMPT')
        assert "search tool" in generator.SYSTEM_PROMPT.lower()


class TestAIGeneratorResponseGeneration:
    """Test response generation (mocked API calls)"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_simple(self, mock_anthropic_class, test_config):
        """Test simple response generation without tools"""
        # Mock the client and its messages.create method
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="This is a response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)
        response = generator.generate_response(query="What is Python?")

        assert isinstance(response, str)
        assert response == "This is a response"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_history(self, mock_anthropic_class, test_config):
        """Test response generation with conversation history"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with context")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)
        history = "User: What is Python?\nAssistant: Python is a language."
        response = generator.generate_response(query="Tell me more", conversation_history=history)

        assert isinstance(response, str)
        # Verify the history was included in the API call
        call_args = mock_client.messages.create.call_args
        assert history in call_args.kwargs['system']

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tools(self, mock_anthropic_class, test_config):
        """Test response generation with tools"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        tools = [
            {
                "name": "search_tool",
                "description": "Search for information",
                "input_schema": {"type": "object", "properties": {}}
            }
        ]

        response = generator.generate_response(query="Find info", tools=tools)

        assert isinstance(response, str)
        # Verify tools were passed
        call_args = mock_client.messages.create.call_args
        assert 'tools' in call_args.kwargs


class TestAIGeneratorToolExecution:
    """Test tool execution handling"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_flow(self, mock_anthropic_class, test_config):
        """Test that tool execution is handled properly"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock initial response with tool use
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.id = "tool_123"
        tool_use_block.input = {"query": "Python"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [tool_use_block]

        # Mock final response after tool execution
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final response")]

        mock_client.messages.create.side_effect = [initial_response, final_response]

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        # Create mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search results"

        tools = [{"name": "search_course_content"}]

        response = generator.generate_response(
            query="Find Python info",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        assert mock_tool_manager.execute_tool.called
        # Verify final response is returned
        assert response == "Final response"

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_execution_constructs_messages_correctly(self, mock_anthropic_class, test_config):
        """Test that tool results are properly constructed in messages"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_tool"
        tool_use_block.id = "tool_1"
        tool_use_block.input = {"query": "test"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [tool_use_block]

        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final")]

        mock_client.messages.create.side_effect = [initial_response, final_response]

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool output"

        tools = [{"name": "search_tool"}]

        generator.generate_response(query="Test", tools=tools, tool_manager=mock_tool_manager)

        # Check the second API call (after tool execution)
        second_call = mock_client.messages.create.call_args_list[1]
        messages = second_call.kwargs['messages']

        # Should have: original message, tool use response, tool result
        assert len(messages) >= 3
        # Last message should be tool results
        assert messages[-1]['role'] == 'user'


class TestAIGeneratorEdgeCases:
    """Test edge cases and error handling"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_no_query(self, mock_anthropic_class, test_config):
        """Test response generation with empty query"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)
        response = generator.generate_response(query="")

        assert isinstance(response, str)

    @patch('ai_generator.anthropic.Anthropic')
    def test_multiple_tool_calls(self, mock_anthropic_class, test_config):
        """Test handling multiple tool calls in one response"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        tool_use_1 = Mock()
        tool_use_1.type = "tool_use"
        tool_use_1.name = "tool_1"
        tool_use_1.id = "call_1"
        tool_use_1.input = {"query": "test1"}

        tool_use_2 = Mock()
        tool_use_2.type = "tool_use"
        tool_use_2.name = "tool_2"
        tool_use_2.id = "call_2"
        tool_use_2.input = {"query": "test2"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [tool_use_1, tool_use_2]

        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final")]

        mock_client.messages.create.side_effect = [initial_response, final_response]

        generator = AIGenerator(test_config.ANTHROPIC_API_KEY, test_config.ANTHROPIC_MODEL)

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

        tools = [{"name": "tool_1"}, {"name": "tool_2"}]

        response = generator.generate_response(query="Test", tools=tools, tool_manager=mock_tool_manager)

        # Both tools should have been executed
        assert mock_tool_manager.execute_tool.call_count == 2
        assert response == "Final"
