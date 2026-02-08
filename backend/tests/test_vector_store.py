"""Tests for VectorStore"""
import pytest
from vector_store import VectorStore, SearchResults


class TestSearchResultsDataclass:
    """Test SearchResults utility"""

    def test_search_results_creation(self):
        """Test creating SearchResults"""
        results = SearchResults(
            documents=["doc1", "doc2"],
            metadata=[{"key": "value"}],
            distances=[0.1, 0.2]
        )

        assert results.documents == ["doc1", "doc2"]
        assert len(results.metadata) == 1
        assert not results.is_empty()
        assert results.error is None

    def test_search_results_empty(self):
        """Test empty SearchResults"""
        results = SearchResults.empty("Test error")

        assert results.is_empty()
        assert results.error == "Test error"
        assert results.documents == []

    def test_search_results_from_chroma(self):
        """Test creating from ChromaDB response"""
        chroma_response = {
            'documents': [["doc1", "doc2"]],
            'metadatas': [[{"key": "val1"}, {"key": "val2"}]],
            'distances': [[0.1, 0.2]]
        }

        results = SearchResults.from_chroma(chroma_response)

        assert results.documents == ["doc1", "doc2"]
        assert len(results.metadata) == 2
        assert results.distances == [0.1, 0.2]


class TestVectorStoreInitialization:
    """Test VectorStore initialization"""

    def test_initialization(self, test_vector_store):
        """Test VectorStore can be initialized"""
        assert test_vector_store.client is not None
        assert test_vector_store.embedding_function is not None
        assert test_vector_store.course_catalog is not None
        assert test_vector_store.course_content is not None
        assert test_vector_store.max_results == 3

    def test_max_results_config(self, test_config):
        """Test max_results configuration"""
        store = VectorStore(test_config.CHROMA_PATH, test_config.EMBEDDING_MODEL, 10)
        assert store.max_results == 10


class TestVectorStoreAddContent:
    """Test adding content to vector store"""

    def test_add_course_metadata(self, test_vector_store, sample_course):
        """Test adding course metadata"""
        test_vector_store.add_course_metadata(sample_course)

        # Verify course is in catalog
        titles = test_vector_store.get_existing_course_titles()
        assert sample_course.title in titles

    def test_add_course_content(self, test_vector_store, sample_chunks):
        """Test adding course content"""
        test_vector_store.add_course_content(sample_chunks)

        # Should not raise an error
        assert True

    def test_add_course_content_empty_list(self, test_vector_store):
        """Test adding empty course content list"""
        test_vector_store.add_course_content([])

        # Should not raise an error
        assert True

    def test_course_count_increases(self, test_vector_store, sample_course):
        """Test that course count increases"""
        count_before = test_vector_store.get_course_count()
        test_vector_store.add_course_metadata(sample_course)
        count_after = test_vector_store.get_course_count()

        assert count_after == count_before + 1


class TestVectorStoreSearch:
    """Test searching the vector store"""

    def test_search_empty_store(self, test_vector_store):
        """Test searching empty store"""
        results = test_vector_store.search(query="Python")

        assert results.is_empty()

    def test_search_with_results(self, test_vector_store, sample_course, sample_chunks):
        """Test search with actual results"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(query="Python programming")

        assert not results.is_empty()
        assert len(results.documents) > 0
        assert len(results.metadata) > 0

    def test_search_limit(self, test_vector_store, sample_course, sample_chunks):
        """Test search with limit parameter"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(query="Python", limit=1)

        assert len(results.documents) <= 1

    def test_search_with_course_name_filter(self, test_vector_store, sample_course, sample_chunks):
        """Test search with course name filter"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(query="variables", course_name="Introduction to Python")

        # Should return results only from this course
        assert not results.is_empty()
        for metadata in results.metadata:
            assert metadata["course_title"] == "Introduction to Python"

    def test_search_with_lesson_filter(self, test_vector_store, sample_course, sample_chunks):
        """Test search with lesson filter"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(query="variables", lesson_number=1)

        # Results should be from lesson 1
        assert not results.is_empty()
        for metadata in results.metadata:
            assert metadata["lesson_number"] == 1

    def test_search_with_both_filters(self, test_vector_store, sample_course, sample_chunks):
        """Test search with both course and lesson filters"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(
            query="variables",
            course_name="Introduction to Python",
            lesson_number=1
        )

        if not results.is_empty():
            for metadata in results.metadata:
                assert metadata["course_title"] == "Introduction to Python"
                assert metadata["lesson_number"] == 1

    def test_search_nonexistent_course(self, test_vector_store, sample_course, sample_chunks):
        """Test search with nonexistent course name"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        results = test_vector_store.search(query="test", course_name="Nonexistent Course")

        assert results.is_empty()
        assert "No course found" in results.error


class TestVectorStoreResolveCourseNames:
    """Test course name resolution"""

    def test_resolve_exact_course_name(self, test_vector_store, sample_course):
        """Test resolving exact course name"""
        test_vector_store.add_course_metadata(sample_course)

        resolved = test_vector_store._resolve_course_name("Introduction to Python")

        assert resolved == "Introduction to Python"

    def test_resolve_partial_course_name(self, test_vector_store, sample_course):
        """Test resolving partial course name"""
        test_vector_store.add_course_metadata(sample_course)

        resolved = test_vector_store._resolve_course_name("Python")

        assert resolved is not None  # Should find something related to Python

    def test_resolve_nonexistent_course(self, test_vector_store):
        """Test resolving nonexistent course"""
        resolved = test_vector_store._resolve_course_name("XYZ123NotARealCourse")

        assert resolved is None


class TestVectorStoreFiltering:
    """Test filter building"""

    def test_build_filter_none(self, test_vector_store):
        """Test building filter with no parameters"""
        filter_dict = test_vector_store._build_filter(None, None)

        assert filter_dict is None

    def test_build_filter_course_only(self, test_vector_store):
        """Test building filter with course only"""
        filter_dict = test_vector_store._build_filter("Test Course", None)

        assert filter_dict is not None
        assert filter_dict["course_title"] == "Test Course"

    def test_build_filter_lesson_only(self, test_vector_store):
        """Test building filter with lesson only"""
        filter_dict = test_vector_store._build_filter(None, 1)

        assert filter_dict is not None
        assert filter_dict["lesson_number"] == 1

    def test_build_filter_both(self, test_vector_store):
        """Test building filter with both parameters"""
        filter_dict = test_vector_store._build_filter("Test Course", 2)

        assert filter_dict is not None
        assert "$and" in filter_dict


class TestVectorStoreClearData:
    """Test data clearing"""

    def test_clear_all_data(self, test_vector_store, sample_course, sample_chunks):
        """Test clearing all data"""
        test_vector_store.add_course_metadata(sample_course)
        test_vector_store.add_course_content(sample_chunks)

        count_before = test_vector_store.get_course_count()
        assert count_before > 0

        test_vector_store.clear_all_data()

        count_after = test_vector_store.get_course_count()
        assert count_after == 0


class TestVectorStoreMetadata:
    """Test metadata retrieval"""

    def test_get_existing_course_titles(self, test_vector_store, sample_course):
        """Test getting existing course titles"""
        test_vector_store.add_course_metadata(sample_course)

        titles = test_vector_store.get_existing_course_titles()

        assert sample_course.title in titles

    def test_get_course_link(self, test_vector_store, sample_course):
        """Test getting course link"""
        test_vector_store.add_course_metadata(sample_course)

        link = test_vector_store.get_course_link(sample_course.title)

        assert link == sample_course.course_link

    def test_get_lesson_link(self, test_vector_store, sample_course):
        """Test getting lesson link"""
        test_vector_store.add_course_metadata(sample_course)

        lesson_link = test_vector_store.get_lesson_link(sample_course.title, 0)

        assert lesson_link is not None

    def test_get_all_courses_metadata(self, test_vector_store, sample_course):
        """Test getting all course metadata"""
        test_vector_store.add_course_metadata(sample_course)

        metadata = test_vector_store.get_all_courses_metadata()

        assert len(metadata) > 0
        assert any(m["title"] == sample_course.title for m in metadata)
