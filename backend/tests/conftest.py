"""Shared test fixtures and utilities"""
import pytest
import sys
import os
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import Config
from vector_store import VectorStore
from document_processor import DocumentProcessor
from models import Course, Lesson, CourseChunk


@pytest.fixture
def test_config():
    """Create a test configuration with temporary ChromaDB path"""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    config = Config()
    config.CHROMA_PATH = temp_dir
    config.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "test-key")
    config.MAX_RESULTS = 3
    return config


@pytest.fixture
def test_vector_store(test_config):
    """Create a test vector store"""
    return VectorStore(test_config.CHROMA_PATH, test_config.EMBEDDING_MODEL, test_config.MAX_RESULTS)


@pytest.fixture
def test_document_processor(test_config):
    """Create a test document processor"""
    return DocumentProcessor(test_config.CHUNK_SIZE, test_config.CHUNK_OVERLAP)


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    return Course(
        title="Introduction to Python",
        course_link="https://example.com/python",
        instructor="John Doe",
        lessons=[
            Lesson(lesson_number=0, title="Getting Started", lesson_link="https://example.com/python/lesson0"),
            Lesson(lesson_number=1, title="Variables and Types", lesson_link="https://example.com/python/lesson1"),
        ]
    )


@pytest.fixture
def sample_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="Course Introduction to Python Lesson 0 content: Python is a high-level programming language.",
            course_title="Introduction to Python",
            lesson_number=0,
            chunk_index=0
        ),
        CourseChunk(
            content="Variables in Python store values. You can create a variable with an equals sign.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=1
        ),
        CourseChunk(
            content="Course Introduction to Python Lesson 1 content: Strings are sequences of characters.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=2
        ),
        CourseChunk(
            content="Numbers can be integers or floats. Integers are whole numbers without decimals.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=3
        ),
    ]


@pytest.fixture
def sample_document_text():
    """Create sample document text"""
    return """Course Title: Introduction to Python
Course Link: https://example.com/python
Course Instructor: John Doe

Lesson 0: Getting Started
Lesson Link: https://example.com/python/lesson0
Python is a high-level programming language. It is easy to learn.

Lesson 1: Variables and Types
Lesson Link: https://example.com/python/lesson1
Variables in Python store values. Strings are sequences of characters. Numbers can be integers or floats.
"""


@pytest.fixture
def temp_document_file(sample_document_text):
    """Create a temporary document file"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_document_text)
        f.flush()
        yield f.name
    # Cleanup
    try:
        os.unlink(f.name)
    except:
        pass
