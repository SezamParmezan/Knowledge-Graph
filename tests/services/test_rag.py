import pytest
from unittest.mock import MagicMock, patch, call
from app.services.rag import RAGService


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client and collection"""
    with patch('app.services.rag.chromadb.PersistentClient') as mock_client:
        mock_instance = MagicMock()
        mock_collection = MagicMock()
        mock_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_instance
        yield mock_client, mock_instance, mock_collection


@pytest.fixture
def rag_service(mock_chromadb):
    """Create RAGService instance with mocked ChromaDB"""
    mock_client, mock_instance, mock_collection = mock_chromadb
    service = RAGService()
    service.collection = mock_collection
    return service


class TestRAGServiceInit:
    def test_init_creates_client(self, mock_chromadb):
        """Test RAGService initializes ChromaDB client"""
        mock_client, mock_instance, mock_collection = mock_chromadb
        
        service = RAGService()
        
        mock_client.assert_called_once()
        mock_instance.get_or_create_collection.assert_called_once_with(name="chunks")

    def test_init_stores_collection(self, rag_service, mock_chromadb):
        """Test that RAGService stores collection reference"""
        assert rag_service.collection is not None


class TestChunkText:
    def test_chunk_text_default_size(self, rag_service):
        """Test text chunking with default chunk size (500)"""
        text = "a" * 1500
        chunks = rag_service.chunk_text(text)
        
        assert len(chunks) == 3
        assert chunks[0] == "a" * 500
        assert chunks[1] == "a" * 500
        assert chunks[2] == "a" * 500

    def test_chunk_text_custom_size(self, rag_service):
        """Test text chunking with custom chunk size"""
        text = "Hello world! " * 100
        chunks = rag_service.chunk_text(text, chunk_size=100)
        
        assert all(len(chunk) <= 100 for chunk in chunks)
        assert "".join(chunks) == text

    def test_chunk_text_exact_division(self, rag_service):
        """Test chunking when text divides evenly"""
        text = "a" * 1000
        chunks = rag_service.chunk_text(text, chunk_size=500)
        
        assert len(chunks) == 2
        assert chunks[0] == "a" * 500
        assert chunks[1] == "a" * 500

    def test_chunk_text_remainder(self, rag_service):
        """Test chunking when text doesn't divide evenly"""
        text = "a" * 550
        chunks = rag_service.chunk_text(text, chunk_size=500)
        
        assert len(chunks) == 2
        assert len(chunks[0]) == 500
        assert len(chunks[1]) == 50

    def test_chunk_text_smaller_than_chunk_size(self, rag_service):
        """Test text smaller than chunk size"""
        text = "Short text"
        chunks = rag_service.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty_string(self, rag_service):
        """Test chunking empty string"""
        chunks = rag_service.chunk_text("")
        
        assert len(chunks) == 0
        assert chunks == []


class TestIndex:
    def test_index_adds_chunks_to_collection(self, rag_service):
        """Test that index() adds text chunks to ChromaDB collection"""
        session_id = "session_123"
        text = "a" * 1500
        
        rag_service.index(session_id, text)
        
        # add() is called once per chunk (3 times for 1500 chars with 500 chunk size)
        assert rag_service.collection.add.call_count == 3
        
        # Verify each call had correct chunk IDs
        calls = rag_service.collection.add.call_args_list
        for i, call in enumerate(calls):
            assert call[1]["ids"][0] == f"session_123_chunk_{i}"

    def test_index_sets_correct_metadata(self, rag_service):
        """Test that index() sets correct metadata for chunks"""
        session_id = "test_session"
        text = "Sample text" * 100
        
        rag_service.index(session_id, text)
        
        call_args = rag_service.collection.add.call_args
        metadatas = call_args[1]["metadatas"]
        
        assert all(metadata["session_id"] == session_id for metadata in metadatas)

    def test_index_multiple_chunks(self, rag_service):
        """Test that index() creates correct number of add() calls for multiple chunks"""
        session_id = "session_456"
        text = "a" * 300
        
        rag_service.index(session_id, text)
        
        # 300 chars / 500 chunk size = 1 chunk
        assert rag_service.collection.add.call_count == 1

    def test_index_single_chunk(self, rag_service):
        """Test indexing when text fits in a single chunk"""
        session_id = "session_789"
        text = "Short text"
        
        rag_service.index(session_id, text)
        
        # Should be called once for the single chunk
        assert rag_service.collection.add.call_count == 1
        call_args = rag_service.collection.add.call_args
        assert call_args[1]["ids"][0] == "session_789_chunk_0"


class TestQuery:
    def test_query_returns_relevant_chunks(self, rag_service):
        """Test that query() returns relevant chunks from ChromaDB"""
        session_id = "session_123"
        question = "What is quantum computing?"
        
        mock_results = {
            "documents": [[
                "Chunk 1 about quantum computing",
                "Chunk 2 about quantum computing",
                "Chunk 3 about quantum computing"
            ]]
        }
        rag_service.collection.query.return_value = mock_results
        
        result = rag_service.query(session_id, question)
        
        assert len(result) == 3
        assert result[0] == "Chunk 1 about quantum computing"

    def test_query_calls_chromadb_with_correct_params(self, rag_service):
        """Test that query() calls ChromaDB with correct parameters"""
        session_id = "session_456"
        question = "Test question"
        
        rag_service.collection.query.return_value = {"documents": [[]]}
        
        rag_service.query(session_id, question, top_k=5)
        
        rag_service.collection.query.assert_called_once_with(
            query_texts=[question],
            n_results=5,
            where={"session_id": session_id}
        )

    def test_query_default_top_k(self, rag_service):
        """Test that query() uses default top_k=3"""
        session_id = "session_789"
        question = "Test"
        
        rag_service.collection.query.return_value = {"documents": [[]]}
        
        rag_service.query(session_id, question)
        
        call_args = rag_service.collection.query.call_args
        assert call_args[1]["n_results"] == 3

    def test_query_returns_empty_list_when_no_results(self, rag_service):
        """Test that query() returns empty list when ChromaDB has no results"""
        session_id = "nonexistent"
        question = "Test"
        
        rag_service.collection.query.return_value = {"documents": []}
        
        result = rag_service.query(session_id, question)
        
        assert result == []

    def test_query_returns_empty_list_when_documents_is_none(self, rag_service):
        """Test that query() handles None documents"""
        session_id = "session_test"
        question = "Test"
        
        rag_service.collection.query.return_value = {"documents": None}
        
        result = rag_service.query(session_id, question)
        
        assert result == []


class TestClear:
    def test_clear_deletes_session_chunks(self, rag_service):
        """Test that clear() deletes all chunks for a session"""
        session_id = "session_to_clear"
        
        mock_results = {
            "ids": [
                "session_to_clear_chunk_0",
                "session_to_clear_chunk_1",
                "session_to_clear_chunk_2"
            ]
        }
        rag_service.collection.get.return_value = mock_results
        
        rag_service.clear(session_id)
        
        rag_service.collection.delete.assert_called_once_with(ids=mock_results["ids"])

    def test_clear_queries_with_correct_session_id(self, rag_service):
        """Test that clear() queries ChromaDB with correct session_id"""
        session_id = "session_123"
        
        rag_service.collection.get.return_value = {"ids": []}
        
        rag_service.clear(session_id)
        
        rag_service.collection.get.assert_called_once_with(where={"session_id": session_id})

    def test_clear_does_not_delete_if_no_ids(self, rag_service):
        """Test that clear() doesn't call delete if no IDs found"""
        session_id = "empty_session"
        
        rag_service.collection.get.return_value = {"ids": []}
        
        rag_service.clear(session_id)
        
        rag_service.collection.delete.assert_not_called()

    def test_clear_handles_single_chunk(self, rag_service):
        """Test that clear() works with single chunk"""
        session_id = "single_chunk_session"
        
        mock_results = {"ids": ["single_chunk_session_chunk_0"]}
        rag_service.collection.get.return_value = mock_results
        
        rag_service.clear(session_id)
        
        rag_service.collection.delete.assert_called_once_with(ids=["single_chunk_session_chunk_0"])


class TestRAGServiceIntegration:
    def test_index_and_query_workflow(self, rag_service):
        """Test complete index and query workflow"""
        session_id = "workflow_session"
        text = "Quantum computing is fascinating. " * 50
        question = "What is quantum computing?"
        
        # Index phase
        rag_service.index(session_id, text)
        
        # Query phase
        rag_service.collection.query.return_value = {
            "documents": [["Quantum computing is fascinating."]]
        }
        result = rag_service.query(session_id, question)
        
        assert rag_service.collection.add.called
        assert rag_service.collection.query.called
        assert len(result) > 0

    def test_multiple_sessions_isolation(self, rag_service):
        """Test that different sessions don't interfere with each other"""
        session_1 = "session_1"
        session_2 = "session_2"
        
        rag_service.collection.get.return_value = {"ids": ["session_1_chunk_0"]}
        
        # Clear session 1
        rag_service.clear(session_1)
        
        # Verify only session 1 was cleared
        call_args = rag_service.collection.get.call_args
        assert call_args[1]["where"]["session_id"] == session_1
