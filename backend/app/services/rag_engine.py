import chromadb
from chromadb.utils import embedding_functions
import os
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        # Initialize ChromaDB client (using persistent storage for demo)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use simple default embedding function (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="travel_knowledge",
            embedding_function=self.embedding_fn
        )
        
        # Check if empty, if so populate with seed data
        if self.collection.count() == 0:
            self.populate_seed_data()

    def populate_seed_data(self):
        logger.info("Populating RAG with seed data...")
        documents = [
            "Paris is known as the City of Light. It is famous for the Eiffel Tower, Louvre, and cafe culture.",
            "In Paris, standard tipping is not required as service is included, but small change is appreciated.",
            "The best time to visit Tokyo is during cherry blossom season (Sakura) in spring or late autumn.",
            "In Tokyo, do not tip. It can be considered rude. Excellent service is standard.",
            "Delhi offers a mix of Mughal history and modern hustle. Visit Chandni Chowk for food.",
            "For Delhi travel, prefer the Metro for reliable and cool transport relative to traffic.",
            "Jaipur, the Pink City, is famous for Hawa Mahal and Amer Fort.",
            "In India, dress modestly when visiting religious sites. Cover shoulders and knees.",
        ]
        
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = [{"city": "paris"}, {"city": "paris"}, {"city": "tokyo"}, {"city": "tokyo"}, 
                     {"city": "delhi"}, {"city": "delhi"}, {"city": "jaipur"}, {"city": "india"}]
        
        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    def query(self, query_text: str, n_results: int = 2) -> list[str]:
        """
        Retrieves relevant documents for the query.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            return []

# Singleton instance
rag_engine = RAGEngine()
