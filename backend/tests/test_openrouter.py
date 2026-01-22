import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    print(f"API Key (first 20 chars): {api_key[:20] if api_key else 'None'}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",
                    "messages": [{"role": "user", "content": "Say hello in 5 words"}]
                }
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess! Answer: {result['choices'][0]['message']['content']}")
            else:
                print(f"\nError! Status: {response.status_code}")
                
    except Exception as e:
        print(f"\nException: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
