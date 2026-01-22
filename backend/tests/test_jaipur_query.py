import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def test_query():
    from app.services.planner import extract_constraints
    
    test_input = "I need to go to Jaipur"
    
    print(f"Testing query: '{test_input}'")
    print("-" * 50)
    
    try:
        result = await extract_constraints(test_input)
        print("SUCCESS!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())
