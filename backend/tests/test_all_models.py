import httpx
import os
import asyncio
from dotenv import load_dotenv
import time

load_dotenv()

async def test_multiple_models():
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2-7b-instruct:free"
    ]
    
    for model in models:
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Say hello in exactly 3 words"}]
                    }
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']
                    print(f"✅ SUCCESS! Answer: {answer}")
                else:
                    print(f"❌ FAILED! Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:200]}")
        
        await asyncio.sleep(2)  # Wait between requests

if __name__ == "__main__":
    asyncio.run(test_multiple_models())
