import chromadb
#
from app.core.config import settings

'''Retrieval Augmented Generation (RAG) service that uses ChromaDB to store and retrieve chunks of text based on a session id.'''

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self.collection = self.client.get_or_create_collection(name="chunks")


    def chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        '''Splits the text into chunks of chunk_size characters'''
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    
    def index(self, session_id: str, text: str) -> None:
        '''Parses the text into chunks and save them in self.collection of ChromaDB'''
        '''Session id will be id in chromadb, text will be the content of the chunk'''

        for i, chunk in enumerate(self.chunk_text(text)):
            self.collection.add(
                ids=[f"{session_id}_chunk_{i}"],
                documents=[chunk],
                metadatas=[{"session_id": session_id}]
            )

    
    def query(self, session_id: str, question: str, top_k: int = 3) -> list[str]:
        '''Queries the collection for the most relevant chunks based on the question'''
        '''Returns a list of the most k relevant chunks'''
        results = self.collection.query(
            query_texts = [question],
            n_results = top_k,
            where = {"session_id": session_id}
        )
        return results['documents'][0] if results['documents'] else []


    def clear(self, session_id: str) -> None:
        '''Clears the collection for a given session'''
        result = self.collection.get(where={"session_id": session_id})
        ids = result['ids']
        if ids:
            self.collection.delete(ids=ids)