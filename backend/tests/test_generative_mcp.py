import asyncio
import os
import sys
import logging

# Add the backend directory to sys.path
start_path = os.path.dirname(os.path.abspath(__file__)) 
backend_path = os.path.dirname(start_path)            
sys.path.append(backend_path)

try:
    from app.mcp.travel_data import search_pois
    from app.mcp.models import POISearchRequest
    from dotenv import load_dotenv
    
    # Load env vars
    load_dotenv(os.path.join(backend_path, ".env"))
    
    # Configure logging to see errors from travel_data.py
    logging.basicConfig(level=logging.INFO)
    
    async def test_generative_search():
        print("Testing Generative City Info...")
        
        # Test Case 1: Hospitals in London
        print("\n--- Test 1: Hospitals in London ---")
        req1 = POISearchRequest(city="London", interests=["Hospitals", "Medical Centres"])
        results1 = await search_pois(req1)
        for p in results1:
            print(f"- {p.name} ({p.category})")
            print(f"  Details: {p.details}")
            
        # Test Case 2: Shopping in Dubai
        print("\n--- Test 2: Shopping in Dubai ---")
        req2 = POISearchRequest(city="Dubai", interests=["Luxury Shopping", "Malls"])
        results2 = await search_pois(req2)
        for p in results2:
            print(f"- {p.name}")
            
    if __name__ == "__main__":
        asyncio.run(test_generative_search())

except Exception as e:
    print(f"Error: {e}")
