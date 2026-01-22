import sys
import os
import csv
import datetime

# Add the backend directory to sys.path
start_path = os.path.dirname(os.path.abspath(__file__)) 
backend_path = os.path.dirname(start_path)            
sys.path.append(backend_path)

try:
    from app.services.rag_engine import rag_engine
    
    print(f"Connected to RAG Engine.")
    collection = rag_engine.collection
    count = collection.count()
    print(f"Found {count} documents.")
    
    # Get all data
    data = collection.get()
    
    filename = "vector_db_export.csv"
    output_path = os.path.join(start_path, filename)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'city', 'content']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        if data['ids']:
            for i, doc_id in enumerate(data['ids']):
                meta = data['metadatas'][i]
                content = data['documents'][i]
                
                writer.writerow({
                    'id': doc_id,
                    'city': meta.get('city', 'N/A'),
                    'content': content
                })
        
    print(f"Successfully exported {count} documents to: {output_path}")

except Exception as e:
    print(f"Error exporting database: {e}")
