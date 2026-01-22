import sys
import os

# Add the backend directory to sys.path so we can import app modules
start_path = os.path.dirname(os.path.abspath(__file__)) # .../backend/tests
backend_path = os.path.dirname(start_path)            # .../backend
sys.path.append(backend_path)

try:
    from app.services.rag_engine import rag_engine
    
    print(f"Connected to RAG Engine.")
    collection = rag_engine.collection
    print(f"Collection: {collection.name}")
    print(f"Count: {collection.count()} documents")
    
    # Get all data
    data = collection.get()
    
    print("\n--- Documents ---")
    if data['ids']:
        for i, doc in enumerate(data['documents']):
            meta = data['metadatas'][i]
            doc_id = data['ids'][i]
            print(f"[{i+1}] ID: {doc_id}")
            print(f"    City: {meta.get('city', 'N/A')}")
            print(f"    Content: {doc}")
            print("-" * 40)
    else:
        print("No documents found in the collection.")

except Exception as e:
    print(f"Error accessing RAG engine: {e}")
